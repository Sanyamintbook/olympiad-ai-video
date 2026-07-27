import json
import sys
import re
import os

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

# Find the best version of base_agent.py from view_file outputs
longest_len = 0
longest_code = ""
longest_step = -1

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
        if "base_agent.py" in content and ("File Path:" in content or "class BaseAgent" in content) and "Showing lines" in content:
            cleaned_lines = []
            for l in content.splitlines():
                m_line = re.match(r"^\s*\d+:\s?(.*)$", l)
                if m_line:
                    cleaned_lines.append(m_line.group(1))
            cleaned_content = "\n".join(cleaned_lines).strip()
            if "class BaseAgent" in cleaned_content and len(cleaned_content) > longest_len:
                longest_len = len(cleaned_content)
                longest_code = cleaned_content
                longest_step = step_idx

if longest_code:
    print(f"FOUND BEST base_agent.py in Step {longest_step} (length={longest_len})")
    target_path = os.path.join(dst_root.replace("/", os.sep), "app", "infrastructure", "ai", "agents", "base_agent.py")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as out:
        out.write(longest_code)
    print("Successfully restored base_agent.py!")
    print("\nFirst 300 chars:")
    print(longest_code[:300])
else:
    print("Could not find complete base_agent.py in logs.")
