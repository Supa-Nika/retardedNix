import cv2, os, time, numpy
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

    for frame in ImageSequence.Iterator(pil_gif):
        # 1. Get duration (convert ms to seconds, floor at 20ms / 50 FPS max limit)
        raw_duration = frame.info.get('duration', 100) or 100
        duration = max(raw_duration / 1000.0, 0.02)

        # 2. Convert PIL (RGB) to OpenCV (BGR)
        cv_frame = cv2.cvtColor(numpy.array(frame.convert('RGB')), cv2.COLOR_RGB2BGR)
        
        # 3. Center crop to 4:3 target aspect ratio
        h, w = cv_frame.shape[:2]
        frame_ratio = w / h

        if frame_ratio > TARGET_RATIO: 
            new_w = int(h * TARGET_RATIO)
            offset = (w - new_w) // 2
            cv_frame = cv_frame[:, offset:offset+new_w]
        elif frame_ratio < TARGET_RATIO: 
            new_h = int(w / TARGET_RATIO)
            offset = (h - new_h) // 2
            cv_frame = cv_frame[offset:offset+new_h, :]

        cv_frame = cv2.resize(cv_frame, (TARGET_W, TARGET_H))

        # 4. Fast Contrast & Brightness
        cv_frame = cv2.convertScaleAbs(cv_frame, alpha=CONTRAST, beta=BRIGHTNESS)

        # 5. Fast Saturation (In-place C++ uint8 math)
        if SATURATION != 1.0:
            hsv = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2HSV)
            h_chan, s_chan, v_chan = cv2.split(hsv)
            s_chan = cv2.multiply(s_chan, SATURATION)
            hsv = cv2.merge([h_chan, s_chan, v_chan])
            cv_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # 6. Encode frame to JPEG (Quality 55 balances visual fidelity & small UDP payloads)
        _, jpeg = cv2.imencode('.jpg', cv_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        frames.append((jpeg.tobytes(), duration))

    pil_gif.close()

    if not frames:
        print("[GIF] Error: No valid frames found in GIF!")
        return

    print(f"[GIF] Loaded {len(frames)} frames. Starting UDP playback loop...")

    # 7. Low-CPU Playback Loop
    while not should_stop():
        for jpeg_bytes, duration in frames:
            if should_stop():
                return

            frame_start = time.time()
            sendJpegOverUdp.send(jpeg_bytes)

            elapsed = time.time() - frame_start
            sleep_time = duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)