import re
import unicodedata
from datetime import datetime
from unify_characters_v2 import get_canonical_name_v2

# Marqueurs explicites de fermeture de RP (enrichi pour couvrir interruptions et accords)
EXPLICIT_END_REGEX = re.compile(
    r'(\bsc[èe]ne\s+(?:termin[eé]e?|close?|finie?|abr[eé]g[eé]e?|interrompue?)\b|'
    r'\bsalon\s+libre\b|'
    r'\bfin\s+de\s+(?:sc[èe]ne|mission|rp)\b|'
    r'\brp\s+(?:clos?|fini|termin[eé]e?)\b|'
    r'\baccord\s+mutuel\b)',
    re.IGNORECASE
)

# Marqueurs majeurs de démarrage RP (incluant convocations et bannières de mission)
EXPLICIT_START_REGEX = re.compile(
    r'(```ansi.*🎭|#\s+⊱═─────|```\s*🎭|◦\s*─────────────\s*¤|\bacte\s+\d+\b|béni\s+soit\s+le\s+fruit|que\s+le\s+seigneur\s+ouvre|par-delà\s+le\s+voile)',
    re.IGNORECASE | re.DOTALL
)

# Séparateurs décoratifs purs à exclure (tirets, barres de soulignement, astérisques)
SEPARATOR_LINE_REGEX = re.compile(r'^[\s\-_=*~•◦¤♅\.\/]+$')

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

def is_thread_or_duo_channel(channel_name):
    if not channel_name:
        return False
    ch_norm = unicodedata.normalize('NFKD', str(channel_name)).lower()
    ch_norm = re.sub(r'[\u0300-\u036f]', '', ch_norm)
    if ch_norm.startswith('↳'):
        return True
    if any(k in ch_norm for k in ['&', ' / ', ' - ', 'chouette', 'quete', 'chambre', 'dortoir']):
        return True
    return False

