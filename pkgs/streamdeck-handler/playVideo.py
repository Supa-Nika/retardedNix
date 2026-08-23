import cv2, serial, time, struct, os, sys, numpy

def play(ser: serial.Serial, video_path: str, should_stop=lambda: False):
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found!")
        return

    cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened(): 
        print(f"Error: Could not open video '{video_path}'")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    ser.reset_input_buffer()
    print("Starting real-time video stream...")

    start_time = time.time()
    frame_idx = 0

    try:
        while cap.isOpened():
            # Check for daemon state interrupt
            if should_stop():
                print("[Video] Interrupt received, stopping stream...")
                break

            elapsed = time.time() - start_time
            expected_frame = int(elapsed * video_fps)

            # 1. RUNNING TOO FAST: Script is ahead of framerate
            if frame_idx > expected_frame:
                time.sleep(0.001)
                continue

            # 2. LAGGING: Drop frames to catch up
            if frame_idx < expected_frame:
                ret = cap.grab() 
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    start_time = time.time()
                    frame_idx = 0
                else:
                    frame_idx += 1
                continue
            
            # 3. ON TIME: Read actual frame
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                start_time = time.time()
                frame_idx = 0
                continue
            
            frame_idx += 1
            
            # Center Crop to 4:3
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
            
            # Encode and transmit over serial
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
            data = jpeg.tobytes()

            ser.write(struct.pack('>I', len(data)) + data)
            ser.read(1) # Wait for ACK byte

    finally:
        cap.release()