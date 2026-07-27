import json

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        tool_calls = step.get("tool_calls", [])
        content_str = step.get("content", "")
        if content_str and (content_str.strip().startswith("{") or "tool_calls" in content_str):
            try:
                nested = json.loads(content_str)
                tool_calls = nested.get("tool_calls", [])
            except Exception:
                pass
                
        for call in tool_calls:
            if call.get("name") == "view_file":
                args = call.get("args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        continue
                filepath = args.get("AbsolutePath", "")
                if "settings.py" in filepath:
                    print(f"Step {step.get('step_index')}: view_file on {filepath}")
