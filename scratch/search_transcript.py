import json

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript.jsonl"

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
        
        # Look for commands run
        tool_calls = step.get("tool_calls", [])
        content_str = step.get("content", "")
        if content_str and (content_str.strip().startswith("{") or "tool_calls" in content_str):
            try:
                nested = json.loads(content_str)
                tool_calls = nested.get("tool_calls", [])
            except Exception:
                pass
                
        for call in tool_calls:
            name = call.get("name")
            args = call.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    continue
            if name == "run_command":
                cmd = args.get("CommandLine", "")
                if "redis" in cmd.lower() or "celery" in cmd.lower() or "wsl" in cmd.lower():
                    print(f"Step {step.get('step_index')}: run_command: {cmd}")
        
        # Check user inputs
        if step.get("type") == "USER_INPUT" and "redis" in content_str.lower():
            print(f"Step {step.get('step_index')}: User input: {content_str}")
        
        # Check agent responses
        if step.get("type") == "PLANNER_RESPONSE" and "redis" in content_str.lower():
            print(f"Step {step.get('step_index')}: Planner response has redis mention")
