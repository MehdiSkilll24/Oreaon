import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav


SAMPLE_RATE = 16000
CLAP_THRESHOLD = 0.3
SILENCE_TIMEOUT = 2
CHUNK_DURATION = 0.1
OUTPUT_WAV = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\command.wav"


def wait_for_clap():
    print("waiting for clap...")
    while True:
        chunk = sd.rec(int(CHUNK_DURATION*SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()
        peak = np.max(np.abs(chunk))
        if peak > CLAP_THRESHOLD:
            print(f"Clap detected! (peak: {peak:.2f})")
            sd.sleep(300)
            return
        
def record_command():
    silence = 0
    frames = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        chunk_samples = int(CHUNK_DURATION * SAMPLE_RATE)
        print("Waiting for command...")
        while True:
            chunk, _ = stream.read(chunk_samples)
            frames.append(chunk)
            peak = np.max(np.abs(chunk))
            if peak < 0.15:
                silence += CHUNK_DURATION

                if silence >= SILENCE_TIMEOUT:
                    break
            else:
                silence = 0
    audio = np.concatenate(frames, axis=0)
    audio_16 = (audio*32767).astype(np.int16)
    wav.write(OUTPUT_WAV, SAMPLE_RATE, audio_16)
    return OUTPUT_WAV

if __name__ == "__main__":
    wait_for_clap()
    record_command()


