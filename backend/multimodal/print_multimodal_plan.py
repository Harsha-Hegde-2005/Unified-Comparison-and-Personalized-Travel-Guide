with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for idx in range(1830, min(len(lines), 1950)):
    print(f"{idx+1}: {lines[idx].rstrip()}")
