import os

search_paths = [r"C:\Program Files", r"C:\Program Files (x86)", r"C:\ProgramData"]

found = False
for path in search_paths:
    if not os.path.exists(path):
        continue
    for root, dirs, files in os.walk(path):
        if "redis-server.exe" in files:
            print(f"FOUND: {os.path.join(root, 'redis-server.exe')}")
            found = True
            break

if not found:
    print("Not found in standard paths.")
