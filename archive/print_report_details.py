import json
import sys

# Force UTF-8 stdout
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

with open('rp_analysis_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

inc_by_type = {}
for inc in report['inconsistencies']:
    inc_by_type.setdefault(inc['type'], []).append(inc)

for t, items in inc_by_type.items():
    print(f"=== {t} ({len(items)}) ===")
    for item in items:
        scene_id = item.get('scene_id', 'N/A')
        channel = item.get('channel', 'Inconnu')
        title = item.get('title', '')
        details = item.get('details', '')
        print(f"  [{scene_id}] {channel} | {title} => {details}")
    print()
