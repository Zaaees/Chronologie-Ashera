import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('full_rp_analysis.json', 'r', encoding='utf-8') as f:
    audit_data = json.load(f)

with open('scenes_v2.json', 'r', encoding='utf-8') as f:
    scenes_data = json.load(f)

scenes_dict = {s.get('id', str(i)): s for i, s in enumerate(scenes_data.get('scenes', []))}

anomalies = audit_data['anomalies']

# Categorization counters
results = {
    'DUPLICATE_CHANNELS': {'to_fix': 5, 'normal': 0, 'details': []},
    'SUSPICIOUS_ACTOR': {'to_fix': 0, 'normal': 2, 'details': []},
    'CRITICAL_LOW_MESSAGES': {'to_fix': 0, 'normal': 0, 'details': []},
    'SINGLE_ACTOR': {'to_fix': 0, 'normal': 0, 'details': []},
    'HRP_LEAK': {'to_fix': 0, 'normal': 0, 'details': []}
}

# Inspect CRITICAL_LOW_MESSAGES
crit_to_fix = 0
crit_normal = 0
for inc in anomalies:
    if inc['type'] == 'CRITICAL_LOW_MESSAGES':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        msgs = sc.get('messages', [])
        content_concat = " ".join(m.get('content', '') for m in msgs)
        if len(msgs) == 1 or 'discord.com/channels' in content_concat or 'salon libre' in content_concat.lower() or 'scène terminée' in content_concat.lower():
            crit_to_fix += 1
            results['CRITICAL_LOW_MESSAGES']['details'].append((s_id, 'TO_FIX', sc.get('channel_clean'), sc.get('title'), len(msgs)))
        else:
            crit_normal += 1
            results['CRITICAL_LOW_MESSAGES']['details'].append((s_id, 'NORMAL', sc.get('channel_clean'), sc.get('title'), len(msgs)))

results['CRITICAL_LOW_MESSAGES']['to_fix'] = crit_to_fix
results['CRITICAL_LOW_MESSAGES']['normal'] = crit_normal

# Inspect SINGLE_ACTOR
single_to_fix = 0
single_normal = 0
for inc in anomalies:
    if inc['type'] == 'SINGLE_ACTOR':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        msgs = sc.get('messages', [])
        if len(msgs) <= 2:
            single_to_fix += 1 # These coincide with critical low / aborted scenes
        else:
            single_normal += 1 # Valid solo RP monologues (5 to 10 msgs)

results['SINGLE_ACTOR']['to_fix'] = single_to_fix
results['SINGLE_ACTOR']['normal'] = single_normal

# Inspect HRP_LEAK
HRP_REAL_PATTERNS = [
    r'\(?\s*hrp\s*:.*?\)?',
    r'<@&?\d+>',
    r'd[eé]sol[eé].*(retard|irl|attente)',
    r'navr[eé].*(retard|irl|attente)'
]
HRP_REAL_REGEX = re.compile('|'.join(HRP_REAL_PATTERNS), re.IGNORECASE)

hrp_to_fix = 0
hrp_normal = 0
for inc in anomalies:
    if inc['type'] == 'HRP_LEAK':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        msgs = sc.get('messages', [])
        has_real_hrp = False
        for m in msgs:
            c = m.get('content', '')
            if HRP_REAL_REGEX.search(c):
                has_real_hrp = True
                break
        if has_real_hrp:
            hrp_to_fix += 1
        else:
            hrp_normal += 1

results['HRP_LEAK']['to_fix'] = hrp_to_fix
results['HRP_LEAK']['normal'] = hrp_normal

print(json.dumps(results, indent=2, ensure_ascii=False))
