import json
import os
import webbrowser

if os.path.exists("targets.json"):
    with open("targets.json", "r") as f:
        TARGETS = json.load(f)
else:
    TARGETS = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "steam": "steam://open/main",
    "settings": "ms-settings:",
    "music": "https://open.spotify.com"
    }
    with open("targets.json", "w") as f:
        json.dump(TARGETS, f)


def comparison(target_url):
    url = TARGETS.get(target_url, "Nothing found!")
    if url == "Nothing found!":
        decision = str(input("Would you like to add this new command?"))
        while decision.lower() != 'yes' and decision.lower() != 'no':
            decision = str(input("Wrong, input. Would you like to add this new command?(yes/no)"))

        if decision == 'yes':
            new_target = str((input("Enter the website name")))
            new_url = str((input("Please, paste its URL")))
            TARGETS[new_target] = new_url
            with open("targets.json", "w") as f:
                json.dump(TARGETS, f)
            
            return new_url
        
        return None
    webbrowser.open(url)
    return url 