def segment_messages_into_scenes_v2(channel_name_clean, channel_name_raw, valid_msgs, create_scene_func, max_inactivity_days=5.0, hard_cutoff_days=7.0, lookahead_days=3.0):
    """
    Segmentation Narrative Fiabilisée des messages RP.
    - Seuil dur contextuel : 14 jours pour les duos/fils privés, 10 jours pour dialogue actif entre pairs, 4 jours pour nouveaux arrivants, 7 jours par défaut.
    - Absorption prioritaire des marqueurs de fin avec traitement propre des scellements administratifs tardifs (> 14j).
    - Lookahead borné à 3 jours désactivé pour les nouveaux arrivants.
    - Élimination des séparateurs décoratifs purs.
    """
    if not valid_msgs:
        return []

    # 1. Éliminer les séparateurs décoratifs purs avant tout traitement
    filtered_msgs = []
    for m_tuple in valid_msgs:
        m, text = m_tuple
        if SEPARATOR_LINE_REGEX.match(text.strip()):
            continue
        filtered_msgs.append(m_tuple)

    if not filtered_msgs:
        return []

    valid_msgs_sorted = sorted(filtered_msgs, key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))

    scenes = []
    current_scene_msgs = [valid_msgs_sorted[0]]
    scene_counter = 1

    is_thread_duo = is_thread_or_duo_channel(channel_name_clean) or is_thread_or_duo_channel(channel_name_raw)

    for i in range(1, len(valid_msgs_sorted)):
        if not current_scene_msgs:
            current_scene_msgs = [valid_msgs_sorted[i]]
            continue

        prev_msg, prev_text = current_scene_msgs[-1]
        curr_msg, curr_text = valid_msgs_sorted[i]

        prev_ts = parse_timestamp_v2(prev_msg.get('timestamp'))
        curr_ts = parse_timestamp_v2(curr_msg.get('timestamp'))
        diff_days = (curr_ts - prev_ts) / 86400.0 if (prev_ts and curr_ts) else 0.0

        # Évaluation en PRIORITÉ ABSOLUE du marqueur de fin sur le message courant
        curr_is_end = bool(EXPLICIT_END_REGEX.search(curr_text))
        if curr_is_end:
            is_pure_seal = len(re.sub(r'[^\w]', '', curr_text)) < 40
            if diff_days > 14.0 and is_pure_seal:
                # Marqueur administratif tardif (> 14 jours) sans contenu RP :
                # Sceller la scène précédente à sa date réelle de fin
                scene_obj = create_scene_func(
                    channel_name_clean,
                    channel_name_raw,
                    scene_counter,
                    current_scene_msgs,
                    extract_title_from_text(current_scene_msgs[0][1], channel_name_clean, scene_counter)
                )
                if scene_obj:
                    scenes.append(scene_obj)
                    scene_counter += 1
                current_scene_msgs = []
                continue
            else:
                # Absorption normale du scellement
                current_scene_msgs.append(valid_msgs_sorted[i])
                scene_obj = create_scene_func(
                    channel_name_clean,
                    channel_name_raw,
                    scene_counter,
                    current_scene_msgs,
                    extract_title_from_text(current_scene_msgs[0][1], channel_name_clean, scene_counter)
                )
                if scene_obj:
                    scenes.append(scene_obj)
                    scene_counter += 1
                current_scene_msgs = []
                continue

        current_scene_actors = {
            get_canonical_name_v2(m[0].get('author_name', m[0].get('author', '')))
            for m in current_scene_msgs
        }
        curr_actor = get_canonical_name_v2(curr_msg.get('author_name', curr_msg.get('author', '')))
        prev_actor = get_canonical_name_v2(prev_msg.get('author_name', prev_msg.get('author', '')))

        prev_is_sealed = bool(EXPLICIT_END_REGEX.search(prev_text))
        curr_is_start = bool(EXPLICIT_START_REGEX.search(curr_text))

        player_scene_actors = current_scene_actors - GM_BOT_ACTORS
        other_player_scene_actors = player_scene_actors - {curr_actor}
        is_newcomer = curr_actor not in current_scene_actors and curr_actor not in GM_BOT_ACTORS

        # Seuil d'inactivité adaptatif :
        # - Nouveau venu : 4.0 jours
        # - Thread / Duo privé ou paire établie (<= 2 joueurs) : 14.0 jours
        # - Dialogue actif entre joueurs établis dans un salon public : 10.0 jours
        # - Défaut : 7.0 jours
        if is_newcomer:
            effective_hard_cutoff = 4.0
        elif is_thread_duo or len(player_scene_actors) <= 2:
            effective_hard_cutoff = 14.0
        elif curr_actor in other_player_scene_actors:
            effective_hard_cutoff = 10.0
        else:
            effective_hard_cutoff = hard_cutoff_days

        # Vérification des réponses ultérieures dans une fenêtre bornée à 3 jours (joueurs établis uniquement)
        has_player_actor_replied = False
        has_other_player_actor_replied = False
        if not is_newcomer:
            for nm, _ in valid_msgs_sorted[i:]:
                nts = parse_timestamp_v2(nm.get('timestamp'))
                if nts and curr_ts and (nts - curr_ts) / 86400.0 > lookahead_days:
                    break
                act = get_canonical_name_v2(nm.get('author_name', nm.get('author', '')))
                if act in player_scene_actors:
                    has_player_actor_replied = True
                if act in other_player_scene_actors:
                    has_other_player_actor_replied = True

        is_new_scene = False

        # 1. Marqueur explicite de fin dans le message précédent
        if prev_is_sealed:
            is_new_scene = True
        # 2. Coupure ferme après inactivité prolongée adaptée au contexte
        elif diff_days > effective_hard_cutoff:
            is_new_scene = True
        # 3. Arrivée d'un nouveau personnage après inactivité (> 4 jours)
        elif diff_days > 4.0 and is_newcomer:
            is_new_scene = True
        # 4. Bannière majeure après inactivité (> 5 jours)
        elif diff_days > 5.0 and curr_is_start:
            is_new_scene = True
        # 5. Relance après inactivité (> 5 jours) sans retour des co-acteurs
        elif diff_days > 5.0 and curr_actor == prev_actor and not has_other_player_actor_replied and not current_scene_actors.issubset(GM_BOT_ACTORS):
            is_new_scene = True
        # 6. Message GM neutre -> continuation si dans la fenêtre active
        elif (curr_actor in GM_BOT_ACTORS or current_scene_actors.issubset(GM_BOT_ACTORS)) and diff_days <= effective_hard_cutoff:
            is_new_scene = False
        # 7. Continuité RP entre joueurs établis
        elif (curr_actor in player_scene_actors or has_player_actor_replied) and not is_newcomer:
            is_new_scene = False
        # 8. Bannière majeure lancée par un nouvel arrivant
        elif curr_is_start and curr_actor not in current_scene_actors:
            is_new_scene = True
        # 9. Sinon, continuation naturelle
        else:
            is_new_scene = False

        if is_new_scene:
            scene_obj = create_scene_func(
                channel_name_clean,
                channel_name_raw,
                scene_counter,
                current_scene_msgs,
                extract_title_from_text(current_scene_msgs[0][1], channel_name_clean, scene_counter)
            )
            if scene_obj:
                scenes.append(scene_obj)
                scene_counter += 1
            current_scene_msgs = [valid_msgs_sorted[i]]
        else:
            current_scene_msgs.append(valid_msgs_sorted[i])


    if current_scene_msgs:
        scene_obj = create_scene_func(
            channel_name_clean,
            channel_name_raw,
            scene_counter,
            current_scene_msgs,
            extract_title_from_text(current_scene_msgs[0][1], channel_name_clean, scene_counter)
        )
        if scene_obj:
            scenes.append(scene_obj)

    return scenes
