# Oreaon — Local Voice Assistant

A fully offline, Iron Man-inspired voice assistant for Windows. Double-clap or press F8 to activate, speak a command, and Oreaon handles it — no cloud, no API keys, no cost.

---

## How It Works

```
Clap/F8 → Record command → Whisper transcribes → Ollama parses → Browser/OS executes
```

---

## Stack

| Layer | Tool |
|---|---|
| Wake detection | RMS pre-filter → CNN binary classifier on mel spectrogram, or F8 |
| Speech-to-text | `faster-whisper` (tiny, CUDA float16) |
| Command parsing | Ollama — `qwen2.5:1.5b` |
| Browser control | Playwright (CDP connection to Brave) |
| Text-to-speech | Piper TTS — Ryan voice (local, offline) |
| Audio playback | `sounddevice` + `numpy` |
| UI overlay | PyQt5 floating blob widget |
| Clap classifier | PyTorch CNN trained on mel spectrograms |

---

## Requirements

### System
- Windows 10/11
- NVIDIA GPU with CUDA 12.x
- [Ollama](https://ollama.com) installed and running
- [Brave Browser](https://brave.com) installed
- [Piper TTS](https://github.com/rhasspy/piper/releases) — `piper_windows_amd64.zip` extracted
- Piper voice model — `en_US-ryan-medium.onnx` + `.onnx.json` from [HuggingFace](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ryan/medium)

### Python
```bash
pip install faster-whisper sounddevice numpy scipy playwright pyautogui ollama pyqt5 keyboard psutil screen-brightness-control send2trash pygetwindow pycaw imaplib2 torch torchaudio scikit-learn
playwright install
```

### Ollama model
```bash
ollama pull qwen2.5:1.5b
```

---

## Project Structure

```
Oreaon/
    main.py               # Orchestrator — runs the main loop
    brain.py              # Whisper transcription + Ollama command parsing
    executor.py           # All action handlers + browser control
    tts.py                # Text-to-speech via Piper, async + interruptible
    listener.py           # Voice recording with silence detection
    clap_detector.py      # Double-clap activation — RMS pre-filter + ML verification
    inference.py          # ClapDetector class — loads model, runs prediction
    model.py              # CNN architecture definition
    dataset.py            # Dataset class — loads wavs, mel spectrogram transform
    train.py              # Training script — stratified split, BCEWithLogitsLoss
    cfg.py                # Shared config — MEL_PARAMS, SAMPLE_RATE, TARGET_LENGTH
    best_model.pt         # Trained model weights
    record_negatives.py   # Utility script to record negative training samples
    ui.py                 # Floating PyQt5 bubble overlay
    state.py              # Shared state between threads
    reminder_checker.py   # Reminder scheduling and firing
    email_handler.py      # Gmail send/read via SMTP and IMAP
    targets.json          # URL dictionary (auto-generated)
    contacts.json         # Email contacts (auto-generated)
    secrets.json          # Gmail credentials (never commit this)
    calendar.json         # Scheduled events
    conversation_history.json  # Persistent chat memory
    data/
        claps/            # Positive training samples (wav) — not committed
        negatives/        # Negative training samples (wav) — not committed
    voices/
        piper/
            piper.exe
            en_US-ryan-medium.onnx
            en_US-ryan-medium.onnx.json
```

---

## Configuration

Update the hardcoded paths in `tts.py`, `listener.py`, and `executor.py` to match your machine before running.

Create `secrets.json` for email features:
```json
{
    "gmail_address": "your.email@gmail.com",
    "gmail_app_password": "your-16-char-app-password"
}
```

Never commit `secrets.json` to version control.

---

## Usage

```bash
cd C:\path\to\Oreaon
python main.py
```

1. Oreaon announces itself and loads models (~7 seconds warm start)
2. Double-clap for the first launch intro sequence (weather, system status, fun fact)
3. Double-clap or press F8 to activate, speak your command
4. Press F7 to type a command instead
5. Press F8 mid-speech to interrupt Oreaon and give a new command

---

## What It Can Do

| Command example | What happens |
|---|---|
| "open YouTube" | Opens YouTube in Brave, reuses existing tab |
| "open new YouTube" | Forces a new tab regardless |
| "search for quantum physics" | Searches Brave, reads AI summary aloud |
| "play rap music" | Opens Spotify, searches genre, starts first track |
| "open YouTube and play Bohemian Rhapsody" | Chains two actions |
| "set volume to 60" | Sets system volume via NirCmd |
| "increase brightness by 20" | Adjusts screen brightness |
| "pause" / "next" | Media controls via keyboard injection into active browser tab |
| "what's the weather in 3 hours?" | Fetches Open-Meteo forecast, speaks it |
| "remind me to call mom at 3 PM" | Schedules a reminder |
| "check my emails" | Reads subject lines of 5 most recent Gmail messages |
| "summarize emails from Mehdi" | Fetches body, summarizes via Ollama |
| "send an email to mom saying I'll be late" | Sends via Gmail SMTP |
| "what's my CPU?" | Reads system stats |
| "minimize chrome" | Controls windows via pygetwindow |
| "should I eat apples or bananas?" | Conversational response with history |
| "goodbye" | Shuts down cleanly |

---

## Why These Tools

**faster-whisper over standard Whisper**

Standard Whisper runs on CPU by default. faster-whisper uses a CTranslate2 backend that runs on the RTX 2060 with float16 — roughly 4x faster. The tradeoff is the tiny model misses words occasionally, which is partially handled by confidence thresholds: segments with high `no_speech_prob` or low `avg_logprob` get rejected rather than passed as garbage to the parser.

**qwen2.5:1.5b over qwen3:1.7b**

qwen3:1.7b has a built-in reasoning chain that it runs regardless of whether you tell it not to. Every command triggered 3-8 seconds of internal "thinking" before returning an answer. qwen2.5:1.5b has no thinking chain, drops response time to under a second, and the accuracy difference on structured command parsing is negligible.

**Piper over gTTS or ElevenLabs**

gTTS requires internet and sends your text to Google. ElevenLabs charges per character. Piper runs entirely on-device, adds zero network latency, works without internet, and works in regions with API restrictions. The tradeoff is voice quality — it's not ElevenLabs. For a voice assistant that speaks short commands and weather reports, it's fine.

**Playwright + CDP over webbrowser module**

`webbrowser.open()` is fire-and-forget — you can't interact with the page after opening it. Playwright connects to an already-running Brave instance via Chrome DevTools Protocol, which means it reuses your existing session with all cookies and logins intact. Spotify stays logged in, tabs restore between restarts, and Oreaon can click, type, and read page content.

**format="json" over regex parsing**

Regex on LLM output breaks the moment the model adds an extra space, newline, or decides to wrap its answer in a sentence. `format="json"` enforces valid JSON at the inference level — the model physically cannot produce malformed output. It also runs slightly faster since the model skips generating any prose.

**Conversation summarization over truncation**

At 25 exchanges, the history gets summarized into a few sentences by the same model, then replaces the full log. Truncation would just delete early context. Summarization keeps the semantic content — if you mentioned something important 20 messages ago, it survives in the summary. The 25-message limit was chosen to balance context depth against the 4096-token context window.

**Threading at startup**

Cold startup used to take 23 seconds. Whisper and Ollama were loading sequentially. Both are now loaded in parallel threads, and Ollama was moved from a cloud/remote endpoint to a local instance. Startup is now ~7 seconds.

---

## Clap Detection — ML Pipeline

The original clap detector triggered on any sound exceeding an RMS amplitude threshold. This meant blowing into the mic, dropping something, or any sharp noise would activate Oreaon. RMS measures loudness only — it carries no information about what the sound actually is.

**The fix: mel spectrogram + CNN binary classifier.**

A mel spectrogram converts a raw audio waveform into a 2D frequency-time representation — the x-axis is time, the y-axis is frequency on a perceptually-scaled mel scale, and pixel intensity encodes energy. A clap has a distinctive pattern in this space: a sharp vertical stripe of broadband energy (all frequencies excited simultaneously) that appears and disappears in milliseconds. Blowing into a mic produces sustained low-frequency energy — a completely different shape. This gives the model a feature-rich 2D image to classify rather than a single amplitude scalar.

The architecture is a three-layer CNN followed by global average pooling and two linear layers ending in a single sigmoid output (binary classification: clap vs not-clap). Training used BCEWithLogitsLoss with a stratified 80/20 train/val split.

**Training data:** 164 double-clap recordings, 250 negative samples. Negatives were recorded in two phases — first a broad ambient session (silence, talking, keyboard, footsteps), then a targeted hard-negative session after identifying specific false positives in live testing.

**Iteration log:**

| Run | Claps | Negatives | Best val_loss | Best val_acc | Change |
|---|---|---|---|---|---|
| 1 | 115 | 150 | 0.2095 | 96.2% | Baseline — pipeline smoke test |
| 2 | 115 | 200 | 0.1556 | 96.8% | Added hard negatives (keys falling) — best overall |
| 3 | 115 | 250 | 0.2189 | 91.8% | Added more hard negatives (bottle) — class imbalance degraded results |
| 4 | 164 | 250 | 0.1859 | 92.8% | Rebalanced claps — partially recovered from run 3 regression |

Run 3 revealed that adding negatives without matching clap volume worsens the class ratio and hurts performance — the model sees roughly twice as many negatives per epoch and biases toward predicting "not a clap." Run 4 corrected this by recording additional claps.

**Deployment architecture:** RMS double-clap detection acts as a cheap pre-filter. Only when it fires does the CNN run inference on the buffered audio. This avoids running a neural network on every audio chunk continuously, keeping CPU overhead negligible.

**Honest limitations:** Validation accuracy is measured on held-out data from the same recording session, same room, same microphone. Real-world performance on a different mic or acoustic environment will likely be lower. Certain percussive hard negatives (objects falling on hard surfaces) still occasionally produce false positives despite targeted training data — the acoustic similarity to a clap in the mel spectrogram is high enough that the current dataset volume isn't sufficient to draw a clean boundary for every case.

---

## Known Limitations

- **Whisper tiny** drops words, especially with background noise or non-native accents. Upgrade to `base` or `small` for better accuracy at the cost of ~1-2s latency.
- **Spotify DOM selectors** are hardcoded against Spotify's current web player. If Spotify updates their frontend, playback control will break and selectors need updating.
- **Clap detection** uses a CNN trained on one microphone in one room. On a different mic or acoustic environment, the RMS threshold and/or model confidence threshold (`THRESHOLD = 0.7` in `inference.py`) may need retuning. Noise-cancelling headsets suppress clap transients aggressively — lower the RMS threshold toward 0.05 if double-claps aren't triggering.
- **CDP stale reference bug** — if Brave is closed while Oreaon is running, the browser reference goes stale. Oreaon detects and recovers from this, but the first command after reopen may fail.
- **Email body summarization** depends on plain-text email content. HTML-only emails with no text fallback will return empty body.
- **Command chaining** is limited to two actions. "Open YouTube and play X and search for Y" won't work.

---

## Adding New Commands

If Oreaon doesn't recognize an app or website, it asks whether to add it. New entries go into `targets.json` and are available immediately without restarting.

For email contacts, add them to `contacts.json`:
```json
{
    "mom": "mom@gmail.com",
    "john": "john.doe@gmail.com"
}
```

---

## License

MIT