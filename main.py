from fastapi import FastAPI
from core.middleware import add_middlewares
from libs.networking import listen_for_esp_ip
from routes import user, admin
import threading

app = FastAPI()

app.include_router(user.router)
app.include_router(admin.router)
add_middlewares(app)
    
@app.on_event("startup")
def start_udp_listener():
    thread = threading.Thread(target=listen_for_esp_ip, daemon=True)
    thread.start()