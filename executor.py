import json
import os
import urllib.parse
from playwright.sync_api import sync_playwright
import difflib
import send2trash
import tts
import pyautogui
from screen_brightness_control import get_brightness, set_brightness
import subprocess

DW_DIR = r"C:\Users\mehdi\Downloads"
DC_DIR = r"C:\Users\mehdi\Documents"
MUSIC_DIR = r"C:\Users\mehdi\Music"
NIR_CMD_PATH = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\nircmd-x64\nircmdc.exe"


if os.path.exists("targets.json"):
    with open("targets.json", "r") as f:
        TARGETS = json.load(f)
else:
    TARGETS = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "steam": "steam://open/main",
    "settings": "ms-settings:",
    "spotify": "https://open.spotify.com"
    }
    with open("targets.json", "w") as f:
        json.dump(TARGETS, f)

SEARCH_URLS = {
    "youtube": "https://www.youtube.com/results?search_query=",
    "spotify": "https://open.spotify.com/search/"
}

_playwright = None
_browser = None

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
    try:
        page = context.new_page()
        page.goto(url)
    except Exception as e:
        print(f"Page closed: {e}")


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
        try:
            page.wait_for_selector('a#video-title')
            page.click('a#video-title')
        except Exception as e:
            print(f"Page closed: {e}")
    elif context == "music":
        try:
            page.wait_for_selector('a[href*="/track/"]', state="visible")
            page.locator('a[href*="/track/"]').first.click()
        except Exception as e:
            print(f"Page closed: {e}")


def find_files(filename, folder=None):
    """
    Find files matching the given filename (fuzzy match with 0.85 cutoff).
    Strips extensions before matching. Blocks .exe and .sys files.
    
    If folder is specified, search only that folder.
    If folder is None, search all three (DW → DC → MUSIC) and return all matches.
    
    Returns: List of tuples: [(full_path, display_name, folder_name), ...]
    """
    search_order = [DW_DIR, DC_DIR, MUSIC_DIR]
    blocked_extensions = {'.sys'}
    
    if folder:
        if folder.lower() == "music":
            search_order = [MUSIC_DIR]
        elif folder.lower() == "downloads":
            search_order = [DW_DIR]
        elif folder.lower() == "documents":
            search_order = [DC_DIR]
    
    matches = []
    
    for directory in search_order:
        if not os.path.exists(directory):
            continue
        
        # Get all files in this directory, filter out blocked extensions
        try:
            all_items = [f for f in os.listdir(directory) 
            if os.path.splitext(f)[1].lower() not in blocked_extensions]
        except PermissionError:
            tts.speak(f"Permission denied accessing {directory}.")
            continue
        
        # Strip extensions for matching
        files_without_ext = [os.path.splitext(f)[0] for f in all_items]
        
        # Fuzzy match with cutoff 0.85 (catches single-char typos only)
        close_matches = difflib.get_close_matches(filename, files_without_ext, n=len(files_without_ext), cutoff=0.75)
        
        for match in close_matches:
            # Find the full filename (with extension) that matches
            original_file = all_items[files_without_ext.index(match)]
            full_path = os.path.join(directory, original_file)
            os.startfile(full_path)
            folder_name = os.path.basename(directory)
            matches.append((full_path, original_file, folder_name))
        
        # If folder was specified and we found matches, stop searching
        if matches and folder:
            break
    return matches


def delete(filename, folder=None):
    """
    Delete a file. If multiple matches found, prompt user to confirm.
    
    Args:
        filename: The file to delete
        folder: Optional folder name ("downloads", "documents", "music")
    
    Returns:
        True if deletion succeeded, None if user needs to clarify/retry
    """
    matches = find_files(filename, folder)
    
    if not matches:
        tts.speak(f"File {filename} not found.")
        return None  # Caller will ask retry/ignore
    
    if len(matches) == 1:
        # Unambiguous match—delete it
        full_path, match_name, folder_name = matches[0]
        try:
            send2trash.send2trash(full_path)
            tts.speak(f"Deleted {match_name} from {folder_name}.")
            return True
        except Exception as e:
            tts.speak(f"Could not delete {match_name}. Error: {str(e)}")
            return None
    
    else:
        # Multiple matches—ask user to confirm
        options = [f"{m[1]} (in {m[2]})" for m in matches]
        tts.speak(f"Found multiple matches: {', '.join(options)}. Please specify which one to delete.")
        return None  # Caller will ask user to clarify
    
def control(target, operation, value):
    if value:
        value = max(0, min(100, value))
    else:
        value = 15
    if target == "screenshot":
        pyautogui.screenshot(r"C:\Users\mehdi\Desktop\screenshot.png")
        tts.speak("I have taken a screenshot")
        return

    elif target == "brightness":
        if operation == "set":
            set_brightness(value)
            final_value = value
        elif operation == "increase":
            final_brightness = get_brightness()[0] + value
            set_brightness(final_brightness)
        elif operation == "decrease":
            final_brightness = get_brightness()[0] - value
            set_brightness(final_brightness)
        tts.speak(f"I have set the brightness to {final_brightness}")

    elif target == "volume":
        value = int((value / 100) * 65535)
        if operation == "set":
            subprocess.run([NIR_CMD_PATH, "setsysvolume", str(value)])
        elif operation == "increase":
            subprocess.run([NIR_CMD_PATH, "changesysvolume", str(value)])
        elif operation == "decrease":
            subprocess.run([NIR_CMD_PATH, "changesysvolume", str(-value)])
        volume_pct = int(value/65535) * 100
        tts.speak(f"I have set the volume to {volume_pct}")