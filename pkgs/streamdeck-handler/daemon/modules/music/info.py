"""Now-playing state: Pear Desktop API poller + cover colours + synced lyrics (LRCLIB)."""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import cv2
import numpy as np

PEAR_URL = os.environ.get("PEAR_API_URL", "http://127.0.0.1:26538").rstrip("/")
POLL_INTERVAL = 1.0
UA = "streamdeck-handler/0.2"
AUTH_ID = "streamdeck-handler"

_token = None


def _get(url, timeout=5, auth=False):
    headers = {"User-Agent": UA}
    if auth and _token:
        headers["Authorization"] = f"Bearer {_token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def _request_token():
    """Pear's API server (auth strategy 'ask at first') shows an approval dialog in the app."""
    global _token
    req = urllib.request.Request(
        f"{PEAR_URL}/auth/{AUTH_ID}", data=b"", method="POST", headers={"User-Agent": UA}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        _token = json.loads(r.read())["accessToken"]
    print("[Music] Got Pear API token")


def _fetch_song():
    for path in ("/api/v1/song", "/api/v1/song-info"):
        try:
            status, body = _get(PEAR_URL + path, auth=True)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
        if status == 204 or not body:
            return None
        return json.loads(body)
    return None


# ---------------------------------------------------------------- lyrics
_LRC = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_lrc(text):
    lines = []
    for raw in text.splitlines():
        stamps = _LRC.findall(raw)
        if not stamps:
            continue
        lyric = _LRC.sub("", raw).strip()
        for m, s in stamps:
            lines.append((int(m) * 60 + float(s), lyric))
    lines.sort(key=lambda x: x[0])
    return lines


def _fetch_lyrics(title, artist, album, duration):
    params = {"track_name": title, "artist_name": artist}
    if album:
        params["album_name"] = album
    if duration:
        params["duration"] = int(round(duration))
    data = None
    try:
        _, body = _get("https://lrclib.net/api/get?" + urllib.parse.urlencode(params), timeout=8)
        data = json.loads(body)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    if not data or not data.get("syncedLyrics"):
        q = urllib.parse.urlencode({"track_name": title, "artist_name": artist})
        _, body = _get("https://lrclib.net/api/search?" + q, timeout=8)
        results = [r for r in json.loads(body) if r.get("syncedLyrics")]
        if duration:
            results.sort(key=lambda r: abs((r.get("duration") or 0) - duration))
        data = results[0] if results else None
    if data and data.get("syncedLyrics"):
        return parse_lrc(data["syncedLyrics"])
    return []


# ---------------------------------------------------------------- colours
def extract_colors(img_bgr):
    """Returns (dominant_rgb, accent_rgb). Dominant favours vivid pixels; accent is a bright version."""
    small = cv2.resize(img_bgr, (32, 32), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)
    bgr = small.reshape(-1, 3).astype(np.float32)
    w = (hsv[:, 1] / 255.0) * (0.25 + hsv[:, 2] / 255.0) + 1e-3
    dom = (bgr * w[:, None]).sum(0) / w.sum()
    h, s, v = cv2.cvtColor(np.uint8([[np.clip(dom, 0, 255)]]), cv2.COLOR_BGR2HSV)[0, 0]
    s2 = int(s) if s < 40 else max(int(s), 140)
    acc = cv2.cvtColor(np.uint8([[[h, s2, 255]]]), cv2.COLOR_HSV2BGR)[0, 0]
    return tuple(int(x) for x in dom[::-1]), tuple(int(x) for x in acc[::-1])


def _decode_cover(data):
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    s = min(h, w)
    y, x = (h - s) // 2, (w - s) // 2
    return cv2.resize(img[y:y + s, x:x + s], (256, 256), interpolation=cv2.INTER_AREA)


def _clean_artist(a):
    return re.sub(r"\s*-\s*Topic$", "", a or "").strip()


# ---------------------------------------------------------------- tracker
class MusicTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._refs = 0
        self._thread = None
        self._stop = threading.Event()
        self._elapsed = 0.0
        self._stamp = time.monotonic()
        self._paused = True
        self._key = None
        self._last_auth = 0.0
        self._last_api = None
        self.track = None
        self.connected = False

    # -- lifecycle (ref-counted so the poller only runs while an overlay is active)
    def acquire(self):
        with self._lock:
            self._refs += 1
            if self._thread is None:
                self._stop.clear()
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()

    def release(self):
        with self._lock:
            self._refs = max(0, self._refs - 1)
            if self._refs == 0 and self._thread is not None:
                self._stop.set()
                self._thread = None

    # -- polling
    def _run(self):
        while not self._stop.is_set():
            try:
                song = _fetch_song()
                self.connected = True
                if song:
                    self._ingest(song)
                else:
                    self.track = None
                    self._key = None
            except urllib.error.HTTPError as e:
                self.connected = e.code != 0
                if e.code in (401, 403) and time.monotonic() - self._last_auth > 30:
                    self._last_auth = time.monotonic()
                    try:
                        _request_token()
                    except Exception as ex:
                        print(f"[Music] Auth failed: {ex}")
            except Exception:
                self.connected = False
            self._stop.wait(POLL_INTERVAL)

    def _ingest(self, s):
        title = s.get("title") or "Unknown"
        artist = _clean_artist(s.get("artist"))
        key = s.get("videoId") or f"{title}|{artist}"
        duration = float(s.get("songDuration") or 0)
        elapsed = float(s.get("elapsedSeconds") or 0)
        paused = bool(s.get("isPaused"))

        if key != self._key:
            self._key = key
            self._last_api = None
            track = {
                "key": key, "rev": 0, "title": title, "artist": artist,
                "album": s.get("album") or "", "duration": duration,
                "cover": None, "color": (60, 60, 90), "accent": (255, 255, 255),
                "lyrics": [], "lyric_times": [], "lyrics_state": "loading",
            }
            self.track = track
            with self._lock:
                self._elapsed, self._stamp = elapsed, time.monotonic()
            threading.Thread(target=self._load_cover, args=(track, s.get("imageSrc")), daemon=True).start()
            threading.Thread(target=self._load_lyrics, args=(track,), daemon=True).start()

        # Keep our own clock between polls. Only resync when the API value actually changed
        # and disagrees with us (seek / drift) - a stale or coarse elapsedSeconds is ignored.
        with self._lock:
            cur = self._elapsed + (0 if self._paused else time.monotonic() - self._stamp)
            api_changed = elapsed != self._last_api
            self._last_api = elapsed
            if paused:
                self._elapsed, self._stamp = elapsed, time.monotonic()
            elif self._paused:  # just started/resumed
                self._elapsed, self._stamp = elapsed + 0.4, time.monotonic()
            elif api_changed and not (elapsed - 0.25 <= cur <= elapsed + 1.25):
                self._elapsed, self._stamp = elapsed + 0.4, time.monotonic()
            self._paused = paused

    def _load_cover(self, track, url):
        if not url:
            return
        try:
            _, data = _get(url, timeout=8)
            img = _decode_cover(data)
            if img is None:
                return
            track["cover"] = img
            track["color"], track["accent"] = extract_colors(img)
            track["rev"] += 1
        except Exception as e:
            print(f"[Music] Cover fetch failed: {e}")

    def _load_lyrics(self, track):
        try:
            lines = _fetch_lyrics(track["title"], track["artist"], track["album"], track["duration"])
            track["lyrics"] = lines
            track["lyric_times"] = [t for t, _ in lines]
            track["lyrics_state"] = "synced" if lines else "none"
        except Exception as e:
            print(f"[Music] Lyrics fetch failed: {e}")
            track["lyrics_state"] = "none"
        track["rev"] += 1

    def snapshot(self):
        with self._lock:
            pos = self._elapsed + (0 if self._paused else time.monotonic() - self._stamp)
            paused = self._paused
        track = self.track
        if track and track["duration"]:
            pos = min(pos, track["duration"])
        return track, pos, paused, self.connected


tracker = MusicTracker()