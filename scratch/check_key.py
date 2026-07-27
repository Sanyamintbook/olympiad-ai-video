import os
key = os.environ.get("GEMINI_API_KEY", "")
print("GEMINI_API_KEY exists:", bool(key))
if key:
    print("Length of key:", len(key))
    print("First 5 chars:", key[:5])
    print("Last 5 chars:", key[-5:])
else:
    print("No GEMINI_API_KEY found in active env variables.")
