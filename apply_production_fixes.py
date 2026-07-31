import json
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8')

print("=== APPLYING PRODUCTION FIXES ===")

# Load ultimate dataset
with open('scenes_fixed_ultimate.json', 'r', encoding='utf-8') as f:
    ult_data = json.load(f)

# Update metadata timestamp and counts
scenes = ult_data.get('scenes', [])
characters = ult_data.get('characters', {})

ult_data['metadata'] = {
    "version": "2.0-fixed",
    "generated_at": datetime.datetime.now().isoformat(),
    "total_scenes": len(scenes),
    "total_characters": len(characters)
}

# 1. Update scenes.json
with open('scenes.json', 'w', encoding='utf-8') as f:
    json.dump(ult_data, f, ensure_ascii=False, indent=2)
print("Updated 'scenes.json'.")

# 2. Update scenes_v2.json
with open('scenes_v2.json', 'w', encoding='utf-8') as f:
    json.dump(ult_data, f, ensure_ascii=False, indent=2)
print("Updated 'scenes_v2.json'.")

# 3. Update data.js
js_content = "window.rpData = " + json.dumps(ult_data, ensure_ascii=False, indent=2) + ";"
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
print("Updated 'data.js'.")

print("\nProduction files updated successfully.")
