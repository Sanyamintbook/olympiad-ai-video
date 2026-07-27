import json
import os
import re

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        step_idx = step.get("step_index")
        content = step.get("content", "")
        if "base.py" in content and "File Path:" in content:
            print(f"Step {step_idx} matches base.py check!")
            m_path = re.search(r"File Path:\s*`?file:///([^`\n]+)`?", content)
            if m_path:
                print(f"  Extracted path: {m_path.group(1)}")
            else:
                print("  Failed to extract path!")
