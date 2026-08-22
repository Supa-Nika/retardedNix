import cv2, serial, time, struct, os, sys, numpy
from PIL import Image, ImageSequence

def play(ser: serial.Serial, gif_path: str):
    if not os.path.exists(gif_path):
        print(f"Error: GIF file '{gif_path}' not found!")
        sys.exit(1)

    # Load GIF using Pillow to extract frame delays
    try:
        pil_gif = Image.open(gif_path)
    except Exception as e:
        print(f"Error opening GIF: {e}")
        sys.exit(1)

    # Process and cache all frames in memory with their respective delays
    print("Processing GIF frames...")
    frames = []
    
    for frame in ImageSequence.Iterator(pil_gif):
        # Extract frame delay in seconds (default to 100ms if not specified in metadata)
        duration = frame.info.get('duration', 100) / 1000.0
        
        # Convert PIL Image (RGB) to OpenCV format (BGR)
        cv_frame = cv2.cvtColor(numpy.array(frame.convert('RGB')), cv2.COLOR_RGB2BGR)
        
        # Center crop to 4:3 aspect ratio
        h, w = cv_frame.shape[:2]
        target_ratio = 320 / 240
        frame_ratio = w / h

        if frame_ratio > target_ratio: 
            new_w = int(h * target_ratio)
            offset = (w - new_w) // 2
            cv_frame = cv_frame[:, offset:offset+new_w]
        elif frame_ratio < target_ratio: 
            new_h = int(w / target_ratio)
            offset = (h - new_h) // 2
            cv_frame = cv_frame[offset:offset+new_h, :]

        cv_frame = cv2.resize(cv_frame, (320, 240))

        # =========================================================
        # ADJUSTABLE IMAGE CONTROLS
        # =========================================================
        CONTRAST   = 1.2   
        BRIGHTNESS = -5    
        SATURATION = 1.5   

        # Apply Contrast & Brightness
        cv_frame = cv2.convertScaleAbs(cv_frame, alpha=CONTRAST, beta=BRIGHTNESS)

        # Apply Saturation
        if SATURATION != 1.0:
            hsv = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2HSV).astype("float32")
            (h_chan, s_chan, v_chan) = cv2.split(hsv)
            s_chan = numpy.clip(s_chan * SATURATION, 0, 255)
            hsv = cv2.merge([h_chan, s_chan, v_chan]).astype("uint8")
            cv_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Encode to JPEG bytes
        _, jpeg = cv2.imencode('.jpg', cv_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        data = jpeg.tobytes()
        payload = struct.pack('>I', len(data)) + data

        frames.append((payload, duration))

    pil_gif.close()
    print(f"Loaded {len(frames)} frames. Connecting to ESP32...")

    # Open serial at 3,000,000 baud
    # ser = serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0', 3000000, timeout=2) #replaced by service
    time.sleep(2)
    ser.reset_input_buffer()
    print("Starting GIF animation loop...")

    try:
        while True:
            for payload, duration in frames:
                frame_start = time.time()

                # Send frame data
                ser.write(payload)
                ser.read(1) # Wait for ACK byte from ESP32

                # Enforce the GIF frame delay
                elapsed = time.time() - frame_start
                sleep_time = duration - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nAnimation stopped.")

if __name__ == "__main__":
    gif_file = sys.argv[1] if len(sys.argv) > 1 else 'animation.gif'
    play_gif(gif_file)