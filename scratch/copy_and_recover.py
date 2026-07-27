import os
import shutil
import re

src_root = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video_backup"
dst_root = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video"

print("=== STEP 1: COPYING BASE CODE FROM BACKUP (FILE-BY-FILE) ===")
folders_to_sync = ["app", "prompts", "tests", "scripts"]

for folder in folders_to_sync:
    src_folder = os.path.join(src_root, folder)
    dst_folder = os.path.join(dst_root, folder)
    
    if not os.path.exists(src_folder):
        continue
        
    for root, dirs, files in os.walk(src_folder):
        rel_path = os.path.relpath(root, src_folder)
        target_dir = dst_folder if rel_path == "." else os.path.join(dst_folder, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                pass

print("Base copy complete.")

print("\n=== STEP 2: RECOVERING FROM VIEWS (settings.py, base.py, etc.) ===")
import recover_views

print("\n=== STEP 3: REPLAYING TRANSCRIPT EDITS UP TO STEP 2276 ===")
# Force reload of recover_as_of_step_v2
import importlib
import recover_as_of_step_v2
importlib.reload(recover_as_of_step_v2)

print("\n=== STEP 4: RESTORING COMPLETE OLLAMA PROVIDER ===")
import find_longest_ollama

print("\n=== STEP 5: FIXING PYPROJECT.TOML DUPLICATION ===")
toml_path = os.path.join(dst_root, "pyproject.toml")
if os.path.exists(toml_path):
    with open(toml_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    dup_block = '[tool.hatch.build.targets.wheel]\npackages = ["app"]\n\n\n[tool.hatch.build.targets.wheel]\npackages = ["app"]'
    if dup_block in content:
        content = content.replace(dup_block, '[tool.hatch.build.targets.wheel]\npackages = ["app"]')
    else:
        content = re.sub(r'\[tool\.hatch\.build\.targets\.wheel\]\s*packages\s*=\s*\["app"\]\s*\n\s*\[tool\.hatch\.build\.targets\.wheel\]\s*packages\s*=\s*\["app"\]', '[tool.hatch.build.targets.wheel]\npackages = ["app"]', content)
        
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed pyproject.toml.")

print("\nRestoration pipeline finished!")
