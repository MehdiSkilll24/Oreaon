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
    print("Listening for command...")
    MAX_DURATION = 3
    audio = sd.rec(int(MAX_DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    
    # Find where silence starts at the end
    chunk_samples = int(CHUNK_DURATION * SAMPLE_RATE)
    end_sample = len(audio)
    silent_duration = 0.0
    
    for i in range(0, len(audio), chunk_samples):
        chunk = audio[i:i+chunk_samples]
        peak = np.max(np.abs(chunk))
        if peak < 0.15:
            silent_duration += CHUNK_DURATION
        else:
            silent_duration = 0.0
        if silent_duration >= SILENCE_TIMEOUT:
            end_sample = i
            break
    
    audio = audio[:end_sample]
    audio_int16 = (audio * 32767).astype(np.int16)
    wav.write(OUTPUT_WAV, SAMPLE_RATE, audio_int16)
    return OUTPUT_WAV

if __name__ == "__main__":
    wait_for_clap()
    record_command()


