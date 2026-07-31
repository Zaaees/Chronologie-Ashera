import json
import re
import sys
import os
import unicodedata
from datetime import datetime

# Force UTF-8
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from ai_narrative_segmenter_v2 import segment_messages_into_scenes_v2, parse_timestamp_v2
from unify_characters_v2 import get_canonical_name_v2, build_unified_characters_dict_v2, CHARACTER_METADATA_V2

# --- CORRECTION 1: Canonical Channel Map ---
CANONICAL_CHANNEL_MAP = {
    'cantinemarbree': 'Cantine-marbrée',
    'cantinemarbree': 'Cantine-marbrée',
    'fontainemarbree': 'Fontaine-Marbrée',
    'terrainsnacres': 'Terrains-Nacrés',
    'halldesfetes': 'Hall-Des-Fêtes',
    'terraindentrainement': 'Terrain-d-entraînement',
    'agoradesreines2': 'Agora des Reines'
}

def clean_channel_name_fixed(channel_raw):
    if not channel_raw:
        return "Salon RP"
    
    norm = unicodedata.normalize('NFKC', channel_raw)
    clean = re.sub(r'[^\w\s\-\'’àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', '', norm).strip()
    clean = re.sub(r'\s+', ' ', clean)
    
    # Check canonical map
    key = re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFD', clean.lower()))
    if key in CANONICAL_CHANNEL_MAP:
        return CANONICAL_CHANNEL_MAP[key]
        
    return clean if clean else channel_raw.strip()

# --- CORRECTION 2: In-Message HRP Stripping ---
HRP_EXCL_PATTERNS = [
    r'navr[eé].*\b(retard|impr[eé]vu|attente|temps)\b',
    r'd[eé]sol[eé].*\b(retard|impr[eé]vu|attente|temps)\b',
    r'^\s*\|\|.*\|\|\s*$',
    r'^\s*<@&?\d+>\s*$',
    r'^\s*@\S+\s*$',
    r'^\s*@\S+\s+navr[eé]',
    r'^\s*@\S+\s+d[eé]sol[eé]',
    r'^\s*\|\|?\s*<@&?\d+>.*(retard|impr[eé]vu|attente|navr[eé]|d[eé]sol[eé]|question)',
    r'^\s*\(?\s*hrp\s*:.*?\)?\s*$'
]
HRP_EXCL_REGEX = re.compile('|'.join(HRP_EXCL_PATTERNS), re.IGNORECASE)

HRP_INLINE_STRIP = [
    r'\(?\s*hrp\s*:.*?\)?',
    r'\(\(.*?\)\)',
    r'^\s*\|\|?\s*<@&?\d+>.*?(retard|impr[eé]vu|attente|navr[eé]|d[eé]sol[eé]|question).*?\|\|?',
    r'^\s*<@&?\d+>\s*$',
    r'navr[eé]\s+pour\s+le\s+retard.*$',
    r'd[eé]sol[eé]\s+pour\s+l[\'\"]attente.*$',
    r'd[eé]sol[eé]\s+du\s+retard.*$'
]
HRP_INLINE_REGEX = re.compile('|'.join(HRP_INLINE_STRIP), re.IGNORECASE | re.MULTILINE)

def clean_message_content_fixed(content):
    if not content:
        return ""
    text = str(content).strip()
    # Remove Discord user/role pings
    text = re.sub(r'<@[!&]?\d+>', '', text)
    # Remove Tupperbox ping headers like '@> Ju | Lucia ...'
    text = re.sub(r'^\s*@>\s*[^\n]+', '', text)
    # Remove empty codeblocks like ``` ```
    text = re.sub(r'```\s*```', '', text)
    
    cleaned = HRP_INLINE_REGEX.sub('', text).strip()
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

def is_meaningful_rp_content_fixed(content):
    if not content:
        return False
    text = str(content).strip()
    if not text:
        return False
    if text.startswith('||') and text.endswith('||'):
        return False
    if HRP_EXCL_REGEX.search(text):
        return False

    clean = re.sub(r'<@[!&]?\d+>', '', text)
    clean = re.sub(r'<#\d+>', '', clean)
    clean = re.sub(r'\[Image:\s*https?://\S+\]', '', clean)
    clean = re.sub(r'https?://\S+', '', clean)
    clean = re.sub(r'\[.*?\]\(https?://\S+\)', '', clean)
    clean = re.sub(r'@[^\n@]+', '', clean)
    
    letters_only = re.sub(r'[^\w]', '', clean, flags=re.UNICODE).replace('_', '').strip()
    if len(letters_only) < 5:
        lower = letters_only.lower()
        if lower in ['ping', 'up', 'relance', 'atoai', 'atois', 'avous', 'hrp', 'inrp', 'ok', 'thx', 'oeil', 'loeil']:
            return False

    return len(letters_only) >= 3

def compute_location_image(channel_clean):
    img_dir = "public/channel_images"
    if not os.path.exists(img_dir):
        return None
    img_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    ch_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFD', channel_clean.lower())).strip()
    for img in img_files:
        base = os.path.splitext(img)[0]
        base_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFD', base.lower())).strip()
        if base_c and (base_c == ch_c or base_c in ch_c or ch_c in base_c):
            return f"channel_images/{img}"
    return None

