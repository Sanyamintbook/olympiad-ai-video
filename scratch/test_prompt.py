from pathlib import Path
import os
import sys

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.infrastructure.ai.prompts.loader import PromptLoader

print("=== DIAGNOSTICS ===")
print(f"Current file: {__file__}")
print(f"Current working dir: {os.getcwd()}")

settings = get_settings()
print(f"settings.prompts_directory: {settings.prompts_directory}")

loader = PromptLoader()
print(f"loader.prompt_directory: {loader.prompt_directory}")

try:
    content = loader.load("content_understanding")
    print("SUCCESS: Prompt loaded successfully!")
    print(f"Prompt length: {len(content)} characters")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {str(e)}")
    
    # Let's inspect the files in loader.prompt_directory
    p = Path(loader.prompt_directory)
    if p.exists():
        print(f"Files in {p}:")
        for f in p.iterdir():
            print(f" - {f.name}")
    else:
        print(f"Directory does not exist: {p}")
