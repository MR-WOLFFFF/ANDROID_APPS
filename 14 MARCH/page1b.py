import subprocess
from page1a import setup_can

CAN_IFACE = "can1"

asr_state = False
esp_state = False
hdc_state = False

# IMPORTANT:
# SPORT was provided as 112#00.
# Other drive-mode CAN frames are placeholders. Update after confirmation.
MODE_CAN_FRAMES = {
    "1hmi444": ["112#00"],  # SPORT
    "1hmi555": ["112#01"],  # MUD AND SAND - placeholder
    "1hmi666": ["112#02"],  # SNOW - placeholder
    "1hmi777": ["112#03"],  # AWD - placeholder
    "1hmi888": ["112#04"],  # AUTO - placeholder
}


def run_cansend(frame):
    command = ["cansend", CAN_IFACE, frame]
    print("Running:", " ".join(command))

    result = subprocess.run(command, text=True, capture_output=True)

    if result.returncode != 0:
        error = result.stderr.strip()
        print("ERROR:", error)
        return False, error

    return True, f"Sent {frame}"


def build_main_frame():
    byte0 = 0x01 if hdc_state else 0x00

    byte1 = 0x00
    if esp_state:
        byte1 |= 0x01
    if asr_state:
        byte1 |= 0x02

    byte2 = 0x00

    return f"001#{byte0:02X}{byte1:02X}{byte2:02X}"


def setup_then_send(frames):
    success, message = setup_can()
    if not success:
        return False, f"CAN setup failed: {message}"

    for frame in frames:
        success, message = run_cansend(frame)
        if not success:
            return False, message

    return True, " / ".join(frames)


def handle_asr_on():
    global asr_state
    asr_state = True
    return setup_then_send([build_main_frame()])


def handle_asr_off():
    global asr_state
    asr_state = False
    return setup_then_send([build_main_frame()])


def handle_esp_on():
    global esp_state
    esp_state = True
    return setup_then_send([build_main_frame()])


def handle_esp_off():
    global esp_state
    esp_state = False
    return setup_then_send([build_main_frame()])


def handle_hdc_on():
    global hdc_state
    hdc_state = True
    return setup_then_send([build_main_frame(), "100#20"])


def handle_hdc_off():
    global hdc_state
    hdc_state = False
    return setup_then_send([build_main_frame(), "100#00"])


def handle_mode(command):
    frames = MODE_CAN_FRAMES.get(command)
    if not frames:
        return False, f"Unknown mode command: {command}"
    return setup_then_send(frames)


def handle_hmi_command(command):
    command = command.strip()

    if command == "1hmi101":
        return handle_asr_on()
    if command == "1hmi100":
        return handle_asr_off()

    if command == "1hmi201":
        return handle_esp_on()
    if command == "1hmi200":
        return handle_esp_off()

    if command == "1hmi301":
        return handle_hdc_on()
    if command == "1hmi300":
        return handle_hdc_off()

    if command in MODE_CAN_FRAMES:
        return handle_mode(command)

    return False, f"Unknown HMI command: {command}"
