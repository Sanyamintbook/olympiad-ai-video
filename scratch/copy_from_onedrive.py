import os
import shutil

src_root = r"C:\Users\Sanyami Jain\OneDrive - K-Nomics Techno Solution PVT LTD\Documents\Vidoe_Automation\olympiad-ai-video"
dst_root = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video"

print("=== COPYING LATEST CODEBASE FROM ONEDRIVE ===")
print(f"Source: {src_root}")
print(f"Destination: {dst_root}")

# List of folders and files to copy
items_to_copy = ["app", "prompts", "tests", "main.py", "pyproject.toml", "debug_real_pdf.py", "debug_upload.py"]

for item in items_to_copy:
    src_path = os.path.join(src_root, item)
    dst_path = os.path.join(dst_root, item)
    
    if not os.path.exists(src_path):
        print(f"Skipping {item} (does not exist in source)")
        continue
        
    # If destination exists, delete it first to ensure clean copy
    if os.path.exists(dst_path):
        if os.path.isdir(dst_path):
            shutil.rmtree(dst_path)
        else:
            os.remove(dst_path)
            
    # Copy
    if os.path.isdir(src_path):
        shutil.copytree(src_path, dst_path)
        print(f"Copied folder: {item}")
    else:
        shutil.copy2(src_path, dst_path)
        print(f"Copied file: {item}")

print("\nCopy complete!")
