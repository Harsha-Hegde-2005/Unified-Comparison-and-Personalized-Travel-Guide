with open('backend/multimodal/router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(min(len(lines), 150)):
    print(f"{i+1}: {lines[i].rstrip()}")
