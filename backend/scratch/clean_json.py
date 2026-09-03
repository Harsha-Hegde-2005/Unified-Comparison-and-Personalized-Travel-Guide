import json
import os

with open('scratch/full_user_input.json', 'r', encoding='utf-8') as f:
    text = f.read()

# Strip tags
if text.startswith('<USER_REQUEST>'):
    text = text[len('<USER_REQUEST>'):]
if text.endswith('</USER_REQUEST>'):
    text = text[:-len('</USER_REQUEST>')]
text = text.strip()

# Find the start of the truncation notice
trunc_idx = text.find('<truncated')
print("trunc_idx:", trunc_idx)

if trunc_idx != -1:
    # Cut off everything from the truncation
    clean_text = text[:trunc_idx].rstrip()
    
    # We are inside "night" array of "2026-07-17"
    # Let's find "night" index
    night_idx = clean_text.rfind('"night":')
    print("night_idx:", night_idx)
    if night_idx != -1:
        clean_text = clean_text[:night_idx].rstrip()
        # Remove trailing comma if any
        if clean_text.endswith(','):
            clean_text = clean_text[:-1].rstrip()
        # Add closing braces
        clean_text += '\n  }\n}'
    
    try:
        data = json.loads(clean_text)
        print('Successfully cleaned and parsed JSON!')
        for date in data:
            print(date)
            for slot in data[date]:
                print(f'  {slot}: {len(data[date][slot])} routes')
        with open('scratch/cleaned_benchmark.json', 'w', encoding='utf-8') as out:
            json.dump(data, out, indent=2)
    except Exception as e:
        print('Failed to parse clean text:', e)
else:
    print("No truncation notice found!")
