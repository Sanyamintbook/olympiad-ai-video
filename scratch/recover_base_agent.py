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
        if "class BaseAgent:" in content and "def _build_prompt" in content:
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
            if "generate_structured" in full_code:
                print(f"FOUND FULL BASE_AGENT.PY IN STEP {step.get('step_index')}")
                target_path = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\base_agent.py"
                with open(target_path, "w", encoding="utf-8") as out:
                    out.write(full_code)
                print("Successfully recovered base_agent.py!")
                break
