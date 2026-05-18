import subprocess

CAN_IFACE = "can1"
BITRATE = "125000"


def run_command(command):
    print("Running:", " ".join(command))
    result = subprocess.run(command, text=True, capture_output=True)

    if result.returncode != 0:
        error = result.stderr.strip()
        print("ERROR:", error)
        return False, error

    return True, "OK"


def setup_can():
    commands = [
        ["ip", "link", "set", CAN_IFACE, "down"],
        [
            "ip", "link", "set", CAN_IFACE,
            "type", "can",
            "bitrate", BITRATE,
            "sample-point", "0.875",
            "restart-ms", "100"
        ],
        ["ip", "link", "set", CAN_IFACE, "txqueuelen", "1000"],
        ["ip", "link", "set", CAN_IFACE, "up"],
    ]

    for cmd in commands:
        ok, msg = run_command(cmd)
        if not ok:
            return False, msg

    return True, f"{CAN_IFACE} ready at {BITRATE}"
