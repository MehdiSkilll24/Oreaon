import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

REQUIRED_FIELDS = {
    "piper_dir": "Path to your Piper TTS folder (contains piper.exe)",
    "piper_voice": "Voice model name (e.g. en_US-ryan-medium)",
    "whisper_model": "Full path to your faster-whisper model folder",
    "nircmd_path": "Full path to nircmdc.exe",
    "brave_exe": "Full path to brave.exe",
    "intro_song": "Full path to your intro MP3 (leave blank to skip)",
    "logo_path": "Full path to logo.png",
    "downloads_dir": "Full path to your Downloads folder",
    "documents_dir": "Full path to your Documents folder",
    "music_dir": "Full path to your Music folder",
    "output_wav": "Full path for command.wav output file",
    "temp_speech": "Full path for temp_speech.txt",
    "calendar_file": "Full path for calendar.json",
    "calendar_html": "Full path for calendar.html",
    "latitude": "Your latitude for weather (e.g. 30.5728)",
    "longitude": "Your longitude for weather (e.g. 104.0668)",
}

PATH_FIELDS = {
    "piper_dir", "whisper_model", "nircmd_path",
    "brave_exe", "logo_path", "downloads_dir",
    "documents_dir", "music_dir", "output_wav", "temp_speech"
}

def _setup():
    # Load existing config if it exists
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            try:
                cfg = json.load(f)
            except json.JSONDecodeError:
                cfg = {}

    changed = False
    for key, prompt in REQUIRED_FIELDS.items():
        # Skip fields that are already filled
        if cfg.get(key):
            continue

        value = input(f"{prompt}: ").strip()

        # Validate path fields — warn but don't block
        if key in PATH_FIELDS and value and not os.path.exists(value):
            print(f"Warning: path '{value}' does not exist. Check it before running.")

        # Validate numeric fields
        if key in ("latitude", "longitude"):
            try:
                float(value)
            except ValueError:
                print(f"Invalid number for {key}, defaulting to 0.")
                value = "0"

        cfg[key] = value
        changed = True

    if changed:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        print("Config saved to config.json.\n")

    return cfg


_cfg = _setup()

PIPER_DIR     = _cfg.get("piper_dir", "")
PIPER_VOICE   = _cfg.get("piper_voice", "")
WHISPER_MODEL = _cfg.get("whisper_model", "")
NIR_CMD_PATH   = _cfg.get("nircmd_path", "")
BRAVE_EXE     = _cfg.get("brave_exe", "")
INTRO_SONG    = _cfg.get("intro_song", "")
LOGO_PATH     = _cfg.get("logo_path", "")
DW_DIR        = _cfg.get("downloads_dir", "")
DC_DIR        = _cfg.get("documents_dir", "")
MUSIC_DIR     = _cfg.get("music_dir", "")
OUTPUT_WAV    = _cfg.get("output_wav", "")
TEMP_SPEECH   = _cfg.get("temp_speech", "")
CALENDAR_FILE = _cfg.get("calendar_file", "")
HTML_FILE     = _cfg.get("calendar_html", "")

try:
    CHENGDU_LAT = float(_cfg.get("latitude", 0))
    CHENGDU_LON = float(_cfg.get("longitude", 0))

except ValueError:
    CHENGDU_LAT = 0.0
    CHENGDU_LON = 0.0   