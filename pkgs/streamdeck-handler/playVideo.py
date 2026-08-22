import cv2, serial, time, struct, os, sys, numpy

def play(ser: serial.Serial, video_path: str):
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found!")
        sys.exit(1)

    cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened(): 
        sys.exit(1)

    # Get the native FPS of the video
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    # Increased baud rate to 3,000,000
    # ser = serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0', 3000000, timeout=2) #replaced by service
    print("Waiting for ESP32 to boot...")
    time.sleep(2)
    ser.reset_input_buffer()
    print("Starting real-time stream...")

    start_time = time.time()
    frame_idx = 0

    while cap.isOpened():
        elapsed = time.time() - start_time
        expected_frame = int(elapsed * video_fps)

        # 1. RUNNING TOO FAST: Script is ahead of the video framerate. Wait and check again.
        if frame_idx > expected_frame:
            time.sleep(0.001) # Tiny sleep prevents 100% CPU usage
            continue

        # 2. LAGGING: Serial was slow, drop frames to catch up.
        if frame_idx < expected_frame:
            ret = cap.grab() 
            if not ret:
                # LOOP VIDEO
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                start_time = time.time()
                frame_idx = 0
            else:
                frame_idx += 1
            continue
        
        # 3. ON TIME: Grab and retrieve the actual frame pixels
        ret, frame = cap.read()
        if not ret:
            # LOOP VIDEO
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            start_time = time.time()
            frame_idx = 0
            continue
        
        frame_idx += 1
        
        # FIX ASPECT RATIO (Center Crop to 4:3)
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

        # =========================================================
        # ADJUSTABLE IMAGE CONTROLS
        # =========================================================
        CONTRAST   = 1.2   
        BRIGHTNESS = -5    
        SATURATION = 1.5   
        
        # Apply Contrast & Brightness
        frame = cv2.convertScaleAbs(frame, alpha=CONTRAST, beta=BRIGHTNESS)

        # Apply Saturation
        if SATURATION != 1.0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype("float32")
            (h, s, v) = cv2.split(hsv)
            
            s = s * SATURATION
            s = numpy.clip(s, 0, 255)
            
            hsv = cv2.merge([h, s, v]).astype("uint8")
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # ENCODE AND SEND (Quality 40)
        _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
        data = jpeg.tobytes()

        ser.write(struct.pack('>I', len(data)) + data)
        
        # Wait for ACK from ESP32
        ser.read(1)