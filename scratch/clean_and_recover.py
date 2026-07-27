import os
import shutil

dst_root = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\olympiad-ai-video"

print("=== CLEANING ACTIVE APP FOLDER ===")
app_dir = os.path.join(dst_root, "app")
if os.path.exists(app_dir):
    try:
        shutil.rmtree(app_dir)
        print("Successfully deleted app folder!")
    except Exception as e:
        print(f"Error deleting app folder: {e}")
        # If it failed, delete contents recursively
        for root, dirs, files in os.walk(app_dir, topdown=False):
            for f in files:
                try: os.remove(os.path.join(root, f))
                except: pass
            for d in dirs:
                try: os.rmdir(os.path.join(root, d))
                except: pass
        print("Recursively cleaned app folder contents.")

# Run the recovery as of step script
print("\n=== RUNNING RECOVERY AS OF STEP 2276 (V2) ===")
import recover_as_of_step_v2
