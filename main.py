import tts, listener, brain, executor, state, ui, keyboard, reminder_checker, threading, ollama, os
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
    ollama.chat(model="qwen2.5:1.5b", messages=[{"role": "user", "content": "hi"}])
    print("Ollama ready")


ui_thread = threading.Thread(target=ui.run_ui, daemon=True)
ui_thread.start()
print("Ui on")

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
    "email_send": executor.handle_email_send,
    "email_check": executor.handle_email_check
}

def handle_unknown(response, context):
    tts.speak("I don't know this action")
    return True, context


def dispatch(action, response, context):
    handler = ACTION_HANDLERS.get(action, handle_unknown)
    return handler(response, context)

def wait_for_input():
    keyboard.wait('f8')
    tts.stop_speaking()
    state.current_state = "listening"
    return listener.rec()

if __name__ == "__main__":
    state.current_state = "speaking"
    tts.speak_async("Ready")
    flag = True
    context = None
    while flag:
        state.current_state = "idle"
        path = wait_for_input()
        
        try:
            text = brain.transcribe(path).lower()
            state.current_state = "thinking"
        except Exception:
            state.current_state = "speaking"
            tts.speak_async("Could you repeat that?")
            continue
        if not text:
            tts.speak_async("Could you repeat that?")
            continue

        print(text)

        response = brain.understand(text)
        action = response.get("action")

        if action == "speak":
            answer = brain.converse(text)
            print(answer)
            state.current_state = "speaking"
            tts.speak_async(answer)
            continue

        print(response)
        flag, context = dispatch(action, response, context)
        if response.get("then"):
            then = response.get("then")
            flag, context = dispatch(then["action"], then, context)
            