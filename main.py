import tts, listener, brain, executor


if __name__ == "__main__":
    tts.speak("Jarvis online and ready, how can I help you, sir ?")
    while True:
        listener.wait_for_clap()
        path = listener.record_command()
        text = brain.transcribe(path).lower()
        response = brain.understand(text)
        url = executor.comparison(response["target"])
        if not url:
            tts.speak("Would you like to do something else?")
            ans = str(input(""))
            if ans != 'yes':
                break

    