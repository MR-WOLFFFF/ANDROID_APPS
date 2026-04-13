"""Raspberry Pi 5 receiver for Android USB-tethering signal demo.

Run:
    python3 pi_receiver_gui.py

Install dependencies:
    pip install flask
"""

from __future__ import annotations

import socket
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field

from flask import Flask, jsonify, request


@dataclass
class SignalState:
    last_value: int = 0
    last_received_at: float = 0.0
    last_client_ip: str = "-"
    lock: threading.Lock = field(default_factory=threading.Lock)

    def update(self, value: int, client_ip: str) -> None:
        with self.lock:
            self.last_value = value
            self.last_received_at = time.time()
            self.last_client_ip = client_ip

    def snapshot(self) -> tuple[int, float, str]:
        with self.lock:
            return self.last_value, self.last_received_at, self.last_client_ip


state = SignalState()
app = Flask(__name__)


@app.route("/signal", methods=["POST"])
def receive_signal():
    data = request.get_json(silent=True) or {}
    value = int(data.get("value", 0))
    client_ip = request.remote_addr or "unknown"

    if value == 1:
        state.update(value=1, client_ip=client_ip)
        return jsonify({"status": "received", "value": 1}), 200

    return jsonify({"status": "ignored", "value": value}), 400


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


def get_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class ReceiverGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Raspberry Pi USB Receiver")
        self.root.geometry("500x300")
        self.root.configure(bg="#f4f6f8")

        self.server_ip = get_local_ip()

        title = tk.Label(
            root,
            text="Raspberry Pi Signal Receiver",
            font=("Arial", 20, "bold"),
            bg="#f4f6f8",
            fg="#111827",
        )
        title.pack(pady=(20, 10))

        self.status_box = tk.Label(
            root,
            text="NO DATA",
            width=20,
            height=3,
            font=("Arial", 18, "bold"),
            bg="#ffffff",
            fg="#b91c1c",
            relief="solid",
            bd=2,
        )
        self.status_box.pack(pady=10)

        self.detail_label = tk.Label(
            root,
            text=f"Listening on: http://{self.server_ip}:5000/signal",
            font=("Arial", 11),
            bg="#f4f6f8",
            fg="#374151",
        )
        self.detail_label.pack(pady=8)

        self.client_label = tk.Label(
            root,
            text="Last sender IP: -",
            font=("Arial", 11),
            bg="#f4f6f8",
            fg="#374151",
        )
        self.client_label.pack(pady=4)

        self.note_label = tk.Label(
            root,
            text="Connect the phone with USB cable and enable USB tethering.",
            font=("Arial", 10),
            bg="#f4f6f8",
            fg="#6b7280",
        )
        self.note_label.pack(pady=8)

        self.root.after(200, self.refresh_status)

    def refresh_status(self) -> None:
        value, last_received_at, client_ip = state.snapshot()
        elapsed = time.time() - last_received_at

        if value == 1 and elapsed < 3:
            self.status_box.config(text="RECEIVED", fg="#065f46")
        else:
            self.status_box.config(text="NO DATA", fg="#b91c1c")

        self.client_label.config(text=f"Last sender IP: {client_ip}")
        self.root.after(200, self.refresh_status)


def start_server() -> None:
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def main() -> None:
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    root = tk.Tk()
    ReceiverGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
