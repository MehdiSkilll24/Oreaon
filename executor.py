import json
import os
import urllib.parse
from playwright.sync_api import sync_playwright
import difflib
import send2trash
import tts
import pyautogui
from screen_brightness_control import get_brightness, set_brightness
import subprocess, psutil
import requests
from datetime import datetime, timedelta
import pythoncom
import re, webbrowser, calendar, time
import pygetwindow as gw

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL


DW_DIR = r"C:\Users\mehdi\Downloads"
DC_DIR = r"C:\Users\mehdi\Documents"
MUSIC_DIR = r"C:\Users\mehdi\Music"
NIR_CMD_PATH = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\nircmd-x64\nircmdc.exe"
CALENDAR_FILE = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\calendar.json"
HTML_FILE = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\calendar.html"

CHENGDU_LAT = 30.5728
CHENGDU_LON = 104.0668

windows = gw.getAllWindows()

# Map word numbers to digits
word_to_num = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12 
}

def extract_domain(url):
    return urllib.parse.urlparse(url).netloc.replace("www.", "")


def invalidate_browser():
    global _browser
    _browser = None

def get_current_volume():
    # Initialize COM for the current thread
    pythoncom.CoInitialize()
    try:
        # Get the default speakers
        devices = AudioUtilities.GetSpeakers()
        
        # Access the EndpointVolume attribute directly
        # Modern pycaw versions map this to the correct COM interface for us
        interface = devices.EndpointVolume
        
        # GetLevelScalar returns a float 0.0 to 1.0
        current_level = interface.GetMasterVolumeLevelScalar()
        
        # Rouding since we're doing base 10 math for matching values (laptop <-> user)

        return round(current_level * 100)
    except Exception as e:
        print(f"Volume detection failed: {e}")
        return 0
    finally:
        # Uninitializing to prevent memory leaks in threads
        pythoncom.CoUninitialize()

month_dict = {i: calendar.month_name[i] for i in range(1,13)}

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


    """
    Connects to an existing Brave instance via CDP, or launches a fresh one if none is running.
    Handles two failure modes:
    - No browser running: launches Brave via subprocess and retries connection up to 10 times
    - Stale browser reference: invalidate_browser() resets the global, forcing a full reconnect on next call
    ( this fixes a bug in open_url() )
    """



    # connects to the local port. Has a fallback cmd launch in case of failure

    global _playwright, _browser
    if _playwright is None:
        _playwright = sync_playwright().start()

    if _browser is not None and _browser.is_connected():
        return _browser
    
    try: 

        # Try to connect

        print("Initial connect")
        _browser = _playwright.chromium.connect_over_cdp("http://localhost:9222")
        return _browser
    
    except Exception:

        # If failure, close any brave session and launch a fresh brave.exe script 

        print("No existing browser")
        try:
            subprocess.run("taskkill /f /im brave.exe", shell=True)
            subprocess.Popen(
                r'"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222',
                shell=True
            )
            for i in range(10):
                try:

                    # Try to connect it to the port (10 attempts in case the port is faster than the launch during the first times)

                    time.sleep(1)
                    _browser = _playwright.chromium.connect_over_cdp("http://localhost:9222")
                    print("Connected succesfully!")
                    return _browser
                except Exception:
                    print(f"Waiting... (attempt {i+1}/10)")
        except Exception:

            # If nothing workds, we open a different google page (empty session)

            print("Fallback...")
            _browser = _playwright.chromium.launch(headless=False)
            return _browser

def comparison(target_url, context):

    # Compares the target to be opened with existent data

    print("Checking...")
    url = TARGETS.get(target_url.lower(), "Nothing found!")
    if url == "Nothing found!": 
        
        # Option to add the new command (it didn't match anything in the dictionary)
        
        decision = str(input("Would you like to add this new command?"))
        while decision.lower() != 'yes' and decision.lower() != 'no':
            decision = str(input("Wrong, input. Would you like to add this new command?(yes/no)"))

        if decision == 'yes':
            new_target = str((input("Enter the website name"))).lower()
            new_url = str((input("Please, paste its URL")))
            TARGETS[new_target] = new_url
            with open("targets.json", "w") as f:
                json.dump(TARGETS, f)
            
            return new_url
        
        return None
    
    return url 

