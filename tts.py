import subprocess
import sounddevice as sd
import numpy as np
import wave
import time

PIPER_EXE = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\voices\piper\piper.exe"
VOICE_MODEL = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\voices\piper\en_US-lessac-medium.onnx.json"
OUTPUT_WAV = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\test.wav"

def speak(text: str):
    temp_file = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\temp_speech.txt"
    with open(temp_file, "w") as f:
        f.write(text)
    
    piper_dir = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\voices\piper"
    cmd = f'powershell -Command "Get-Content \'{temp_file}\' | & \'{piper_dir}\\piper.exe\' --model \'{piper_dir}\\en_US-lessac-medium.onnx\' --output_file \'{OUTPUT_WAV}\'"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    
    if result.returncode != 0:
        print(f"Stderr: {result.stderr}")
        return
    
    with wave.open(OUTPUT_WAV, 'rb') as f:
        rate = f.getframerate()
        frames = f.readframes(f.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
    
    audio = (audio * 0.7).astype(np.int16)

    time.sleep(0.3)
    sd.play(audio, samplerate=rate)
    sd.wait()

if __name__ == "__main__":
    speak("Oreaon ready sir")