import json
import re
import sys

# Force UTF-8
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

with open('scenes_fixed_simulated.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scenes = data.get('scenes', [])

HRP_PATTERNS = [
    r'navr[eé].*(retard|impr[eé]vu|attente|temps)',
    r'd[eé]sol[eé].*(retard|impr[eé]vu|attente|temps)',
    r'\(?\s*hrp\s*:.*?\)?',
    r'<@&?\d+>',
    r'@\S+',
    r'^\s*\|\|.*\|\|\s*$'
]
HRP_REGEX = re.compile('|'.join(HRP_PATTERNS), re.IGNORECASE)

print("=== 1. ANALYSE DES LEAKS HRP RESTANTS ===")
hrp_scenes = []
for s in scenes:
    matches_in_scene = []
    for m in s.get('messages', []):
        c = m.get('content', '')
        match = HRP_REGEX.search(c)
        if match:
            matches_in_scene.append((match.group(0), c))
    if matches_in_scene:
        hrp_scenes.append((s, matches_in_scene))

print(f"Total scènes avec HRP restant: {len(hrp_scenes)}")
for s, matches in hrp_scenes:
    print(f"[{s['id']}] Salon: {s['channel_clean']}")
    for match_str, content in matches[:3]:
        print(f"   Match: {repr(match_str)}")
        print(f"   Extrait: {repr(content[:150])}")
    print()

print("=== 2. ANALYSE DES 12 SCÈNES SINGLE ACTOR ===")
single_actor_scenes = [s for s in scenes if len(s.get('actors', [])) == 1]
for s in single_actor_scenes:
    act = s.get('actors', [])[0]
    print(f"[{s['id']}] Salon: {s['channel_clean']} | Acteur: {act} | Msgs: {s['message_count']}")
    print(f"   Titre: {s['title']}")
    # print raw authors in messages to see if there are missing mappings
    authors = set(m.get('author') for m in s.get('messages', []))
    print(f"   Auteurs réels dans les messages: {list(authors)}")
    print(f"   Extrait: {repr(s.get('preview', '')[:100])}\n")

print("=== 3. ANALYSE DES 10 SCÈNES DE 3-4 MESSAGES ===")
short_scenes = [s for s in scenes if 3 <= s.get('message_count', 0) <= 4]
for s in short_scenes:
    print(f"[{s['id']}] Salon: {s['channel_clean']} | Acteurs: {s.get('actors', [])} | Msgs: {s['message_count']}")
    print(f"   Titre: {s['title']}")
    print(f"   Extrait: {repr(s.get('preview', '')[:100])}\n")
