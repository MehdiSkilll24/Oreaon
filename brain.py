from faster_whisper import WhisperModel
import ollama
import json, os

audio_path = r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\OREAON\command.wav"

counter = 0

COUNTER_LIMIT = 15

SYSTEM_PROMPT = f"""
You are a command parser for a voice assistant.
Return ONLY a JSON object. No prose, no explanation.

ACTIONS & FORMATS:
{{"action": "open", "target": "<app_or_site>", "new": <boolean>}}
{{"action": "search", "target": "<query>"}}
{{"action": "speak", "target": "<concise_answer>"}}
{{"action": "control", "target": "<volume|brightness|screenshot|pause|resume|next|previous>", "operation": "<set|increase|decrease|execute>", "value": <number|null>}}
{{"action": "stop"}}
{{"action": "delete", "target": "<filename>", "folder": "<downloads|documents|music|null>"}}
{{"action": "find", "target": "<filename>", "folder": "<downloads|documents|music|null>"}}
{{"action": "weather", "time": "<duration|null>", "location": "<city|null>"}}
{{"action": "sysinfo", "target": "<battery|cpu|ram|storage|gpu|null>"}}
{{"action": "window", "operation": "<minimize|maximize|close|focus>", "target": "<window_name>"}}
{{"action": "spotify", "genre": "<genre>"}}
{{"action": "reminder", "time": "<time>", "label": "<text>", "recurring": "<daily|weekly|null>"}}
{{"action": "calendar"}}
{{"action": "schedule", "title": "<event>", "date": "<date>", "time": "<time>"}}
{{"action": "unknown"}}

RULES:
- "open" → open app/site
- "open" → if preceded by "new", set "new": true, otherwise omit "new"
- "speak" → for opinion questions, comparisons, advice, casual conversation. Anything that fails all other features defaults to speech.
- "search" → ONLY for specific facts, news, current events, or lookups requiring real-time data.
- "stop"/"exit"/"goodbye" → stop
- "delete"/"remove" → delete; "find"/"look for" → find
- "control" → set/increase/decrease/pause/resume/next/previous/screenshot
- "weather" → extract time and location; default location Chengdu, default time null
- "sysinfo" → battery/cpu/ram/storage/gpu; null target = all
- "window" → minimize/maximize/close/focus + window name
- "spotify" → ONLY if user says "music"; extract genre (never use "target")
- "reminder" → remind/set reminder; extract time, label, recurring
- "calendar" → show calendar/schedule/events
- "schedule" → add event; extract title, date, time
- "unknown" → absurd or corrupted input

HAINING: If user says "and" or "then", return nested actions (max 2):
{{"action": "<first>", ..., "then": {{"action": "<second>", ...}}}}
IMPORTANT: Everything after "and play" is ALWAYS a literal song/video title, even if it resembles a command, direction, or common word. Never interpret it as anything other than a title.
Examples:
"open new youtube and play left and right" → {{"action": "open", "target": "youtube", "new": true, "then": {{"action": "play", "target": "trinity titoli"}}}}
"open new spotify and play smooth criminal" → {{"action": "open", "target": "spotify", "new": true, "then": {{"action": "play", "target": "smooth criminal"}}}}
"open spotify and play bohemian rhapsody" → {{"action": "open", "target": "spotify", "new": false, "then": {{"action": "play", "target": "bohemian rhapsody"}}}}
"open spotify and play her" → {{"action": "open", "target": "spotify", "new": false, "then": {{"action": "play", "target": "her"}}}}
"open youtube and play no signal" → {{"action": "open", "target": "youtube", "new": false, "then": {{"action": "play", "target": "no signal"}}}}
"open youtube and play left and right" → {{"action": "open", "target": "youtube", "new": false, "then": {{"action": "play", "target": "left and right"}}}}
"open youtube and play trinity titoli" → {{"action": "open", "target": "youtube", "new": false, "then": {{"action": "play", "target": "trinity titoli"}}}}
"play rap music and show my calendar" → {{"action": "spotify", "genre": "rap", "new": false, "then": {{"action": "calendar"}}}}
"pause and open youtube" → {{"action": "control", "target": "pause", "operation": "execute", "value": null, "then": {{"action": "open", "target": "youtube", "new": false,}}}}
"set brightness to 50 and play chill music" → {{"action": "control", "target": "brightness", "operation": "set", "value": 50, "then": {{"action": "spotify", "genre": "chill"}}}}
"should I eat apples or bananas?" → {{"action": "speak", "target": "Both are healthy. Bananas have more carbs and potassium, apples have more fiber. Depends on your goal."}}
"""
SPEECH_PROMPT = """
You are Oreaon, a smart and concise voice assistant.
Answer the user's question or statement directly and naturally.
Keep responses moderate — 2 to 4 sentences max. No markdown, no headers.
You are speaking out loud, so write like you talk.
You can include edge cases in anything you say if that's necessary.
You are allowed to have opinions on topics and can justify those opinions however you see fit.
You have to answer questions no matter how unrelated they are. If the user talks about apples and bananas,
then jumps to a different topic, you must adapt accordingly.
"""

