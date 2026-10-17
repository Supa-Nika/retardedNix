import modules as interact

import os
import time
import json
import socket
import threading
import serial
import traceback

STATE_FILE = os.path.expanduser("~/.local/state/streamdeck/state.json")
SOCKET_PATH = "/tmp/streamdeck.sock"
SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"

# Default settings per media type
DEFAULT_QUALITY = {
    "image": 100,  # Static image: full quality since it renders once
    "gif": 100,    # GIF: full quality
    "video": 30,  # Video: lower quality for fast UDP streaming
    "yt": 30
}

DEFAULT_FPS = {
    "image": 0,
    "gif": 15,
    "video": 20,
    "yt": 20
}

# Global state & lock for thread-safe updates
current_state = {
    "path": "",
    "type": "image",  # Options: "video", "gif", "image" "yt"
    "quality": 30,
    "fps": 0
}
state_lock = threading.Lock()

# =========================================================
# MEDIA PLAYERS 
# =========================================================
def is_state_changed(active_path: str, active_type: str, active_quality: int, active_fps: int):
    """Returns True if CLI sent new settings or device was unplugged."""
    def check():
        if not os.path.exists(SERIAL_PORT):
            return True
            
        with state_lock:
            return (
                current_state["path"] != active_path or
                current_state["type"] != active_type or
                current_state["quality"] != active_quality or
                current_state["fps"] != active_fps
            )
    return check

def play_video(file_path, quality, fps):
    interact.playVideo.play(
        file_path, 
        quality=quality, 
        fps=fps, 
        should_stop=is_state_changed(file_path, "video", quality, fps)
    )

def play_gif(file_path, quality, fps):
    interact.playGif.play(
        file_path, 
        quality=quality, 
        should_stop=is_state_changed(file_path, "gif", quality, fps)
    )

def play_image(file_path, quality):
    # FPS is ignored for static images
    interact.playImage.play(
        file_path, 
        quality=quality, 
        should_stop=is_state_changed(file_path, "image", quality, 0)
    )

def play_yt(file_path, quality, fps):
    interact.playYT.play(
        file_path, 
        quality=quality, 
        fps=fps, 
        should_stop=is_state_changed(file_path, "yt", quality, fps)
    )


# =========================================================
# STATE MANAGEMENT
# =========================================================
def load_state():
    """Reads saved path, type, quality, and fps from disk."""
    global current_state
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                with state_lock:
                    current_state["path"] = data.get("path", "")
                    current_state["type"] = data.get("type", "image")
                    current_state["quality"] = data.get("quality", 30)
                    current_state["fps"] = data.get("fps", 20)
                print(f"[State] Loaded from file: {current_state}")
        except Exception as e:
            print(f"[State] Error loading state.json: {e}")
    else:
        print("[State] No previous state file found. Using defaults.")


def save_state(path: str, media_type: str, quality: int, fps: int):
    """Persists current playing configuration to state.json."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({
                "path": path, 
                "type": media_type,
                "quality": quality,
                "fps": fps
            }, f, indent=2)
        print(f"[State] Saved to file: {path} ({media_type}, q={quality}, fps={fps})")
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
        try:
            # Inside socket_listener() in daemon.py
            raw_msg = conn.recv(1024).decode('utf-8').strip()
            if raw_msg:
                parts = raw_msg.split(" ", 3)
                if len(parts) == 4:
                    media_type = parts[0].lower()
                    
                    try:
                        quality = int(parts[1])
                        fps = int(parts[2])
                    except ValueError:
                        quality, fps = 0, 0

                    path = parts[3]

                    path_ok = os.path.exists(path) if media_type != "yt" else path.startswith("http")
                    if media_type in ["video", "gif", "image", "yt"] and path_ok:
                        # Fallback to type-specific defaults if 0 or invalid
                        resolved_quality = quality if quality > 0 else DEFAULT_QUALITY.get(media_type, 30)
                        resolved_fps = fps if fps > 0 else DEFAULT_FPS.get(media_type, 20)

                        with state_lock:
                            current_state["path"] = path
                            current_state["type"] = media_type
                            current_state["quality"] = resolved_quality
                            current_state["fps"] = resolved_fps

                        save_state(path, media_type, resolved_quality, resolved_fps)
                        conn.send(b"OK: State updated\n")
        except Exception as e:
            print(f"[IPC] Error handling connection: {e}")
        finally:
            conn.close()

# =========================================================
# MAIN DISPATCHER & DEVICE HOTPLUG LOOP
# =========================================================
def main():
    print(f"[Debug] Running from: {__file__}")
    print(f"[Debug] cwd: {os.getcwd()}")
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
            ser = serial.Serial(SERIAL_PORT, 115200, timeout=2)
            time.sleep(1)

            # Start background serial thread for non-blocking keypad handling
            serial_thread = threading.Thread(target=interact.readSerial.read_serial, args=(ser,), daemon=True)
            serial_thread.start()

            print("[Device] Serial port opened. Starting main render loop.")

            # Hardware execution loop
            while os.path.exists(SERIAL_PORT):
                with state_lock:
                    path = current_state["path"]
                    media_type = current_state["type"]
                    quality = current_state["quality"]
                    fps = current_state["fps"]

                if not path:
                    time.sleep(0.2)
                    continue
                if media_type != "yt" and not os.path.exists(path):
                    time.sleep(0.2)
                    continue

                # Route execution based on current media type state
                if media_type == "video":
                    play_video(path, quality, fps)
                elif media_type == "gif":
                    play_gif(path, quality, fps)
                elif media_type == "image":
                    play_image(path, quality)
                elif media_type == "yt":
                    play_yt(path, quality, fps)

            ser.close()

        except serial.SerialException as e:
            print(f"[Device] Disconnected or serial error: {e}")
        except Exception as e:
            print(f"[Device] Unexpected error: {e}")
            traceback.print_exc()

        print("[Device] Device lost. Retrying connection...")
        time.sleep(2)


if __name__ == "__main__":
    main()