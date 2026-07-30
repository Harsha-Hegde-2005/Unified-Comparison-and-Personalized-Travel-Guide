import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = content.find('function ResultCard')
    if idx != -1:
        print(content[idx:idx+8000])

if __name__ == '__main__':
    main()
