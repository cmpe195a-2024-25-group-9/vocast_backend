from fastapi import FastAPI
from pydantic import BaseModel
import threading

app = FastAPI()

stream_thread = None
stop_flag = threading.Event()

# Request model
class StreamControl(BaseModel):
    start: bool

def stream_mic():
    import sounddevice as sd
    import socket
    import numpy as np

    SAMPLE_RATE = 48000
    CHUNK_SIZE = 256
    UDP_IP = "10.0.0.12"
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

@app.post("/stream")
def control_stream(req: StreamControl):
    global stream_thread

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
