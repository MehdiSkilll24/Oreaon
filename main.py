import tts, listener, brain, executor

if __name__ == "__main__":
    tts.speak("Jarvis online and ready, how can I help you, sir ?")
    _ = None
    listener.wait_for_clap()
    while True:
        path = listener.record_command()
        text = brain.transcribe(path).lower()
        print(text)
        response = brain.understand(text)
        print(response)
        action = response.get("action")
        target = response.get("target")

        if action == "speak":
            _ = tts.speak(target)
        elif action == "stop":
            _ = tts.speak("Shutting down.")
            break
        elif action == "search":
            _ = executor.run_search(target)
        elif action == "open":
            _ = executor.comparison(target)
        else:
            tts.speak("I'm not sure I understood that.")

        if _ == None:
            tts.speak("How can I help ?")

    