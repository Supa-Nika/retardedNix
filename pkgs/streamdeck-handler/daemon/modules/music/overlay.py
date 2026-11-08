"""Now-playing renderer for the 320x240 display.

mode="overlay": translucent tinted panel along the bottom of an existing frame (image/gif/video/yt).
mode="full":    standalone screen with a blurred, beat-reactive background built from the cover art.
"""
import bisect
import math
import os
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .audio import analyzer
from .info import tracker

W, H = 320, 240

# ---- tweakables ---------------------------------------------------------
BACKDROP_ALPHA = 0.55   # strength of the cover-coloured backdrop in overlay mode
BACKDROP_DARKEN = 0.40  # how much the cover colour is darkened for the backdrop
LYRIC_LEAD = 0.25       # show a lyric line slightly early (display latency)
OV_Y0 = 120             # overlay panel top (px); panel height = H - OV_Y0
OV_H = H - OV_Y0
RAMP = 18               # soft fade-in at the top edge of the panel

# ---- fonts --------------------------------------------------------------
_REG = [os.environ.get("STREAMDECK_FONT", ""),
        "/run/current-system/sw/share/X11/fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans.ttf"]
_BOLD = [os.environ.get("STREAMDECK_FONT_BOLD", ""),
         "/run/current-system/sw/share/X11/fonts/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
_fonts = {}


def _font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        f = None
        for p in (_BOLD if bold else _REG):
            if not p:
                continue
            try:
                f = ImageFont.truetype(p, size)
                break
            except OSError:
                continue
        if f is None:
            try:
                f = ImageFont.load_default(size)
            except TypeError:
                f = ImageFont.load_default()
        _fonts[key] = f
    return _fonts[key]


def _fit(draw, text, max_w, size, min_size, bold=False):
    """Shrink font until text fits, then ellipsize."""
    s = size
    while s >= min_size:
        f = _font(s, bold)
        if draw.textlength(text, font=f) <= max_w:
            return f, text
        s -= 1
    f = _font(min_size, bold)
    while len(text) > 1 and draw.textlength(text + "…", font=f) > max_w:
        text = text[:-1]
    return f, text.rstrip() + "…"


def _fmt(t):
    t = int(max(t, 0))
    return f"{t // 60}:{t % 60:02d}"


class _Canvas:
    """RGB image + coverage mask so text/cover can be composited over any frame."""

    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), bg)
        self.mask = Image.new("L", (w, h), 0)
        self.d = ImageDraw.Draw(self.img)
        self.m = ImageDraw.Draw(self.mask)

    def text(self, xy, s, font, fill, anchor="lt"):
        if not s:
            return
        self.d.text(xy, s, font=font, fill=fill, anchor=anchor)
        self.m.text(xy, s, font=font, fill=255, anchor=anchor)

    def fit_text(self, xy, s, max_w, size, min_size, fill, anchor="lt", bold=False):
        f, s = _fit(self.d, s, max_w, size, min_size, bold)
        self.text(xy, s, f, fill, anchor)

    def cover(self, cover_bgr, xy, size, radius):
        rgb = cv2.cvtColor(cv2.resize(cover_bgr, (size, size), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        rm = Image.new("L", (size, size), 0)
        ImageDraw.Draw(rm).rounded_rectangle((0, 0, size - 1, size - 1), radius, fill=255)
        self.img.paste(pil, xy, rm)
        self.mask.paste(255, (xy[0], xy[1], xy[0] + size, xy[1] + size), rm)

    def finish(self, backdrop_alpha):
        """-> (premultiplied BGR float32, 1-alpha float32) for  out = frame*inv + pm."""
        m = np.asarray(self.mask, dtype=np.float32) / 255.0
        bgr = np.asarray(self.img)[:, :, ::-1].astype(np.float32)
        if backdrop_alpha <= 0.0:
            # Canvas background is black, so the image is already premultiplied by coverage
            return bgr, (1.0 - m)[..., None]
        a = backdrop_alpha + (1.0 - backdrop_alpha) * m
        return bgr * a[..., None], (1.0 - a)[..., None]


def _ramp_alpha():
    a = np.full((OV_H, W), BACKDROP_ALPHA, dtype=np.float32)
    t = np.linspace(0, 1, RAMP, dtype=np.float32)
    a[:RAMP] = (BACKDROP_ALPHA * (t * t * (3 - 2 * t)))[:, None]
    return a


_RAMP = _ramp_alpha()


def _draw_bars(frame, levels, x0, x1, base_y, max_h, color_bgr):
    n = len(levels)
    bw = (x1 - x0) / n
    cap = (255, 255, 255)
    for i, l in enumerate(levels):
        h = int(max(1, float(l) * max_h))
        xa = int(x0 + i * bw) + 1
        xb = max(xa, int(x0 + (i + 1) * bw) - 2)
        cv2.rectangle(frame, (xa, base_y - h), (xb, base_y), color_bgr, -1)
        if h > 3:
            cv2.rectangle(frame, (xa, base_y - h), (xb, base_y - h + 1), cap, -1)


def _draw_progress(frame, ratio, x0, x1, y0, y1, color_bgr):
    cv2.rectangle(frame, (x0, y0), (x1, y1), (70, 70, 70), -1)
    xe = x0 + int((x1 - x0) * min(max(ratio, 0.0), 1.0))
    if xe > x0:
        cv2.rectangle(frame, (x0, y0), (xe, y1), color_bgr, -1)


class MusicOverlay:
    def __init__(self, mode="overlay"):
        assert mode in ("overlay", "full")
        self.mode = mode
        self._sig = None
        self._layer = None
        self._inv = None
        self._bg_sig = None
        self._closed = False
        tracker.acquire()
        analyzer.acquire()

    def close(self):
        if not self._closed:
            self._closed = True
            tracker.release()
            analyzer.release()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------ public
    def render(self, base=None):
        """Returns a new BGR 320x240 frame with the overlay applied."""
        track, pos, paused, connected = tracker.snapshot()
        accent = tuple(track["accent"][::-1]) if track else (255, 255, 255)
        levels = analyzer.levels

        if self.mode == "full":
            frame = self._render_bg(track, analyzer.pulse, analyzer.energy)
        else:
            frame = base.copy()

        self._refresh_layer(track, pos, connected)

        if self.mode == "full":
            frame = (frame.astype(np.float32) * self._inv + self._layer).astype(np.uint8)
            _draw_bars(frame, levels, 14, 306, 216, 32, accent)
            ratio = pos / track["duration"] if track and track["duration"] else 0
            _draw_progress(frame, ratio, 14, 305, 236, 238, accent)
        else:
            reg = frame[OV_Y0:].astype(np.float32)
            frame[OV_Y0:] = (reg * self._inv + self._layer).astype(np.uint8)
            _draw_bars(frame, levels, 10, 310, OV_Y0 + 100, 22, accent)
            ratio = pos / track["duration"] if track and track["duration"] else 0
            _draw_progress(frame, ratio, 10, 309, 236, 238, accent)
        return frame

    # ------------------------------------------------------------ layers
    @staticmethod
    def _lyric_idx(track, pos):
        times = track["lyric_times"] if track else []
        return bisect.bisect_right(times, pos + LYRIC_LEAD) - 1 if times else -2

    def _refresh_layer(self, track, pos, connected):
        idx = self._lyric_idx(track, pos)
        sig = (track["key"] if track else None, track["rev"] if track else 0, idx, int(pos), connected)
        if sig == self._sig:
            return
        self._sig = sig
        if self.mode == "full":
            self._layer, self._inv = self._build_full(track, pos, idx, connected)
        else:
            self._layer, self._inv = self._build_overlay(track, pos, idx, connected)

    @staticmethod
    def _line(track, i):
        lines = track["lyrics"]
        if 0 <= i < len(lines):
            return lines[i][1] or "♪"
        return ""

    def _headline(self, track, connected):
        if track:
            return track["title"], track["artist"]
        if not connected:
            return "Pear Desktop not reachable", "Enable the API Server plugin"
        return "Nothing playing", ""

    def _build_overlay(self, track, pos, idx, connected):
        tint = tuple(int(c * BACKDROP_DARKEN) for c in (track["color"] if track else (40, 40, 60)))
        c = _Canvas(W, OV_H, tint)
        title, artist = self._headline(track, connected)
        x = 10
        if track and track["cover"] is not None:
            c.cover(track["cover"], (10, 8), 44, 6)
            x = 62
        c.fit_text((x, 8), title, W - x - 10, 14, 10, (255, 255, 255), bold=True)
        c.fit_text((x, 27), artist, W - x - 10, 11, 9, (215, 215, 215))

        if track:
            if track["lyrics_state"] == "loading":
                cur = "…"
            elif idx == -1:
                cur = "♪"
            else:
                cur = self._line(track, idx)
            c.fit_text((W // 2, 66), cur, 300, 14, 9, (255, 255, 255), anchor="mm")
            f = _font(10)
            c.text((10, 103), _fmt(pos), f, (225, 225, 225))
            c.text((310, 103), _fmt(track["duration"]), f, (225, 225, 225), anchor="rt")

        # backdrop alpha with soft top edge, plus text/cover coverage
        m = np.asarray(c.mask, dtype=np.float32) / 255.0
        a = _RAMP + (1.0 - _RAMP) * m
        bgr = np.asarray(c.img)[:, :, ::-1].astype(np.float32)
        return bgr * a[..., None], (1.0 - a)[..., None]

    def _build_full(self, track, pos, idx, connected):
        c = _Canvas(W, H, (0, 0, 0))
        title, artist = self._headline(track, connected)
        if track and track["cover"] is not None:
            c.cover(track["cover"], (14, 14), 96, 10)
        c.fit_text((122, 16), title, 188, 16, 11, (255, 255, 255), bold=True)
        c.fit_text((122, 40), artist, 188, 12, 9, (225, 225, 225))
        if track:
            c.fit_text((122, 58), track["album"], 188, 10, 8, (190, 190, 190))

            state = track["lyrics_state"]
            if state == "loading":
                c.text((W // 2, 148), "…", _font(17), (255, 255, 255), anchor="mm")
            elif state == "none":
                c.text((W // 2, 148), "No synced lyrics", _font(12), (180, 180, 180), anchor="mm")
            else:
                cur = "♪" if idx == -1 else self._line(track, idx)
                c.fit_text((W // 2, 124), self._line(track, idx - 1), 296, 11, 8, (205, 205, 205), anchor="mm")
                c.fit_text((W // 2, 148), cur, 296, 17, 10, (255, 255, 255), anchor="mm", bold=True)
                c.fit_text((W // 2, 174), self._line(track, idx + 1), 296, 12, 8, (215, 215, 215), anchor="mm")

            f = _font(10)
            c.text((14, 223), _fmt(pos), f, (225, 225, 225))
            c.text((306, 223), _fmt(track["duration"]), f, (225, 225, 225), anchor="rt")
        return c.finish(0.0)

    # ------------------------------------------------------------ full-mode background
    def _prepare_bg(self, track):
        color = track["color"] if track else (60, 60, 90)
        accent = track["accent"] if track else (200, 200, 255)
        cover = track["cover"] if track else None

        if cover is not None:
            small = cv2.resize(cover, (64, 48), interpolation=cv2.INTER_AREA)
            small = cv2.GaussianBlur(small, (0, 0), 4)
            # blurring averages colours toward grey, so push saturation back up
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * 1.5, 0, 255)
            small = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) * 0.5
        else:
            bg = np.zeros((H, W, 3), np.float32) + np.array(color[::-1], np.float32) * 0.3

        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        bg *= np.clip(1.15 - 0.45 * d, 0.45, 1.0)[..., None]
        self._bg = bg

        g1 = np.exp(-(((xx - 62) ** 2 + (yy - 62) ** 2) / (2 * 70.0 ** 2)))
        self._g1 = g1[..., None] * np.array(accent[::-1], np.float32) * 0.45

        BW, BH = W + 160, H + 120
        y2, x2 = np.mgrid[0:BH, 0:BW].astype(np.float32)
        g2 = np.exp(-(((x2 - BW / 2) ** 2 + (y2 - BH / 2) ** 2) / (2 * 90.0 ** 2)))
        self._g2 = g2[..., None] * np.array(color[::-1], np.float32)

    def _render_bg(self, track, pulse, energy):
        sig = (track["key"], track["rev"]) if track else None
        if sig != self._bg_sig or not hasattr(self, "_bg"):
            self._bg_sig = sig
            self._prepare_bg(track)
        t = time.monotonic()
        ox = int(80 + 70 * math.sin(t * 0.4))
        oy = int(60 + 50 * math.cos(t * 0.31))
        # glows are additive but small: keep the sum well below 255 so colours never wash out
        out = (self._bg * (0.9 + 0.2 * pulse)
               + self._g1 * (0.2 + 0.8 * pulse)
               + self._g2[oy:oy + H, ox:ox + W] * (0.10 + 0.30 * energy))
        return np.clip(out, 0, 255).astype(np.uint8)