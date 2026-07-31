import json
import sys

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('scenes.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

scenes = raw_data.get('scenes', raw_data if isinstance(raw_data, list) else [])
porcelaine_scenes = [s for s in scenes if 'porcelaine' in s.get('channel_clean', '').lower()]

all_msgs = []
for sc in porcelaine_scenes:
    for m in sc.get('messages', []):
        all_msgs.append(m)

all_msgs.sort(key=lambda m: m.get('timestamp', ''))

for idx in range(43, len(all_msgs)):
    m = all_msgs[idx]
    author = m.get('author_name', m.get('author', 'INCONNU'))
    ts = m.get('timestamp', '')
    print(f"==================== MSG {idx+1} | {ts} | {author} ====================")
    print(m.get('content', ''))
    print()
