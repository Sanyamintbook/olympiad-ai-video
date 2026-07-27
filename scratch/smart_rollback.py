import json
import os
import re
from pathlib import Path

log_path = Path("C:/Users/Sanyami Jain/.gemini/antigravity/brain/66215fa5-0146-44f7-b208-67cfbed0ff43/.system_generated/logs/transcript_full.jsonl")
dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"

MAX_STEP = 5298

# List of files we know were changed/created after MAX_STEP
files_to_check = [
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\domain\models\lesson_plan.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\domain\models\understanding.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\content\chunk_topic_extractor.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\content\metadata_extractor.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\content\topic_merger.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\content_understanding_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\lesson\audience_profiler_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\lesson\lesson_plan_compiler_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\lesson_planner_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\script\script_writer_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\script\tone_refiner_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\script_generator_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\teaching_unit_planner_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\unit\unit_content_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\unit\unit_goal_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\validator\constraint_validator_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\validator\fact_checker_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\agents\validator_agent.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\ai\providers\ollama_provider.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\app\infrastructure\queue\tasks.py",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\audience_profiler.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\content_extraction_chunk.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\content_understanding.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\teaching_unit_planner.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\tone_refiner.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\unit_content_generator.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\unit_goal_generator.md",
    r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video\prompts\validator.md"
]
files_to_check = [os.path.abspath(f) for f in files_to_check]

# Map from file path to the reconstructed content
file_states = {}

# 1. Forward pass from step 0 to MAX_STEP to reconstruct files from write_to_file and view_file
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            step = json.loads(line)
            if step.get("step_index") > MAX_STEP:
                break
                
            tool_calls = step.get("tool_calls", [])
            content_str = step.get("content", "")
            
            if not tool_calls and content_str:
                if content_str.strip().startswith("{") or "tool_calls" in content_str:
                    try:
                        nested = json.loads(content_str)
                        tool_calls = nested.get("tool_calls", [])
                    except:
                        pass

            for call in tool_calls:
                name = call.get("name")
                args = call.get("args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        continue
                
                if name == "view_file":
                    filepath = args.get("AbsolutePath")
                    if filepath:
                        filepath = os.path.abspath(filepath.strip('"').strip("'"))
                        if filepath in files_to_check:
                            if "Showing lines" in content_str:
                                cleaned_lines = []
                                for l in content_str.splitlines():
                                    m = re.match(r"^\s*\d+:\s?(.*)$", l)
                                    if m:
                                        cleaned_lines.append(m.group(1))
                                cleaned_content = "\n".join(cleaned_lines)
                                file_states[filepath] = cleaned_content
                                
                elif name == "write_to_file":
                    target_file = args.get("TargetFile")
                    if target_file:
                        target_file = os.path.abspath(target_file.strip('"').strip("'"))
                        if target_file in files_to_check:
                            file_states[target_file] = args.get("CodeContent", "")
                            
                elif name == "replace_file_content":
                    target_file = args.get("TargetFile")
                    if target_file:
                        target_file = os.path.abspath(target_file.strip('"').strip("'"))
                        if target_file in files_to_check and target_file in file_states:
                            target_content = args.get("TargetContent", "")
                            replacement_content = args.get("ReplacementContent", "")
                            if target_content in file_states[target_file]:
                                file_states[target_file] = file_states[target_file].replace(target_content, replacement_content, 1)

                elif name == "multi_replace_file_content":
                    target_file = args.get("TargetFile")
                    if target_file:
                        target_file = os.path.abspath(target_file.strip('"').strip("'"))
                        if target_file in files_to_check and target_file in file_states:
                            chunks = args.get("ReplacementChunks", [])
                            if isinstance(chunks, str):
                                try:
                                    chunks = json.loads(chunks)
                                except:
                                    pass
                            for chunk in chunks:
                                if isinstance(chunk, str):
                                    try:
                                        chunk = json.loads(chunk)
                                    except:
                                        continue
                                target_content = chunk.get("TargetContent", "")
                                replacement_content = chunk.get("ReplacementContent", "")
                                if target_content in file_states[target_file]:
                                    file_states[target_file] = file_states[target_file].replace(target_content, replacement_content, 1)

        except Exception as e:
            continue

# 2. Apply states or delete if they didn't exist
print(f"Rolling back {len(files_to_check)} files...")
for filepath in files_to_check:
    if filepath in file_states:
        print(f"Restoring {os.path.basename(filepath)} to state at step {MAX_STEP}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as out_f:
            out_f.write(file_states[filepath])
    else:
        print(f"Deleting {os.path.basename(filepath)} (did not exist at step {MAX_STEP})")
        if os.path.exists(filepath):
            os.remove(filepath)
            
print("Rollback complete.")
