import base64
import time
import traceback

import paho.mqtt.client as mqtt

from merged_b import *


BROKER = "broker.hivemq.com"
PORT = 1883

SUB_TOPIC = "mark3/hmi/android_to_pi"
PUB_TOPIC = "mark3/hmi/pi_to_android"


COMMANDS = {
    # =====================================================
    # PAGE 1
    # =====================================================
    "1hmi101": (p1_asr_on, "1hmi100"),
    "1hmi100": (p1_asr_off, "1hmi100"),

    "1hmi201": (p1_esp_on, "1hmi200"),
    "1hmi200": (p1_esp_off, "1hmi200"),

    "1hmi301": (p1_hdc_on, "1hmi300"),
    "1hmi300": (p1_hdc_off, "1hmi300"),

    "1hmi401": (p1_sport_on, "1hmi400"),
    "1hmi400": (p1_sport_off, "1hmi400"),

    "1hmi501": (p1_mud_on, "1hmi500"),
    "1hmi500": (p1_mud_off, "1hmi500"),

    "1hmi601": (p1_snow_on, "1hmi600"),
    "1hmi600": (p1_snow_off, "1hmi600"),

    "1hmi701": (p1_awd_on, "1hmi700"),
    "1hmi700": (p1_awd_off, "1hmi700"),

    "1hmi801": (p1_auto_on, "1hmi800"),
    "1hmi800": (p1_auto_off, "1hmi800"),

    # =====================================================
    # PAGE 2 LEFT CONTROLS
    # =====================================================
    "2hmi101": (p2_force_on, "2hmi100"),
    "2hmi100": (p2_force_off, "2hmi100"),

    "2hmi201": (p2_awd_demand_on, "2hmi200"),
    "2hmi200": (p2_awd_demand_off, "2hmi200"),

    "2hmi301": (p2_precontrol_on, "2hmi300"),
    "2hmi300": (p2_precontrol_off, "2hmi300"),

    "2hmi401": (p2_rear_axle_on, "2hmi400"),
    "2hmi400": (p2_rear_axle_off, "2hmi400"),

    "2hmi501": (p2_enable_on, "2hmi500"),
    "2hmi500": (p2_enable_off, "2hmi500"),

    # =====================================================
    # PAGE 2 PWT MODES
    # =====================================================
    "2hmi601": (p2_pwt_auto, "2hmi600"),
    "2hmi701": (p2_pwt_awd, "2hmi700"),
    "2hmi801": (p2_pwt_snow, "2hmi800"),
    "2hmi901": (p2_pwt_mud, "2hmi900"),
    "2hmi1001": (p2_pwt_sport, "2hmi1000"),

    # =====================================================
    # PAGE 2 ESP MODES
    # =====================================================
    "2hmi1101": (p2_esp_normal, "2hmi1100"),
    "2hmi1201": (p2_esp_snow, "2hmi1200"),
    "2hmi1301": (p2_esp_mud, "2hmi1300"),
    "2hmi1401": (p2_esp_sport, "2hmi1400"),
}


def decode_payload(raw):
    raw = raw.strip()

    if raw.startswith("1hmi") or raw.startswith("2hmi"):
        return raw

    # Supports old app if payload is Base64.
    try:
        decoded = base64.b64decode(raw).decode("utf-8").strip()
        if decoded.startswith("1hmi") or decoded.startswith("2hmi"):
            return decoded
    except Exception:
        pass

    return raw


def publish(client, text):
    print("Publishing:", text)
    client.publish(PUB_TOPIC, text, qos=1, retain=False)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected")
        client.subscribe(SUB_TOPIC, qos=1)
        publish(client, "RASPBERRY_CONNECTED")
    else:
        print("MQTT connect error:", rc)


def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode("utf-8", errors="ignore")
        command = decode_payload(raw)

        print("\n==============================")
        print("RAW     :", raw)
        print("COMMAND :", command)

        if command not in COMMANDS:
            print("UNKNOWN COMMAND")
            publish(client, "UNKNOWN_COMMAND")
            return

        function, feedback = COMMANDS[command]

        ok, result = function()

        if ok:
            print("OK:", result)
            publish(client, feedback)
        else:
            print("FAILED:", result)
            publish(client, "2FB_FAIL")

    except Exception as e:
        traceback.print_exc()
        publish(client, f"PYTHON_ERROR:{e}")


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            print("Connecting MQTT...")
            client.connect(BROKER, PORT, 60)
            break
        except Exception as e:
            print("MQTT error:", e)
            time.sleep(3)

    client.loop_forever()


if __name__ == "__main__":
    main()
