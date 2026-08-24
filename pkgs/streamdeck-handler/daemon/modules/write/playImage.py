import cv2, os, time, numpy
from . import sendJpegOverUdp

def play(image_path: str, quality: int, should_stop=lambda: False):
    if not os.path.exists(image_path):
        print(f"[Image] Error: Image file '{image_path}' not found!")
        return

    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[Image] Error loading image '{image_path}'")
        return

    TARGET_W, TARGET_H = 320, 240
    TARGET_RATIO = TARGET_W / TARGET_H

    # 1. Center crop to 4:3 ratio
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

    # Controls
    CONTRAST   = 1.2   
    BRIGHTNESS = -5    
    SATURATION = 1.5   
    
    # 2. Fast Contrast & Brightness
    frame = cv2.convertScaleAbs(frame, alpha=CONTRAST, beta=BRIGHTNESS)

    # 3. Fast Saturation (In-place C++ uint8 math)
    if SATURATION != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h_chan, s_chan, v_chan = cv2.split(hsv)
        s_chan = cv2.multiply(s_chan, SATURATION)
        hsv = cv2.merge([h_chan, s_chan, v_chan])
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    # 4. Encode to higher-quality JPEG (Quality 75 for still images)
    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    data = jpeg.tobytes()

    print("[Image] Displaying static image over UDP...")

    # 5. Hold state & re-transmit every 1s so display recovers from packet drops
    while not should_stop():
        sendJpegOverUdp.send(data)
        time.sleep(1.0)