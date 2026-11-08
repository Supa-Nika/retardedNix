import time

import cv2

from . import sendJpegOverUdp


def play(overlay, quality: int, fps: int, should_stop=lambda: False):
    """Music-only screen: renders the full now-playing view (blurred reactive background)."""
    delay = 1.0 / max(fps, 1)
    print(f"[Music] Streaming now-playing screen at {fps} FPS...")

    while not should_stop():
        t0 = time.monotonic()
        frame = overlay.render(None)
        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        sendJpegOverUdp.send(jpeg.tobytes())

        sleep_time = delay - (time.monotonic() - t0)
        if sleep_time > 0:
            time.sleep(sleep_time)
