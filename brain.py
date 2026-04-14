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
You will receive a transcribed voice command as input.
You must return ONLY a JSON object, no explanation, no extra text.
The JSON must follow this exact format:
{{"action": "open", "target": "<target_name>"}}
Valid targets are: {valid_targets}
If the command doesn't match any valid target, return:
{{"action": "unknown", "target": null}}
Examples:
"open YouTube" -> {{"action": "open", "target": "youtube"}}
"launch steam" -> {{"action": "open", "target": "steam"}}
"play some music" -> {{"action": "open", "target": "music"}}
"open my fridge" -> {{"action": "unknown", "target": null}}
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