def open_url(url, new= False):
    # Early exit if no url is found
    if not url:
        print("None returned")
        return
    target_page =None
    browser = get_browser()
    if not new:
        for b_context in browser.contexts:
            for p in b_context.pages:
                try:
                    if extract_domain(url) in extract_domain(p.url):
                        print("found!")
                        target_page = p
                        break
                except Exception:
                    continue
            if target_page:
                break

    if target_page:
        try:
            if not target_page.is_closed():
                target_page.bring_to_front()
                if "search" in url and url!=target_page.url :
                    target_page.goto(url, wait_until="commit")
                elif extract_domain(url) not in extract_domain(target_page.url):
                    target_page.goto(url, wait_until="commit")
                return target_page
        except Exception as e:
            print(f"Page closed {e}")
            target_page = None

    if not target_page:
        print("Not found")
        try:
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            target_page = context.new_page()
            print("1st block")
            target_page.goto(url, wait_until="commit")
        except Exception as e:

            """ (PS. "Context" is the term they use for one browser sessions (ie. one browser exe running) 
            Here, we want to disable the global browser variable, and create a fresh one for the new open, 
            we achieve that by: calling invalidate_browser() -> opening browser -> Null browser_context 
            -> Loop all contexts and assign the one that works -> Use that one as the new context for the new opening.
            -> IF failure -> We open a new browser context""" 

            invalidate_browser() # nullify browser variable to open a fresh one 
            browser = get_browser() # open through subprocess
            browser_context = None # Nullify context to try looping
            for ctx in browser.contexts: # Context looping
                try:
                    test_page = ctx.new_page()
                    test_page.close() # that's just a test to see which context works
                    browser_context = ctx # if the page opens and closes, context works, so we assign that one as the anchor
                    break
                except Exception:
                    continue
            if not browser_context: # If no anchor context was created, create a new context and execute from it
                browser_context = browser.new_context()
            target_page = browser_context.new_page()
            print("2nd block")
            target_page.goto(url, wait_until="commit")
    
    return target_page

def run_search(query):

    if not query:
        return

    encoded_query = urllib.parse.quote(query)
    
    # (Changed from google.com to search.brave.com) We anchor the user query to the default browser's query syntax: browser_query + <actual search query>
    
    url = f"https://search.brave.com/search?q={encoded_query}"
    open_url(url)
    return url

def play(search_url, context):
    print(f"play() called with: {search_url}, {context}")
    browser = get_browser()
    target_page = None

    # If existent page -> Use that very page as the target, then apply the changes to it instead of creating a new page, else -> new page 
    for b_context in browser.contexts:
        for p in b_context.pages:
            if context.lower() in p.url.lower():
                target_page = p
                break
        if target_page:
            break

    if target_page:
        target_page.bring_to_front()
        if search_url not in target_page.url:
            target_page.goto(search_url, wait_until="commit")
    else:
        browser_context = browser.contexts[0] if browser.contexts else browser.new_context()
        target_page = browser_context.new_page()
        target_page.goto(search_url)

    # If it's youtube, use its appropriate button to select the first song

    try:
        if context == "youtube":
            target_page.wait_for_selector('a#video-title', state="attached", timeout=10000)
            target_page.click('a#video-title', force= True)

    # Same logic for spotify

        elif context == "spotify":
            target_page.wait_for_selector('a[href*="/track/"]', timeout=15000)
            target_page.locator('a[href*="/track/"]').first.click(force=True)
    
    except Exception as e:
        print(f"Failure {e}")

    return True, context

def parse_time_string(time_str):
    """Extract hours from strings like '3 hours', 'in 2 hours', 'tomorrow', etc."""

    if not time_str:
        return 0
    
    time_lower = time_str.lower()

    # if the input contains (day/ days), multiply the output (hours by 24) to reflect in (24 hours)

    for word, num in word_to_num.items():
        if f"{word} days" in time_lower or f"{word} day" in time_lower or f"{num} days" in time_lower or f"{num} day" in time_lower:
            return num * 24

    # else, we return the num (hours) that the user mentioned

    for word, num in word_to_num.items():
        if word in time_lower or str(num) in time_lower:
            return num

    # We search for the word hour(s), if found, we retun its value

    match = re.search(r'(\d+)s*hours?', time_lower)
    if match:
        return int(match.group(1))
    
    # We search for the word day(s), if found, we retun its value *24 -> relative to hours

    match = re.search(r'(\d+)\s*days?', time_lower)
    if match:
        return int(match.group(1)) * 24
    
    if "tomorrow" in time_str.lower():
        return 24
    
    # Match "tonight"
    if "tonight" in time_str.lower():
        return 12
    
    return 0

