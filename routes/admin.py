from fastapi import APIRouter
from models.request_params import ConnectRequest, Message
from libs.networking import get_local_ip
from singleton.global_vars import global_state
import requests

router = APIRouter()
active_connections = []

# ADMIN endpoint, return IP address of esp
@router.get("/esp_ip")
def get_esp_ip():
    if global_state.esp_ip:
        return {"esp_ip": global_state.esp_ip}
    else:
        return {"error": "ESP IP not found"}
    
# ADMIN endpoint, return IP address of this computer
@router.get("/admin_ip")
def read_admin_ip():
    ip = get_local_ip()
    return {"admin_ip": ip}

# ADMIN endpoint, handle connection request from user
# expect user ip address in connection request
@router.post("/admin_connect_handler")
def handle_connection(req: ConnectRequest):
    global active_connections
    active_connections.append({
        "address": req.ip,
        "name": req.name,
        "status": False
    })

    return {"message": f"successfully added {req.name} at {req.ip}"}

# ADMIN endpoint, handle connection leave request from user
# expect user ip address in connection request
@router.post("/admin_leave_handler")
def handle_connection(req: ConnectRequest):
    global active_connections
    for conn in active_connections:
        if conn["address"] == req.ip:
            active_connections.remove(conn)
            return {"message": f"successfully removed {req.name} at {req.ip}"}
    return {"error": "Connection not found"}

# ADMIN endpoint, return list of active connections
@router.get("/active_connections")
def get_active_connections():
    global active_connections
    return {"active_connections": active_connections}

# ADMIN endpoint, return mic perm status of given user ip
@router.get("/get_status/")
def get_status(user_ip: str):
    global active_connections
    for conn in active_connections:
        if conn["address"] == user_ip:
            return {"connected_status": True, "mic_status": conn["status"]}
    return {"connected_status": False, "mic_status": False}

# ADMIN endpoint, toggle mic permission for specific connected user/ ip addr 
# assume payload is ip and name of user being given permission
@router.post("/toggle_mic_permission")
def toggle_mic_permission(req: ConnectRequest):
    global active_connections
    for conn in active_connections:
        if conn["address"] == req.ip:
            conn["status"] = not conn["status"]
            # TODO send message to user backend that mic permission toggled
            requests.post(f"http://{req.ip}:8000/receive_message", json={"msg": f"MIC_PERM {conn['status']}"})
            return {"message": f"Mic permission for {req.name} at {req.ip} toggled to {conn['status']}"}
    return {"error": "Connection not found"}

# ADMIN endpoint, broadcast given name to all active connections
# used to send name of speaker, and also sends "" when user turns off mic
@router.post("/broadcast_name")
def broadcast_name(req: Message):
    for conn in active_connections:
        requests.post(f"http://{conn['address']}:8000/receive_message", json={"msg": f"SPEAKER {req.msg}"})

    return {"message": "broadcasted name to all active connections"}

@router.post("/post_question")
def post_question(req: Message):
    for conn in active_connections:
        requests.post(f"http://{conn['address']}:8000/receive_message", json={"msg": f"QUESTION {req.msg}"})

    return {"message": "broadcasted question to all active connections"}

def handle_hand_movement(movement: str, req: ConnectRequest):
    requests.post(f"http://{req.ip}:8000/receive_message", json={"msg": f"{movement} {req.name}"})

    return {"message": f"alerted admin that user {req.name} has {movement}"}

@router.post("/handle_raise_hand")
def handle_raise_hand(req: ConnectRequest):
    return handle_hand_movement("RAISE_HAND", req)

@router.post("/handle_lower_hand")
def handle_lower_hand(req: ConnectRequest):
    return handle_hand_movement("LOWER_HAND", req)