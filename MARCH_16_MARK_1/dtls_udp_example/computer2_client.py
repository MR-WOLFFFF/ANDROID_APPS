#!/usr/bin/env python3
"""Computer 2: DTLS-over-UDP client using python-mbedtls and PSK.

This client connects to the server on Computer 1, sends messages, and
measures round-trip time (RTT) for each message.

Usage example:
    python computer2_client.py --server-ip 192.168.1.10 --port 4433
"""
# Install DTLS library
%pip install --upgrade pip
%pip install python-mbedtls
    
from __future__ import annotations

import argparse
import socket
import sys
import time

from mbedtls.tls import ClientContext, DTLSConfiguration

PSK_IDENTITY = "raj-client"
PSK_SECRET = b"raj-demo-secret-123456"
BUFFER_SIZE = 4096


class DTLSClient:
    def __init__(self, server_ip: str, port: int) -> None:
        self.server_ip = server_ip
        self.port = port
        self.sock = None

    def connect(self) -> None:
        config = DTLSConfiguration(
            validate_certificates=False,
            pre_shared_key=(PSK_IDENTITY, PSK_SECRET),
            read_timeout=5.0,
        )
        raw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        raw.connect((self.server_ip, self.port))
        wrapped = ClientContext(config).wrap_socket(raw, server_hostname=self.server_ip)
        wrapped.do_handshake()
        self.sock = wrapped
        print(f"[CLIENT] Connected securely to {self.server_ip}:{self.port}")

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def interactive_loop(self) -> None:
        if self.sock is None:
            raise RuntimeError("Client not connected.")

        print("[CLIENT] Type a message and press Enter.")
        print("[CLIENT] Type 'quit' to close the session.")

        while True:
            message = input("\nYou: ").strip()
            if not message:
                continue

            payload = message.encode("utf-8")
            t0 = time.perf_counter()
            self.sock.send(payload)
            reply = self.sock.recv(BUFFER_SIZE)
            t1 = time.perf_counter()
            rtt_ms = (t1 - t0) * 1000.0

            print(f"[CLIENT] Reply: {reply.decode('utf-8', errors='replace')}")
            print(f"[CLIENT] RTT: {rtt_ms:.3f} ms")

            if message.lower() == "quit":
                break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DTLS UDP client (Computer 2)")
    parser.add_argument("--server-ip", required=True, help="IP address of Computer 1")
    parser.add_argument("--port", default=4433, type=int, help="UDP port")
    return parser.parse_args()


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        raise SystemExit("Python 3.8+ is required.")

    args = parse_args()
    client = DTLSClient(args.server_ip, args.port)
    try:
        client.connect()
        client.interactive_loop()
    except KeyboardInterrupt:
        print("\n[CLIENT] Stopped by user.")
    finally:
        client.close()
