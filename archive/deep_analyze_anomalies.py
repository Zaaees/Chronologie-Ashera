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

print("=== DEEP ANALYSIS OF ANOMALIES ===")

# 1. DUPLICATE_CHANNEL_VARIANTS
print("\n--- 1. DUPLICATE_CHANNEL_VARIANTS (5 items) ---")
for inc in anomalies:
    if inc['type'] == 'DUPLICATE_CHANNEL_VARIANTS':
        print(f"[BUG CERTAIN] Channel duplicate: {inc['channel']} => {inc['details']}")

# 2. SUSPICIOUS_ACTOR_NAME
print("\n--- 2. SUSPICIOUS_ACTOR_NAME (2 items) ---")
for inc in anomalies:
    if inc['type'] == 'SUSPICIOUS_ACTOR_NAME':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        print(f"Scene [{s_id}] in '{sc.get('channel')}' - Title: '{sc.get('title')}'")
        print(f"  Actors: {sc.get('actors')}")
        print(f"  Details: {inc['details']}")

# 3. CRITICAL_LOW_MESSAGES (16 items)
print("\n--- 3. CRITICAL_LOW_MESSAGES (16 items) ---")
for inc in anomalies:
    if inc['type'] == 'CRITICAL_LOW_MESSAGES':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        msgs = sc.get('messages', [])
        print(f"\nScene [{s_id}] Channel: '{sc.get('channel_clean')}' | Title: '{sc.get('title')}' | Msgs: {len(msgs)}")
        print(f"  Actors: {sc.get('actors')}")
        for idx, m in enumerate(msgs):
            author = m.get('author') or m.get('character') or m.get('user')
            content = m.get('content', '').replace('\n', ' ')
            print(f"    Msg {idx+1} [{author}]: {content[:150]}")

# 4. SINGLE_ACTOR (24 items)
print("\n--- 4. SINGLE_ACTOR (24 items) ---")
single_actor_types = {'SOLO_RP': 0, 'UNIDENTIFIED_PARTNER': 0, 'SYSTEM_MSG': 0}
for inc in anomalies:
    if inc['type'] == 'SINGLE_ACTOR':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        msgs = sc.get('messages', [])
        msg_authors = set(m.get('author') or m.get('character') or m.get('user') for m in msgs)
        msg_authors.discard(None)
        print(f"Scene [{s_id}] Channel: '{sc.get('channel_clean')}' | Actors in metadata: {sc.get('actors')} | Authors in msgs: {list(msg_authors)} | Msgs count: {len(msgs)}")

# 5. HRP LEAKS overview
print("\n--- 5. HRP_LEAK (50 items) ---")
hrp_examples = []
for inc in anomalies:
    if inc['type'] == 'HRP_LEAK':
        s_id = inc['scene_id']
        sc = scenes_dict.get(s_id, {})
        msgs = sc.get('messages', [])
        for m in msgs:
            c = m.get('content', '')
            if 'retard' in c.lower() or 'hrp' in c.lower() or '<@' in c:
                hrp_examples.append((s_id, m.get('author'), c[:120]))
                if len(hrp_examples) >= 8:
                    break
        if len(hrp_examples) >= 8:
            break

for s_id, auth, snippet in hrp_examples:
    print(f"  [{s_id}] ({auth}): {snippet}")
