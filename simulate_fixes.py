import json
import re
import unicodedata
import os
from collections import defaultdict
from datetime import datetime

# Load original data
with open('scenes_v2.json', 'r', encoding='utf-8') as f:
    orig_data = json.load(f)

orig_scenes = orig_data.get('scenes', [])
print(f"Loaded {len(orig_scenes)} original scenes for simulation.")

# --- CORRECTION 1: Canonical Channel Map ---
CANONICAL_CHANNEL_MAP = {
    'cantinemarbree': 'Cantine-marbrée',
    'fontainemarbree': 'Fontaine-Marbrée',
    'terrainsnacres': 'Terrains-Nacrés',
    'halldesfetes': 'Hall-Des-Fêtes',
    'terraindentrainement': 'Terrain-d-entraînement',
    'agoradesreines2': 'Agora des Reines'
}

def get_canonical_channel(ch_name):
    if not ch_name:
        return "Salon RP"
    norm = unicodedata.normalize('NFKD', ch_name.lower())
    clean_key = re.sub(r'[^a-z0-9]', '', norm)
    if clean_key in CANONICAL_CHANNEL_MAP:
        return CANONICAL_CHANNEL_MAP[clean_key]
    
    # Capitalize hyphenated words neatly
    words = ch_name.replace('_', '-').split('-')
    cleaned_words = [w.strip() for w in words if w.strip()]
    return '-'.join(cleaned_words) if cleaned_words else ch_name

# --- CORRECTION 2: In-Message HRP Cleaning ---
HRP_STRIP_PATTERNS = [
    r'\(?\s*hrp\s*:.*?\)?',
    r'\(\(.*?\)\)',
    r'^\s*\|\|?\s*<@&?\d+>.*?(retard|impr[eé]vu|attente|navr[eé]|d[eé]sol[eé]|question).*?\|\|?',
    r'^\s*<@&?\d+>\s*$',
    r'^\s*@\S+\s+(navr[eé]|d[eé]sol[eé]).*$',
    r'navr[eé]\s+pour\s+le\s+retard.*$',
    r'd[eé]sol[eé]\s+pour\s+l[\'\"]attente.*$',
    r'd[eé]sol[eé]\s+du\s+retard.*$'
]
HRP_STRIP_REGEX = re.compile('|'.join(HRP_STRIP_PATTERNS), re.IGNORECASE | re.MULTILINE)

def clean_message_content(text):
    if not text:
        return ""
    cleaned = HRP_STRIP_REGEX.sub('', text).strip()
    # Clean leftover empty lines or leading/trailing HRP quotes
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

# --- SIMULATION PIPELINE ---
new_channel_messages = defaultdict(list)

# Step 1: Re-group all raw messages by Canonical Channel
for sc in orig_scenes:
    raw_ch = sc.get('channel_raw', sc.get('channel', ''))
    clean_ch = get_canonical_channel(sc.get('channel_clean', raw_ch))
    
    for m in sc.get('messages', []):
        raw_text = m.get('content', '')
        cleaned_text = clean_message_content(raw_text)
        
        # Keep if cleaned text is meaningful (> 5 chars)
        letters_only = re.sub(r'[^\w]', '', cleaned_text)
        if len(letters_only) >= 5:
            new_msg = dict(m)
            new_msg['content'] = cleaned_text
            new_channel_messages[clean_ch].append(new_msg)

print(f"Grouped messages into {len(new_channel_messages)} canonical channels.")

# Step 2: Re-build scenes with micro-scene merging & threshold filtering
simulated_scenes = []

for ch_name, msgs in new_channel_messages.items():
    if not msgs:
        continue
    
    # Sort messages by timestamp
    msgs.sort(key=lambda x: x.get('timestamp', ''))
    
    # Simple segmentation: group messages with gap < 18h into same scene
    current_scene_msgs = [msgs[0]]
    scene_index = 1
    
    def finalize_scene(scene_msgs, idx):
        if len(scene_msgs) < 3:
            # Drop standalone micro-scenes with < 3 messages (e.g. 1-2 msgs tests)
            return None
        
        actors = list(set(m.get('author', 'Narrateur') for m in scene_msgs if m.get('author')))
        if not actors:
            actors = ["Narrateur"]
            
        first_m = scene_msgs[0]
        last_m = scene_msgs[-1]
        
        words = sum(len(m.get('content', '').split()) for m in scene_msgs)
        preview = scene_msgs[0].get('content', '')[:157] + "..." if len(scene_msgs[0].get('content', '')) > 160 else scene_msgs[0].get('content', '')
        
        scene_id = f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', ch_name).lower()}_{idx}"
        
        return {
            "id": scene_id,
            "channel": ch_name,
            "channel_raw": ch_name,
            "channel_clean": ch_name,
            "title": f"{ch_name} — Scène {idx}",
            "actors": actors,
            "main_actor": actors[0],
            "start_time": first_m.get('timestamp', ''),
            "end_time": last_m.get('timestamp', ''),
            "duration_minutes": 1,
            "preview": preview,
            "message_count": len(scene_msgs),
            "word_count": words,
            "location_image": None,
            "messages": scene_msgs
        }

    for i in range(1, len(msgs)):
        prev_ts = msgs[i-1].get('timestamp', '')
        curr_ts = msgs[i].get('timestamp', '')
        
        # Check gap (default break if gap > 18 hours = 64800s)
        time_diff = 0
        try:
            t1 = datetime.fromisoformat(prev_ts.replace('Z', '+00:00')).timestamp()
            t2 = datetime.fromisoformat(curr_ts.replace('Z', '+00:00')).timestamp()
            time_diff = t2 - t1
        except Exception:
            pass
            
        if time_diff > 64800:
            sc_obj = finalize_scene(current_scene_msgs, scene_index)
            if sc_obj:
                simulated_scenes.append(sc_obj)
                scene_index += 1
            current_scene_msgs = [msgs[i]]
        else:
            current_scene_msgs.append(msgs[i])
            
    sc_obj = finalize_scene(current_scene_msgs, scene_index)
    if sc_obj:
        simulated_scenes.append(sc_obj)

print(f"Generated {len(simulated_scenes)} simulated scenes after corrections.")

# Step 3: Run Diagnostic check on Simulated dataset
sim_report = {
    'scenes': simulated_scenes
}
with open('scenes_simulated.json', 'w', encoding='utf-8') as f:
    json.dump(sim_report, f, ensure_ascii=False, indent=2)

print("Saved 'scenes_simulated.json'. Running evaluation...")
