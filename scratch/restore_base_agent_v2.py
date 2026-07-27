import json
import sys
import re
import os

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

# Find view_file outputs specifically for base_agent.py
best_code = ""
best_step = -1
best_len = 0

MAX_STEP = 2276

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        step_idx = step.get("step_index")
        if step_idx > MAX_STEP:
            continue
            
        content = step.get("content", "")
        
        # Look for view_file responses for base_agent.py
        if "File Path:" in content and "base_agent.py" in content and "Showing lines" in content:
            m_path = re.search(r"File Path:\s*`?file:///([^`\n]+)`?", content)
            if m_path and "base_agent" in m_path.group(1):
                cleaned_lines = []
                for l in content.splitlines():
                    m_line = re.match(r"^\s*\d+:\s?(.*)$", l)
                    if m_line:
                        cleaned_lines.append(m_line.group(1))
                cleaned_content = "\n".join(cleaned_lines).strip()
                if len(cleaned_content) > best_len and "class BaseAgent" in cleaned_content:
                    best_len = len(cleaned_content)
                    best_code = cleaned_content
                    best_step = step_idx

if best_code:
    print(f"FOUND BEST base_agent.py in Step {best_step} (length={best_len})")
    target_path = os.path.join(dst_root.replace("/", os.sep), "app", "infrastructure", "ai", "agents", "base_agent.py")
    with open(target_path, "w", encoding="utf-8") as out:
        out.write(best_code)
    print("Successfully restored base_agent.py!")
    print(best_code[:500])
else:
    print("Could not find view_file content for base_agent.py.")
    # Try write_to_file tool calls
    print("\nLooking for write_to_file calls...")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                step = json.loads(line)
            except Exception:
                continue
            
            step_idx = step.get("step_index")
            if step_idx > MAX_STEP:
                continue
            
            tool_calls = step.get("tool_calls", []) or []
            content_str = step.get("content", "")
            if content_str and "tool_calls" in content_str:
                try:
                    nested = json.loads(content_str)
                    tc = nested.get("tool_calls", [])
                    if tc:
                        tool_calls = tc
                except Exception:
                    pass
            
            for call in tool_calls:
                if call.get("name") == "write_to_file":
                    args = call.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            continue
                    target = args.get("TargetFile", "")
                    if "base_agent.py" in target and "class BaseAgent" in str(args.get("CodeContent", "")):
                        code = args.get("CodeContent", "")
                        print(f"Step {step_idx}: write_to_file for base_agent.py (len={len(code)})")
                        if len(code) > best_len:
                            best_len = len(code)
                            best_code = code
                            best_step = step_idx

if best_code and not best_step == -1:
    print(f"\nBest code found at step {best_step} (len={best_len})")
    target_path = os.path.join(dst_root.replace("/", os.sep), "app", "infrastructure", "ai", "agents", "base_agent.py")
    with open(target_path, "w", encoding="utf-8") as out:
        out.write(best_code)
    print("Written!")
