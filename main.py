from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import socket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stream_thread = None
stop_flag = threading.Event()
esp_ip = None # esp ip address to stream audio and display on admin panel for users to connect to
admin_ip = None # admin ip address to display on admin panel for users to join session

# Request model
class StreamControl(BaseModel):
    start: bool
    ip: str = None

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
    global esp_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 12345))  # Listen on all interfaces, port 12345
    print("Listening for ESP IP broadcasts on port 12345...")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()
        print(f"Received from {addr}: {message}")
        if message.startswith("ESP IP:"):
            esp_ip = addr[0]  # Save just the sender's IP

def stream_mic():
    import sounddevice as sd
    import socket
    import numpy as np

    SAMPLE_RATE = 48000
    CHUNK_SIZE = 256
    UDP_IP = esp_ip
    UDP_PORT = 12345

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def callback(indata, frames, time, status):
        if status:
            print(status)
        mono = indata[:, 0]
        mono_int16 = (mono * 32767).astype(np.int16)
        stereo = np.empty((mono_int16.shape[0], 2), dtype=np.int16)
        stereo[:, 0] = mono_int16
        stereo[:, 1] = mono_int16
        sock.sendto(stereo.tobytes(), (UDP_IP, UDP_PORT))

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32',
                        blocksize=CHUNK_SIZE, callback=callback): # latency = '0.00001'
        print("Streaming mic audio as stereo via UDP...")
        stop_flag.clear()
        while not stop_flag.is_set():
            pass

'''
    startup function, listens for esp ip address when it is initially broadcasting
'''
    
@app.on_event("startup")
def start_udp_listener():
    thread = threading.Thread(target=listen_for_esp_ip, daemon=True)
    thread.start()

'''
    api endpoints defined below
'''

# ADMIN endpoint, return IP address of esp
@app.get("/esp_ip")
def get_esp_ip():
    if 'IP' in globals():
        return {"esp_ip": esp_ip}
    else:
        return {"error": "ESP IP not found"}
    
# ADMIN endpoint, return IP address of this computer
@app.get("/admin_ip")
def read_admin_ip():
    ip = None
    if admin_ip:
        ip = admin_ip
    else:
        ip = get_local_ip()
    return {"admin_ip": ip}

# USER endpoint, start stream to ESP
@app.post("/stream")
def control_stream(req: StreamControl):
    global stream_thread
    global esp_ip 
    esp_ip = req.ip

    if req.start:
        if stream_thread and stream_thread.is_alive():
            return {"status": "already streaming"}
        stream_thread = threading.Thread(target=stream_mic, daemon=True)
        stream_thread.start()
        return {"status": "stream started"}
    else:
        if stream_thread and stream_thread.is_alive():
            stop_flag.set()
            stream_thread.join(timeout=2)
            return {"status": "stream stopped"}
        return {"status": "not streaming"}
