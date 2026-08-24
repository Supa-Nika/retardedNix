import cv2, time, os
from . import sendJpegOverUdp

def play(video_path: str, quality: int, fps: int, should_stop=lambda: False):
    if not os.path.exists(video_path):
        print(f"[Video] Error: File '{video_path}' not found!")
        return

    cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened(): 
        print(f"[Video] Error: Could not open '{video_path}'")
        return

    # Cap maximum FPS to 20 so ESP32 decoding isn't overwhelmed
    native_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    target_fps = min(native_fps, fps) 
    frame_delay = 1.0 / target_fps
    
    print(f"[Video] Starting UDP stream at {target_fps} FPS...")

    TARGET_W, TARGET_H = 320, 240
    TARGET_RATIO = TARGET_W / TARGET_H

    try:
        while cap.isOpened():
            if should_stop():
                print("[Video] Interrupt received, stopping stream...")
                break

            loop_start = time.time()

            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # Crop to 320x240 aspect ratio
            h, w = frame.shape[:2]
            frame_ratio = w / h

            if frame_ratio > TARGET_RATIO: 
                new_w = int(h * TARGET_RATIO)
                offset = (w - new_w) // 2
                frame = frame[:, offset:offset+new_w]
            elif frame_ratio < TARGET_RATIO: 
                new_h = int(w / TARGET_RATIO)
                offset = (h - new_h) // 2
                frame = frame[offset:offset+new_h, :]

            frame = cv2.resize(frame, (TARGET_W, TARGET_H))

            # Encode with JPEG quality 30 (smaller payload = zero packet drops)
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            sendJpegOverUdp.send(jpeg.tobytes())

            # Maintain constant framerate
            elapsed = time.time() - loop_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        cap.release()