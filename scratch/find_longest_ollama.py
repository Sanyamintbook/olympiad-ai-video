import json
import os
import re

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

longest_len = 0
longest_code = ""
longest_step = -1

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        step_idx = step.get("step_index")
        if step_idx > 2276: # Only up to Step 2276
            continue
            
        content = step.get("content", "")
        if "ollama_provider.py" in content and "class OllamaProvider" in content and "import json" in content and "@@ -" not in content and "[diff_block_start]" not in content:
            cleaned_lines = []
            for l in content.splitlines():
                m = re.match(r"^\s*\d+:\s?(.*)$", l)
                if m:
                    cleaned_lines.append(m.group(1))
                    
            full_code = "\n".join(cleaned_lines).strip()
            if len(full_code) > longest_len:
                longest_len = len(full_code)
                longest_code = full_code
                longest_step = step_idx

if longest_code:
    print(f"FOUND LONGEST OLLAMA PROVIDER IN STEP {longest_step} (length={longest_len})")
    target_path = os.path.join(dst_root, r"app\infrastructure\ai\providers\ollama_provider.py")
    with open(target_path, "w", encoding="utf-8") as out:
        out.write(longest_code)
    print("Successfully restored complete ollama_provider.py!")
else:
    print("Could not find complete ollama_provider.py in logs.")
