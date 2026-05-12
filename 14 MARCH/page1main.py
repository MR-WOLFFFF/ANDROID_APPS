import base64
import tkinter as tk
from tkinter import ttk

try:
    import paho.mqtt.client as mqtt
except ModuleNotFoundError:
    print("Missing dependency: paho-mqtt")
    print("Install:")
    print("python3 -m venv ~/mqtt_env")
    print("source ~/mqtt_env/bin/activate")
    print("pip install paho-mqtt")
    raise SystemExit(1)

from page1a import setup_can
from page1b import handle_hmi_command

BROKER = "broker.hivemq.com"
PORT = 1883
SUBSCRIBE_TOPIC = "mark3/hmi/android_to_pi"
SECRET_KEY = "MARK3_HMI_KEY"


def decrypt_xor_base64(payload):
    payload = payload.strip()

    if not payload.startswith("ENC:"):
        return payload

    encrypted = base64.b64decode(payload[4:])
    key = SECRET_KEY.encode("utf-8")
    output = bytearray()

    for i, value in enumerate(encrypted):
        output.append(value ^ key[i % len(key)])

    return output.decode("utf-8")


class MqttCanBridge:
    def __init__(self, root):
        self.root = root
        self.root.title("MARK_3 MQTT to CAN Bridge")
        self.root.geometry("720x420")
        self.root.resizable(False, False)

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.build_ui()
        self.connect_mqtt()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="MARK_3 MQTT to CAN Bridge",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=15)

        self.mqtt_status = tk.Label(
            self.root,
            text="MQTT: connecting...",
            font=("Arial", 12),
            fg="blue"
        )
        self.mqtt_status.pack(pady=5)

        self.last_command = tk.Label(
            self.root,
            text="Last command: none",
            font=("Arial", 12)
        )
        self.last_command.pack(pady=5)

        self.last_can = tk.Label(
            self.root,
            text="CAN status: waiting",
            font=("Arial", 12)
        )
        self.last_can.pack(pady=5)

        button_frame = ttk.Frame(self.root, padding=20)
        button_frame.pack(fill="x")

        reset_button = tk.Button(
            button_frame,
            text="RESET CAN",
            font=("Arial", 12, "bold"),
            width=18,
            height=2,
            command=self.reset_can
        )
        reset_button.grid(row=0, column=0, padx=15)

        reconnect_button = tk.Button(
            button_frame,
            text="MQTT RECONNECT",
            font=("Arial", 12, "bold"),
            width=18,
            height=2,
            command=self.reconnect_mqtt
        )
        reconnect_button.grid(row=0, column=1, padx=15)

        self.log_box = tk.Text(self.root, height=10, width=85)
        self.log_box.pack(pady=10)

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        print(text)

    def connect_mqtt(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as error:
            self.mqtt_status.config(text="MQTT: connection error", fg="red")
            self.log(f"MQTT connection error: {error}")

    def reconnect_mqtt(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

        self.mqtt_status.config(text="MQTT: reconnecting...", fg="blue")
        self.connect_mqtt()

    def reset_can(self):
        success, message = setup_can()
        self.last_can.config(
            text=f"CAN status: {message}",
            fg="green" if success else "red"
        )
        self.log(f"RESET CAN: {message}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(SUBSCRIBE_TOPIC)
            self.root.after(0, lambda: self.mqtt_status.config(text="MQTT: connected", fg="green"))
            self.root.after(0, lambda: self.log(f"Subscribed: {SUBSCRIBE_TOPIC}"))
        else:
            self.root.after(0, lambda: self.mqtt_status.config(text=f"MQTT: error {rc}", fg="red"))

    def on_disconnect(self, client, userdata, rc):
        self.root.after(0, lambda: self.mqtt_status.config(text="MQTT: disconnected", fg="red"))

    def on_message(self, client, userdata, msg):
        raw_payload = msg.payload.decode("utf-8", errors="replace")

        try:
            command = decrypt_xor_base64(raw_payload)
        except Exception as error:
            self.root.after(0, lambda: self.log(f"Decrypt error: {error} | payload={raw_payload}"))
            return

        self.root.after(0, lambda: self.process_command(command, raw_payload))

    def process_command(self, command, raw_payload):
        self.last_command.config(text=f"Last command: {command}")
        self.log(f"MQTT raw: {raw_payload}")
        self.log(f"Decrypted command: {command}")

        success, message = handle_hmi_command(command)

        self.last_can.config(
            text=f"CAN status: {message}",
            fg="green" if success else "red"
        )

        self.log(f"CAN result: {message}")

    def close(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MqttCanBridge(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
