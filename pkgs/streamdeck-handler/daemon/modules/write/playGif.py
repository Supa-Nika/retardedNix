import cv2, os, time, numpy as np
from PIL import Image, ImageSequence
from . import sendJpegOverUdp

def play(gif_path: str, quality: int, should_stop=lambda: False):
    if not os.path.exists(gif_path):
        print(f"[GIF] Error: File '{gif_path}' not found!")
        return

    try:
        pil_gif = Image.open(gif_path)
    except Exception as e:
        print(f"[GIF] Error opening GIF: {e}")
        return

    TARGET_W, TARGET_H = 320, 240
    TARGET_RATIO = TARGET_W / TARGET_H
    CONTRAST   = 1.2   
    BRIGHTNESS = -5    
    SATURATION = 1.5   

    frames = []
    print("[GIF] Pre-rendering frames...")

    # Canvas maintains background state across GIF disposal steps
    canvas = Image.new("RGBA", pil_gif.size)

    for frame in ImageSequence.Iterator(pil_gif):
        raw_duration = frame.info.get('duration', 100) or 100
        duration = max(raw_duration / 1000.0, 0.02)

        frame_rgba = frame.convert("RGBA")
        canvas = Image.new("RGBA", pil_gif.size, (0, 0, 0, 0))
        canvas.paste(frame_rgba, (0, 0), frame_rgba)

        # Keep the alpha mask around — we'll use it to force true black later
        alpha = np.array(canvas.split()[-1])

        cv_frame = cv2.cvtColor(np.array(canvas.convert('RGB')), cv2.COLOR_RGB2BGR)

        # Center crop to 4:3 target aspect ratio
        h, w = cv_frame.shape[:2]
        frame_ratio = w / h

        if frame_ratio > TARGET_RATIO:
            new_w = int(h * TARGET_RATIO)
            offset = (w - new_w) // 2
            cv_frame = cv_frame[:, offset:offset+new_w]
            alpha = alpha[:, offset:offset+new_w]
        elif frame_ratio < TARGET_RATIO:
            new_h = int(w / TARGET_RATIO)
            offset = (h - new_h) // 2
            cv_frame = cv_frame[offset:offset+new_h, :]
            alpha = alpha[offset:offset+new_h, :]

        cv_frame = cv2.resize(cv_frame, (TARGET_W, TARGET_H))
        alpha = cv2.resize(alpha, (TARGET_W, TARGET_H), interpolation=cv2.INTER_NEAREST)

        # Contrast & Brightness
        cv_frame = cv2.convertScaleAbs(cv_frame, alpha=CONTRAST, beta=BRIGHTNESS)

        # Saturation adjustment using convertScaleAbs to prevent type errors
        if SATURATION != 1.0:
            hsv = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2HSV)
            h_chan, s_chan, v_chan = cv2.split(hsv)
            s_chan = cv2.convertScaleAbs(s_chan, alpha=SATURATION)
            hsv = cv2.merge([h_chan, s_chan, v_chan])
            cv_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # Force fully-transparent pixels to true black, overriding any
        # rounding drift from the contrast/saturation math above.
        cv_frame[alpha == 0] = (0, 0, 0)

        # Encode frame to JPEG
        _, jpeg = cv2.imencode('.jpg', cv_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        frames.append((jpeg.tobytes(), duration))

    pil_gif.close()

    if not frames:
        print("[GIF] Error: No valid frames found in GIF!")
        return

    print(f"[GIF] Loaded {len(frames)} frames. Starting UDP playback loop...")

    # Low-CPU Playback Loop using monotonic clock
    while not should_stop():
        for jpeg_bytes, duration in frames:
            if should_stop():
                return

            frame_start = time.monotonic()
            sendJpegOverUdp.send(jpeg_bytes)

            elapsed = time.monotonic() - frame_start
            sleep_time = duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)