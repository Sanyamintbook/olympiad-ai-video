import os
import shutil

src_root = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video_backup"
dst_root = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video"

print("=== OVERWRITING CODEBASE FROM BACKUP (FILE-BY-FILE) ===")
print(f"Source: {src_root}")
print(f"Destination: {dst_root}")

# List of folders to sync
folders_to_sync = ["app", "prompts", "tests", "scripts"]

for folder in folders_to_sync:
    src_folder = os.path.join(src_root, folder)
    dst_folder = os.path.join(dst_root, folder)
    
    if not os.path.exists(src_folder):
        continue
        
    for root, dirs, files in os.walk(src_folder):
        # Determine relative path from src_folder
        rel_path = os.path.relpath(root, src_folder)
        target_dir = dst_folder if rel_path == "." else os.path.join(dst_folder, rel_path)
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy files
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)
            
            try:
                shutil.copy2(src_file, dst_file)
                print(f"Copied file: {os.path.relpath(dst_file, dst_root)}")
            except Exception as e:
                print(f"Error copying {os.path.relpath(dst_file, dst_root)}: {str(e)}")

print("\nOverwriting complete!")
