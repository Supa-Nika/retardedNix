import playImage, playGif, playVideo
import os
import sys
import time
import json
import socket
import threading
import serial

STATE_FILE = os.path.expanduser("~/.local/state/streamdeck/state.json")
SOCKET_PATH = "/tmp/streamdeck.sock"
SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"

# Global state & lock for thread-safe updates
current_state = {
    "path": "",
    "type": "image"  # Options: "video", "gif", "image"
}
state_lock = threading.Lock()


# =========================================================
# MEDIA PLAYERS (Skeleton Functions)
# =========================================================
def play_video(ser: serial.Serial, file_path: str):
  playVideo.play(ser, file_path)
  


def play_gif(ser: serial.Serial, file_path: str):
  playGif(ser, file_path)


def play_image(ser: serial.Serial, file_path: str):
  playImage.play(ser, file_path)


# =========================================================
# STATE MANAGEMENT
# =========================================================
def load_state():
    """Reads saved path and type from disk on startup/device connection."""
    global current_state
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                with state_lock:
                    current_state["path"] = data.get("path", "")
                    current_state["type"] = data.get("type", "image")
                print(f"[State] Loaded from file: {current_state}")
        except Exception as e:
            print(f"[State] Error loading state.json: {e}")
    else:
        print("[State] No previous state file found. Using defaults.")


def save_state(path: str, media_type: str):
    """Persists current playing configuration to state.json."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"path": path, "type": media_type}, f, indent=2)
        print(f"[State] Saved to file: {path} ({media_type})")
    except Exception as e:
        print(f"[State] Failed to write state.json: {e}")


# =========================================================
# IPC SOCKET LISTENER (FOR CLI INTERACTION)
# =========================================================
def socket_listener():
    """Listens for commands from streamdeck-cli (e.g. 'video /path/to/vid.mp4')."""
    global current_state

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o777)  # Allow standard user CLI access
    server.listen(1)

    print(f"[IPC] Listening for CLI commands on {SOCKET_PATH}")

    while True:
        conn, _ = server.accept()
        raw_msg = conn.recv(1024).decode('utf-8').strip()
        if raw_msg:
            # Expecting commands formatted like: "video /path/to/file.mp4"
            parts = raw_msg.split(" ", 1)
            media_type = parts[0].lower()
            path = parts[1] if len(parts) > 1 else ""

            if media_type in ["video", "gif", "image"] and os.path.exists(path):
                with state_lock:
                    current_state["path"] = path
                    current_state["type"] = media_type

                save_state(path, media_type)
                conn.send(b"OK: State updated\n")
            else:
                conn.send(b"ERROR: Invalid arguments or file path\n")

        conn.close()


# =========================================================
# MAIN DISPATCHER & DEVICE HOTPLUG LOOP
# =========================================================
def main():
    # 1. Start the IPC thread so the CLI works even if the device isn't plugged in yet
    threading.Thread(target=socket_listener, daemon=True).start()

    while True:
        print(f"[Device] Searching for serial port {SERIAL_PORT}...")
        
        # Wait until the device is plugged in
        while not os.path.exists(SERIAL_PORT):
            time.sleep(1)

        print("[Device] Stream Deck / ESP32 detected!")

        # Load initial state right on device connection
        load_state()

        try:
            ser = serial.Serial(SERIAL_PORT, 3000000, timeout=2)
            time.sleep(2)
            ser.reset_input_buffer()
            print("[Device] Serial port opened. Starting main render loop.")

            # Hardware execution loop
            while os.path.exists(SERIAL_PORT):
                with state_lock:
                    path = current_state["path"]
                    media_type = current_state["type"]

                if not path or not os.path.exists(path):
                    time.sleep(0.2)
                    continue

                # Route execution based on current media type state
                if media_type == "video":
                    play_video(ser, path)
                elif media_type == "gif":
                    play_gif(ser, path)
                elif media_type == "image":
                    play_image(ser, path)

            ser.close()

        except serial.SerialException as e:
            print(f"[Device] Disconnected or serial error: {e}")
        except Exception as e:
            print(f"[Device] Unexpected error: {e}")

        print("[Device] Device lost. Retrying connection...")
        time.sleep(2)


if __name__ == "__main__":
    main()