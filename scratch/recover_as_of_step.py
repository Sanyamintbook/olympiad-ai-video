import json
import os
import re
from pathlib import Path

log_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript_full.jsonl")
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

MAX_STEP = 5298

if not log_path.exists():
    print("Transcript log file not found!")
    exit(1)

print(f"Starting chronological codebase reconstruction from conversation transcripts up to Step {MAX_STEP}...")

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

steps = []
for line in lines:
    try:
        step = json.loads(line)
        if step.get("step_index") <= MAX_STEP:
            steps.append(step)
    except Exception:
        continue

# 1. Reconstruct all files ever viewed with view_file chronologically
print("Replaying view_file events...")
for step in steps:
    tool_calls = step.get("tool_calls", [])
    if not tool_calls and "content" in step:
        content_str = step["content"]
        if content_str.strip().startswith("{") or "tool_calls" in content_str:
            try:
                nested = json.loads(content_str)
                tool_calls = nested.get("tool_calls", [])
            except Exception:
                pass

    for call in tool_calls:
        if call.get("name") == "view_file":
            args = call.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    continue
            filepath = args.get("AbsolutePath")
            if filepath:
                filepath = filepath.strip('"').strip("'")
                filepath = os.path.abspath(filepath)
                
                # Check if it belongs to active project
                if "olympiad-ai-video" in filepath and "olympiad-ai-video_backup" not in filepath and "recover_code.py" not in filepath and "recover_all.py" not in filepath:
                    content = step.get("content", "")
                    if content and "Showing lines" in content:
                        # Reconstruct file content from line output
                        cleaned_lines = []
                        for l in content.splitlines():
                            m = re.match(r"^\s*\d+:\s?(.*)$", l)
                            if m:
                                cleaned_lines.append(m.group(1))
                            else:
                                continue
                        cleaned_content = "\n".join(cleaned_lines).strip()
                        
                        if cleaned_content:
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            with open(filepath, "w", encoding="utf-8") as out_f:
                                out_f.write(cleaned_content)
                            print(f"Restored from view: {os.path.relpath(filepath, dst_root)}")

# 2. Replay all write_to_file and replacement tool calls chronologically
print("\nReplaying write/replace events...")
for step in steps:
    tool_calls = step.get("tool_calls", [])
    if not tool_calls and "content" in step:
        content_str = step["content"]
        if content_str.strip().startswith("{") or "tool_calls" in content_str:
            try:
                nested = json.loads(content_str)
                tool_calls = nested.get("tool_calls", [])
            except Exception:
                pass

    for call in tool_calls:
        name = call.get("name")
        args = call.get("args", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                continue

        target_file = args.get("TargetFile")
        if not target_file:
            continue

        target_file = target_file.strip('"').strip("'")
        target_file = os.path.abspath(target_file)

        if "olympiad-ai-video" not in target_file or "olympiad-ai-video_backup" in target_file or "recover" in target_file:
            continue

        if name == "write_to_file":
            content = args.get("CodeContent")
            if content is not None:
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                with open(target_file, "w", encoding="utf-8") as tf:
                    tf.write(content)
                print(f"Recreated: {os.path.relpath(target_file, dst_root)}")

        elif name == "replace_file_content" or name == "multi_replace_file_content":
            if not os.path.exists(target_file):
                continue

            with open(target_file, "r", encoding="utf-8") as tf:
                file_content = tf.read()

            if name == "replace_file_content":
                target_content = args.get("TargetContent")
                replacement_content = args.get("ReplacementContent")
                if target_content and target_content in file_content:
                    file_content = file_content.replace(target_content, replacement_content, 1)
                    with open(target_file, "w", encoding="utf-8") as tf:
                        tf.write(file_content)
                    print(f"Applied replacement to: {os.path.relpath(target_file, dst_root)}")

            elif name == "multi_replace_file_content":
                chunks = args.get("ReplacementChunks", [])
                if isinstance(chunks, str):
                    try:
                        chunks = json.loads(chunks)
                    except Exception:
                        continue
                applied_any = False
                for chunk in chunks:
                    if isinstance(chunk, str):
                        try:
                            chunk = json.loads(chunk)
                        except Exception:
                            continue
                    target_content = chunk.get("TargetContent")
                    replacement_content = chunk.get("ReplacementContent")
                    if target_content and target_content in file_content:
                        file_content = file_content.replace(target_content, replacement_content, 1)
                        applied_any = True
                if applied_any:
                    with open(target_file, "w", encoding="utf-8") as tf:
                        tf.write(file_content)
                    print(f"Applied multi-replacement to: {os.path.relpath(target_file, dst_root)}")

print("\nRestoration complete!")
