#!/usr/bin/env python3
"""
ESP Page 1 MQTT -> CAN receiver for Raspberry Pi.

Android Auto app publishes Base64 commands on MQTT:
  ESP ON  -> 1hmi101
  ESP OFF -> 1hmi100

This receiver subscribes to the MQTT topic, decodes the command,
configures can1, and sends the matching CAN frame.

Default mapping used for this ESP test:
  1hmi101 -> cansend can1 001#000100
  1hmi100 -> cansend can1 001#000000
"""

import argparse
import base64
import subprocess
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_RX = "mark3/hmi/android_to_pi"

CAN_IFACE = "can1"
CAN_BITRATE = "125000"
CAN_SAMPLE_POINT = "0.875"

# User-requested Android codes for ESP test
COMMAND_TO_CAN = {
    "1hmi101": ["cansend", CAN_IFACE, "001#000100"],  # ESP ON
    "1hmi100": ["cansend", CAN_IFACE, "001#000000"],  # ESP OFF
}


def log(message: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def run_command(cmd, dry_run=False):
    if dry_run:
        log("DRY RUN: " + " ".join(cmd))
        return
    subprocess.run(cmd, check=True)


def setup_can(dry_run=False):
    """Configure can1 before sending, using the same style as your Page 1 setup."""
    commands = [
        ["sudo", "ip", "link", "set", CAN_IFACE, "down"],
        ["sudo", "ip", "link", "set", CAN_IFACE, "type", "can", "bitrate", CAN_BITRATE,
         "sample-point", CAN_SAMPLE_POINT, "restart-ms", "100"],
        ["sudo", "ip", "link", "set", CAN_IFACE, "txqueuelen", "1000"],
        ["sudo", "ip", "link", "set", CAN_IFACE, "up"],
    ]
    for cmd in commands:
        try:
            run_command(cmd, dry_run=dry_run)
        except subprocess.CalledProcessError as exc:
            # The first 'down' can fail if the interface is not up yet. Continue to show useful logs.
            log(f"CAN setup command failed: {' '.join(cmd)} | error={exc}")


def decode_payload(payload_bytes: bytes) -> str:
    raw = payload_bytes.decode("utf-8", errors="replace").strip()

    # First try Base64 because the Android app sends Base64(command).
    try:
        decoded = base64.b64decode(raw, validate=True).decode("utf-8", errors="replace").strip()
        if decoded:
            return decoded
    except Exception:
        pass

    # Fallback: accept plain text commands too.
    return raw


def create_client(args):
    client_id = f"raspi-esp-page1-{int(time.time())}"
    client = mqtt.Client(client_id=client_id, clean_session=True)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            log(f"Connected to MQTT broker {BROKER}:{PORT}")
            client.subscribe(TOPIC_RX, qos=0)
            log(f"Subscribed to topic: {TOPIC_RX}")
        else:
            log(f"MQTT connection failed with rc={rc}")

    def on_message(client, userdata, msg):
        command = decode_payload(msg.payload)
        log(f"MQTT received topic={msg.topic} payload={msg.payload!r} decoded={command}")

        if command not in COMMAND_TO_CAN:
            log(f"Unknown command ignored: {command}")
            return

        try:
            setup_can(dry_run=args.dry_run)
            can_cmd = COMMAND_TO_CAN[command]
            run_command(can_cmd, dry_run=args.dry_run)
            log(f"CAN sent for {command}: {' '.join(can_cmd)}")
        except Exception as exc:
            log(f"ERROR sending CAN for {command}: {exc}")

    client.on_connect = on_connect
    client.on_message = on_message
    return client


def main():
    parser = argparse.ArgumentParser(description="ESP Page1 MQTT to CAN receiver")
    parser.add_argument("--dry-run", action="store_true", help="Print commands but do not execute cansend/ip commands")
    args = parser.parse_args()

    log("Starting ESP Page1 MQTT -> CAN receiver")
    if args.dry_run:
        log("Dry-run mode enabled. No CAN commands will be executed.")

    client = create_client(args)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Stopped by user")
        sys.exit(0)
