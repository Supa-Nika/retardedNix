import cv2, serial, time, struct, os, sys, numpy

def play(ser: serial.Serial, image_path: str):
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found!")
        sys.exit(1)

    # Read static image
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not decode image file.")
        sys.exit(1)

    # Open serial at 3,000,000 baud
    # ser = serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0', 3000000, timeout=2) #replaced by service
    print("Waiting for ESP32 to boot...")
    time.sleep(2)
    ser.reset_input_buffer()
    print("Sending static image stream...")

    # 1. FIX ASPECT RATIO (Center Crop to 4:3)
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
    # ADJUSTABLE IMAGE CONTROLS (Tweak these for static images)
    # =========================================================
    CONTRAST   = 1.2   
    BRIGHTNESS = -5    
    SATURATION = 1.5   
    # =========================================================

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

    # ENCODE IMAGE (Quality 70 for higher static image fidelity)
    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    data = jpeg.tobytes()
    payload = struct.pack('>I', len(data)) + data

    # Continuously push frame to maintain screen display & handle reboot reconnects
    try:
        while True:
            ser.write(payload)
            ser.read(1) # Wait for ACK byte
            time.sleep(0.1) # 10 FPS rate-limit is plenty for a static image
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    # Pass image filename as command line arg or update 'image.jpg' below
    img_file = sys.argv[1] if len(sys.argv) > 1 else 'image.jpg'
    display_image(img_file)