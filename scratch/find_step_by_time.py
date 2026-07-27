import json
from pathlib import Path

log_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript.jsonl")

if not log_path.exists():
    print("Transcript log file not found!")
    exit(1)

target_time = "2026-07-09T12:58"

last_step = -1
found = False

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
            created_at = step.get("created_at", "")
            
            if created_at.startswith("2026-07-09T12:") or created_at.startswith("2026-07-09T13:") or created_at.startswith("2026-07-09T14:"):
                print(f"Step: {step.get('step_index')}, Time: {created_at}, Type: {step.get('type')}")
        except Exception:
            continue
