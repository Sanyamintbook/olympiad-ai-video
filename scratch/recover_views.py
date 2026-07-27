import json
import os
import re
from pathlib import Path

log_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript_full.jsonl")
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

MAX_STEP = 2276

if not log_path.exists():
    print("Transcript log file not found!")
    exit(1)

print(f"Starting view_file reconstruction from conversation transcripts up to Step {MAX_STEP}...")

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
        if not content:
            continue
            
        # Check if this content is a view_file output
        if "File Path:" in content and ("Showing lines" in content or "Total Lines" in content or "Total Bytes" in content):
            # Extract file path
            m_path = re.search(r"File Path:\s*`?file:///([^`\n]+)`?", content)
            if not m_path:
                continue
            orig_path = m_path.group(1).replace("%20", " ")
            
            # Resolve path relative to dst_root
            orig_path_norm = orig_path.replace("\\", "/")
            if "olympiad-ai-video_backup" in orig_path_norm:
                continue # skip backups
                
            if "olympiad-ai-video/" in orig_path_norm:
                rel = orig_path_norm.split("olympiad-ai-video/")[-1]
                target_path = os.path.join(dst_root, rel.replace("/", os.sep))
            else:
                continue
                
            if "recover" in target_path:
                continue
                
            # Clean content
            cleaned_lines = []
            for l in content.splitlines():
                m_line = re.match(r"^\s*\d+:\s?(.*)$", l)
                if m_line:
                    cleaned_lines.append(m_line.group(1))
                    
            cleaned_content = "\n".join(cleaned_lines).strip()
            if cleaned_content:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as out_f:
                    out_f.write(cleaned_content)
                print(f"Recovered from view (Step {step_idx}): {os.path.relpath(target_path, dst_root)} (len={len(cleaned_content)})")

print("View recovery finished!")
