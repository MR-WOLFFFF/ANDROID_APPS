# ================================
# COMPUTER 1 : DTLS SERVER
# ================================

import socket
import time
from contextlib import suppress

from mbedtls.tls import DTLSConfiguration, HelloVerifyRequest, ServerContext

# ----------------
# USER SETTINGS
# ----------------
BIND_IP = "0.0.0.0"
PORT = 4433

PSK_IDENTITY = "raj-client"
PSK_SECRET = b"raj-demo-secret-123456"

BUFFER_SIZE = 4096

# ----------------
# HELPER FUNCTION
# ----------------
def make_dtls_connection(server_sock):
    """
    Complete DTLS server handshake with cookie verification.
    """
    conn, addr = server_sock.accept()
    conn.setcookieparam(addr[0].encode("ascii"))

    with suppress(HelloVerifyRequest):
        conn.do_handshake()

    previous_conn = conn
    _, (conn, addr) = conn, conn.accept()
    previous_conn.close()

    conn.setcookieparam(addr[0].encode("ascii"))
    conn.do_handshake()

    return conn, addr

# ----------------
# CREATE SERVER
# ----------------
config = DTLSConfiguration(
    validate_certificates=False,
    pre_shared_key_store={PSK_IDENTITY: PSK_SECRET},
    read_timeout=5.0,
)

raw_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_sock = ServerContext(config).wrap_socket(raw_sock)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((BIND_IP, PORT))

print(f"[SERVER] Listening on {BIND_IP}:{PORT}")
print(f"[SERVER] PSK Identity = {PSK_IDENTITY}")
print("[SERVER] Waiting for secure DTLS client...\n")

# ----------------
# MAIN LOOP
# ----------------
while True:
    try:
        conn, addr = make_dtls_connection(server_sock)
        print(f"[SERVER] Secure connection established with {addr}")

        while True:
            data = conn.recv(BUFFER_SIZE)

            if not data:
                time.sleep(0.01)
                continue

            text = data.decode("utf-8", errors="replace")
            print(f"[SERVER] Received: {text}")

            if text.lower().strip() == "quit":
                conn.send(b"bye")
                print("[SERVER] Client requested disconnect.\n")
                break

            reply = f"ACK:{text}".encode("utf-8")
            conn.send(reply)

    except KeyboardInterrupt:
        print("\n[SERVER] Stopped by user.")
        break

    except Exception as e:
        print(f"[SERVER] Error: {e}")
        print("[SERVER] Waiting for next client...\n")
