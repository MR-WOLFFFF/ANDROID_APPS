RASPBERRY PI FINAL SIGNAL LOGIC

Run:

sudo apt update
sudo apt install -y can-utils python3-pip
pip3 install paho-mqtt

cd ~/Desktop/raspberrypi_final_project
sudo python3 merged_main.py

MQTT:
Android -> Raspberry:
mark3/hmi/android_to_pi

Raspberry -> Android ACK:
mark3/hmi/pi_to_android

PAGE 2 ACK LOGIC:
Android sends ON command, LED becomes orange.
Raspberry sends CAN to VN.
Raspberry listens for CAN ACK.
If ACK is received, Raspberry publishes the OFF/ACK code.
Android receives ACK and LED becomes green.
