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

    output = result.stdout.strip()
    if output:
        print(output)

    return True, "OK"


def setup_can():
    commands = [
        ["sudo", "ip", "link", "set", CAN_IFACE, "down"],
        [
            "sudo", "ip", "link", "set", CAN_IFACE,
            "type", "can",
            "bitrate", BITRATE,
            "sample-point", "0.875",
            "restart-ms", "100"
        ],
        ["sudo", "ip", "link", "set", CAN_IFACE, "txqueuelen", "1000"],
        ["sudo", "ip", "link", "set", CAN_IFACE, "up"],
    ]

    for command in commands:
        success, message = run_command(command)
        if not success:
            return False, message

    return True, f"{CAN_IFACE} configured at {BITRATE} bps"
