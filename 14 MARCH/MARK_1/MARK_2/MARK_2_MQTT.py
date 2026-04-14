import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
PUBLISH_TOPIC = "mark2/mqtt/pi_to_android"
SUBSCRIBE_TOPIC = "mark2/mqtt/android_to_pi"

class Mark2MqttGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MARK_2_MQTT")
        self.root.geometry("420x300")
        self.root.resizable(False, False)

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.build_ui()
        self.connect_mqtt()

    def build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="MARK_2_MQTT", font=("Arial", 18, "bold"))
        title.pack(pady=(0, 20))

        self.canvas = tk.Canvas(main, width=90, height=90, highlightthickness=0, bg=self.root.cget("bg"))
        self.canvas.pack()
        self.indicator = self.canvas.create_oval(10, 10, 80, 80, fill="red", outline="")

        self.status_label = ttk.Label(main, text="Receiver: 0", font=("Arial", 12))
        self.status_label.pack(pady=(12, 20))

        self.send_button = tk.Button(
            main,
            text="PRESS AND HOLD",
            font=("Arial", 13),
            width=18,
            height=2
        )
        self.send_button.pack()

        self.send_button.bind("<ButtonPress-1>", self.on_press)
        self.send_button.bind("<ButtonRelease-1>", self.on_release)

        info = ttk.Label(
            main,
            text="Press sends 1 to Android. Release sends 0.",
            font=("Arial", 10)
        )
        info.pack(pady=(18, 0))

    def connect_mqtt(self) -> None:
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(SUBSCRIBE_TOPIC)
            self.root.after(0, lambda: self.status_label.config(text="Receiver: connected"))
        else:
            self.root.after(0, lambda: self.status_label.config(text=f"Receiver: connect error {rc}"))

    def on_message(self, client, userdata, msg):
        value = msg.payload.decode().strip()
        self.root.after(0, lambda: self.update_indicator(value))

    def update_indicator(self, value: str) -> None:
        if value == "1":
            self.canvas.itemconfig(self.indicator, fill="green")
            self.status_label.config(text="Receiver: 1")
        else:
            self.canvas.itemconfig(self.indicator, fill="red")
            self.status_label.config(text="Receiver: 0")

    def publish_value(self, value: str) -> None:
        self.client.publish(PUBLISH_TOPIC, value)

    def on_press(self, event) -> None:
        self.publish_value("1")

    def on_release(self, event) -> None:
        self.publish_value("0")

    def close(self) -> None:
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        self.root.destroy()

def main() -> None:
    root = tk.Tk()
    app = Mark2MqttGui(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

if __name__ == "__main__":
    main()
