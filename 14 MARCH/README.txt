MARK_3 Raspberry Pi MQTT to CAN files

Files:
1. page1a.py    -> CAN setup commands
2. page1b.py    -> CAN command mapping and cansend logic
3. page1main.py -> MQTT receiver + decrypt + GUI + dispatch to page1b

Install:
sudo apt install python3-venv -y
python3 -m venv ~/mqtt_env
source ~/mqtt_env/bin/activate
pip install paho-mqtt

Run:
cd ~/Desktop
python3 page1main.py

MQTT:
Broker: broker.hivemq.com
Topic: mark3/hmi/android_to_pi

Important:
- Keep page1a.py, page1b.py, and page1main.py in the same folder.
- CAN setup uses sudo ip link commands.
- Only SPORT CAN frame was confirmed as 112#00.
- Other mode frames are placeholders in page1b.py.
