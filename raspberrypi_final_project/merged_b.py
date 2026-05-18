import subprocess
import time

from merged_a import CAN_IFACE, setup_can


def run_cansend(frame):
    cmd = ["cansend", CAN_IFACE, frame]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.returncode != 0:
        error = result.stderr.strip()
        print("ERROR:", error)
        return False, error

    return True, f"Sent {frame}"


def wait_ack(expected_items, timeout=1.2):
    """
    Listen for VN/CAN acknowledgement.
    If expected_items contains 114#68C0, output must contain it.
    If expected_items contains 114#, any 114 frame is accepted.
    """

    print("Waiting for CAN ACK:", expected_items)
    cmd = ["timeout", str(timeout), "candump", CAN_IFACE]

    result = subprocess.run(cmd, text=True, capture_output=True)
    output = result.stdout.strip()
    compact = output.replace(" ", "").upper()

    if output:
        print(output)
    else:
        print("No CAN feedback received during ACK window")

    for item in expected_items:
        if item.upper().replace(" ", "") in compact:
            return True, item

    return False, "NO_ACK"


def send_frames(frames, ack_items=None, delay=0.01):
    ok, msg = setup_can()
    if not ok:
        return False, msg

    for frame in frames:
        ok, msg = run_cansend(frame)
        if not ok:
            return False, msg
        time.sleep(delay)

    if ack_items:
        return wait_ack(ack_items)

    return True, "SENT"


# =========================================================
# PAGE 1: BASIC HMI
# Page 1 Android sends 1hmi...
# No VN ACK required for Page 1 in current logic.
# =========================================================

def p1_asr_on(): return send_frames(["001#000200"])
def p1_asr_off(): return send_frames(["001#000000"])

def p1_esp_on(): return send_frames(["001#000100"])
def p1_esp_off(): return send_frames(["001#000000"])

def p1_hdc_on(): return send_frames(["001#010000", "100#20"])
def p1_hdc_off(): return send_frames(["001#000000", "100#00"])

def p1_sport_on(): return send_frames(["112#00"])
def p1_sport_off(): return send_frames(["112#00"])

def p1_mud_on(): return send_frames(["112#20"])
def p1_mud_off(): return send_frames(["112#00"])

def p1_snow_on(): return send_frames(["112#40"])
def p1_snow_off(): return send_frames(["112#00"])

def p1_awd_on(): return send_frames(["112#60"])
def p1_awd_off(): return send_frames(["112#00"])

def p1_auto_on(): return send_frames(["112#80"])
def p1_auto_off(): return send_frames(["112#00"])


# =========================================================
# PAGE 2: ADVANCED HMI
# Page 2 Android sends 2hmi...
# ACK is checked using CAN feedback, then MQTT green feedback is sent.
# =========================================================

def p2_force_on(): return send_frames(["113#9900", "113#9900"], ["114#"])
def p2_force_off(): return send_frames(["113#9800", "113#9800"], ["114#"])

def p2_awd_demand_on(): return send_frames(["113#9A00", "113#9A00"], ["114#"])
def p2_awd_demand_off(): return send_frames(["113#9800", "113#9800"], ["114#"])

def p2_precontrol_on(): return send_frames(["113#9C00", "113#9C00"], ["114#"])
def p2_precontrol_off(): return send_frames(["113#9800", "113#9800"], ["114#"])

def p2_rear_axle_on(): return send_frames(["113#9880", "113#9880"], ["114#"])
def p2_rear_axle_off(): return send_frames(["113#9800", "113#9800"], ["114#"])

def p2_enable_on(): return send_frames(["113#9A00", "113#9A00"], ["113#9A00", "114#"])
def p2_enable_off(): return send_frames(["113#9800", "113#9800"], ["113#9800", "114#"])


# PWT modes
def p2_pwt_auto(): return send_frames(["113#9A80", "113#9A80"], ["114#7080"])
def p2_pwt_awd(): return send_frames(["113#7A80", "113#7A80"], ["114#6C60"])
def p2_pwt_snow(): return send_frames(["113#5A80", "113#5A80"], ["114#68C0"])
def p2_pwt_mud(): return send_frames(["113#3A80", "113#3A80"], ["114#64C0"])
def p2_pwt_sport(): return send_frames(["113#1A80", "113#1A80"], ["114#60C0"])


# ESP modes
def p2_esp_normal(): return send_frames(["113#1800", "113#1800"], ["114#"])
def p2_esp_snow(): return send_frames(["113#9000", "113#9000"], ["114#50C0", "114#"])
def p2_esp_mud(): return send_frames(["113#8800", "113#8800"], ["114#30C0", "114#"])
def p2_esp_sport(): return send_frames(["113#8000", "113#8000"], ["114#10C0", "114#"])
