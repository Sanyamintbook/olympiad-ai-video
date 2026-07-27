import json

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated/logs/transcript.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
        
        step_index = step.get("step_index")
        content_str = step.get("content", "")
        
        # Look for commands run
        tool_calls = step.get("tool_calls", [])
        if content_str and (content_str.strip().startswith("{") or "tool_calls" in content_str):
            try:
                nested = json.loads(content_str)
                tool_calls = nested.get("tool_calls", [])
            except Exception:
                pass
                
        if not tool_calls and "tool_calls" in step:
            tool_calls = step["tool_calls"]
            
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
                if "redis" in cmd.lower() or "winget" in cmd.lower():
                    print(f"[Step {step_index}] run_command: {cmd}")
        
        # Look for any textual mentions of "redis" in prompts or replies
        if "redis" in content_str.lower():
            # Print a snippet of the text containing redis
            lines = content_str.splitlines()
            for l in lines:
                if "redis" in l.lower() or "server" in l.lower() or "winget" in l.lower():
                    out_line = f"[Step {step_index}] Text: {l.strip()}"
                    print(out_line.encode('ascii', errors='replace').decode('ascii'))
