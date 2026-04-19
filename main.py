import tts, listener, brain, executor, time


def handle_action(action, target, then, context = None):
    print(f"handle_action called: action={action}, target={target}, context={context}")
    if action == "speak":
        tts.speak(target)
        return True, context
    
    elif action == "stop":
        tts.speak("Shutting down.")
        return False, context
    
    elif action == "search":
        if context and context in executor.SEARCH_URLS:
            url = executor.SEARCH_URLS[context] + target.replace(" ", "+")
            executor.open_url(url)
        else:
            url = executor.run_search(target)
        return True, context
    
    elif action == "open":
        context = target
        url = executor.comparison(target)
        if url == None:
            return False, context
        if not then:
            executor.open_url(url)
        
        return True, context
        
    elif action == "play":
        if not context or context not in executor.SEARCH_URLS:
            tts.speak("I don't know where to play that.")
            return True, context
        url = executor.SEARCH_URLS[context] + target.replace(" ", "+")
        executor.play(url, context)
        return True, context

    else:
        tts.speak("I'm not sure I understood that.")
        return True, context
        
if __name__ == "__main__":
    tts.speak("Jarvis online and ready, how can I help you, sir ?")
    flag = True
    context = None
    while flag:
        listener.wait_for_clap()
        path = listener.record_command()
        t = time.time()
        text = brain.transcribe(path).lower()
        print(text)
        response = brain.understand(text)
        print(response)
        print(response.get("then"))
        action = response.get("action")
        target = response.get("target")
        flag, context = handle_action(action, target, bool(response.get("then")))
        if response.get("then"):
            then = response.get("then")
            flag, context = handle_action(then["action"], then["target"], True, context)

