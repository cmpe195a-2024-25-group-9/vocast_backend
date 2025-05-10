from singleton.global_vars import global_state
import socket

# returns this devices ip address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def listen_for_esp_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 12345))  # Listen on all interfaces, port 12345
    print("Listening for ESP IP broadcasts on port 12345...")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()
        print(f"Received from {addr}: {message}")
        global_state.esp_ip = addr[0]  # Save just the sender's IP