import tts, listener, brain, executor, keyboard, subprocess


def handle_action(action, target, then, folder, operation, value, context = None):
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

    elif action == "delete":
        executor.delete(target, folder)
        return True, context

    elif action == "find":
        matches = executor.find_files(target, folder)
        if matches:
            full_path, file_name, folder_name = matches[0]
            subprocess.Popen(f'explorer /select,"{full_path}"')
        else:
            tts.speak(f"File {target} not found.")

        return True, context
    
    elif action == "control":
        executor.control(target, operation, value)
        return True, context
    
    else:
        tts.speak("I'm not sure I understood that.")
        return True, context

def wait_for_input():
    keyboard.wait('f8')
    return listener.rec()

if __name__ == "__main__":
    tts.speak("Jarvis online and ready, how can I help you, sir ?")
    flag = True
    context = None
    while flag:
        path = wait_for_input()
        text = brain.transcribe(path).lower()
        print(text)
        response = brain.understand(text)
        print(response)
        action = response.get("action")
        target = response.get("target")
        folder = response.get("folder")
        operation = response.get("operation")
        value = response.get("value")
        print(response.get("then"))
        flag, context = handle_action(action, target, bool(response.get("then")), folder, operation, value, context)
        if response.get("then"):
            then = response.get("then")
            operation = then.get("operation")
            value = then.get("value")
            flag, context = handle_action(then["action"], then["target"], True, folder, operation, value, context)
            

