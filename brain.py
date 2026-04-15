from faster_whisper import WhisperModel
import ollama
import json, os
import re 

audio_path = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\command.wav"

if os.path.exists("targets.json"):
    with open("targets.json", "r") as f:
        TARGETS = json.load(f)
else:
    TARGETS = {}

valid_targets = ", ".join(TARGETS.keys())

SYSTEM_PROMPT = f"""
You are a command parser for a voice assistant.
Receive transcribed text and return ONLY a JSON object. No prose.

JSON Format:
{{"action": "open", "target": "<app_name>"}}
{{"action": "search", "target": "<query>"}}
{{"action": "speak", "target": "<response>"}}
{{"action": "stop", "target": null}}

Rules:
1. ACTION "open": Use only if the command matches these targets: {valid_targets}.
2. ACTION "search": Triggered by "search" or "search for". The target is only the query after these keywords. If the query is empty, return action "unknown".
3. ACTION "speak": Default for questions or greetings. Provide a concise, pragmatic answer as the target.
4. ACTION "stop": Triggered by "stop", "exit", or "goodbye".
5. ACTION "unknown": Use for absurd requests or corrupted input.

Examples:
"open YouTube" -> {{"action": "open", "target": "youtube"}}
"search for quantum physics" -> {{"action": "search", "target": "quantum physics"}}
"who is the president?" -> {{"action": "speak", "target": "The President is [Name]."}}
"search for" -> {{"action": "unknown", "target": null}}
"goodbye jarvis" -> {{"action": "stop", "target": null}}
"""

model = WhisperModel("tiny", device="cuda", compute_type="float16")

def transcribe(path):
    segments, _ = model.transcribe(path)
    text = " ".join([s.text for s in segments]).strip(".")
    return text

def understand(text):

    in_response = ollama.chat(model="qwen3:1.7b", messages=[{"role" : "system", "content" : SYSTEM_PROMPT},
                                                            {"role" : "user", "content" : text}])
    content = in_response['message']['content']
    content = re.sub(r'<think>.*?</think>', '', content, flags = re.DOTALL).strip()
    response = json.loads(content)
    return response


if __name__  == "__main__":
    text= transcribe(audio_path)
    result = understand(text)
