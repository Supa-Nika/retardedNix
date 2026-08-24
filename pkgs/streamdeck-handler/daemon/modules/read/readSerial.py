import threading
import serial
import subprocess

KEYCODES = {
    '1': 164,  # KEY_PLAYPAUSE
    '2': 163,  # KEY_NEXTSONG
    '3': 165,  # KEY_PREVIOUSSONG
    '4': 166,  # KEY_STOPCD
    '5': 113,  # KEY_MUTE
    '6': 114,  # KEY_VOLUMEDOWN
    '7': 115,  # KEY_VOLUMEUP
    '8': 208,  # KEY_FASTFORWARD
}

def handle_key_press(key: str):
    print(f"[Keypad] Pressed: '{key}'", flush=True)
    if key in KEYCODES:
        code = KEYCODES[key]
        subprocess.run(["ydotool", "key", f"{code}:1", f"{code}:0"], check=False)

def read_serial(ser: serial.Serial):
    while ser and ser.is_open:
        try:
            raw_line = ser.readline()
        except Exception as e:
            print(f"[Serial Read] Error: {e}")
            break

        if not raw_line:
            continue

        # Decode bytes to str and strip trailing whitespace (\r\n)
        line = raw_line.decode('utf-8', errors='ignore').strip()

        # Check for ESP32 keypad format "K:<key>"
        if not line.startswith("K:"):
            # print(f"[Serial] {line}")
            continue

        key = line[2:]  # Extract key character after 'K:'
        try:
            handle_key_press(key)
        except Exception as e:
            print(f"[Keypad] handle_key_press failed: {e}")