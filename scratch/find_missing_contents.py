import json
from pathlib import Path

def find_contents():
    transcript_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript.jsonl")
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    targets = ["settings.py", "pyproject.toml", "main.py", ".env"]
    
    for target in targets:
        print(f"\n=== Searching for matches of: {target} ===")
        found = False
        for i, line in enumerate(lines):
            if target in line:
                try:
                    step = json.loads(line)
                    # Print context
                    print(f"Line {i} (Type: {step.get('type')}):")
                    # If tool call has the filename, print args
                    for call in step.get("tool_calls", []):
                        args = call.get("args", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                pass
                        if target in str(args):
                            print(f"  Tool: {call.get('name')}")
                            # Print a snippet of args
                            args_str = str(args)
                            print(f"  Args snippet: {args_str[:300]}...")
                            found = True
                except Exception:
                    pass
        if not found:
            print("  No JSON tool call match found.")

if __name__ == "__main__":
    find_contents()
