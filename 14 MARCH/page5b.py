import json
import re
import subprocess
from typing import Any, Dict, Optional, Tuple

from page5a import CAN_IFACE, setup_can

# Page 5 CAN frame from the supplied ASC logs:
# CAN ID: 004
# DLC: 8
# Byte 2: activation bit, 0x40 when activated
# Byte 3: torque distribution signed int8, -100..+100
# Bytes 4-5: front axle slip signed int16, scale 640 per m/s
# Bytes 6-7: rear axle slip signed int16, scale 640 per m/s
CAN_ID = "004"
SLIP_SCALE = 640

state = {
    "activation": False,
    "torque_percent": 0,
    "rear_slip_mps": 0,
    "front_slip_mps": 0,
}


def run_cansend(frame: str) -> Tuple[bool, str]:
    command = ["cansend", CAN_IFACE, frame]
    print("Running:", " ".join(command))

    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        error = result.stderr.strip()
        print("ERROR:", error)
        return False, error

    return True, f"Sent {frame}"


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def encode_signed_u8(value: int) -> int:
    value = clamp(value, -128, 127)
    return value & 0xFF


def encode_slip_bytes(value_mps: int) -> Tuple[int, int]:
    value_mps = clamp(value_mps, -10, 32)
    raw = int(round(value_mps * SLIP_SCALE)) & 0xFFFF
    high = (raw >> 8) & 0xFF
    low = raw & 0xFF
    return high, low


def build_page5_frame() -> str:
    activation_byte = 0x40 if state["activation"] else 0x00
    torque_byte = encode_signed_u8(int(state["torque_percent"]))
    front_high, front_low = encode_slip_bytes(int(state["front_slip_mps"]))
    rear_high, rear_low = encode_slip_bytes(int(state["rear_slip_mps"]))

    data = [
        0x00,
        0x00,
        activation_byte,
        torque_byte,
        front_high,
        front_low,
        rear_high,
        rear_low,
    ]
    return CAN_ID + "#" + "".join(f"{byte:02X}" for byte in data)


def reset_can_then_send_current_state() -> Tuple[bool, str]:
    success, message = setup_can()
    if not success:
        return False, f"CAN setup failed: {message}"

    frame = build_page5_frame()
    return run_cansend(frame)


def set_activation(enabled: bool) -> Tuple[bool, str]:
    state["activation"] = bool(enabled)
    return reset_can_then_send_current_state()


def set_torque(percent: int) -> Tuple[bool, str]:
    state["torque_percent"] = clamp(int(percent), -100, 100)
    return reset_can_then_send_current_state()


def set_rear_slip(value_mps: int) -> Tuple[bool, str]:
    state["rear_slip_mps"] = clamp(int(value_mps), -10, 32)
    return reset_can_then_send_current_state()


def set_front_slip(value_mps: int) -> Tuple[bool, str]:
    state["front_slip_mps"] = clamp(int(value_mps), -10, 32)
    return reset_can_then_send_current_state()


def parse_code_number(code: str) -> Optional[int]:
    match = re.fullmatch(r"5hmi(\d{3})", code.strip())
    if not match:
        return None
    return int(match.group(1))


def handle_json_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    function = str(data.get("function", "")).strip().lower()
    code = str(data.get("code", "")).strip()
    value = data.get("value", None)
    number = parse_code_number(code)

    if function == "activation":
        if value is not None:
            return set_activation(int(value) == 1)
        return set_activation(code == "5hmi101")

    if function == "torque":
        if value is not None:
            return set_torque(int(value))
        if number is None:
            return False, f"Invalid torque code: {code}"
        return set_torque(number - 100)

    if function == "rear_slip":
        if value is not None:
            return set_rear_slip(int(value))
        if number is None:
            return False, f"Invalid rear slip code: {code}"
        return set_rear_slip(number - 310)

    if function == "front_slip":
        if value is not None:
            return set_front_slip(int(value))
        if number is None:
            return False, f"Invalid front slip code: {code}"
        return set_front_slip(number - 410)

    return False, f"Unknown JSON function: {function}"


def handle_raw_code(code: str) -> Tuple[bool, str]:
    """
    Raw fallback for manual testing.

    Important: raw Page 5 codes are ambiguous because torque uses 5hmi000..5hmi200,
    while activation also uses 5hmi100 and 5hmi101. For that reason, JSON mode from
    the Android app is recommended.
    """
    code = code.strip()
    number = parse_code_number(code)
    if number is None:
        return False, f"Ignored non Page-5 command: {code}"

    # Activation is prioritized for exact raw activation commands.
    # In raw mode this means torque 0% and torque +1% cannot be distinguished.
    if code == "5hmi101":
        return set_activation(True)
    if code == "5hmi100":
        return set_activation(False)

    if 0 <= number <= 200:
        return set_torque(number - 100)

    if 300 <= number <= 342:
        return set_rear_slip(number - 310)

    if 400 <= number <= 442:
        return set_front_slip(number - 410)

    return False, f"Code outside Page-5 ranges: {code}"


def handle_mqtt_payload(payload: str) -> Tuple[bool, str]:
    payload = payload.strip()
    print("MQTT payload:", payload)

    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            return handle_json_command(data)
    except json.JSONDecodeError:
        pass

    return handle_raw_code(payload)
