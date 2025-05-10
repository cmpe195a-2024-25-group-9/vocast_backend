import threading

class GlobalState:
    def __init__(self):
        self.stop_flag = threading.Event()
        self.esp_ip = None  # esp ip address to stream audio and display on admin panel for users to connect to

global_state = GlobalState()