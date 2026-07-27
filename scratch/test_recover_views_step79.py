import json
import os
import re

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
            print("Step 79 content matches base.py view?")
            print(f"Content contains 'File Path:': {'File Path:' in content}")
            print(f"Content contains 'Showing lines': {'Showing lines' in content}")
            m_path = re.search(r"File Path:\s*`?file:///([^`\n]+)`?", content)
            if m_path:
                orig_path = m_path.group(1).replace("%20", " ")
                print(f"Original path: {orig_path}")
                rel = orig_path.replace("\\", "/").split("olympiad-ai-video/")[-1]
                target_path = os.path.join(dst_root, rel.replace("/", os.sep))
                print(f"Target path: {target_path}")
                
                # Clean content
                cleaned_lines = []
                for l in content.splitlines():
                    m_line = re.match(r"^\s*\d+:\s?(.*)$", l)
                    if m_line:
                        cleaned_lines.append(m_line.group(1))
                cleaned_content = "\n".join(cleaned_lines).strip()
                print(f"Cleaned content length: {len(cleaned_content)}")
                print(cleaned_content[:200])
