"""Live view of what the music overlay sees.  Run: streamdeck-music-debug"""
import bisect
import json
import time

from . import info
from .info import tracker


def main():
    print(f"Pear API: {info.PEAR_URL}   (Ctrl+C to quit)")
    tracker.acquire()
    try:
        while True:
            try:
                raw = info._fetch_song()
                api = "no song" if raw is None else f"elapsed={raw.get('elapsedSeconds')} paused={raw.get('isPaused')} dur={raw.get('songDuration')}"
            except Exception as e:
                api = f"API ERROR: {e!r}"
            track, pos, paused, conn = tracker.snapshot()
            if track:
                times = track["lyric_times"]
                idx = bisect.bisect_right(times, pos + 0.25) - 1 if times else -2
                line = track["lyrics"][idx][1] if 0 <= idx < len(track["lyrics"]) else ""
                lyr = f"lyrics={track['lyrics_state']}({len(times)}) idx={idx} '{line[:40]}'"
                print(f"{api} | pos={pos:6.1f} | {track['title'][:30]} | {lyr}", flush=True)
            else:
                print(f"{api} | connected={conn} | no track", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()