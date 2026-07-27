import json
import re

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

longest_len = 0
longest_code = ""
longest_step = -1

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        content = step.get("content", "")
        # Must be a complete file view (no diff markers)
        if "class BaseAgent:" in content and "self.router" in content and "@@ -" not in content and "[diff_block_start]" not in content:
            # Clean up line numbers
            cleaned_lines = []
            for l in content.splitlines():
                m = re.match(r"^\s*\d+:\s?(.*)$", l)
                if m:
                    cleaned_lines.append(m.group(1))
                else:
                    if not re.match(r"^\s*\d+\s*$", l) and "Showing lines" not in l and "Total Lines" not in l:
                        cleaned_lines.append(l)
            
            full_code = "\n".join(cleaned_lines)
            if "The above content shows" in full_code:
                full_code = full_code.split("The above content shows")[0].strip()
            if "The above content does NOT show" in full_code:
                full_code = full_code.split("The above content does NOT show")[0].strip()
                
            if len(full_code) > longest_len:
                longest_len = len(full_code)
                longest_code = full_code
                longest_step = step.get("step_index")

if longest_code:
    print(f"FOUND LONGEST COMPLETE BASE_AGENT.PY IN STEP {longest_step} (length={longest_len})")
    target_path = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\base_agent.py"
    with open(target_path, "w", encoding="utf-8") as out:
        out.write(longest_code)
    print("Successfully recovered the complete base_agent.py!")
else:
    print("No complete base_agent.py found.")
