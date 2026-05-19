import sounddevice as sd
import numpy as np
import time
import state
import listener

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
CLAP_THRESHOLD = 0.1  # RMS threshold — tune this to your mic sensitivity
DOUBLE_CLAP_WINDOW = 0.8

def get_rms(chunk):
    return np.sqrt(np.mean(chunk.astype(np.float32) ** 2) / 32768 ** 2)

def detect_claps(audio_queue):
    last_clap_time = 0
    clap_count = 0
    in_clap = False
    triggered = False

    def callback(indata, frame, time_info, status):
        nonlocal last_clap_time, clap_count, in_clap, triggered

        if state.current_state == "listening":
            return
        
        rms = get_rms(indata[:, 0])

        if rms >= CLAP_THRESHOLD and not in_clap:
            in_clap = True
            now = time.time()
            if now - last_clap_time < DOUBLE_CLAP_WINDOW:
                clap_count += 1
            else:
                clap_count = 1

            last_clap_time = now

            if clap_count >= 2:
                clap_count = 0
                triggered = True

        elif rms < CLAP_THRESHOLD * 0.5:
            in_clap = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,dtype=np.int16, blocksize=CHUNK_SIZE, callback=callback, device=1):
        while True:
            if triggered:
                state.current_state = "listening"
                triggered = False
                audio_queue.put(listener.rec(True))
            time.sleep(0.05)