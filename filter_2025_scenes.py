import json, sys, os, shutil

sys.stdout.reconfigure(encoding='utf-8')

with open('scenes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scenes = data.get('scenes', [])
original_count = len(scenes)

filtered_scenes = [s for s in scenes if not s.get('start_time', '').startswith('2025')]
removed_count = original_count - len(filtered_scenes)

data['scenes'] = filtered_scenes

print(f"Removed {removed_count} scenes from 2025. Total scenes remaining: {len(filtered_scenes)}")

with open('scenes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

if os.path.exists('src/scenes.json'):
    with open('src/scenes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

with open('data.js', 'w', encoding='utf-8') as f:
    f.write('window.rpData = ')
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write(';\n')

if os.path.exists('Ancien_site/data.js'):
    shutil.copy('data.js', 'Ancien_site/data.js')

print('Filtered database saved to scenes.json, src/scenes.json, data.js, and Ancien_site/data.js!')
