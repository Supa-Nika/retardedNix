import cv2, serial, time, struct, os, sys, numpy

def play(ser: serial.Serial, image_path: str, should_stop=lambda: False):
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found!")
        return

    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error loading image '{image_path}'")
        return

    # Center crop to 4:3
    h, w = frame.shape[:2]
    target_ratio = 320 / 240
    frame_ratio = w / h

    if frame_ratio > target_ratio: 
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        frame = frame[:, offset:offset+new_w]
    elif frame_ratio < target_ratio: 
        new_h = int(w / target_ratio)
        offset = (h - new_h) // 2
        frame = frame[offset:offset+new_h, :]

    frame = cv2.resize(frame, (320, 240))

    # Controls
    CONTRAST   = 1.2   
    BRIGHTNESS = -5    
    SATURATION = 1.5   
    
    frame = cv2.convertScaleAbs(frame, alpha=CONTRAST, beta=BRIGHTNESS)

    if SATURATION != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype("float32")
        (h, s, v) = cv2.split(hsv)
        s = numpy.clip(s * SATURATION, 0, 255)
        hsv = cv2.merge([h, s, v]).astype("uint8")
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    # Encode and send ONCE
    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    data = jpeg.tobytes()

    ser.reset_input_buffer()
    ser.write(struct.pack('>I', len(data)) + data)
    ser.read(1) # ACK byte

    # Hold state and check for CLI cancellation
    while not should_stop():
        time.sleep(0.1)