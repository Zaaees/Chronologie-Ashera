import json
import sys
import re
import unicodedata
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

def analyze():
    with open('scenes_v2.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])
    characters = data.get('characters', {})

    # Channel stats mapping
    channel_data = defaultdict(lambda: {
        'clean_name': '',
        'raw_names': set(),
        'scenes': [],
        'total_messages': 0,
        'total_words': 0,
        'participants': set()
    })

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
        ch_raw = s.get('channel_raw') or s.get('channel') or 'Inconnu'
        ch_clean = s.get('channel_clean') or ch_raw
        title = s.get('title', 'Sans Titre')
        actors = s.get('actors', [])
        messages = s.get('messages', [])
        msg_count = s.get('message_count', len(messages))
        word_count = s.get('word_count', 0)
        start_time = s.get('start_time', '')
        end_time = s.get('end_time', '')
        duration = s.get('duration_minutes', 0)
        
        c = channel_data[ch_clean]
        c['clean_name'] = ch_clean
        c['raw_names'].add(ch_raw)
        c['total_messages'] += msg_count
        c['total_words'] += word_count
        for act in actors:
            c['participants'].add(act)
        
        scene_info = {
            'id': s_id,
            'title': title,
            'actors': actors,
            'msg_count': msg_count,
            'word_count': word_count,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'raw_channel': ch_raw
        }
        c['scenes'].append(scene_info)

        # 1. Low message count anomalies
        if msg_count <= 2:
            anomalies.append({
                'type': 'CRITICAL_LOW_MESSAGES',
                'severity': 'HIGH' if msg_count == 1 else 'MEDIUM',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': actors,
                'msg_count': msg_count,
                'details': f"Scène avec seulement {msg_count} message(s) (avortée, message système ou découpage erroné)."
            })
        elif msg_count <= 4:
            anomalies.append({
                'type': 'LOW_MESSAGES',
                'severity': 'LOW',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': actors,
                'msg_count': msg_count,
                'details': f"Scène très courte ({msg_count} messages)."
            })

        # 2. Participant anomalies
        if len(actors) == 0:
            anomalies.append({
                'type': 'NO_ACTORS',
                'severity': 'HIGH',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': [],
                'msg_count': msg_count,
                'details': "Aucun participant dans la scène."
            })
        elif len(actors) == 1:
            anomalies.append({
                'type': 'SINGLE_ACTOR',
                'severity': 'MEDIUM',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': actors,
                'msg_count': msg_count,
                'details': f"Un seul participant ({actors[0]}). Monologue ou second joueur non identifié."
            })

        # Message author vs metadata actors mismatch
        msg_authors = set()
        for m in messages:
            auth = m.get('author') or m.get('character') or m.get('user')
            if auth:
                msg_authors.add(auth)
        
        missing_in_actors = msg_authors - set(actors)
        if missing_in_actors:
            anomalies.append({
                'type': 'AUTHOR_NOT_IN_ACTORS',
                'severity': 'MEDIUM',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': actors,
                'msg_count': msg_count,
                'details': f"Auteur(s) de message non listé(s) dans actors: {list(missing_in_actors)}"
            })

        # Suspicious actor names
        suspicious = [a for a in actors if a in {'Narrateur', 'Oeil', 'Tupperbox', 'System', 'Unknown'} or re.search(r'^\d+$', a)]
        if suspicious:
            anomalies.append({
                'type': 'SUSPICIOUS_ACTOR_NAME',
                'severity': 'LOW',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': actors,
                'msg_count': msg_count,
                'details': f"Nom(s) d'acteur(s) suspect(s): {suspicious}"
            })

        # 3. HRP leak check
        hrp_count = sum(1 for m in messages if HRP_REGEX.search(m.get('content', '')))
        if hrp_count > 0:
            anomalies.append({
                'type': 'HRP_LEAK',
                'severity': 'LOW',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'actors': actors,
                'msg_count': msg_count,
                'details': f"{hrp_count} message(s) contiennent des résidus HRP, excuses ou pings."
            })

    # 4. Duplicate / Accentuated channel variants
    channel_norm_map = defaultdict(list)
    for ch_name in channel_data.keys():
        norm = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFD', ch_name.lower()))
        norm = re.sub(r'[^a-z0-9]', '', norm)
        channel_norm_map[norm].append(ch_name)

    for norm, variants in channel_norm_map.items():
        if len(variants) > 1:
            anomalies.append({
                'type': 'DUPLICATE_CHANNEL_VARIANTS',
                'severity': 'HIGH',
                'scene_id': 'N/A',
                'channel': ', '.join(variants),
                'title': 'Variantes de salon dupliquées',
                'actors': [],
                'msg_count': 0,
                'details': f"Variantes de noms du salon détectées: {variants}"
            })

    # Save output summary
    out = {
        'total_channels': len(channel_data),
        'total_scenes': len(scenes),
        'total_anomalies': len(anomalies),
        'anomaly_counts': dict(Counter(a['type'] for a in anomalies)),
        'channels': {
            ch: {
                'clean_name': data['clean_name'],
                'raw_names': list(data['raw_names']),
                'scene_count': len(data['scenes']),
                'total_messages': data['total_messages'],
                'total_words': data['total_words'],
                'participants': sorted(list(data['participants'])),
                'scenes': data['scenes']
            } for ch, data in channel_data.items()
        },
        'anomalies': anomalies
    }

    with open('full_rp_analysis.json', 'w', encoding='utf-8') as out_f:
        json.dump(out, out_f, ensure_ascii=False, indent=2)

    print("Full RP Analysis complete.")
    print(f"Channels: {len(channel_data)} | Scenes: {len(scenes)} | Anomalies: {len(anomalies)}")

if __name__ == '__main__':
    analyze()
