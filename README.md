# Jarvis

[README.md](https://github.com/user-attachments/files/26698211/README.md)
# Jarvis — Local Voice Assistant

A fully offline, Iron Man-inspired voice assistant for Windows. Press f8 to activate, speak a command, and Oreaon opens apps or websites — no cloud, no API keys, no cost.

---

## How It Works

```
Clap → Record command → Whisper transcribes → Ollama parses → Browser/OS executes
```

---

## Stack

| Layer | Tool |
|---|---|
| Wake detection | `sounddevice` (clap via amplitude spike) |
| Speech-to-text | `faster-whisper` (tiny, CUDA) |
| Reasoning | Ollama — `qwen3:1.7b` |
| Browser control | `webbrowser` (built-in) |
| Text-to-speech | Piper TTS (local, offline) |
| Audio playback | `sounddevice` + `numpy` |

---

## Requirements

### System
- Windows 10/11
- NVIDIA GPU with CUDA 12.x
- [Ollama](https://ollama.com) installed and running
- [Piper TTS](https://github.com/rhasspy/piper/releases) — `piper_windows_amd64.zip` extracted
- Piper voice model — `en_US-lessac-medium.onnx` + `.onnx.json` from [HuggingFace](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium)

### Python
```bash
pip install faster-whisper sounddevice numpy scipy playwright pyautogui ollama
```

### Ollama model
```bash
ollama pull qwen3:1.7b
```

---

## Project Structure

```
Jarvis/
    main.py           # Orchestrator — runs the main loop
    tts.py            # Text-to-speech via Piper
    listener.py       # Clap detection + voice recording
    brain.py          # Whisper transcription + Ollama command parsing
    executor.py       # URL/app launcher + target dictionary
    targets.json      # Persistent command dictionary (auto-generated)
    voices/
        piper/
            piper.exe
            en_US-lessac-medium.onnx
            en_US-lessac-medium.onnx.json
            espeak-ng-data/
```

---

## Configuration

Before running, update the hardcoded paths in `tts.py` and `listener.py` to match your machine:

```python
# tts.py
PIPER_EXE = r"C:\path\to\piper.exe"
VOICE_MODEL = r"C:\path\to\en_US-lessac-medium.onnx"

# listener.py
OUTPUT_WAV = r"C:\path\to\command.wav"
```

### Tunable parameters in `listener.py`

| Parameter | Default | Description |
|---|---|---|
| `CLAP_THRESHOLD` | `0.3` | Minimum amplitude to detect a clap (0–1) |
| `SILENCE_TIMEOUT` | `2` | Seconds of silence before stopping recording |
| `MAX_DURATION` | `3` | Maximum command recording length in seconds |

> If clap detection is too sensitive or not sensitive enough, adjust `CLAP_THRESHOLD` to match your mic and environment.

---

## Usage

```bash
cd C:\path\to\Jarvis
python main.py
```

1. Jarvis announces itself via TTS
2. Clap near your microphone
3. Speak your command (e.g. *"open YouTube"*)
4. Jarvis opens the target in your browser

---

## Default Commands

| Command | Target |
|---|---|
| open youtube | https://youtube.com |
| open google | https://google.com |
| launch steam | steam://open/main |
| open settings | ms-settings: |
| play music | https://open.spotify.com |

### Adding new commands

If Jarvis doesn't recognise a command, it will ask if you want to add it. New entries are saved to `targets.json` and available immediately on the next run.

---

## Known Limitations

- **Whisper tiny** may mishear commands, especially with non-native accents. Upgrade to `base` or `small` for better accuracy at the cost of speed.
- **Fan/background noise** can interfere with silence detection. Tune `CLAP_THRESHOLD` and the silence threshold in `listener.py` (`0.15` by default) to match your environment.
- **Max command duration** is capped at 3 seconds. Longer commands get truncated.
- **Single action only** — current version supports `open` commands only. Search, file operations, and OS control are planned for future versions.

---

## Roadmap

- [ ] Search commands ("search X on YouTube")
- [ ] OS-level control (open apps, move files)
- [ ] Wake word instead of clap activation
- [ ] Upgrade to `qwen3:8b` for complex commands
- [ ] GUI overlay

---

## License

MIT
