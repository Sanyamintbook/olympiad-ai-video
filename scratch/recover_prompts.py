import json
import os
import re

log_path = r"C:\Users\Sanyami Jain\.gemini\antigravity\brain\66215fa5-0146-44f7-b208-67cfbed0ff43\.system_generated\logs\transcript_full.jsonl"
prompts_dir = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts"

os.makedirs(prompts_dir, exist_ok=True)

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
        
        # Look in tool calls
        tool_calls = []
        content_str = step.get("content", "")
        if content_str and (content_str.strip().startswith("{") or "tool_calls" in content_str):
            try:
                nested = json.loads(content_str)
                tool_calls = nested.get("tool_calls", [])
            except Exception:
                pass
        
        if not tool_calls and "tool_calls" in step:
            tool_calls = step["tool_calls"]
            
        for call in tool_calls:
            name = call.get("name")
            args = call.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    continue
            
            # Check write_to_file calls
            if name == "write_to_file":
                target = args.get("TargetFile", "")
                if "content_understanding.md" in target or "lesson_planner.md" in target:
                    content = args.get("CodeContent")
                    if content:
                        filename = os.path.basename(target)
                        dest = os.path.join(prompts_dir, filename)
                        with open(dest, "w", encoding="utf-8") as tf:
                            tf.write(content)
                        print(f"Reconstructed from write_to_file: {filename}")
            
            # Check replace_file_content calls where file didn't exist, maybe we can see TargetContent/ReplacementContent
            if name in ("replace_file_content", "multi_replace_file_content"):
                target = args.get("TargetFile", "")
                if "content_understanding.md" in target or "lesson_planner.md" in target:
                    print(f"Replacement call for {os.path.basename(target)}:")
                    print(json.dumps(args, indent=2))
                    
        # Check if the output of some read_file / view_file call contained the prompt contents
        if step.get("source") == "SYSTEM" and "content" in step:
            sys_content = step["content"]
            # Look for file contents in system output
            if "File Path: " in sys_content and ("content_understanding.md" in sys_content or "lesson_planner.md" in sys_content):
                print("Found file viewing content in logs!")
                # Let's extract file name and contents
                # The format is typically:
                # File Path: `file:///.../content_understanding.md`
                # Total Lines: ...
                # Total Bytes: ...
                # Showing lines ...
                # <line_number>: <content>
                match = re.search(r"File Path: `file:///(.*?)`", sys_content)
                if match:
                    filepath = match.group(1)
                    filename = os.path.basename(filepath)
                    lines = []
                    for line in sys_content.splitlines():
                        line_match = re.match(r"^\d+: (.*)", line)
                        if line_match:
                            lines.append(line_match.group(1))
                    if lines:
                        dest = os.path.join(prompts_dir, filename)
                        with open(dest, "w", encoding="utf-8") as tf:
                            tf.write("\n".join(lines))
                        print(f"Reconstructed from view_file output: {filename}")
