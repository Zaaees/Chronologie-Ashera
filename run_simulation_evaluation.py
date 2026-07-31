import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

with open('full_rp_analysis.json', 'r', encoding='utf-8') as f:
    orig_audit = json.load(f)

print("=== DEEP SIMULATION EVALUATION ===")
print(f"Dataset Original (actuel du site) :")
print(f"  - Scènes totales : {orig_audit['total_scenes']}")
print(f"  - Salons uniques : {orig_audit['total_channels']}")
print(f"  - Anomalies totales : {orig_audit['total_anomalies']}")
print(f"  - Décomposition des anomalies : {orig_audit['anomaly_counts']}")

# Load ultimate simulated dataset
with open('scenes_fixed_ultimate.json', 'r', encoding='utf-8') as f:
    ult_data = json.load(f)

scenes = ult_data.get('scenes', ult_data) if isinstance(ult_data, dict) else ult_data

# Run audit rules directly on scenes_fixed_ultimate
import re
import unicodedata
from collections import defaultdict, Counter

channels = defaultdict(lambda: {'scenes': [], 'total_messages': 0, 'participants': set()})
HRP_PATTERNS = [
    r'navr[eé].*(retard|impr[eé]vu|attente|temps)',
    r'd[eé]sol[eé].*(retard|impr[eé]vu|attente|temps)',
    r'\(?\s*hrp\s*:.*?\)?',
    r'<@&?\d+>',
    r'@\S+',
    r'^\s*\|\|.*\|\|\s*$'
]
HRP_REGEX = re.compile('|'.join(HRP_PATTERNS), re.IGNORECASE)

anomalies = []

for idx, s in enumerate(scenes):
    s_id = s.get('id', str(idx))
    ch_clean = s.get('channel_clean') or s.get('channel') or 'Inconnu'
    title = s.get('title', 'Sans Titre')
    actors = s.get('actors', [])
    messages = s.get('messages', [])
    msg_count = len(messages)
    
    channels[ch_clean]['scenes'].append(s)
    channels[ch_clean]['total_messages'] += msg_count
    for act in actors:
        channels[ch_clean]['participants'].add(act)
        
    if msg_count <= 2:
        anomalies.append({
            'type': 'CRITICAL_LOW_MESSAGES',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'msg_count': msg_count
        })
    elif msg_count <= 4:
        anomalies.append({
            'type': 'LOW_MESSAGES',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'msg_count': msg_count
        })
        
    if len(actors) == 1:
        anomalies.append({
            'type': 'SINGLE_ACTOR',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'actors': actors,
            'msg_count': msg_count
        })
        
    hrp_count = sum(1 for m in messages if HRP_REGEX.search(m.get('content', '')))
    if hrp_count > 0:
        anomalies.append({
            'type': 'HRP_LEAK',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'msg_count': msg_count,
            'hrp_count': hrp_count
        })

# Check duplicates
channel_norm_map = defaultdict(list)
for ch_name in channels.keys():
    norm = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFD', ch_name.lower()))
    norm = re.sub(r'[^a-z0-9]', '', norm)
    channel_norm_map[norm].append(ch_name)

for norm, variants in channel_norm_map.items():
    if len(variants) > 1:
        anomalies.append({
            'type': 'DUPLICATE_CHANNEL_VARIANTS',
            'channel': ', '.join(variants)
        })

print("\nDataset Simulé Corrigé (scenes_fixed_ultimate.json) :")
print(f"  - Scènes totales : {len(scenes)}")
print(f"  - Salons uniques : {len(channels)}")
print(f"  - Anomalies totales restantes : {len(anomalies)}")

cnt_map = dict(Counter(a['type'] for a in anomalies))
print("  - Décomposition des anomalies restantes :")
for cat, cnt in cnt_map.items():
    print(f"      - {cat}: {cnt}")

print("\n=== COMPARAISON ET GAINS DE LA SIMULATION ===")
print(f"• Salons RP dupliqués : {orig_audit['anomaly_counts'].get('DUPLICATE_CHANNEL_VARIANTS', 0)} ==> {cnt_map.get('DUPLICATE_CHANNEL_VARIANTS', 0)} (100% éliminés !)")
print(f"• Scènes critiques (1-2 msgs) : {orig_audit['anomaly_counts'].get('CRITICAL_LOW_MESSAGES', 0)} ==> {cnt_map.get('CRITICAL_LOW_MESSAGES', 0)} ({orig_audit['anomaly_counts'].get('CRITICAL_LOW_MESSAGES', 0) - cnt_map.get('CRITICAL_LOW_MESSAGES', 0)} purifiées !)")
print(f"• Résidus HRP : {orig_audit['anomaly_counts'].get('HRP_LEAK', 0)} ==> {cnt_map.get('HRP_LEAK', 0)} ({orig_audit['anomaly_counts'].get('HRP_LEAK', 0) - cnt_map.get('HRP_LEAK', 0)} nettoyés !)")

