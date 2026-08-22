import argparse
import os
import socket
import sys

SOCKET_PATH = "/tmp/streamdeck.sock"


def send_to_daemon(media_type: str, file_path: str):
    """Formats payload and transmits command to daemon via Unix socket."""
    abs_path = os.path.abspath(file_path)

    if not os.path.exists(abs_path):
        print(f"Error: File '{abs_path}' does not exist.")
        sys.exit(1)

    payload = f"{media_type} {abs_path}"

    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(SOCKET_PATH)
        s.send(payload.encode("utf-8"))

        # Receive daemon acknowledgment
        response = s.recv(1024).decode("utf-8")
        print(f"Daemon response: {response}", end="")
        s.close()
    except FileNotFoundError:
        print("Error: Stream Deck daemon is not running (socket file missing).")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to communicate with daemon: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Put things on stream deck display"
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--play-video",
        type=str,
        metavar="PATH",
        help="Path to the video file",
    )
    group.add_argument(
        "--play-gif",
        type=str,
        metavar="PATH",
        help="Path to the gif (can* play imgs)",
    )
    group.add_argument(
        "--play-img",
        type=str,
        metavar="PATH",
        help="Path to the image file (not gif)",
    )

    args = parser.parse_args()

    if args.play_video:
        send_to_daemon("video", args.play_video)
    elif args.play_gif:
        send_to_daemon("gif", args.play_gif)
    elif args.play_img:
        send_to_daemon("image", args.play_img)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()