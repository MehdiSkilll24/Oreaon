import sounddevice as sd
import scipy.io.wavfile
import os
import time

os.makedirs("data/negatives", exist_ok=True)

DURATION = 1          # seconds per clip
SAMPLE_RATE = 44100
NUM_CLIPS = 250      # adjust to taste
DEVICE = 1             # confirmed: Headset Microphone (Jabra Link 380)

print(f"Recording {NUM_CLIPS} negative clips of {DURATION}s each.")
print("Vary what you do between clips: talk, type, move chair, footsteps,")
print("door, single isolated claps, silence, background noise, etc.")
print("Starting in 3 seconds...")
time.sleep(3)

for i in range(199, NUM_CLIPS):
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        device=DEVICE,
    )
    sd.wait()
    filename = f"data/negatives/neg_{i}.wav"
    scipy.io.wavfile.write(filename, SAMPLE_RATE, audio)
    print(f"Recorded {i+1}/{NUM_CLIPS} -> {filename}")

print("Done.")