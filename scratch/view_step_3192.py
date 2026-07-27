import json

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        if step.get("step_index") == 3186: # Wait, let's view 3186 which is the test output showing errors!
            print("=== STEP 3186 ===")
            print(step.get("content"))
        if step.get("step_index") == 3188:
            print("=== STEP 3188 ===")
            print(step.get("content")[:1000])
        if step.get("step_index") == 3192:
            print("=== STEP 3192 ===")
            print(step.get("content"))
