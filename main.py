from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import socket
import requests

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
self_ip = None # admin ip address to display on admin panel for users to join session
active_connections = [] # list of active connections to the admin panel

# stream request model
class StreamControl(BaseModel):
    start: bool
    ip: str = None

class ConnectRequest(BaseModel):
    ip: str
    name: str

class Message(BaseModel):
    mic_permission: bool

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
    global esp_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 12345))  # Listen on all interfaces, port 12345
    print("Listening for ESP IP broadcasts on port 12345...")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()
        print(f"Received from {addr}: {message}")
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
    if esp_ip:
        return {"esp_ip": esp_ip}
    else:
        return {"error": "ESP IP not found"}
    
# ADMIN endpoint, return IP address of this computer
@app.get("/admin_ip")
def read_admin_ip():
    ip = None
    if self_ip:
        ip = self_ip
    else:
        ip = get_local_ip()
    return {"admin_ip": ip}

# ADMIN endpoint, handle connection request from user
# expect user ip address in connection request
@app.post("/admin_connect_handler")
def handle_connection(req: ConnectRequest):
    # TODO save given user ip in a list of active connections
    global active_connections
    active_connections.append({
        "address": req.ip,
        "name": req.name,
        "status": False
    })

    return {"message": f"successfully added {req.name} at {req.ip}"}

# ADMIN endpoint, handle connection leave request from user
# expect user ip address in connection request
@app.post("/admin_leave_handler")
def handle_connection(req: ConnectRequest):
    # TODO save given user ip in a list of active connections
    global active_connections
    for conn in active_connections:
        if conn["address"] == req.ip:
            active_connections.remove(conn)

    return {"message": f"successfully removed {req.name} at {req.ip}"}

# ADMIN endpoint, return list of active connections
@app.get("/active_connections")
def get_active_connections():
    global active_connections
    return {"active_connections": active_connections}

# ADMIN endpoint, toggle mic permission for specific connected user/ ip addr 
# assume payload is ip and name of user being given permission
@app.post("/toggle_mic_permission")
def toggle_mic_permission(req: ConnectRequest):
    global active_connections
    for conn in active_connections:
        if conn["address"] == req.ip:
            conn["status"] = not conn["status"]
            # TODO send message to user backend that mic permission toggled
            requests.post(f"http://{req.ip}:8000/receive_message", json={"mic_permission": conn['status']})
            return {"message": f"Mic permission for {req.name} at {req.ip} toggled to {conn['status']}"}
    return {"error": "Connection not found"}

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
    
# USER endpoint, request to connection to session given in req (expected to be admin session id/ip)
@app.post("/connect_to_session")
def connect_to_session(req: ConnectRequest):
    # get current ip address, make request to admin_ip provided in post request
    url = f"http://{req.ip}:8000/admin_connect_handler"
    payload = {"ip": get_local_ip(), "name": req.name}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to connect to session, status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    
# USER endpoint, request to leave session given in req (expected to be admin session id/ip)
@app.post("/leave_session")
def leave_session(req: ConnectRequest):
    # get current ip address, make request to admin_ip provided in post request
    url = f"http://{req.ip}:8000/admin_leave_handler"
    payload = {"ip": get_local_ip(), "name": req.name}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to connect to session, status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    
websocket = None 

@app.websocket("/ws")
async def websocket_endpoint(websocket_in: WebSocket):
    global websocket
    await websocket_in.accept()
    websocket = websocket_in
    try: 
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("WebSocket disconnected")

# USER endpoint, receive message from admin
@app.post("/receive_message")
async def receive_message(req: Message):
    print(req)
    await websocket.send_text(str(req.mic_permission))
    # TODO handle message from admin
    # this is where the user will receive messages from the admin
    # for now, just return a success message
    return {"message": "Message sent successfully"}
