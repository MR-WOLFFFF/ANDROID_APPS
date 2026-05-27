import subprocess

CAN_IFACE = "can1"
BITRATE = "125000"
SAMPLE_POINT = "0.875"
RESTART_MS = "100"
TX_QUEUE_LEN = "1000"


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
    """
    CAN setup requested for Page 5.

    Equivalent terminal commands:
    sudo ip link set can1 down
    sudo ip link set can1 type can bitrate 125000 sample-point 0.875 restart-ms 100
    sudo ip link set can1 txqueuelen 1000
    sudo ip link set can1 up
    """
    commands = [
        ["ip", "link", "set", CAN_IFACE, "down"],
        [
            "ip", "link", "set", CAN_IFACE,
            "type", "can",
            "bitrate", BITRATE,
            "sample-point", SAMPLE_POINT,
            "restart-ms", RESTART_MS,
        ],
        ["ip", "link", "set", CAN_IFACE, "txqueuelen", TX_QUEUE_LEN],
        ["ip", "link", "set", CAN_IFACE, "up"],
    ]

    for command in commands:
        success, message = run_command(command)
        if not success:
            return False, message

    return True, f"{CAN_IFACE} configured at {BITRATE} bps"
