import cv2, serial, time, struct, os, sys, numpy
from PIL import Image, ImageSequence

def play(ser: serial.Serial, gif_path: str, should_stop=lambda: False):
    if not os.path.exists(gif_path):
        print(f"Error: GIF file '{gif_path}' not found!")
        return

    try:
        pil_gif = Image.open(gif_path)
    except Exception as e:
        print(f"Error opening GIF: {e}")
        return

    frames = []
    for frame in ImageSequence.Iterator(pil_gif):
        duration = frame.info.get('duration', 100) / 1000.0
        cv_frame = cv2.cvtColor(numpy.array(frame.convert('RGB')), cv2.COLOR_RGB2BGR)
        
        # Center crop 4:3
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
        cv_frame = cv2.convertScaleAbs(cv_frame, alpha=1.2, beta=-5)

        # Saturation adjustment
        hsv = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2HSV).astype("float32")
        (h_chan, s_chan, v_chan) = cv2.split(hsv)
        s_chan = numpy.clip(s_chan * 1.5, 0, 255)
        hsv = cv2.merge([h_chan, s_chan, v_chan]).astype("uint8")
        cv_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        _, jpeg = cv2.imencode('.jpg', cv_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        data = jpeg.tobytes()
        payload = struct.pack('>I', len(data)) + data

        frames.append((payload, duration))

    pil_gif.close()
    ser.reset_input_buffer()

    # Play until interrupted by state change or port disconnect
    while not should_stop():
        for payload, duration in frames:
            if should_stop():
                return  # Instantly yield back to main daemon loop

            frame_start = time.time()
            ser.write(payload)
            ser.read(1) # Wait for ACK byte

            elapsed = time.time() - frame_start
            sleep_time = duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)