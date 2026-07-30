import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('backend/multimodal/router.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = content.find('def multimodal_plan')
    if idx != -1:
        # print 3000 chars from the match
        print(content[idx:idx+3000])
    else:
        print("multimodal_plan not found")

if __name__ == '__main__':
    main()
