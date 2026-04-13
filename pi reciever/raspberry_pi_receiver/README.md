# Raspberry Pi Receiver GUI

## What it does
- Starts an HTTP server on port 5000
- Waits for POST `/signal` with JSON `{ "value": 1 }`
- GUI shows:
  - `RECEIVED` when a signal was received recently
  - `NO DATA` otherwise

## Install
```bash
sudo apt update
sudo apt install python3-tk -y
pip install -r requirements.txt
```

## Run
```bash
python3 pi_receiver_gui.py
```

## Phone side
1. Connect the phone to the Raspberry Pi with USB cable
2. Enable **USB tethering** on the phone
3. Note the IP displayed in the GUI
4. Put that IP in the Android app `MainActivity.kt`
5. Build and install the app
