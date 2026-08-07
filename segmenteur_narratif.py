import re
from datetime import datetime
from unify_characters_v2 import get_canonical_name_v2

# Marqueurs explicites de fermeture et d'ouverture de RP
EXPLICIT_END_REGEX = re.compile(
    r'(sc[èe]ne\s+termin[eé]|salon\s+libre|fin\s+de\s+sc[èe]ne|mission\s+termin[eé]|fin\s+du\s+rp|rp\s+clos|sc[eè]ne\s+close|sc[èe]ne\s+abr[eé]g[eé]e|sc[eè]ne\s+de\s+rp\s+fini|rp\s+fini|rp\s+termin[eé])',
    re.IGNORECASE
)

# Marqueurs majeurs de démarrage RP (incluant convocations et bannières de mission)
EXPLICIT_START_REGEX = re.compile(
    r'(```ansi.*🎭|#\s+⊱═─────|```\s*🎭|◦\s*─────────────\s*¤|\bacte\s+\d+\b|béni\s+soit\s+le\s+fruit|que\s+le\s+seigneur\s+ouvre|par-delà\s+le\s+voile)',
    re.IGNORECASE | re.DOTALL
)

SYSTEM_BOTS = {"carl-bot", "dyno", "mee6", "ticket-tool", "disboard", "raidprotect"}
GM_BOT_ACTORS = {"LE CONSEILLER", "Oeil", "OWL LE MESSAGER", "LES MISSIVES", "Narrateur"}

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

def segment_messages_into_scenes_v2(channel_name_clean, channel_name_raw, valid_msgs, create_scene_func, max_inactivity_days=5.0, hard_cutoff_days=45.0):
    """
    Segmentation Narrative des messages RP.
    Suit la continuité du récit et le fil de répliques entre personnages joueurs.
    Prend en compte le RP Long (réponses lentes entre mêmes acteurs) tout en coupant lors de
    l'arrivée d'un nouveau personnage après inactivité ou après arrêt prolongé (> 45 jours).
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

        player_scene_actors = current_scene_actors - GM_BOT_ACTORS

        prev_ts = parse_timestamp_v2(prev_msg.get('timestamp'))
        curr_ts = parse_timestamp_v2(curr_msg.get('timestamp'))
        diff_days = (curr_ts - prev_ts) / 86400.0 if (prev_ts and curr_ts) else 0.0

        prev_actor = get_canonical_name_v2(prev_msg.get('author_name', prev_msg.get('author', '')))
        other_player_scene_actors = player_scene_actors - {curr_actor}

        # Vérification des réponses ultérieures des joueurs dans la fenêtre active (max hard_cutoff_days)
        has_player_actor_replied = False
        has_other_player_actor_replied = False
        for nm, _ in valid_msgs_sorted[i:]:
            nts = parse_timestamp_v2(nm.get('timestamp'))
            if nts and curr_ts and (nts - curr_ts) / 86400.0 > hard_cutoff_days:
                break
            act = get_canonical_name_v2(nm.get('author_name', nm.get('author', '')))
            if act in player_scene_actors:
                has_player_actor_replied = True
            if act in other_player_scene_actors:
                has_other_player_actor_replied = True

        is_new_scene = False

        # 1. Marqueur explicite de fin de RP dans le message précédent
        if prev_is_sealed:
            is_new_scene = True
        # 2. Coupure ferme après inactivité totale prolongée (> 45 jours) du salon (sauf si début par GM bot)
        elif diff_days > hard_cutoff_days and not current_scene_actors.issubset(GM_BOT_ACTORS):
            is_new_scene = True
        # 3. Arrivée d'un NOUVEAU personnage après inactivité (> 5 jours)
        elif diff_days > max_inactivity_days and curr_actor not in current_scene_actors and curr_actor not in GM_BOT_ACTORS:
            is_new_scene = True
        # 4. Bannière d'ouverture majeure lancée après inactivité (> 5 jours)
        elif diff_days > max_inactivity_days and curr_is_start:
            is_new_scene = True
        # 4.5. Relance après inactivité (> 5 jours) par le même auteur sans retour des co-acteurs précédents
        elif diff_days > max_inactivity_days and curr_actor == prev_actor and not has_other_player_actor_replied and not current_scene_actors.issubset(GM_BOT_ACTORS):
            is_new_scene = True
        # 5. Message d'un GM/Bot neutre (Le Conseiller, Oeil, Narrateur...) ou début de scène par GM -> continuation
        elif curr_actor in GM_BOT_ACTORS or current_scene_actors.issubset(GM_BOT_ACTORS):
            is_new_scene = False
        # 6. Continuité RP Long : si l'acteur fait déjà partie des joueurs de la scène ou réplique dans la scène active
        elif curr_actor in player_scene_actors or has_player_actor_replied:
            is_new_scene = False
        # 7. Bannière d'ouverture majeure lancée par un nouveau groupe de joueurs
        elif curr_is_start and curr_actor not in current_scene_actors:
            is_new_scene = True
        # 8. Sinon, continuation naturelle du fil RP
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
