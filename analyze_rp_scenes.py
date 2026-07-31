import json
import re
import unicodedata
from datetime import datetime
from collections import defaultdict

# Load dataset
with open('scenes_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scenes = data.get('scenes', [])
characters = data.get('characters', {})

print(f"Loaded {len(scenes)} scenes.")

channel_analysis = defaultdict(list)
inconsistencies = []

# Regex patterns for HRP detection
HRP_PATTERNS = [
    r'navr[eé].*(retard|impr[eé]vu|attente|temps)',
    r'd[eé]sol[eé].*(retard|impr[eé]vu|attente|temps)',
    r'\(?\s*hrp\s*:.*?\)?',
    r'<@&?\d+>',
    r'@\S+',
    r'^\s*\|\|.*\|\|\s*$'
]
HRP_REGEX = re.compile('|'.join(HRP_PATTERNS), re.IGNORECASE)

# Track clean channels
clean_to_raw_channels = defaultdict(set)

for idx, s in enumerate(scenes):
    s_id = s.get('id', str(idx))
    ch_raw = s.get('channel_raw') or s.get('channel') or 'Inconnu'
    ch_clean = s.get('channel_clean') or ch_raw
    clean_to_raw_channels[ch_clean].add(ch_raw)
    
    title = s.get('title', 'Sans Titre')
    actors = s.get('actors', [])
    main_actor = s.get('main_actor', 'Inconnu')
    msg_count = s.get('message_count', len(s.get('messages', [])))
    word_count = s.get('word_count', 0)
    messages = s.get('messages', [])
    start_time = s.get('start_time', '')
    end_time = s.get('end_time', '')
    duration = s.get('duration_minutes', 0)
    
    # Store in channel analysis
    channel_analysis[ch_clean].append({
        'id': s_id,
        'raw_channel': ch_raw,
        'title': title,
        'actors': actors,
        'main_actor': main_actor,
        'msg_count': msg_count,
        'word_count': word_count,
        'start_time': start_time,
        'end_time': end_time,
        'duration': duration
    })
    
    # --- Check 1: Message count anomalies ---
    if msg_count <= 2:
        inconsistencies.append({
            'type': 'CRITICAL_LOW_MESSAGES',
            'severity': 'HIGH' if msg_count == 1 else 'MEDIUM',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"Scène avec seulement {msg_count} message(s) (souvent une scène avortée, un message système ou un faux découpage)."
        })
    elif msg_count <= 4:
        inconsistencies.append({
            'type': 'LOW_MESSAGES',
            'severity': 'LOW',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"Scène courte avec seulement {msg_count} messages."
        })
        
    # --- Check 2: Participant anomalies ---
    if len(actors) == 0:
        inconsistencies.append({
            'type': 'NO_ACTORS',
            'severity': 'HIGH',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': "Aucun participant détecté dans les métadonnées de la scène."
        })
    elif len(actors) == 1:
        inconsistencies.append({
            'type': 'SINGLE_ACTOR',
            'severity': 'MEDIUM',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"Un seul participant détecté ({actors[0]}). Est-ce un monologue RP, une scène solo ou un second joueur non identifié ?"
        })
        
    # Check if actors in array match message authors
    msg_authors = set()
    for m in messages:
        auth = m.get('author') or m.get('character') or m.get('user')
        if auth:
            msg_authors.add(auth)
            
    actor_set = set(actors)
    missing_in_msg = actor_set - msg_authors
    missing_in_actors = msg_authors - actor_set
    
    if missing_in_msg:
        inconsistencies.append({
            'type': 'ACTOR_ARRAY_MISMATCH',
            'severity': 'MEDIUM',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"Personnages listés dans actors mais sans aucun message dans la scène: {list(missing_in_msg)}"
        })
        
    if missing_in_actors:
        inconsistencies.append({
            'type': 'AUTHOR_NOT_IN_ACTORS',
            'severity': 'MEDIUM',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"Auteurs de messages non répertoriés dans l'array actors: {list(missing_in_actors)}"
        })
        
    # Check suspicious names (e.g. Narrateur, Oeil, handles, Tupperbox)
    suspicious_names = {'Narrateur', 'Oeil', 'Tupperbox', 'System', 'Unknown'}
    for act in actors:
        if act in suspicious_names or re.search(r'^\d+$', act) or re.search(r'#\d{4}$', act):
            inconsistencies.append({
                'type': 'SUSPICIOUS_ACTOR_NAME',
                'severity': 'LOW',
                'scene_id': s_id,
                'channel': ch_clean,
                'title': title,
                'details': f"Nom d'acteur suspect ou générique détecté: '{act}'"
            })

    # --- Check 3: HRP leakage in messages ---
    hrp_found = 0
    for m in messages:
        content = m.get('content', '')
        if HRP_REGEX.search(content):
            hrp_found += 1
    if hrp_found > 0:
        inconsistencies.append({
            'type': 'HRP_LEAK',
            'severity': 'LOW',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"{hrp_found} message(s) contiennent encore des résidus HRP, excuses ou pings."
        })
        
    # --- Check 4: Duration / Timestamp anomalies ---
    if msg_count > 5 and duration == 0:
        inconsistencies.append({
            'type': 'ZERO_DURATION',
            'severity': 'LOW',
            'scene_id': s_id,
            'channel': ch_clean,
            'title': title,
            'details': f"Scène de {msg_count} messages avec une durée calculée de 0 minute (horodatages identiques ou très proches)."
        })

# --- Check 5: Duplicate / Accentuated channel names ---
cleaned_names_map = defaultdict(list)
for ch in channel_analysis.keys():
    # normalize accents and lower case
    norm = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFD', ch.lower()))
    norm = re.sub(r'[^a-z0-9]', '', norm)
    cleaned_names_map[norm].append(ch)

for norm, variants in cleaned_names_map.items():
    if len(variants) > 1:
        inconsistencies.append({
            'type': 'DUPLICATE_CHANNEL_VARIANTS',
            'severity': 'HIGH',
            'scene_id': 'N/A',
            'channel': ', '.join(variants),
            'title': 'Variantes de salon dupliquées',
            'details': f"Doublon de salon lié aux accents ou à la casse: {variants}"
        })

# Summary output
print("\n=== SYNTHÈSE DE L'ANALYSE ===")
print(f"Nombre total de salons analysés: {len(channel_analysis)}")
print(f"Nombre total de scènes analysées: {len(scenes)}")
print(f"Nombre total d'anomalies / incohérences trouvées: {len(inconsistencies)}")

# Group inconsistencies by type
type_counts = defaultdict(int)
for inc in inconsistencies:
    type_counts[inc['type']] += 1

print("\nDécomposition par type d'incohérence:")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {t}: {count}")

# Save detailed JSON report
report = {
    'summary': {
        'total_channels': len(channel_analysis),
        'total_scenes': len(scenes),
        'total_inconsistencies': len(inconsistencies),
        'inconsistency_breakdown': dict(type_counts)
    },
    'channels': {ch: scenes_list for ch, scenes_list in channel_analysis.items()},
    'inconsistencies': inconsistencies
}

with open('rp_analysis_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\nRapport complet sauvegardé dans 'rp_analysis_report.json'.")