if os.path.exists("conversation_history.json"):
    with open("conversation_history.json", "r") as f:
        try:
            conversation_history = json.load(f)
        except json.JSONDecodeError:
            conversation_history = []
else:
    conversation_history = []

if os.path.exists("targets.json"):
    with open("targets.json", "r") as f:
        TARGETS = json.load(f)
else:
    TARGETS = {}

valid_targets = ", ".join(TARGETS.keys())


model = WhisperModel(r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Oreaon\models", device="cuda", compute_type="float16")



def transcribe(path):
    segments, _ = model.transcribe(path)
    results = []
    for s in segments:
        if s.no_speech_prob < 0.5 and s.avg_logprob > -1.0:
            results.append(s.text)
    text = " ".join(results).strip(".")
    return text if text else None

def summarizer(history):
    global conversation_history
    in_response = ollama.chat(
        model="qwen2.5:1.5b", 
        messages=[
            {"role": "system", "content": f"Summarize this conversation in 3-5 sentences,preserving the key points and context: {json.dumps(history)}"}
        ],
        stream=False, 
        options={
            "temperature": 0.7, 
            "num_ctx": 4096,  
            "think": False
        }
    )
    summary = in_response.message.content
    conversation_history = [{"role": "assistant", "content": summary}]
    with open ("conversation_history.json", "w") as f:
        json.dump(conversation_history, f)

    return 


def converse(text):
    global counter

    in_response = ollama.chat(
        model="qwen2.5:1.5b", 
        messages=[
            {"role": "system", "content": "/no_think\n" + SPEECH_PROMPT},
            *conversation_history,
            {"role": "user", "content": text + " /no_think"} 
        ],
        stream=False, 
        options={
            "temperature": 0.7, 
            "num_ctx": 4096,  
            "think": False    
        }
    )
    content = in_response.message.content
    conversation_history.append({"role": "user", "content": text})
    conversation_history.append({"role": "assistant", "content": content})
    with open("conversation_history.json", "w") as f:
        json.dump(conversation_history, f)

    counter += 1
    if counter == COUNTER_LIMIT:
        print("Summarizing convo...")
        summarizer(conversation_history)
        counter = 0
    return content


def understand(text):
    try:
        # Use the official chat method with the speed-boosting parameters
        in_response = ollama.chat(
            model="qwen2.5:1.5b", 
            messages=[
                {"role": "system", "content": "/no_think\n" + SYSTEM_PROMPT},
                {"role": "user", "content": text + " /no_think"} 
            ],
            
            # --- THE SPEED ENGINE ---
            format="json",           # 1. Hardware-level JSON enforcement (No Regex needed!)
            stream=False,            # 2. Return the whole object at once
            keep_alive="24h",        # 3. Stay in VRAM so the next command is instant
            options={
                "temperature": 0,    # 4. Zero 'randomness' = faster logic
                "num_ctx": 4096,     # 5. Ensure enough room for your big prompt
                "think": False       # 6. Disable internal reasoning steps to save time
            }
        )

        content = in_response.message.content
        return json.loads(content)

    except Exception as e:
        print(f"Brain error{e}")
        return {"action" : "unknown", "target": None}


if __name__  == "__main__":
    text= transcribe(audio_path)
    result = understand(text)