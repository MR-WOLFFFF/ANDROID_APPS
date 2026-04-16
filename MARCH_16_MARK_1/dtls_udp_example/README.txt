DTLS over UDP example for two computers on the same Wi-Fi
=========================================================

Files
-----
1. computer1_server.py  -> run this on Computer 1
2. computer2_client.py  -> run this on Computer 2

What this example does
----------------------
- Uses UDP secured with DTLS
- Uses a pre-shared key (PSK) for simplicity
- Lets Computer 2 send messages to Computer 1
- Computer 1 echoes them back
- Computer 2 measures round-trip time (RTT)

Install
-------
On BOTH computers:

    pip install python-mbedtls

How to run
----------
Step 1: On Computer 1, find its local IP address.
Example: 192.168.1.10

Step 2: Start the server on Computer 1:

    python computer1_server.py --bind 0.0.0.0 --port 4433

Step 3: Start the client on Computer 2:

    python computer2_client.py --server-ip 192.168.1.10 --port 4433

Step 4: Type messages in the client window.
You will see:
- the server acknowledgement
- the RTT in milliseconds

Notes
-----
- Both devices must be on the same Wi-Fi/LAN.
- Allow UDP port 4433 in the firewall if needed.
- The PSK identity and secret must match in both files.
- This is the simplest secure example. Certificate-based DTLS is possible too,
  but PSK is much easier for first testing.

About Google Colab
------------------
These scripts are best run in a normal Python environment on each computer.
For real peer-to-peer UDP/DTLS testing, local Python/Jupyter/terminal on both
machines is the practical setup.
