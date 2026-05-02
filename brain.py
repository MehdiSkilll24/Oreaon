from faster_whisper import WhisperModel
import ollama
import json, os
import re, time

audio_path = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON-MAIN\command.wav"


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



Examples:

"what's my battery status?" -> {{"action": "sysinfo", "target": "battery"}}
"what's my CPU?" -> {{"action": "sysinfo", "target": "cpu"}}
"system status?" -> {{"action": "sysinfo", "target": null}}
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

"what's the weather?" -> {{"action": "weather", "time": null, "location": null}}
"what's the weather in 3 hours?" -> {{"action": "weather", "time": "3 hours", "location": null}}
"what's the weather in London tomorrow?" -> {{"action": "weather", "time": "tomorrow", "location": "London"}}

"minimize all windows" -> {{"action": "window", "operation": "minimize", "target": "all"}}
"close chrome" -> {{"action": "window", "operation": "close", "target": "chrome"}}
"focus on brave" -> {{"action": "window", "operation": "focus", "target": "brave"}}
Valid targets: any window name (chrome, vscode, calculator, etc.)

Optional chaining:
{{"action": "open", "target": "<app_name>", "then": {{"action": "search", "target": "<query>"}}}}
Example:
"open youtube and play we are the people" -> {{"action": "open", "target": "youtube", "then": {{"action": "play", "target": "we are the people"}}}}
"open youtube and search for lofi" -> {{"action": "open", "target": "youtube", "then": {{"action": "search", "target": "lofi"}}}}
"""

model = WhisperModel("tiny", device="cuda", compute_type="float16")

def transcribe(path):
    segments, _ = model.transcribe(path)
    text = " ".join([s.text for s in segments]).strip(".")
    return text

def understand(text):
    t = time.time()
    in_response = ollama.chat(model= "qwen3:1.7b", messages=[
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": text}
    ])
    content = in_response.message.content
    content = re.sub(r'<think>.*?</think>', '', content, flags = re.DOTALL).strip()
    response = json.loads(content)
    return response


if __name__  == "__main__":
    text= transcribe(audio_path)
    result = understand(text)
