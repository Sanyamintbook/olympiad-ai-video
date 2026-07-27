import json
import os
from pathlib import Path

log_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript_full.jsonl")

MAX_STEP = 5298

files_created_or_modified = set()

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
            if step.get("step_index") > MAX_STEP:
                tool_calls = step.get("tool_calls", [])
                
                # Check for tool_calls in nested json string
                if not tool_calls and "content" in step:
                    content_str = step["content"]
                    if content_str.strip().startswith("{") or "tool_calls" in content_str:
                        try:
                            nested = json.loads(content_str)
                            tool_calls = nested.get("tool_calls", [])
                        except:
                            pass
                            
                for call in tool_calls:
                    name = call.get("name")
                    if name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
                        args = call.get("args", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except:
                                continue
                        target_file = args.get("TargetFile")
                        if target_file and "olympiad-ai-video" in target_file and "scratch" not in target_file and "backup" not in target_file:
                            files_created_or_modified.add(target_file)
        except Exception:
            continue

print("Files modified/created AFTER step 5298:")
for f in sorted(files_created_or_modified):
    print(f)
