import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = content.find('@app.post("/api/compare")')
    if idx != -1:
        print(content[idx:idx+8000])

if __name__ == '__main__':
    main()
