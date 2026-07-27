log_path = r"C:\Users\Sanyami Jain\Documents\Vidoe_Automation\logs\application.log"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Print last 50 lines first
print("\n=== LAST 50 LOG LINES ===")
for l in lines[-50:]:
    print(l.strip())

# Search for errors from today (2026-07-08)
print("\n=== ERRORS TODAY ===")
count = 0
for l in lines:
    if "2026-07-08" in l and ("failed" in l.lower() or "error" in l.lower() or "exception" in l.lower() or "warn" in l.lower()):
        print(l.strip())
        count += 1
        if count > 100:
            print("... truncated ...")
            break
