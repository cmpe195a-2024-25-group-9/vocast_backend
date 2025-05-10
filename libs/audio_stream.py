from singleton.global_vars import global_state
import sounddevice as sd
import socket
import numpy as np

def stream_mic():
    SAMPLE_RATE = 48000
    CHUNK_SIZE = 256
    UDP_IP = global_state.esp_ip
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
        global_state.stop_flag.clear()
        while not global_state.stop_flag.is_set():
            pass