DTLS UDP example

Files:
- computer1_server.py
- computer2_client.py

Client SERVER_IP is already set to:
10.223.132.67

Run in PowerShell:
cd "D:\1.Internship\16_MARCH\MARCH_16_MARK_1\dtls_udp_example"
pip install python-mbedtls
python computer1_server.py

On client laptop:
cd "D:\1.Internship\16_MARCH\MARCH_16_MARK_1\dtls_udp_example"
pip install python-mbedtls
python computer2_client.py
