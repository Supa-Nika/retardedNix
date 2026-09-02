import argparse
import os
import socket
import sys

SOCKET_PATH = "/tmp/streamdeck.sock"


def send_to_daemon(media_type: str, file_path: str, quality: int, fps: int):
    """Formats payload and transmits command to daemon via Unix socket."""
    if media_type == "yt":
        target = file_path  # URLs pass through untouched
    else:
        target = os.path.abspath(file_path)
        if not os.path.exists(target):
            print(f"Error: File '{target}' does not exist.")
            sys.exit(1)

    # Format: "video <quality> <fps> <abs_path>"
    payload = f"{media_type} {quality} {fps} {target}"
        
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(SOCKET_PATH)
        s.send(payload.encode("utf-8"))

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

    # Optional JPEG Quality (1 to 100)
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=30,
        choices=range(1, 101),
        metavar="[1-100]",
        help="Compression quality (jpegs export quality, 1-100, defaults [img, gif, vid]: 80, 50, 30)",
    )

    # Optional Target FPS (1 to 60)
    parser.add_argument(
        "-f",
        "--fps",
        type=int,
        default=20,
        choices=range(1, 61),
        metavar="[1-60]",
        help="Playback framerate (1-60, default: 20; ignored for gif and img)",
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
    group.add_argument(
        "--play-yt",
        type=str,
        metavar="PATH",
        help="Link to the yt video",
    )


    args = parser.parse_args()

    if args.play_video:
        send_to_daemon("video", args.play_video, args.quality, args.fps)
    elif args.play_gif:
        send_to_daemon("gif", args.play_gif, args.quality, args.fps)
    elif args.play_img:
        # FPS passed as 0/default since daemon ignores it for images
        send_to_daemon("image", args.play_img, args.quality, 0)
    elif args.play_yt:                                              
        send_to_daemon("yt", args.play_yt, args.quality, args.fps)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()