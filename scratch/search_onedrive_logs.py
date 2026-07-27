log_path = r"C:\Users\Sanyami Jain\OneDrive - K-Nomics Techno Solution PVT LTD\Documents\Vidoe_Automation\olympiad-ai-video\logs\application.log"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Print last 50 lines first
print("\n=== LAST 50 LOG LINES ===")
for l in lines[-50:]:
    out = l.strip()
    print(out.encode('ascii', errors='replace').decode('ascii'))

# Search for errors from today (2026-07-08)
print("\n=== ERRORS TODAY ===")
count = 0
for l in lines:
    if "2026-07-08" in l and ("failed" in l.lower() or "error" in l.lower() or "exception" in l.lower() or "warn" in l.lower()):
        out = l.strip()
        print(out.encode('ascii', errors='replace').decode('ascii'))
        count += 1
        if count > 100:
            print("... truncated ...")
            break
