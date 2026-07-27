import json
import re

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
            
        content = step.get("content", "")
        if "PROJECT_ROOT =" in content and "class Settings(" in content and "def get_settings()" in content:
            # We found a text snippet with the full settings.py content!
            # Clean up line numbers
            cleaned_lines = []
            for l in content.splitlines():
                # Matches patterns like "23: some code" or " 23: some code"
                m = re.match(r"^\s*\d+:\s?(.*)$", l)
                if m:
                    cleaned_lines.append(m.group(1))
                else:
                    if not re.match(r"^\s*\d+\s*$", l) and "Showing lines" not in l and "Total Lines" not in l:
                        cleaned_lines.append(l)
            
            full_code = "\n".join(cleaned_lines)
            # Verify if it contains the full settings class
            if "max_local_retries_before_escalation" in full_code:
                print(f"FOUND FULL SETTINGS.PY IN STEP {step.get('step_index')}")
                target_path = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\config\settings.py"
                with open(target_path, "w", encoding="utf-8") as out:
                    out.write(full_code)
                print("Successfully recovered settings.py!")
                break