def compute_faction_distribution(actors, characters_dict):
    factions = {}
    for act in actors:
        char_info = characters_dict.get(act, CHARACTER_METADATA_V2.get(act, {}))
        role = char_info.get('role', 'Indéfini') if isinstance(char_info, dict) else 'Indéfini'
        factions[role] = factions.get(role, 0) + 1
    return factions

def create_scene_object_fixed(channel_clean, channel_raw, scene_index, message_tuples, title_suggested):
    rp_msgs = [m for m in message_tuples if is_meaningful_rp_content_fixed(m[1])]
    if not rp_msgs:
        rp_msgs = message_tuples

    first_msg = rp_msgs[0][0]
    last_msg = rp_msgs[-1][0]

    raw_actors = set()
    total_words = 0
    cleaned_messages = []

    for msg, text in rp_msgs:
        author = msg.get('author_name', msg.get('author', ''))
        canon = get_canonical_name_v2(author)
        raw_actors.add(canon)
        
        cleaned_txt = clean_message_content_fixed(text)
        total_words += len(cleaned_txt.split())
        
        cleaned_messages.append({
            "id": msg.get('id', ''),
            "author": canon,
            "timestamp": msg.get('timestamp', ''),
            "content": cleaned_txt if cleaned_txt else text
        })

    actors = list(raw_actors) if raw_actors else ["Narrateur"]
    main_actor = actors[0] if actors else "Narrateur"

    start_ts = parse_timestamp_v2(first_msg.get('timestamp'))
    end_ts = parse_timestamp_v2(last_msg.get('timestamp'))
    duration_mins = max(1, int((end_ts - start_ts) / 60)) if (end_ts > start_ts and start_ts > 0) else 1

    preview = cleaned_messages[0]['content']
    clean_p = re.sub(r'^\s*\|\|?\s*<@&?\d+>\s*\|\|?', '', preview).strip()
    if clean_p:
        preview = clean_p
    if len(preview) > 160:
        preview = preview[:157] + "..."

    location_image = compute_location_image(channel_clean)
    scene_id = f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', channel_clean).lower()}_{scene_index}"

    return {
        "id": scene_id,
        "channel": channel_raw,
        "channel_raw": channel_raw,
        "channel_clean": channel_clean,
        "title": title_suggested if title_suggested else f"{channel_clean} — Scène {scene_index}",
        "actors": actors,
        "main_actor": main_actor,
        "start_time": first_msg.get('timestamp', ''),
        "end_time": last_msg.get('timestamp', ''),
        "duration_minutes": duration_mins,
        "preview": preview,
        "message_count": len(cleaned_messages),
        "word_count": total_words,
        "location_image": location_image,
        "messages": cleaned_messages
    }

def run_simulation():
    src_file = 'src/scenes.json'
    with open(src_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    existing_scenes = raw_data.get('scenes', raw_data if isinstance(raw_data, list) else [])

    channels_map = {}
    for sc in existing_scenes:
        ch_raw = sc.get('channel_raw', sc.get('channel', 'Salon Inconnu'))
        ch_clean = clean_channel_name_fixed(ch_raw)

        if ch_clean not in channels_map:
            channels_map[ch_clean] = {'raw': ch_raw, 'messages': []}

        msgs = sc.get('messages', [])
        if msgs:
            for m in msgs:
                full_text = m.get('content', '')
                if is_meaningful_rp_content_fixed(full_text):
                    channels_map[ch_clean]['messages'].append((m, full_text))

    all_v2_scenes = []

    for ch_clean, ch_info in channels_map.items():
        ch_raw = ch_info['raw']
        sorted_msgs = sorted(ch_info['messages'], key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))
        valid_msgs = [m for m in sorted_msgs if m[1].strip()]

        if not valid_msgs:
            continue

        ch_scenes = segment_messages_into_scenes_v2(
            ch_clean,
            ch_raw,
            valid_msgs,
            create_scene_object_fixed
        )
        
        # --- CORRECTION 3: Standalone Micro-Scene Filter ---
        # Filter out standalone micro-scenes with < 3 messages
        ch_scenes_filtered = [s for s in ch_scenes if s.get('message_count', 0) >= 3]
        all_v2_scenes.extend(ch_scenes_filtered)

    all_v2_scenes.sort(key=lambda s: parse_timestamp_v2(s.get('start_time', '')))

    characters_v2 = build_unified_characters_dict_v2(all_v2_scenes)
    for sc in all_v2_scenes:
        sc['faction_distribution'] = compute_faction_distribution(sc.get('actors', []), characters_v2)

    sim_data = {
        "metadata": {
            "version": "2.0-FIXED",
            "generated_at": datetime.now().isoformat(),
            "total_scenes": len(all_v2_scenes),
            "total_characters": len(characters_v2)
        },
        "characters": characters_v2,
        "scenes": all_v2_scenes
    }

    with open('scenes_fixed_simulated.json', 'w', encoding='utf-8') as f:
        json.dump(sim_data, f, ensure_ascii=False, indent=2)

    print(f"Simulation terminée : {len(all_v2_scenes)} scènes générées dans 'scenes_fixed_simulated.json'.")

if __name__ == '__main__':
    run_simulation()
