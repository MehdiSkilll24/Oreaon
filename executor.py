import json
import os, glob
import urllib.parse
from playwright.sync_api import sync_playwright
import difflib
import subprocess
import tts


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

SEARCH_URLS = {
    "youtube": "https://www.youtube.com/results?search_query=",
    "music": "https://open.spotify.com/search/"
}

_playwright = None
_browser = None

MUSIC_DIR = r"C:\Users\mehdi\Music"

def get_browser():
    global _playwright, _browser
    if _browser is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.connect_over_cdp("http://localhost:9222")
    return _browser

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
    return url 

def open_url(url):
    browser = get_browser()
    context = browser.contexts[0]
    page = context.new_page()
    page.goto(url)

def run_search(query):
    if not query:
        return
    encoded_query = urllib.parse.quote(query)
    # Changed from google.com to search.brave.com
    url = f"https://search.brave.com/search?q={encoded_query}"
    open_url(url)
    return url

def play(search_url, context):
    print(f"play() called with: {search_url}, {context}")
    browser = get_browser()
    browser_context = browser.contexts[0]
    page = browser_context.new_page()
    page.goto(search_url)
    if context == "youtube":
        page.wait_for_selector('a#video-title')
        page.click('a#video-title')
    elif context == "music":
        page.wait_for_selector('a[href*="/track/"]', state="visible")
        page.locator('a[href*="/track/"]').first.click()

def play_local(query):
    files = glob.glob(MUSIC_DIR + "\\*.mp3")
    names = [os.path.basename(f) for f in files]
    normalized_name = [os.path.splitext(n)[0].lower() for n in names]
    normalized_query = query.lower()
    matches = difflib.get_close_matches(normalized_query, normalized_name, n=1, cutoff=0.3)
    if matches:
        idx = normalized_name.index(matches[0])
        match_path = files[idx]
        subprocess.Popen([match_path], shell=True)
    else:
        tts.speak("I couldn't find that song.")