import re
import os

dst_root = "C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video"
path_str = "C:/Users/Sanyami%20Jain/Documents/Vidoe_Automation/olympiad-ai-video/app/infrastructure/ai/providers/base.py"

orig_path = path_str.replace("%20", " ")
orig_path_norm = orig_path.replace("\\", "/")

if "olympiad-ai-video_backup" in orig_path_norm:
    print("Skipped due to backup")
elif "olympiad-ai-video/" in orig_path_norm:
    rel = orig_path_norm.split("olympiad-ai-video/")[-1]
    target_path = os.path.join(dst_root, rel.replace("/", os.sep))
    print(f"Target path: {target_path}")
else:
    print("Skipped, no olympiad-ai-video/")
