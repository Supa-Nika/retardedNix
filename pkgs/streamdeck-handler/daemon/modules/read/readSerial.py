import threading
import serial
import subprocess

KEYCODES = {
    '1': 164,  # KEY_PLAYPAUSE
    '2': 163,        # KEY_NEXTSONG
    '3': 165,    # KEY_PREVIOUSSONG
    '4': 166,        # KEY_STOPCD
    '5': 113,        # KEY_MUTE
    '6': 114, # KEY_VOLUMEDOWN
    '7': 115,   # KEY_VOLUMEUP
    '8': 208,# KEY_FASTFORWARD
}

def handle_key_press(key: str):
    print(f"[Keypad] Pressed: {key}", flush=True)
    if key in KEYCODES:
        code = KEYCODES[key]
        subprocess.run(["ydotool", "key", f"{code}:1", f"{code}:0"], check=False)


ack_event = threading.Event()

def read_serial(ser: serial.Serial):
    """Sole owner of ser.read(). Routes 'R' bytes to ack_event, K: lines to keypad handler."""
    buffer = bytearray()
    while ser and ser.is_open:
        try:
            b = ser.read(1)  # blocks up to ser.timeout (2s), returns b'' on timeout
        except Exception as e:
            print(f"[Serial Read] Error: {e}")
            break

        if not b:
            continue

        if b == b'R':
            ack_event.set()
            continue

        buffer += b
        if b == b'\n':
            line = bytes(buffer).strip()
            buffer = bytearray()
            if line.startswith(b"K:"):
                key = line[2:].decode(errors="ignore")
                try:
                    handle_key_press(key)
                except Exception as e:
                    print(f"[Keypad] handle_key_press failed: {e}")