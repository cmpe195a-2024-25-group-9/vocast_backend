from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from models.request_params import ConnectRequest, Message, StreamControl
from libs.audio_stream import stream_mic
from libs.networking import get_local_ip
from singleton.global_vars import global_state
import threading
import requests

router = APIRouter()
stream_thread = None

# USER endpoint, start stream to ESP
@router.post("/stream")
def control_stream(req: StreamControl):
    global stream_thread
    global_state.esp_ip = req.ip

    if req.start:
        if stream_thread and stream_thread.is_alive():
            return {"status": "already streaming"}
        stream_thread = threading.Thread(target=stream_mic, daemon=True)
        stream_thread.start()
        return {"status": "stream started"}
    else:
        if stream_thread and stream_thread.is_alive():
            global_state.stop_flag.set()
            stream_thread.join(timeout=2)
            return {"status": "stream stopped"}
        return {"status": "not streaming"}
    
# USER endpoint, request to connection to session given in req (expected to be admin session id/ip)
@router.post("/connect_to_session")
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
@router.post("/leave_session")
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

@router.websocket("/ws")
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
@router.post("/receive_message")
async def receive_message(req: Message):
    print(req)
    await websocket.send_text(req.msg)
    # TODO handle message from admin
    # this is where the user will receive messages from the admin
    # for now, just return a success message
    return {"message": "Message sent successfully"}