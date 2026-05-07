import json
from datetime import datetime, timedelta
from win10toast import ToastNotifier
import pyttsx3
import re
import tts

REMINDERS_FILE = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\reminders.json"

def parse_reminder_time(time_str):
    
    now = datetime.now()
    time_lower = time_str.lower()

    time_clean = re.sub(r'\b(tomorrow|today|at|on|in)\b', '', time_lower).strip()

    time_normalized = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', lambda m: m.group(1).upper().replace('.', ''), time_clean, flags=re.IGNORECASE)

    try:
        reminder_time = datetime.strptime(time_normalized, "%I %p") #if it's 3pm
    except:
        try:
            reminder_time = datetime.strptime(time_normalized, "%I:%M %p")  # minute-specific "3:07 PM"
        except:
            return None
    
    reminder_time = reminder_time.replace(year=now.year, month=now.month, day=now.day)

    if reminder_time < now or "tomorrow" in time_lower:
        reminder_time += timedelta(days=1)

    return reminder_time.strftime("%Y-%m-%d %H:%M:%S")

def handle_reminder(response, context):
    time_str = response.get("time")  # "3 PM", "tomorrow 2 PM"
    label = response.get("label")    # "call mom"
    recurring = response.get("recurring")  # "daily" or null

    reminder_datetime = parse_reminder_time(time_str)

    if not reminder_datetime:
        tts.speak("Couldn't parse time")
        return True, context

    try:
        with open(REMINDERS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"reminders" :[]}

    data["reminders"].append({
        "time": reminder_datetime,
        "label": label,
        "recurring": recurring
    })

    with open(REMINDERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    tts.speak(f"Reminder set for {time_str}: {label}")
    return True, context

def check_reminders():
    try:
        with open(REMINDERS_FILE, "r") as f:
            data = json.load(f)

    except:
        return
    
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M")
    
    reminder_to_remove = []

    for idx, reminder in enumerate(data["reminders"]):
        reminder_time = reminder["time"][:16]

        if reminder_time == current_time:
            label = reminder["label"] or "Reminder"
            toaster = ToastNotifier()
            toaster.show_toast(
                msg=label,
                duration=10,
                threaded=True
            )

            engine = pyttsx3.init()
            engine.say(f"Reminder: {label}")
            engine.runAndWait()

            if reminder["recurring"]:
                if reminder["recurring"] == "daily":
                    next_time = datetime.strptime(reminder["time"], "%Y-%m-%d %H:%M:%S")
                    next_time += timedelta(days=1)
                    data["reminders"][idx]["time"] = next_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                reminder_to_remove.append(idx)
        
    for idx in reversed(reminder_to_remove):
        data["reminders"].pop(idx)

    with open(REMINDERS_FILE, "w") as f:
        json.dump(data, f, indent=2)    

if __name__ == "__main__":
    check_reminders()
    