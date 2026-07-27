import json

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

steps_to_view = [2819, 2845, 3102]

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        step_idx = step.get("step_index")
        if step_idx in steps_to_view:
            print(f"=== STEP {step_idx} ===")
            print(step.get("content")[:1500])
            print("...\n")
