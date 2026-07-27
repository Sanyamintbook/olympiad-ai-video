import json
import sys
import re
import os

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        step_idx = step.get("step_index")
        if step_idx == 79:
            content = step.get("content", "")
            cleaned_lines = []
            for l in content.splitlines():
                m_line = re.match(r"^\s*\d+:\s?(.*)$", l)
                if m_line:
                    cleaned_lines.append(m_line.group(1))
            cleaned_content = "\n".join(cleaned_lines).strip()
            
            target_path = os.path.join(dst_root.replace("/", os.sep), "app", "infrastructure", "ai", "providers", "base.py")
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as out:
                out.write(cleaned_content)
            print(f"Restored base.py (length={len(cleaned_content)})")
            print("First 200 chars:")
            print(cleaned_content[:200])
            break
