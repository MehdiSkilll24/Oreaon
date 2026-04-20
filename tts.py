import subprocess
import sounddevice as sd
import numpy as np
import wave
import time

PIPER_EXE = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\voices\piper\piper.exe"
VOICE_MODEL = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\voices\piper\en_US-lessac-medium.onnx"
OUTPUT_WAV = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\test.wav"

def speak(text: str):
    subprocess.run(
        f'echo {text} | "{PIPER_EXE}" --model "{VOICE_MODEL}" --output_file "{OUTPUT_WAV}"',
        shell=True
    )
    with wave.open(OUTPUT_WAV, 'rb') as f:
        rate = f.getframerate()
        frames = f.readframes(f.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
    time.sleep(0.3)
    sd.play(audio, samplerate=rate)
    sd.wait()

if __name__ == "__main__":
    speak("Jarvis online and ready.")