def get_weather(hours_ahead):
    """Fetch weather from Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast"

    # Due to regional limitation, I hardcoded one city (More generic approach will be added ..)

    params = {
        "latitude": CHENGDU_LAT,
        "longitude": CHENGDU_LON,
        "hourly": "temperature_2m,weather_code,wind_speed_10m,precipitation",
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    # Get current hour + offset
    now = datetime.now()
    target_time = now + timedelta(hours=hours_ahead)
    hour_index = target_time.hour
    
    # Extract weather for that hour
    temps = data['hourly']['temperature_2m']
    wind = data['hourly']['wind_speed_10m']
    precip = data['hourly']['precipitation']
    
    # Return a dictionary with temperature, wind speed and rain status for that hour index (from parse_time_string())
    return {
        "temp": temps[hour_index],
        "wind": wind[hour_index],
        "precipitation": precip[hour_index]
    }

def format_weather_response(weather_data, hours_ahead):
    """Create a natural response."""
    temp = weather_data["temp"]
    wind = weather_data["wind"]
    precip = weather_data["precipitation"]
    
    
    time_str = f"in {hours_ahead} hours" if hours_ahead > 0 else "right now"
    
    response = f"The weather {time_str} is {temp} degrees, with {wind} killometers per hour winds"
    
    if precip > 0:
        response += f", and {precip}mm of rain expected"
    
    else:
        response += f", and no precipitations expected"
    
    return response


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

    # Set a dictionary for each command (for media control)

    media_map = {
    "pause": "Space",
    "resume": "Space",
    "next": "Control+ArrowRight",
    "previous": "Control+ArrowLeft",
    }

    # For brightness and volume, if no value specified, default to an adjustment of +-15 

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
            final_brightness = value
        elif operation == "increase":
            final_brightness = get_brightness()[0] + value
            set_brightness(final_brightness)
        elif operation == "decrease":
            final_brightness = get_brightness()[0] - value
            set_brightness(final_brightness)
        tts.speak(f"I have set the brightness to {final_brightness}")
        return

    elif target == "volume":
        original_value = value
        value = int((value / 100) * 65535)
        if operation == "set":
            subprocess.run([NIR_CMD_PATH, "setsysvolume", str(value)])
        elif operation == "increase":
            subprocess.run([NIR_CMD_PATH, "changesysvolume", str(value)])
        elif operation == "decrease":
            subprocess.run([NIR_CMD_PATH, "changesysvolume", str(-value)])
        current = get_current_volume()
        tts.speak(f"I have set the volume to {current}")
        return
    
    # If none of the above, it must be a media control command. 
    # Get browser -> Extract command -> assign to variable -> feed to keyboard method 

    browser = get_browser()
    if not browser:
        tts.speak("No browser found")
        return
    
    for context in browser.contexts:
        for page in context.pages:
            if any(d in extract_domain(page.url) for d in ["spotify.com", "youtube.com"]):
                command = media_map.get(target)
                if command:
                    page.keyboard.press(command)
                    return
    tts.speak("Couldn't find an active music tab") 
    return

def handle_speak(response, context):
    target = response.get("target")
    tts.speak(target)
    return True, context

def handle_stop(response, context):
    tts.speak("Shutting down.")
    return False, context

def handle_search(response, context):
    target = response.get("target")
    if context and context in SEARCH_URLS:
        url = SEARCH_URLS[context] + target.replace(" ", "+")
        open_url(url)
    else:
        url = run_search(target)
    return True, context

def handle_open(response, context):
    target = response.get("target")
    SYSTEM_APPS = {
        "brave": r'"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222', 
        "steam": "steam://open/main",
        "settings": "ms-settings:",
    }
    context = target
    if context in SYSTEM_APPS:
        try:
            subprocess.Popen(SYSTEM_APPS[target], shell=True)
            time.sleep(2)
            return True, context
        except Exception as e:
            tts.speak(f"I couldn't open the {target} application: {e}")
            return True, context
    print("Calling comp")
    url = comparison(target, context)
    if url is None:
        return True, context
    new = response.get("new")
    print(new)
    open_url(url, new)
    return True, context

def handle_play(response, context):
    target = response.get("target")
    if not context or context not in SEARCH_URLS:
        tts.speak("I don't know where to play that.")
        return True, context
    url = SEARCH_URLS[context] + target.replace(" ", "+")
    play(url, context)
    return True, context

def handle_delete(response, context):
    target = response.get("target")
    folder = response.get("folder")
    delete(target, folder)
    return True, context

def handle_find(response, context):
    import subprocess
    target = response.get("target")
    folder = response.get("folder")
    matches = find_files(target, folder)
    if matches:
        full_path, file_name, folder_name = matches[0]
        subprocess.Popen(f'explorer /select,"{full_path}"')
    else:
        tts.speak(f"File {target} not found.")
    return True, context

def handle_control(response, context):
    target = response.get("target")
    operation = response.get("operation")
    value = response.get("value")
    control(target, operation, value)
    return True, context

def handle_weather(response, context):
    time = response.get("time")
    hours = parse_time_string(time)
    print(f"Parsed hours{hours}")
    info = get_weather(hours)
    answer = format_weather_response(info, hours)
    print(f"Answer {answer}")
    tts.speak(answer)
    return True, context

def handle_sys(response, context):
    try:
        gpu_result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        gpu = gpu_result.stdout.strip()
    except:
        gpu = "unavailable"
    target = response.get("target")
    tasks = {
        "battery": psutil.sensors_battery().percent,
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "storage": psutil.disk_usage('C:').percent,
        "gpu": gpu_result.stdout.strip()
    }
    if target and target in tasks:
        answer = f"{target} usage is currently at {tasks[target]}%"
    else:
        # All info
        answer = f"System status: CPU {tasks['cpu']}%, RAM {tasks['ram']}%, Storage {tasks['storage']}%, Battery {tasks['battery']}%, GPU {tasks['gpu']}%"
    
    tts.speak(answer)
    return True, context

def handle_window(response, context):
    operation = response.get("operation")
    target = response.get("target").lower()
    
    try:
        window = gw.getWindowsWithTitle(target)[0]
    except IndexError:
        tts.speak(f"Could not find window {target}")
        return True, context

    operations = {
        "minimize": lambda w: w.minimize(),
        "maximize": lambda w: w.maximize(),
        "close": lambda w: w.close(),
        "focus": lambda w: (w.minimize(), __import__('time').sleep(0.3), w.restore())
    }
    
    try:
        operations[operation](window)
    except Exception as e:
        print(f"Window operation failed: {e}")
    
    tts.speak(f"{operation}d {target}")
    return True, context

def handle_spotify(response, context):
    genre = response.get("genre")
    url = TARGETS.get("spotify", "") 
    target_page = open_url(url)

    try:
        if target_page:
            search_box = target_page.wait_for_selector('[data-testid="search-input"]', state="attached", timeout=15000) 
            search_box.fill(f"{genre} playlist", force=True)
            target_page.keyboard.press("Enter")

            playlist_link = target_page.wait_for_selector('a[href*="/playlist/"]', state="visible", timeout=15000)
            playlist_link.click()
            
            pause_btn = target_page.query_selector('button[aria-label="Pause"]')
            if pause_btn:
                pause_btn.click()
                target_page.wait_for_timeout(300)
            for i in range(5):
                try:
                    track_link = target_page.wait_for_selector('a[data-testid="internal-track-link"]', state="visible", timeout=5000)
                    time.sleep(1)
                except Exception as e:
                    print(e)
                    return
            tts.speak(f"Playing {genre}")
            track_link.dblclick(force=True)

    except Exception as e:
        print(f"Track playing failed {e}")
        target_page.wait_for_load_state("domcontentloaded")

    return True, context

def handle_calendar(response, context):
    try:
        with open(CALENDAR_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            events = data.get("events", [])
    except:
        events = []

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Oreaon Calendar</title>
        <style>
            body {{ font-family: Arial; background: #1e1e1e; color: white; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; }}
            h1 {{ color: #00d4ff; }}
            .event {{ background: #2d2d2d; padding: 15px; margin: 10px 0; border-left: 4px solid #00d4ff; }}
            .time {{ color: #00d4ff; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 Oreaon Calendar</h1>
    """
    if events:
        for event in events:
            html_content += f"""
            <div class="event">
                <div class="time">{event.get('date')} at {event.get('time')}</div>
                <div>{event.get('title')}</div>
            </div>
            """
    else:
        html_content += "<p>No events scheduled</p>"

    html_content += """
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, "w", encoding='utf-8') as f:
        f.write(html_content)

    webbrowser.open(f"file:///{HTML_FILE}")
    tts.speak("Opening your calendar")
    return True, context

def parse_date(date_str):
    now = datetime.now()
    date_lower = date_str.lower()

    if date_lower == "tomorrow":  # lowercase
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_lower == "today":
        return now.strftime("%Y-%m-%d")
    else:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            return None

def handle_schedule(response, context):
    title = response.get("title")
    date_str = response.get("date")
    time_str = response.get("time")

    if not date_str or not title or not time_str:
        tts.speak("Missing event details")
        return True, context
    
    time_normalized = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', lambda m: m.group(1).upper().replace('.', ''), time_str, flags=re.IGNORECASE)

    parsed_date = parse_date(date_str)
    if not parsed_date:
        tts.speak("Could not parse date")
        return True, context

    try:
        with open(CALENDAR_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"events": []}

    data["events"].append({
        "date": parsed_date,  # Use parsed_date, not date_str
        "time": time_normalized,
        "title": title
    })

    with open(CALENDAR_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    date_obj = datetime.strptime(parsed_date, "%Y-%m-%d")
    day = date_obj.day
    month = date_obj.month
    tts.speak(f"Event scheduled: {title} on {month_dict[month]} {day} at {time_normalized}")
    return True, context