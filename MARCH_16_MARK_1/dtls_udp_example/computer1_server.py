#!/usr/bin/env python3
"""Computer 1: DTLS-over-UDP echo server using python-mbedtls and PSK.

This example is intended for two computers on the same Wi-Fi network.
It uses DTLS (secure UDP) with a pre-shared key (PSK), which is the
simplest way to demonstrate encrypted UDP without generating certificates.

Usage example:
    python computer1_server.py --bind 0.0.0.0 --port 4433
"""

from __future__ import annotations

import argparse
import socket
import sys
import time
from contextlib import suppress
from typing import Callable

from mbedtls.tls import DTLSConfiguration, HelloVerifyRequest, ServerContext, TLSWrappedSocket

PSK_IDENTITY = "raj-client"
PSK_SECRET = b"raj-demo-secret-123456"
BUFFER_SIZE = 4096


def make_dtls_connection(sock: TLSWrappedSocket) -> TLSWrappedSocket:
    """Complete the DTLS server handshake with cookie verification."""
    conn, addr = sock.accept()
    conn.setcookieparam(addr[0].encode("ascii"))

    # First handshake attempt may trigger HelloVerifyRequest.
    with suppress(HelloVerifyRequest):
        conn.do_handshake()

    previous = conn
    _unused, (conn, addr) = conn, conn.accept()
    previous.close()
    conn.setcookieparam(addr[0].encode("ascii"))
    conn.do_handshake()
    return conn


class DTLSServer:
    def __init__(self, bind_ip: str, port: int) -> None:
        self.bind_ip = bind_ip
        self.port = port
        self.sock: TLSWrappedSocket | None = None

    def start(self) -> None:
        config = DTLSConfiguration(
            validate_certificates=False,
            pre_shared_key_store={PSK_IDENTITY: PSK_SECRET},
            read_timeout=5.0,
        )
        raw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wrapped = ServerContext(config).wrap_socket(raw)
        wrapped.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        wrapped.bind((self.bind_ip, self.port))
        self.sock = wrapped
        print(f"[SERVER] Listening on {self.bind_ip}:{self.port}")
        print(f"[SERVER] PSK identity: {PSK_IDENTITY}")

    def stop(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def run(self, handler: Callable[[TLSWrappedSocket], None]) -> None:
        if self.sock is None:
            raise RuntimeError("Server not started.")

        while True:
            print("[SERVER] Waiting for DTLS client...")
            with make_dtls_connection(self.sock) as conn:
                print("[SERVER] Handshake complete. Secure session established.")
                handler(conn)
                print("[SERVER] Session closed. Waiting for next client.\n")


def echo_and_measure(conn: TLSWrappedSocket) -> None:
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            time.sleep(0.01)
            continue

        text = data.decode("utf-8", errors="replace")
        print(f"[SERVER] Received: {text}")

        if text.strip().lower() == "quit":
            conn.send(b"bye")
            break

        # Echo back immediately so the client can compute RTT.
        reply = f"ACK:{text}".encode("utf-8")
        sent = 0
        view = memoryview(reply)
        while sent < len(reply):
            sent += conn.send(view[sent:])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DTLS UDP server (Computer 1)")
    parser.add_argument("--bind", default="0.0.0.0", help="Bind IP address")
    parser.add_argument("--port", default=4433, type=int, help="UDP port")
    return parser.parse_args()


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        raise SystemExit("Python 3.8+ is required.")

    args = parse_args()
    server = DTLSServer(args.bind, args.port)
    try:
        server.start()
        server.run(echo_and_measure)
    except KeyboardInterrupt:
        print("\n[SERVER] Stopped by user.")
    finally:
        server.stop()
