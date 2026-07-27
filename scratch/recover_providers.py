import json
import os
import re

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"

targets = {
    "gemini_provider.py": r"app\infrastructure\ai\providers\gemini_provider.py",
    "openai_provider.py": r"app\infrastructure\ai\providers\openai_provider.py",
    "base.py": r"app\infrastructure\ai\providers\base.py",
    "router.py": r"app\infrastructure\ai\providers\router.py",
    "provider_factory.py": r"app\infrastructure\ai\providers\provider_factory.py",
    "llm_response.py": r"app\infrastructure\ai\schemas\llm_response.py",
}

for name, rel_path in targets.items():
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
            # We look for files matching the name
            if name in content and ("class " in content or "def " in content) and "@@ -" not in content and "[diff_block_start]" not in content:
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
        print(f"FOUND LONGEST {name} IN STEP {longest_step} (length={longest_len})")
        target_path = os.path.join(r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video", rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # Clean headers
        code_lines = longest_code.splitlines()
        clean_lines = []
        started = False
        for l in code_lines:
            if l.startswith("Created At:") or l.startswith("Completed At:") or l.startswith("File Path:") or l.startswith("Total Bytes:") or "modified to include a line number" in l:
                continue
            clean_lines.append(l)
        clean_code = "\n".join(clean_lines).strip()
        
        with open(target_path, "w", encoding="utf-8") as out:
            out.write(clean_code)
        print(f"Successfully recovered {name} to {target_path}!")
    else:
        print(f"Could not find any complete source for {name} in transcript.")
