import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        content = step.get("content", "")
        if "audio_metadata" in content and "class " in content:
            print(f"Step {step.get('step_index')}: found (len={len(content)})")
            print(content[:1500])
            print("...\n")
