import tts, listener, brain, executor, keyboard, reminder_checker, threading, ollama, os
from faster_whisper import WhisperModel

os.environ["HF_HUB_OFFLINE"] = "1"

def load_whisper():
    global whisper_model
    whisper_model = WhisperModel(
        r"C:\Users\mehdi\.cache\huggingface\hub\models--Systran--faster-whisper-tiny\snapshots\d90ca5fe260221311c53c58e660288d3deb8d356",
        device="cuda",
        compute_type="float16",
    )
    print("Whisper ready")

def load_browser():
    global browser
    browser = executor.get_browser()
    print("Browser ready")

def load_ollama():
    # Warm up Ollama with dummy request
    ollama.chat(model="qwen3:1.7b", messages=[{"role": "user", "content": "hi"}])
    print("Ollama ready")

t1 = threading.Thread(target=load_whisper)
t3 = threading.Thread(target=load_ollama)

t1.start()
t3.start()

t1.join()
t3.join()

ACTION_HANDLERS = {
    "speak": executor.handle_speak,
    "stop": executor.handle_stop,
    "search": executor.handle_search,
    "open": executor.handle_open,
    "play": executor.handle_play,
    "delete": executor.handle_delete,
    "find": executor.handle_find,
    "control": executor.handle_control,
    "weather": executor.handle_weather,
    "sysinfo": executor.handle_sys,
    "window": executor.handle_window,
    "spotify": executor.handle_spotify,
    "reminder": reminder_checker.handle_reminder,
    "calendar": executor.handle_calendar,
    "schedule": executor.handle_schedule,

}

def handle_unknown(response, context):
    tts.speak("I don't know this action")
    return True, context


def dispatch(action, response, context):
    handler = ACTION_HANDLERS.get(action, handle_unknown)
    return handler(response, context)

def wait_for_input():
    keyboard.wait('f8')
    return listener.rec()

if __name__ == "__main__":
    tts.speak("Ready")
    flag = True
    context = None
    while flag:
        path = wait_for_input()
        text = brain.transcribe(path).lower()
        print(text)
        response = brain.understand(text)
        action = response.get("action")
        
        print(response)
        flag, context = dispatch(action, response, context)
        if response.get("then"):
            then = response.get("then")
            flag, context = dispatch(then["action"], then, context)