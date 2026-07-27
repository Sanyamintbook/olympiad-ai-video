import json
import os
import re
from pathlib import Path

def recover_all():
    transcript_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript_full.jsonl")
    if not transcript_path.exists():
        transcript_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript.jsonl")
    
    print(f"Reading from transcript path: {transcript_path}")
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    steps = []
    for line in lines:
        try:
            steps.append(json.loads(line))
        except Exception:
            continue
            
    print(f"Total parsed steps: {len(steps)}")
    
    # 1. First, let's find the full contents of pyproject.toml, settings.py, main.py, and .env
    # from any view_file system responses in the logs!
    for i, step in enumerate(steps):
        tool_calls = step.get("tool_calls", [])
        for call in tool_calls:
            if call.get("name") == "view_file":
                args = call.get("args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        pass
                filepath = args.get("AbsolutePath", "")
                filepath = filepath.strip('"').strip("'")
                
                # Check if it matches any target
                for t in ["main.py", "pyproject.toml", ".env", "settings.py"]:
                    if t in filepath:
                        # Find the next step which is the response content
                        if i + 1 < len(steps):
                            next_step = steps[i+1]
                            content = next_step.get("content", "")
                            if content:
                                # Clean line numbers - only keep lines starting with <number>:
                                cleaned_lines = []
                                for line in content.splitlines():
                                    m = re.match(r"^\s*\d+:\s?(.*)$", line)
                                    if m:
                                        cleaned_lines.append(m.group(1))
                                    else:
                                        # Skip all metadata header/footer lines
                                        continue
                                cleaned_content = "\n".join(cleaned_lines).strip()
                                
                                # Resolve path
                                target_path = os.path.abspath(filepath)
                                if "olympiad-ai-video_backup" not in target_path:
                                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                    with open(target_path, "w", encoding="utf-8") as out_f:
                                        out_f.write(cleaned_content)
                                    print(f"RESTORED FROM VIEW: {target_path} (len={len(cleaned_content)})")

    # 2. Replay all write_to_file and replacement tool calls chronologically
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

            # Helper function to clean strings
            def clean_str(s):
                return s

            def clean_content(s):
                return s

            target_file = clean_str(target_file)
            target_file = os.path.abspath(target_file)

            if "olympiad-ai-video_backup" in target_file:
                continue

            if "recover_all.py" in target_file or "recover_code.py" in target_file:
                continue

            if name == "write_to_file":
                content = clean_content(args.get("CodeContent"))
                if content is not None:
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    with open(target_file, "w", encoding="utf-8") as tf:
                        tf.write(content)
                    print(f"Recreated: {target_file}")

            elif name == "replace_file_content" or name == "multi_replace_file_content":
                if not os.path.exists(target_file):
                    # If file doesn't exist, we skip replacement
                    continue

                with open(target_file, "r", encoding="utf-8") as tf:
                    file_content = tf.read()

                if name == "replace_file_content":
                    target_content = clean_content(args.get("TargetContent"))
                    replacement_content = clean_content(args.get("ReplacementContent"))
                    if target_content in file_content:
                        file_content = file_content.replace(target_content, replacement_content, 1)
                        with open(target_file, "w", encoding="utf-8") as tf:
                            tf.write(file_content)
                        print(f"Applied replacement to: {target_file}")

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
                        target_content = clean_content(chunk.get("TargetContent"))
                        replacement_content = clean_content(chunk.get("ReplacementContent"))
                        if target_content in file_content:
                            file_content = file_content.replace(target_content, replacement_content, 1)
                            applied_any = True
                    if applied_any:
                        with open(target_file, "w", encoding="utf-8") as tf:
                            tf.write(file_content)
                        print(f"Applied multi-replacement to: {target_file}")

if __name__ == "__main__":
    recover_all()
