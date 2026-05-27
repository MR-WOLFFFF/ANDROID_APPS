import time

import paho.mqtt.client as mqtt

from page5a import setup_can
from page5b import build_page5_frame, handle_mqtt_payload, state

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "mark3/hmi/android_to_pi"
CLIENT_ID = "page5_raspberrypi_hmi"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to: {MQTT_TOPIC}")
    else:
        print(f"MQTT connection failed, rc={rc}")


def on_disconnect(client, userdata, rc):
    print(f"MQTT disconnected, rc={rc}")


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8", errors="replace")
    print("-" * 70)
    print("Topic:", message.topic)

    success, result = handle_mqtt_payload(payload)
    print("Result:", result)
    print("Current state:", state)
    print("Current frame:", build_page5_frame())

    # Optional acknowledgement back to Android app can be added here later.


def create_client():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client


def main():
    print("Page 5 Raspberry Pi MQTT → CAN bridge")
    print("Initial CAN setup...")
    success, message = setup_can()
    print(message)
    print("Initial frame, not sent yet:", build_page5_frame())

    client = create_client()

    while True:
        try:
            print(f"Connecting MQTT broker {MQTT_BROKER}:{MQTT_PORT} ...")
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except KeyboardInterrupt:
            print("Stopped by user")
            break
        except Exception as error:
            print("MQTT loop error:", error)
            print("Retrying in 3 seconds...")
            time.sleep(3)

    try:
        client.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    main()
