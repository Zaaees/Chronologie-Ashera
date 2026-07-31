import re
from datetime import datetime
from unify_characters_v2 import get_canonical_name_v2

# Explicit RP closing markers
EXPLICIT_END_REGEX = re.compile(
    r'(sc[èe]ne\s+termin[eé]|salon\s+libre|fin\s+de\s+sc[èe]ne|mission\s+termin[eé]|fin\s+du\s+rp|fin\s+d\'?acte|rp\s+clos|sc[eè]ne\s+close)',
    re.IGNORECASE
)

# Explicit Event / Mission start markers
EXPLICIT_START_REGEX = re.compile(
    r'(```ansi.*🎭|#\s+⊱═─────|```\s*🎭|◦\s*─────────────\s*¤|#\s+.*🎭|\bacte\s+\d+\b|@L\'Oeil|@Garde Pourpre|@Cercle d\'Azur|@Voile d\'Ivoire|@Sans guilde)',
    re.IGNORECASE | re.DOTALL
)

# Purely administrative / moderation bots (Tupperbox & RP Webhooks ARE NOT included)
SYSTEM_BOTS = {"carl-bot", "dyno", "mee6", "ticket-tool", "disboard", "raidprotect"}

GAP_LIMIT_SECONDS = 30 * 24 * 3600  # 30 jours (720h) au lieu de 7 jours pour éviter le morcellement d'une même scène RP

def parse_timestamp_v2(ts_str):
    if not ts_str:
        return 0
    
    ts_clean = str(ts_str).strip().replace('\xa0', ' ')
    if not ts_clean:
        return 0

    try:
        iso_clean = ts_clean.replace('Z', '+00:00') if 'Z' in ts_clean else ts_clean
        dt = datetime.fromisoformat(iso_clean)
        return dt.timestamp()
    except Exception:
        pass

    formats = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(ts_clean.split('.')[0], fmt)
            return dt.timestamp()
        except Exception:
            continue

    return 0

def extract_title_from_text(text, channel_clean, scene_index):
    if not text:
        return f"{channel_clean} — Scène {scene_index}"

    lines = text.strip().split('\n')
    for line in lines[:4]:
        line_s = line.strip()
        if line_s.startswith('# ') and not line_s.startswith('## '):
            title = re.sub(r'^#+\s*', '', line_s)
            title = re.sub(r'[^\w\s\-\'’àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', '', title).strip()
            if len(title) > 3 and len(title) < 60:
                return title

        if line_s.startswith('**') and line_s.endswith('**'):
            title = line_s.strip('*').strip()
            if len(title) > 3 and len(title) < 60:
                return title

    return f"{channel_clean} — Scène {scene_index}"

def segment_messages_into_scenes_v2(channel_name_clean, channel_name_raw, valid_msgs, create_scene_func):
    """
    Segmentation V2 avec prise en compte INTÉGRALE de tous les Tupperbots, webhooks et narrateurs RP.
    Aucune scène n'est supprimée ou morcelée à cause de la présence d'un bot RP / Tupperbot MJ.
    """
    if not valid_msgs:
        return []

    valid_msgs_sorted = sorted(valid_msgs, key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))

    scenes = []
    current_scene_msgs = [valid_msgs_sorted[0]]
    scene_counter = 1

    for i in range(1, len(valid_msgs_sorted)):
        prev_msg, prev_text = valid_msgs_sorted[i - 1]
        curr_msg, curr_text = valid_msgs_sorted[i]

        current_scene_actors = {
            get_canonical_name_v2(m[0].get('author_name', m[0].get('author', '')))
            for m in current_scene_msgs
        }
        curr_actor = get_canonical_name_v2(curr_msg.get('author_name', curr_msg.get('author', '')))

        prev_is_sealed = bool(EXPLICIT_END_REGEX.search(prev_text))
        curr_is_start = bool(EXPLICIT_START_REGEX.search(curr_text))

        prev_ts = parse_timestamp_v2(prev_msg.get('timestamp'))
        curr_ts = parse_timestamp_v2(curr_msg.get('timestamp'))
        time_gap = (curr_ts - prev_ts) if (curr_ts > 0 and prev_ts > 0) else 0

        has_previous_actor_replied = False
        for nm, _ in valid_msgs_sorted[i:]:
            act = get_canonical_name_v2(nm.get('author_name', nm.get('author', '')))
            if act in current_scene_actors:
                has_previous_actor_replied = True
                break

        is_new_scene = False

        if prev_is_sealed:
            is_new_scene = True
        elif time_gap > GAP_LIMIT_SECONDS:
            is_new_scene = True
        elif curr_is_start and curr_actor not in current_scene_actors and not has_previous_actor_replied and time_gap > 24 * 3600:
            is_new_scene = True
        elif curr_actor in current_scene_actors or has_previous_actor_replied or time_gap <= 7 * 24 * 3600:
            is_new_scene = False
        else:
            is_new_scene = False

        if is_new_scene:
            scenes.append(create_scene_func(
                channel_name_clean,
                channel_name_raw,
                scene_counter,
                current_scene_msgs,
                extract_title_from_text(current_scene_msgs[0][1], channel_name_clean, scene_counter)
            ))
            scene_counter += 1
            current_scene_msgs = [valid_msgs_sorted[i]]
        else:
            current_scene_msgs.append(valid_msgs_sorted[i])

    if current_scene_msgs:
        scenes.append(create_scene_func(
            channel_name_clean,
            channel_name_raw,
            scene_counter,
            current_scene_msgs,
            extract_title_from_text(current_scene_msgs[0][1], channel_name_clean, scene_counter)
        ))

    return scenes
