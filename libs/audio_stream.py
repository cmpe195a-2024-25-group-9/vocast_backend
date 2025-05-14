from singleton.global_vars import global_state
import sounddevice as sd
import socket
import numpy as np

def stream_mic():
    ESP_IP = global_state.esp_ip
    UDP_PORT = 12345

    SAMPLE_RATE = 48000
    PACKET_SIZE = 1024
    OUTPUT_CHANNELS = 2
    DTYPE = 'float32'

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def callback(indata, frames, time, status):
        if status:
            print(status)
        # indata shape: (frames, 1), dtype float32
        mono = indata[:, 0]  # take mono input
        # Convert float32 [-1.0, 1.0] to int32
        int_data = np.int32(mono * 0x7FFFFFFF)
        # Duplicate for stereo (L = R)
        stereo_data = np.column_stack((int_data, int_data)).flatten()
        # Convert to bytes (little-endian int32)
        byte_data = stereo_data.astype('<i4').tobytes()

        # Stream in 1024-byte chunks
        for i in range(0, len(byte_data), PACKET_SIZE):
            chunk = byte_data[i:i + PACKET_SIZE]
            sock.sendto(chunk, (ESP_IP, UDP_PORT))

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype=DTYPE,
            blocksize=PACKET_SIZE, callback=callback): # latency = '0.00001'
        print("Streaming mic audio as stereo via UDP...")
        global_state.stop_flag.clear()
        while not global_state.stop_flag.is_set():
            pass