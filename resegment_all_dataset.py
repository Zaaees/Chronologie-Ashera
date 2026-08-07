import json, sys, os, re
from datetime import datetime

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

from segmenteur_narratif import segment_messages_into_scenes_v2, parse_timestamp_v2
from unify_characters_v2 import get_canonical_name_v2, build_unified_characters_dict_v2

DESCRIPTION_JSON_PATH = 'description_scene.json'
IMAGE_REGEX = re.compile(r'\[Image:\s*(https?://[^\s\]]+)\]|https?://[^\s]+\.(?:jpg|png|jpeg)', re.IGNORECASE)
GM_ROLE_ID = "1327646236798353535"
GM_MEMBERS_FILE = "discord_gm_members.json"

PARENT_CHANNEL_MAP = {
    "Ruelle-Basse-ville": "Egregore",
    "Ruelles": "Egregore",
    "Course-Poursuite": "Egregore",
    "Passage": "Egregore",
    "Le-Secret": "Egregore",
    "Place": "Egregore",
    "Petit-Salon": "Quartiers",
    "Isolement": "Quartiers",
    "Scène Kalès Kalem": "L-Epicurien",
    "Scène Kalès JAVUS": "L-Epicurien",
    "Zone-Buffet": "Hall-Des-Fêtes",
    "Cours-Fleurie": "Hall-Des-Fêtes",
    "Un début de soirée à la serre de lune": "Serre-de-lune",
    "Salle-d’Alchimie": "Cour-des-alchimistes",
    "Une chouette découvre enfin l'eau": "Port-du-Levant",
    "Fuir - Katelyn Hoffmann Isis Faerieth": "Port-du-Levant"
}

