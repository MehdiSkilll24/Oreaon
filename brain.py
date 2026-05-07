from faster_whisper import WhisperModel
import ollama
import json, os, re
import re, time

audio_path = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\command.wav"


if os.path.exists("targets.json"):
    with open("targets.json", "r") as f:
        TARGETS = json.load(f)
else:
    TARGETS = {}

valid_targets = ", ".join(TARGETS.keys())

SYSTEM_PROMPT = f"""
/no_think
You are a command parser for a voice assistant.
Receive transcribed text and return ONLY a JSON object. No prose.

JSON Format:
{{"action": "open", "target": "<app_name>"}}
{{"action": "search", "target": "<query>"}}
{{"action": "speak", "target": "<response>"}}
{{"action": "control", "target": "<parameter>", "operation": "<set|increase|decrease|execute>", "value": <number|null>}}
{{"action": "stop", "target": null}}
{{"action": "delete", "target": "<filename>", "folder": "<folder_name>"}}
{{"action": "find", "target": "<filename>", "folder": "<folder_name>"}}



Rules:
1.ACTION "open": Use only if the command matches these targets: {valid_targets}.
2.ACTION "search": Triggered by "search" or "search for". The target is only the query after these keywords. If the query is empty, return action "unknown".
3.ACTION "speak": Default for questions or greetings. Provide a concise, pragmatic answer as the target.
4.ACTION "stop": Triggered by "stop", "exit", or "goodbye".
5.ACTION "delete": Triggered by "delete" or "remove". target is the filename, folder is one of: downloads, documents, music. If no folder mentioned, default to None
6.ACTION "find": Triggered by "find" or "look for". target is the filename, folder is one of: downloads, documents, music. If no folder mentioned, default to None
7.ACTION "control": Triggered by "set", "increase", or "decrease" commands.
Valid targets: volume, brightness, screenshot
Returns JSON with operation type.
8.ACTION "unknown": Use for absurd requests or corrupted input.

9.ACTION "weather": Triggered by "what's the weather", "how's the weather", "weather forecast", etc.
    Rules:
    1. If time/duration mentioned ("in 3 hours", "tomorrow", "tonight"), extract it as "time": "<duration>"
    2. If location mentioned, extract as "location": "<city>"
    3. Otherwise, "time": null (current weather) and "location": Chengdu (default)

10. ACTION "sysinfo": Triggered by "what's my", "show my", "status" commands for system resources.
    Valid targets: battery, cpu, ram, storage, gpu, disk
    If no target specified, return all.

11. ACTION "window": Triggered by "minimize", "maximize", "close", "focus", "hide" commands on windows.

12. ACTION "spotify": Triggered by "play", "spotify" with song or genre name.
    Extract: genre (ALWAYS use key "genre", never "target")

13. ACTION "reminder": Triggered by "remind", "set reminder", "schedule" commands.

Extract: time (e.g., "3 PM", "tomorrow at 2 PM"), label (the reminder text), recurring (optional: "every day", "every week")

14. ACTION "calendar": Triggered by "calendar", "show calendar", "schedule", "what's my schedule", "events".

15. ACTION "schedule": Triggered by "schedule", "add event", "calendar event", "book".
    Extract: title (event name), date (when), time (what time)

Examples of all actions:

"open YouTube" -> {{"action": "open", "target": "youtube"}}
"search for quantum physics" -> {{"action": "search", "target": "quantum physics"}}
"who is the president?" -> {{"action": "speak", "target": "The President is [Name]."}}
"search for" -> {{"action": "unknown", "target": null}}
"goodbye Oreaon" -> {{"action": "stop", "target": null}}
"delete test.mp3 from music" -> {{"action": "delete", "target": "test.mp3", "folder": "music"}}
"delete test.mp3" -> {{"action": "delete", "target": "test.mp3", "folder": "None"}}
"find test.mp3" -> {{"action": "find", "target": "test.mp3", "folder": "None"}}

"set volume to 50" -> {{"action": "control", "target": "volume", "operation": "set", "value": 50}}
"increase brightness by 20" -> {{"action": "control", "target": "brightness", "operation": "increase", "value": 20}}
"take a screenshot" -> {{"action": "control", "target": "screenshot", "operation": "execute", "value": null}} 

"what's my battery status?" -> {{"action": "sysinfo", "target": "battery"}}
"what's my CPU?" -> {{"action": "sysinfo", "target": "cpu"}}
"system status?" -> {{"action": "sysinfo", "target": null}}

"what's the weather?" -> {{"action": "weather", "time": null, "location": null}}
"what's the weather in 3 hours?" -> {{"action": "weather", "time": "3 hours", "location": null}}
"what's the weather in London tomorrow?" -> {{"action": "weather", "time": "tomorrow", "location": "London"}}

"minimize all windows" -> {{"action": "window", "operation": "minimize", "target": "all"}}
"close chrome" -> {{"action": "window", "operation": "close", "target": "chrome"}}
"focus on brave" -> {{"action": "window", "operation": "focus", "target": "brave"}}
Valid targets: any window name (chrome, vscode, calculator, etc.)

"play chill music" -> {{"action": "spotify", "genre": "chill"}}
"spotify upbeat" -> {{"action": "spotify", "genre": "upbeat"}}
"play all eyes on me" -> {{"action": "spotify", "genre": "all eyes on me"}}
"play rock music" -> {{"action": "spotify", "genre": "rock"}}

"remind me to call mom at 3 PM" -> {{"action": "reminder", "time": "3 PM", "label": "call mom", "recurring": null}}
"set a reminder for tomorrow at 2 PM about the meeting" -> {{"action": "reminder", "time": "tomorrow 2 PM", "label": "the meeting", "recurring": null}}
"remind me every day at 9 AM to exercise" -> {{"action": "reminder", "time": "9 AM", "label": "exercise", "recurring": "daily"}}

"show my calendar" -> {{"action": "calendar"}}
"what's my schedule" -> {{"action": "calendar"}}
"open calendar" -> {{"action": "calendar"}}

"schedule a meeting tomorrow at 2 PM" -> {{"action": "schedule", "title": "meeting", "date": "tomorrow", "time": "2 PM"}}
"add dentist appointment on Friday at 10 AM" -> {{"action": "schedule", "title": "dentist appointment", "date": "Friday", "time": "10 AM"}}

OPTIONAL CHAINING:
When user chains commands with "and", "then", or similar connectors, return nested actions.

Format:
{{"action": "<first_action>", "target/genre": "<target>", "then": {{"action": "<second_action>", "target": "<target>"}}}}

Rules:
1. Chain ANY two compatible actions with "and"
2. Extract the second action from keywords after "and"
3. Each action gets its own appropriate keys (genre for spotify, target for others)
4. Chain ONLY two actions max
5. The "then" action's target is everything after the connector word

Examples:
"open spotify and play the next episode" -> {{"action": "open", "target": "spotify", "then": {{"action": "play", "target": "the next episode"}}}}
"play rap music and show my calendar" -> {{"action": "spotify", "genre": "rap", "then": {{"action": "calendar"}}}}
"show my system status and search for parmesan cheese" -> {{"action": "sysinfo", "target": null, "then": {{"action": "search", "target": "parmesan cheese"}}}}
"remind me to call mom and open spotify" -> {{"action": "reminder", "time": "now", "label": "call mom", "then": {{"action": "open", "target": "spotify"}}}}
"set brightness to 50 and play chill music" -> {{"action": "control", "target": "brightness", "operation": "set", "value": 50, "then": {{"action": "spotify", "genre": "chill"}}}}
"what's the weather and my battery status" -> {{"action": "weather", "then": {{"action": "sysinfo", "target": "battery"}}}}

"""

model = WhisperModel("tiny", device="cuda", compute_type="float16")

def transcribe(path):
    segments, _ = model.transcribe(path)
    text = " ".join([s.text for s in segments]).strip(".")
    return text

def understand(text):
    
    in_response = ollama.chat(model= "qwen3:1.7b", messages=[
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": text}
    ])

    content = in_response.message.content
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except:
            return {"action" : "unknown"}
        
    
    return {"action" : "unknown"}


if __name__  == "__main__":
    text= transcribe(audio_path)
    result = understand(text)
