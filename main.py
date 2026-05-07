import tts, listener, brain, executor, keyboard, reminder_checker


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

    _ = brain.transcribe(brain.audio_path)
    _ = brain.understand("test")


    tts.speak("Oreaon online, how can I help ?")
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