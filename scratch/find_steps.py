import json

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

targets = ["OpenAIProvider", "LLMResponse", "LessonPlanSchema"]

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        content = step.get("content", "")
        for t in targets:
            if t in content:
                print(f"Step {step.get('step_index')}: found '{t}' (len={len(content)})")
