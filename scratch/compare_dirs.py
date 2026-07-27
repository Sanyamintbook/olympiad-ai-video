import os
import filecmp

dir1 = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video"
dir2 = r"C:\Users\Sanyami Jain\OneDrive - K-Nomics Techno Solution PVT LTD\Documents\Vidoe_Automation\olympiad-ai-video"

print("=== COMPARISON ===")
print(f"Local: {dir1}")
print(f"OneDrive: {dir2}")

def compare(d1, d2):
    if not os.path.exists(d2):
        print(f"OneDrive directory does not exist: {d2}")
        return
        
    dcmp = filecmp.dircmp(d1, d2)
    
    # Files only in local
    if dcmp.left_only:
        print(f"\nFiles only in Local ({os.path.relpath(d1, dir1)}):")
        for f in dcmp.left_only:
            if not f.startswith(".") and f != "scratch":
                print(f" - {f}")
                
    # Files only in OneDrive
    if dcmp.right_only:
        print(f"\nFiles only in OneDrive ({os.path.relpath(d1, dir1)}):")
        for f in dcmp.right_only:
            if not f.startswith("."):
                print(f" - {f}")
                
    # Differing files
    if dcmp.diff_files:
        print(f"\nDiffering files ({os.path.relpath(d1, dir1)}):")
        for f in dcmp.diff_files:
            print(f" - {f}")
            
    # Recurse into subdirs
    for sub in dcmp.common_dirs:
        if sub.startswith(".") or sub == "scratch" or sub == "htmlcov" or sub == "dist" or sub == "build":
            continue
        compare(os.path.join(d1, sub), os.path.join(d2, sub))

compare(dir1, dir2)
