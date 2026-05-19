import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tts

SAMPLE_RATE = 16000
SILENCE_TIMEOUT = 3
CHUNK_DURATION = 0.1
OUTPUT_WAV = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\command.wav"

def rec(clap_flag=False):
    silence = 0
    frames = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        chunk_samples = int(CHUNK_DURATION * SAMPLE_RATE)
        if clap_flag == False:
            tts.speak_async("Listening")
            
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
    rec()

