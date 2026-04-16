

# Install DTLS library
%pip install --upgrade pip
%pip install python-mbedtls


# ================================
# COMPUTER 2 : DTLS CLIENT
# ================================

import socket
import time

from mbedtls.tls import ClientContext, DTLSConfiguration

# ----------------
# USER SETTINGS
# ----------------
SERVER_IP = "10.223.132.67"   # <-- CHANGE THIS to Computer 1 IP
PORT = 4433

PSK_IDENTITY = "raj-client"
PSK_SECRET = b"raj-demo-secret-123456"

BUFFER_SIZE = 4096

# ----------------
# CREATE CLIENT
# ----------------
config = DTLSConfiguration(
    validate_certificates=False,
    pre_shared_key=(PSK_IDENTITY, PSK_SECRET),
    read_timeout=5.0,
)

raw_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
raw_sock.connect((SERVER_IP, PORT))

client_sock = ClientContext(config).wrap_socket(raw_sock, server_hostname=SERVER_IP)

print(f"[CLIENT] Connecting securely to {SERVER_IP}:{PORT} ...")
client_sock.do_handshake()
print("[CLIENT] DTLS handshake complete.")
print("[CLIENT] Type your message and press Enter.")
print("[CLIENT] Type 'quit' to stop.\n")

# ----------------
# MAIN LOOP
# ----------------
while True:
    try:
        message = input("You: ").strip()

        if not message:
            continue

        payload = message.encode("utf-8")

        t0 = time.perf_counter()
        client_sock.send(payload)
        reply = client_sock.recv(BUFFER_SIZE)
        t1 = time.perf_counter()

        rtt_ms = (t1 - t0) * 1000.0

        print(f"[CLIENT] Reply: {reply.decode('utf-8', errors='replace')}")
        print(f"[CLIENT] RTT: {rtt_ms:.3f} ms\n")

        if message.lower() == "quit":
            break

    except KeyboardInterrupt:
        print("\n[CLIENT] Stopped by user.")
        break

    except Exception as e:
        print(f"[CLIENT] Error: {e}")
        break

client_sock.close()
print("[CLIENT] Connection closed.")