def load_gm_members():
    gms = {"Vosk Sulyvan", "Isis Faerieth", "Jasp Nah"}
    if os.path.exists(GM_MEMBERS_FILE):
        try:
            with open(GM_MEMBERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    gms.update(data)
                elif isinstance(data, dict):
                    gms.update(data.keys())
        except Exception:
            pass
    return gms

KNOWN_GM_MEMBERS = load_gm_members()

def is_meaningful_character_rp(content):
    """
    Détermine si un message contient de la vraie narration écrite de personnage RP.
    Les messages purement HRP (spoilers, pings bruts, parenthèses HRP) et les balises
    neutres de clôture ('Scène terminée', 'Fin de scène') ne sont pas comptabilisés comme du RP de personnage.
    """
    if not content:
        return False
    text = str(content).strip()
    if not text:
        return False

    # 1. Séparateurs Discord _ _ _ _
    if re.match(r'^(_\s*)+$', text):
        return False

    # 2. Nettoyage des blocs de code
    clean_no_code = re.sub(r'```.*?```', '', text, flags=re.DOTALL).strip()
    
    # Si le message est composé uniquement d'un bloc de code (ex: bannières, clôtures)
    if not clean_no_code:
        code_match = re.search(r'```(.*?)```', text, flags=re.DOTALL)
        if code_match:
            code_text = code_match.group(1).lower().strip()
            # Balises neutres de fin de scène / d'acte
            if any(term in code_text for term in ['scène terminée', 'fin de scène', 'scène finie', 'salon libre', 'mission terminée']):
                return False
            # Si le bloc de code contient de la vraie narration écrite de personnage
            if len(code_text) > 35 and any(punct in code_text for punct in ['.', '*', '—', '“', '"']):
                return True
        return False

    # 3. Spoilers purs ||...|| ou pings bruts <@...>
    sans_spoilers = re.sub(r'\|\|.*?\|\|', '', text, flags=re.DOTALL)
    sans_pings_spoilers = re.sub(r'<@&?\d+>|<#\d+>', '', sans_spoilers).strip()
    if not sans_pings_spoilers:
        return False

    # 4. Messages entre parenthèses ou crochets HRP
    is_markdown_link = bool(re.match(r'^\[.*?\]\(https?://[^\s\)]+\)$', text))
    if not is_markdown_link:
        if (text.startswith('(') and text.endswith(')')) or (text.startswith('((') and text.endswith('))')):
            return False
        if (text.startswith('[') and text.endswith(']')) and not text.startswith('[Image:'):
            return False
        if (text.startswith('[[') and text.endswith(']]')):
            return False

    lower_text = text.lower()
    
    # 5. Patterns d'animation/organisation MJ explicites
    gm_admin_patterns = [
        'hrp:', 'hrp :', '(hrp', '[hrp', '//', 
        'prochaine narration', 'veuillez poursuivre', 'voici la fin', 'plan de l\'affrontement',
        'votre lieu d\'affrontement', 'félicitation pour ta nouvelle guilde', 'l\'évent commence',
        'pour ceux qui vont au bal'
    ]
    if any(p in lower_text for p in gm_admin_patterns):
        return False

    # 6. Messages de chat courts non-RP
    short_chat_patterns = [
        'jte rep mtn', 'je rentre et je te fais ça', 'putaing de réseau', 'vous pouvez, d\'autant si tu veux'
    ]
    if any(p in lower_text for p in short_chat_patterns):
        return False

    sans_images_and_links = re.sub(r'\[Image:\s*https?://[^\s\]]+\]|https?://[^\s]+\.(?:jpg|png|jpeg)', '', text, flags=re.IGNORECASE).strip()
    sans_pings_only = re.sub(r'<@&?\d+>|<#\d+>', '', sans_images_and_links).strip()
    if not sans_pings_only:
        return False

    if text in ["Lewis Phoebe Ashbourne", "Fuir - Katelyn Hoffmann & Isis Faerieth", "🟧 Le son de l'Innocence"]:
        return False

    return True

def clean_deduplicate_text(text):
    if not text:
        return ""
    lines = text.split('\n')
    cleaned_lines = []
    seen = set()
    for l in lines:
        stripped = l.strip()
        if not stripped or '────' in stripped or '¤♅¤' in stripped:
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            continue
        if stripped in seen:
            continue
        seen.add(stripped)
        cleaned_lines.append(l)
    return '\n'.join(cleaned_lines).strip()

def extract_info_from_msg(msg):
    content = msg.get('content', '')
    img_match = IMAGE_REGEX.search(content)
    img_url = None
    if img_match:
        img_url = img_match.group(1) if img_match.group(1) else img_match.group(0)
    
    clean_text = IMAGE_REGEX.sub('', content).strip()
    clean_text = clean_deduplicate_text(clean_text)
    return clean_text, img_url

def load_description_map():
    if os.path.exists(DESCRIPTION_JSON_PATH):
        try:
            with open(DESCRIPTION_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_description_map(desc_map):
    with open(DESCRIPTION_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(desc_map, f, ensure_ascii=False, indent=2)

def attach_channel_images_to_dataset(all_scenes):
    import unicodedata
    img_dir = "public/channel_images"
    channel_images_map = {}
    if not os.path.exists(img_dir):
        return channel_images_map

    img_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    pub_clean_map = {}
    for f in img_files:
        base = os.path.splitext(f)[0]
        clean = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', base)).lower()
        if clean:
            pub_clean_map[clean] = f'channel_images/{f}'

    fallback_map = {
        'Isis et Astreüs': 'channel_images/serre-de-lune.jpg',
        'Scène Kalès / JAVUS': 'channel_images/arene-hurlante.jpg',
        'Scène Kalès / Kalem': 'channel_images/terrain-d-entrainement.jpg',
        'Scène Lumia | Ivara': 'channel_images/bibliotheque-azure.jpg',
        'TRIPLE A : Asior - Akane - Aryana': 'channel_images/le-bar-des-lions.jpg',
        '☁️〕𝗣ortail-𝗜voire': 'channel_images/couloir-blanc.jpg',
        '️〕Portail-Ivoire': 'channel_images/couloir-blanc.jpg',
        '🛏️  •  Salle de Réveil': 'channel_images/cellules.jpg',
        'isolement': 'channel_images/cellules.jpg',
        'kalesiscariothaether': 'channel_images/arene-hurlante.jpg',
        'unechouettedecouvreenfinleau': 'channel_images/port-du-levant.jpg',
        'fuirkatelynhoffmannisisfaerieth': 'channel_images/port-du-levant.jpg',
        'ilsnesouhaitentquuneseulechoselapaix': 'channel_images/egregore.jpg'
    }

    for scene in all_scenes:
        ch = scene.get('channel') or scene.get('channel_raw') or scene.get('channel_clean') or ''
        thread = scene.get('thread_name') or ''
        ch_clean_val = scene.get('channel_clean') or ''

        local_img = None
        th_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', thread)).lower()
        ch_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', ch)).lower()
        ch_clean_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', ch_clean_val)).lower()

        for candidate in [thread, ch, ch_clean_val, th_c, ch_c, ch_clean_c]:
            if candidate in fallback_map:
                local_img = fallback_map[candidate]
                break

        if not local_img:
            for c in [th_c, ch_c, ch_clean_c]:
                if not c:
                    continue
                for k, url in pub_clean_map.items():
                    if k and (k == c or k in c or c in k):
                        local_img = url
                        break
                if local_img:
                    break

        img_url = local_img or scene.get('location_image')

        if img_url:
            if ch: channel_images_map[ch] = img_url
            if thread: channel_images_map[thread] = img_url
            scene['location_image'] = img_url

    return channel_images_map

def main():
    src_path = 'scenes.json'
    with open(src_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    existing_scenes = raw.get('scenes', raw if isinstance(raw, list) else [])
    desc_map = load_description_map()
    desc_map_updated = False

    channel_groups = {}
    for sc in existing_scenes:
        ch_raw = sc.get('channel_raw', sc.get('channel', 'Salon Inconnu'))
        ch_clean = sc.get('channel_clean', sc.get('channel', 'Salon Inconnu'))
        key = (ch_raw, ch_clean)
        if key not in channel_groups:
            channel_groups[key] = []

        for m in sc.get('messages', []):
            content = m.get('content', '')
            if content and content.strip():
                channel_groups[key].append((m, content))

    channel_descriptions_cache = {}
    channel_images_cache = {}

    for (ch_raw, ch_clean), msg_tuples in channel_groups.items():
        sorted_tuples = sorted(msg_tuples, key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))
        seen_ids = set()
        dedup_tuples = []
        for m, txt in sorted_tuples:
            mid = m.get('id')
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            dedup_tuples.append((m, txt))

        if not dedup_tuples:
            continue

        if ch_clean not in desc_map and ch_raw not in desc_map:
            desc_map[ch_clean] = "0"
            desc_map_updated = True

        target_msg_id = str(desc_map.get(ch_clean, desc_map.get(ch_raw, "0"))).strip()

        target_msg_tuple = None
        if target_msg_id and target_msg_id != "0":
            for tup in dedup_tuples:
                if str(tup[0].get('id')) == target_msg_id:
                    target_msg_tuple = tup
                    break

        if not target_msg_tuple and dedup_tuples:
            first_msg_tuple = dedup_tuples[0]
            first_content = first_msg_tuple[1]
            if IMAGE_REGEX.search(first_content) or '────' in first_content or '¤' in first_content or '```' in first_content:
                target_msg_tuple = first_msg_tuple

        if target_msg_tuple:
            desc_text, img_url = extract_info_from_msg(target_msg_tuple[0])
            if desc_text:
                channel_descriptions_cache[ch_clean] = desc_text
                channel_descriptions_cache[ch_raw] = desc_text
            if img_url:
                channel_images_cache[ch_clean] = img_url
                channel_images_cache[ch_raw] = img_url

        if target_msg_id == "1336404555226812517" or "Philosophes" in ch_clean:
            cafe_desc = "Espace ou le silence règne, les bruits parasites y sont pourtant toujours légion ; de fait, les tables sont équipées d'artefacts pouvant créer des \"bulles de silence\" idéal pour les discussions les plus discrètes et les débats les plus houleux. Faites cela dit attention de ne pas abuser de la bière à la myrtille... Plus d'un ont ridiculisé leur discours à cause de ce liquide indigo."
            channel_descriptions_cache[ch_clean] = cafe_desc
            channel_descriptions_cache[ch_raw] = cafe_desc
            channel_images_cache[ch_clean] = "channel_images/le-cafe-des-philosophes.jpg"
            channel_images_cache[ch_raw] = "channel_images/le-cafe-des-philosophes.jpg"

    all_scenes = []
    total_locations_assigned = 0

    for (ch_raw, ch_clean), msg_tuples in channel_groups.items():
        sorted_tuples = sorted(msg_tuples, key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))
        seen_ids = set()
        dedup_tuples = []
        for m, txt in sorted_tuples:
            mid = m.get('id')
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            dedup_tuples.append((m, txt))

        if not dedup_tuples:
            continue

        target_msg_id = str(desc_map.get(ch_clean, desc_map.get(ch_raw, "0"))).strip()

        if target_msg_id and target_msg_id != "0":
            dedup_tuples = [tup for tup in dedup_tuples if str(tup[0].get('id')) != target_msg_id]

        if not dedup_tuples:
            continue

        location_desc = channel_descriptions_cache.get(ch_clean) or channel_descriptions_cache.get(ch_raw)
        location_img = channel_images_cache.get(ch_clean) or channel_images_cache.get(ch_raw)

        if not location_desc:
            parent_ch = PARENT_CHANNEL_MAP.get(ch_clean) or PARENT_CHANNEL_MAP.get(ch_raw)
            if parent_ch:
                location_desc = channel_descriptions_cache.get(parent_ch)
                location_img = location_img or channel_images_cache.get(parent_ch)

        if location_desc:
            total_locations_assigned += 1

        def scene_builder(c_clean, c_raw, scene_idx, msg_tups, title_suggested):
            msgs = [t[0] for t in msg_tups]
            texts = [t[1] for t in msg_tups]
            
            all_canonical_authors = [get_canonical_name_v2(m.get('author_name', m.get('author', ''))) for m in msgs]
            
            rp_authors = [
                get_canonical_name_v2(m.get('author_name', m.get('author', '')))
                for m in msgs 
                if is_meaningful_character_rp(m.get('content', ''))
            ]
            
            actors = []
            for act in all_canonical_authors:
                if act in rp_authors and act not in actors:
                    actors.append(act)

            if not actors:
                for act in all_canonical_authors:
                    if act not in actors:
                        actors.append(act)

            main_actor = actors[0] if actors else "Narrateur"
            is_solo = (len(actors) == 1)

            start_ts = parse_timestamp_v2(msgs[0].get('timestamp'))
            end_ts = parse_timestamp_v2(msgs[-1].get('timestamp'))
            duration_mins = max(1, int((end_ts - start_ts) / 60)) if (end_ts > start_ts and start_ts > 0) else 1

            preview = texts[0]
            if len(preview) > 160:
                preview = preview[:157] + "..."

            sc_id = f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', c_clean).lower()}_{scene_idx}"

            scene_dict = {
                "id": sc_id,
                "channel": c_raw,
                "channel_raw": c_raw,
                "channel_clean": c_clean,
                "title": title_suggested if title_suggested else f"{c_clean} — Scène {scene_idx}",
                "actors": actors,
                "main_actor": main_actor,
                "is_solo": is_solo,
                "scene_type": "Solo / Monologue" if is_solo else "Duo / Groupe",
                "start_time": msgs[0].get('timestamp', ''),
                "end_time": msgs[-1].get('timestamp', ''),
                "duration_minutes": duration_mins,
                "preview": preview,
                "message_count": len(msgs),
                "messages": msgs
            }

            if location_desc:
                scene_dict["location_description"] = location_desc
            if location_img:
                scene_dict["location_image"] = location_img

            return scene_dict

        ch_scenes = segment_messages_into_scenes_v2(ch_clean, ch_raw, dedup_tuples, scene_builder)
        all_scenes.extend(ch_scenes)

    if desc_map_updated:
        save_description_map(desc_map)

    all_scenes = [s for s in all_scenes if s.get('message_count', 0) >= 1 and not s.get('start_time', '').startswith('2025')]
    all_scenes.sort(key=lambda s: parse_timestamp_v2(s.get('start_time', '')))

    characters = build_unified_characters_dict_v2(all_scenes)
    channel_images_map = attach_channel_images_to_dataset(all_scenes)

    output_data = {
        "metadata": {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "total_scenes": len(all_scenes),
            "total_characters": len(characters)
        },
        "characters": characters,
        "scenes": all_scenes,
        "channel_images": channel_images_map
    }

    file_paths = ['scenes.json', 'src/scenes.json', 'scenes_v2.json', 'src/scenes_v2.json']
    for p in file_paths:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write('window.RP_DATA = ' + json.dumps(output_data, ensure_ascii=False, indent=2) + ';')

    print(f"✅ Resegmentation avec filtrage HRP/MJ et {len(channel_images_map)} images de salons rattachées terminée !")

if __name__ == '__main__':
    main()
