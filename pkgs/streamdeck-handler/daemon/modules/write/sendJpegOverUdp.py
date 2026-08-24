import math
import socket
import time

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ESP32_IP = "192.168.1.70"
UDP_PORT = 12345

frame_id = 0
CHUNK_SIZE = 1400


def send(jpeg_bytes: bytes):
    global frame_id
    frame_id = (frame_id + 1) % 256
    total_bytes = len(jpeg_bytes)
    total_chunks = math.ceil(total_bytes / CHUNK_SIZE)

    for i in range(total_chunks):
        start = i * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, total_bytes)
        chunk_data = jpeg_bytes[start:end]

        header = bytes([frame_id, total_chunks, i])
        udp_socket.sendto(header + chunk_data, (ESP32_IP, UDP_PORT))
        
        # Micro-delay to prevent ESP32 Wi-Fi RX buffer overflow
        time.sleep(0.00015)