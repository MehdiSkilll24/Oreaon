import sounddevice as sd
import numpy as np
import time
import state
import scipy.io.wavfile
import collections
import os
from inference import ClapDetector

device=sd.default.device[0]
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
CLAP_THRESHOLD = 0.025  # RMS threshold — tune this to mic sensitivity
DOUBLE_CLAP_WINDOW = 0.8
BUFFER_SECONDS = 1.75

os.makedirs("data/claps", exist_ok=True)

buffer = collections.deque(maxlen=int(SAMPLE_RATE / CHUNK_SIZE *BUFFER_SECONDS))

detector = ClapDetector(model_path="best_model.pt")

def get_rms(chunk):
    return np.sqrt(np.mean(chunk.astype(np.float32) ** 2) / 32768 ** 2)

def detect_claps(audio_queue):
    last_clap_time = 0
    clap_count = 0
    in_clap = False
    triggered = False

    def callback(indata, frame, time_info, status):
        nonlocal last_clap_time, clap_count, in_clap, triggered
        buffer.append(indata.copy())


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

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,dtype=np.int16, blocksize=CHUNK_SIZE, callback=callback, device = device):
        while True:
            if triggered:
                triggered = False

                audio = np.concatenate(list(buffer), axis=0).flatten()
                audio_float = audio.astype(np.float32) / 32768.0
                
                if detector.predict(audio_float, SAMPLE_RATE):
                    state.current_state = "listening"
                    import listener
                    path = listener.rec()
                    audio_queue.put(path)

                else:
                    print("RMS detected but ML rejected - Ignoring..")

            time.sleep(0.05)

if __name__ == "__main__":
    import queue
    q = queue.Queue()
    print("Listening for double claps... Ctrl+C to stop.")
    detect_claps(q)