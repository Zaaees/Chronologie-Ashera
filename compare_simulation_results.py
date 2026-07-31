import json
import re
import unicodedata
from collections import defaultdict

with open('scenes_v2.json', 'r', encoding='utf-8') as f:
    orig_data = json.load(f)

with open('scenes_fixed_simulated.json', 'r', encoding='utf-8') as f:
    fixed_data = json.load(f)

orig_scenes = orig_data.get('scenes', [])
fixed_scenes = fixed_data.get('scenes', [])

print("=== COMPARATIF AVANT / APRÈS CORRECTIONS ===")
print(f"Nombre de scènes originales : {len(orig_scenes)}")
print(f"Nombre de scènes simulées   : {len(fixed_scenes)}")

HRP_PATTERNS = [
    r'navr[eé].*(retard|impr[eé]vu|attente|temps)',
    r'd[eé]sol[eé].*(retard|impr[eé]vu|attente|temps)',
    r'\(?\s*hrp\s*:.*?\)?',
    r'<@&?\d+>',
    r'@\S+',
    r'^\s*\|\|.*\|\|\s*$'
]
HRP_REGEX = re.compile('|'.join(HRP_PATTERNS), re.IGNORECASE)

inconsistencies = []
cleaned_names_map = defaultdict(list)
channels_set = set()

for s in fixed_scenes:
    s_id = s.get('id', '')
    ch_clean = s.get('channel_clean', '')
    channels_set.add(ch_clean)
    
    msg_count = s.get('message_count', 0)
    actors = s.get('actors', [])
    messages = s.get('messages', [])
    
    if msg_count <= 2:
        inconsistencies.append({'type': 'CRITICAL_LOW_MESSAGES', 'channel': ch_clean, 'id': s_id})
    elif msg_count <= 4:
        inconsistencies.append({'type': 'LOW_MESSAGES', 'channel': ch_clean, 'id': s_id})
        
    if len(actors) == 1:
        inconsistencies.append({'type': 'SINGLE_ACTOR', 'channel': ch_clean, 'id': s_id})
        
    hrp_cnt = sum(1 for m in messages if HRP_REGEX.search(m.get('content', '')))
    if hrp_cnt > 0:
        inconsistencies.append({'type': 'HRP_LEAK', 'channel': ch_clean, 'id': s_id})

for ch in channels_set:
    norm = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFD', ch.lower()))
    norm = re.sub(r'[^a-z0-9]', '', norm)
    cleaned_names_map[norm].append(ch)

dup_channels = [variants for norm, variants in cleaned_names_map.items() if len(variants) > 1]

print('\n--- RÉSULTATS DES TESTS ET COMPARAISON ---')
print(f"Salons dupliqués (Accents) : AVANT = 5 groupes  --> APRÈS = {len(dup_channels)} groupe(s)")
print(f"Fuites HRP (Out-of-Character): AVANT = 50 scènes  --> APRÈS = {sum(1 for i in inconsistencies if i['type'] == 'HRP_LEAK')} scène(s)")
print(f"Micro-scènes (1-2 msgs)     : AVANT = 16 scènes  --> APRÈS = {sum(1 for i in inconsistencies if i['type'] == 'CRITICAL_LOW_MESSAGES')} scène(s)")
print(f"Scènes 3-4 msgs             : AVANT = 10 scènes  --> APRÈS = {sum(1 for i in inconsistencies if i['type'] == 'LOW_MESSAGES')} scène(s)")
print(f"Single Actor                : AVANT = 24 scènes  --> APRÈS = {sum(1 for i in inconsistencies if i['type'] == 'SINGLE_ACTOR')} scène(s)")
print(f"Total anomalies restantes   : AVANT = 107        --> APRÈS = {len(inconsistencies)}")
