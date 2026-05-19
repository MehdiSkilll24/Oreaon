import subprocess
import sounddevice as sd
import numpy as np
import wave
import time, threading

PIPER_EXE = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\voices\piper\piper.exe"
VOICE_MODEL = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\voices\piper\en_US-lessac-medium.onnx.json"
OUTPUT_WAV = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\test.wav"

_tts_process = None
_stop_flag = False

def speak_async(text):
    threading.Thread(target=speak, args=(text,), daemon=True).start()

def stop_speaking():
    global _stop_flag, _tts_process
    _stop_flag = True
    if _tts_process:
        _tts_process.kill()
    sd.stop()

def speak(text: str):
    global _tts_process, _stop_flag
    _stop_flag = False

    temp_file = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\temp_speech.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(text)
    
    piper_dir = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\voices\piper"
    cmd = f'powershell -Command "Get-Content \'{temp_file}\' | & \'{piper_dir}\\piper.exe\' --model \'{piper_dir}\\en_US-lessac-medium.onnx\' --output_file \'{OUTPUT_WAV}\'"'
    
    _tts_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _tts_process.communicate()
    
    if _tts_process.returncode != 0:
        print(f"Stderr: {_tts_process.returncode}")
        return
    
    with wave.open(OUTPUT_WAV, 'rb') as f:
        rate = f.getframerate()
        frames = f.readframes(f.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
    
    audio = (audio * 0.7).astype(np.int16)

    time.sleep(0.3)
    sd.play(audio, samplerate=rate)

    while sd.get_stream().active and not _stop_flag:
        time.sleep(0.05)
    
    if _stop_flag:
        sd.stop()

if __name__ == "__main__":
    speak("Oreaon ready sir")