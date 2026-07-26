import os
import re
import json
import sys
import unicodedata
import html
from datetime import datetime
from html.parser import HTMLParser

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

TIME_GAP_THRESHOLD_HOURS = 24
ACTIVE_WINDOW_MESSAGES = 10

COLOR_PALETTE = [
  "#eab308",
  "#06b6d4",
  "#a855f7",
  "#10b981",
  "#ef4444",
  "#f97316",
  "#ec4899",
  "#3b82f6",
  "#14b8a6",
  "#84cc16"
]

GLOBAL_GUILD_ID = "1327646236534112318"

def clean_character_name(name):
    if not name:
        return "Narrateur"

    name = unicodedata.normalize('NFKD', name)
    name = re.sub(r'[^\w\s\-\']', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    name = re.sub(r'\s+BOT$', '', name, flags=re.IGNORECASE)

    name_lower = name.lower()

    if 'conseiller' in name_lower:
        return "LE CONSEILLER"
    elif 'owl' in name_lower or 'messager' in name_lower:
        return "OWL LE MESSAGER"
    elif name_lower in ["l'oeil", "l'œil", "oeil", "œil", "loeil", "lœil"]:
        return "L'Oeil"
    elif 'missive' in name_lower:
        return "LES MISSIVES"

    return name if name else "Narrateur"

def parse_channel_name_from_filename(filename):
    base = filename.rsplit('.', 1)[0]
    base = re.sub(r'\s*\[\d+\]$', '', base)

    parts = base.split(' - ')
    channel = parts[-1] if parts else base

    channel = unicodedata.normalize('NFKD', channel)
    channel = re.sub(r'[^\w\s\-\[\]〕〔〕↳♟️🏛️🛡️🥗🍷🏫🌕🍃🌿 Fountain⛲🐻🧸🦾🃏🎯🎲⚙️💎📜🧭⚓🚢👑✨]', '', channel)
    return channel.strip()

def parse_channel_id_from_filename(filename):
    match = re.search(r'\[(\d+)\]\.html$', filename)
    if match:
        return match.group(1)
    return "0"

def parse_html_timestamp(ts_str):
    ts_str = ts_str.strip().replace('\xa0', ' ')

    formats = ["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
    for fmt in formats:
        try:
            dt = datetime.strptime(ts_str, fmt)
            return dt.isoformat() + "Z"
        except ValueError:
            continue

    match = re.search(r'(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})', ts_str)
    if match:
        d, m, y, h, mn = match.groups()
        return f"{y}-{m}-{d}T{h}:{mn}:00Z"

    return ts_str

class DiscordHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.current_message = None
        self.guild_id = None

        self.last_author = "Système"
        self.last_author_id = "0"
        self.last_timestamp = ""

        self.in_author = False
        self.in_timestamp = False
        self.in_content = False
        self.in_embed_title = False
        self.in_embed_description = False

        self.content_div_depth = 0
        self.embed_title_div_depth = 0
        self.embed_desc_div_depth = 0

        self.temp_content = []
        self.temp_embed_title = []
        self.temp_embed_description = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'img' and 'class' in attrs_dict and attrs_dict['class'] == 'preamble__guild-icon':
            src = attrs_dict.get('src', '')
            match = re.search(r'icons/(\d+)/', src)
            if match:
                self.guild_id = match.group(1)

        if tag == 'div' and 'class' in attrs_dict:
            classes = attrs_dict['class'].split()
            if 'chatlog__message-container' in classes:
                if self.current_message:
                    self.save_current_message()

                if 'chatlog__message-container--pinned' in classes:
                    self.current_message = None
                    return

                self.current_message = {
                    'id': attrs_dict.get('data-message-id', ''),
                    'author': '',
                    'author_id': '',
                    'timestamp': '',
                    'content': '',
                    'embed_title': '',
                    'embed_description': ''
                }
                self.temp_content = []
                self.temp_embed_title = []
                self.temp_embed_description = []

        if not self.current_message:
            return

        if tag == 'span' and 'class' in attrs_dict:
            classes = attrs_dict['class'].split()
            if 'chatlog__author' in classes:
                self.in_author = True
                if 'data-user-id' in attrs_dict:
                    self.current_message['author_id'] = attrs_dict['data-user-id']
            elif 'chatlog__timestamp' in classes:
                self.in_timestamp = True

        elif tag == 'div':
            if self.in_content:
                self.content_div_depth += 1
            elif self.in_embed_title:
                self.embed_title_div_depth += 1
            elif self.in_embed_description:
                self.embed_desc_div_depth += 1
            elif 'class' in attrs_dict:
                classes = attrs_dict['class'].split()
                if 'chatlog__content' in classes:
                    self.in_content = True
                    self.content_div_depth = 1
                elif 'chatlog__embed-title' in classes:
                    self.in_embed_title = True
                    self.embed_title_div_depth = 1
                elif 'chatlog__embed-description' in classes:
                    self.in_embed_description = True
                    self.embed_desc_div_depth = 1

    def handle_endtag(self, tag):
        if self.in_author and tag == 'span':
            self.in_author = False
        elif self.in_timestamp and tag == 'span':
            self.in_timestamp = False
        elif tag == 'div':
            if self.in_content:
                self.content_div_depth -= 1
                if self.content_div_depth == 0:
                    self.in_content = False
            elif self.in_embed_title:
                self.embed_title_div_depth -= 1
                if self.embed_title_div_depth == 0:
                    self.in_embed_title = False
            elif self.in_embed_description:
                self.embed_desc_div_depth -= 1
                if self.embed_desc_div_depth == 0:
                    self.in_embed_description = False

    def handle_data(self, data):
        if not self.current_message:
            return

        if self.in_author:
            self.current_message['author'] += data
        elif self.in_timestamp:
            self.current_message['timestamp'] += data
        elif self.in_content:
            self.temp_content.append(data)
        elif self.in_embed_title:
            self.temp_embed_title.append(data)
        elif self.in_embed_description:
            self.temp_embed_description.append(data)

    def save_current_message(self):
        self.current_message['content'] = html.unescape("".join(self.temp_content).strip())
        self.current_message['embed_title'] = html.unescape("".join(self.temp_embed_title).strip())
        self.current_message['embed_description'] = html.unescape("".join(self.temp_embed_description).strip())

        self.current_message['author'] = html.unescape(self.current_message['author'].strip())
        self.current_message['timestamp'] = html.unescape(self.current_message['timestamp'].strip())

        if not self.current_message['author']:
            self.current_message['author'] = self.last_author
            self.current_message['author_id'] = self.last_author_id
        else:
            self.last_author = self.current_message['author']
            self.last_author_id = self.current_message['author_id']

        if not self.current_message['timestamp']:
            self.current_message['timestamp'] = self.last_timestamp
        else:
            self.last_timestamp = self.current_message['timestamp']

        self.messages.append(self.current_message)
        self.current_message = None

    def close(self):
        if self.current_message:
            self.save_current_message()
        super().close()

THREAD_TO_PARENT = {
    "↳🃏𝐋e-𝐑ouge-et-𝐋e-𝐍oir": "🍻〕𝐋-𝐄picurien",
    "↳🎯𝐋e-17": "🍻〕𝐋-𝐄picurien",
    "↳🎲𝐋e-𝐁onneteau": "🍻〕𝐋-𝐄picurien",
    "↳🦾𝐋e-𝐁ras-de-𝐅er": "🍻〕𝐋-𝐄picurien"
}

EXPLICIT_END_REGEX = re.compile(
    r'(sc[èe]ne\s+termin[eé]e|salon\s+libre|fin\s+de\s+sc[èe]ne|mission\s+termin[eé]e|fin\s+du\s+rp)',
    re.IGNORECASE
)

EXPLICIT_START_REGEX = re.compile(
    r'(```ansi.*🎭|#\s+⊱═─────|```\s*🎭|◦\s*─────────────\s*¤)',
    re.IGNORECASE | re.DOTALL
)

NARRATOR_ACTORS = {
    "owl le messager", "le conseiller", "inzu", "narrateur", "l'oeil", "les missives", "soigneuse"
}

def is_initiated_session(first_msg):
    author = (first_msg.get('author') or '').lower()
    content = (first_msg.get('content') or '') + ' ' + (first_msg.get('embed_description') or '')

    if any(n in author for n in NARRATOR_ACTORS):
        return True
    if EXPLICIT_START_REGEX.search(content):
        return True
    if '<@' in content or 'invités' in content.lower() or 'épreuve' in content.lower() or 'cérémonie' in content.lower():
        return True
    return False

def segment_messages_into_scenes(channel_name, channel_id, messages):
    if not messages:
        return []

    valid_msgs = []
    for m in messages:
        full_text = " ".join([m['content'], m['embed_title'], m['embed_description']]).strip()
        if full_text:
            valid_msgs.append((m, full_text))

    if not valid_msgs:
        return []

    scenes = []
    current_scene_tuples = [valid_msgs[0]]
    scene_counter = 1

    for i in range(1, len(valid_msgs)):
        prev_msg, prev_text = valid_msgs[i - 1]
        curr_msg, curr_text = valid_msgs[i]

        try:
            prev_dt = datetime.fromisoformat(parse_html_timestamp(prev_msg['timestamp']).replace('Z', '+00:00'))
            curr_dt = datetime.fromisoformat(parse_html_timestamp(curr_msg['timestamp']).replace('Z', '+00:00'))
            time_diff = (curr_dt - prev_dt).total_seconds() / 3600.0
        except Exception:
            time_diff = 0

        current_scene_actors = {clean_character_name(m[0]['author']) for m in current_scene_tuples}
        curr_actor = clean_character_name(curr_msg['author'])

        prev_is_sealed = bool(EXPLICIT_END_REGEX.search(prev_text))
        curr_is_start = bool(EXPLICIT_START_REGEX.search(curr_text))

        has_previous_actor_replied = False
        for nm, _ in valid_msgs[i:]:
            if clean_character_name(nm['author']) in current_scene_actors:
                has_previous_actor_replied = True
                break

        is_initiated = is_initiated_session(current_scene_tuples[0][0])

        is_new_scene = False

        if prev_is_sealed:
            is_new_scene = True
        elif time_diff >= 720.0: # 30 jours
            is_new_scene = True
        elif curr_is_start and curr_actor not in current_scene_actors and time_diff >= 2.0:
            is_new_scene = True
        elif curr_actor in current_scene_actors:
            is_new_scene = False
        elif has_previous_actor_replied:
            is_new_scene = False
        else:
            limit = 48.0 if is_initiated else 24.0
            if time_diff >= limit:
                is_new_scene = True
            else:
                is_new_scene = False

        if is_new_scene:
            scenes.append(create_scene_dict(channel_name, channel_id, scene_counter, current_scene_tuples))
            scene_counter += 1
            current_scene_tuples = [valid_msgs[i]]
        else:
            current_scene_tuples.append(valid_msgs[i])

    if current_scene_tuples:
        scenes.append(create_scene_dict(channel_name, channel_id, scene_counter, current_scene_tuples))

    return scenes

def create_scene_dict(channel_name, channel_id, scene_index, messages_tuples):
    global GLOBAL_GUILD_ID
    messages = [t[0] for t in messages_tuples]
    texts = [t[1] for t in messages_tuples]

    actors = list({clean_character_name(m['author']) for m in messages})
    parent_channel = THREAD_TO_PARENT.get(channel_name, channel_name)

    preview = texts[0]
    if len(preview) > 160:
        preview = preview[:157] + "..."

    sc_dict = {
        "id": f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', channel_name)}_{scene_index}",
        "channel": parent_channel,
        "channel_id": channel_id,
        "category": "",
        "title": f"Scène {scene_index} - {', '.join(actors[:3])}{'...' if len(actors)>3 else ''}",
        "actors": actors,
        "start_time": parse_html_timestamp(messages[0]['timestamp']),
        "end_time": parse_html_timestamp(messages[-1]['timestamp']),
        "preview": preview,
        "message_count": len(messages),
        "messages": messages
    }

    if channel_name in THREAD_TO_PARENT:
        sc_dict["thread_name"] = channel_name

    return sc_dict
        preview = preview[:157] + "..."

    first_msg_id = messages[0]['id']
    discord_url = f"discord://discord.com/channels/{GLOBAL_GUILD_ID}/{channel_id}/{first_msg_id}"

    formatted_messages = []
    for m in messages:
        formatted_messages.append({
            "id": m['id'],
            "author": clean_character_name(m['author']),
            "timestamp": parse_html_timestamp(m['timestamp']),
            "content": m['content'],
            "embed_title": m['embed_title'],
            "embed_description": m['embed_description']
        })

    return {
        "id": f"scene_{channel_name.replace('-', '_')}_{scene_index}",
        "channel": channel_name,
        "channel_id": channel_id,
        "title": f"Scène {scene_index} - {', '.join(actors[:3])}{'...' if len(actors) > 3 else ''}",
        "actors": actors,
        "start_time": parse_html_timestamp(messages[0]['timestamp']),
        "end_time": parse_html_timestamp(messages[-1]['timestamp']),
        "preview": preview,
        "message_count": len(messages),
        "discord_url": discord_url,
        "messages": formatted_messages
    }

def get_character_guild_and_color(actor_name):
    name = clean_character_name(actor_name).lower()

    if any(x in name for x in ["koya", "profile"]):
        return None, None, None

    if any(x in name for x in ["conseiller", "owl", "messager", "missive", "les missives"]) or name in ["l'oeil", "l'oeil", "l'œil", "oeil", "loeil", "lœil"]:
        return "PNJ", "#a855f7", "char_pnj"

    if any(x in name for x in ["zaes", "dandelion", "raien", "blacksheep", "vaelira", "faelthorn"]):
        return "L'œil", "#0e0d0d", "char_oeil"

    if any(x in name for x in ["emil", "rebenok", "camille", "red", "adelina", "mari", "nyx", "lysander", "jlaus", "eucymile", "leonite", "frey", "elear", "eopia", "asior", "lewis bamer", "historious", "lucia", "bunny", "fiorella"]):
        return "Cercle d'Azur", "#305ed3", "char_azur"

    if any(x in name for x in ["akane", "noci", "urugaki", "magon", "death", "yidmetra", "etoile", "isis", "faerieth"]):
        return "Voile d'Ivoire", "#ffffd4", "char_ivoire"

    if any(x in name for x in ["brutus", "redwitch", "ashbourne", "velka", "chapellet", "hana", "aryana", "taurielle", "happy", "loyis", "delacroix", "kenji", "heavil", "nick sol"]):
        return "La Garde Pourpre", "#b40000", "char_pourpre"

    if any(x in name for x in ["grel", "madana", "nikko", "aytaupe", "saphizu", "vidtz"]):
        return "Autre", "#94a3b8", "char_autre"

    return "Sans guilde", "#e2ce7d", "char_sans_guilde"

def main():
    global GLOBAL_GUILD_ID
    print("--- Démarrage de l'analyse des fichiers HTML réels ---")
    export_folder = "Export"

    if not os.path.exists(export_folder):
        print(f"Erreur : Le dossier '{export_folder}' est introuvable.")
        return

    html_files = [f for f in os.listdir(export_folder) if f.endswith('.html')]
    print(f"Trouvé {len(html_files)} fichiers d'export HTML dans le dossier '{export_folder}'.")

    for filename in html_files:
        file_path = os.path.join(export_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                head = f.read(5000)
                match = re.search(r'https://cdn\.discordapp\.com/icons/(\d+)/', head)
                if match:
                    GLOBAL_GUILD_ID = match.group(1)
                    print(f"Guild ID détecté automatiquement : {GLOBAL_GUILD_ID}")
                    break
        except Exception:
            continue

    all_scenes = []
    all_actors = set()

    for idx, filename in enumerate(html_files):
        channel_name = parse_channel_name_from_filename(filename)
        channel_id = parse_channel_id_from_filename(filename)
        file_path = os.path.join(export_folder, filename)

        print(f"[{idx+1}/{len(html_files)}] Analyse : {channel_name}...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            parser = DiscordHTMLParser()
            parser.feed(html_content)
            parser.close()

            messages = parser.messages

            channel_scenes = segment_messages_into_scenes(channel_name, channel_id, messages)
            print(f"  -> {len(messages)} messages lus, divisés en {len(channel_scenes)} scène(s).")

            all_scenes.extend(channel_scenes)

            for scene in channel_scenes:
                for actor in scene['actors']:
                    all_actors.add(actor)

        except Exception as e:
            print(f"  -> ERREUR lors de la lecture du fichier : {e}")

    def get_start_time(scene):
        try:
            return scene['start_time']
        except Exception:
            return "0000-00-00"

    all_scenes.sort(key=get_start_time)

    character_map = {}
    valid_actors = set()
    for actor in all_actors:
        if not actor or len(actor) >= 50:
            continue
        role, color, color_name = get_character_guild_and_color(actor)
        if role is not None:
            character_map[actor] = {
                "role": role,
                "color": color,
                "colorName": color_name
            }
            valid_actors.add(actor)

    for scene in all_scenes:
        scene['actors'] = [a for a in scene['actors'] if a in valid_actors]

    output_data = {
        "characters": character_map,
        "scenes": all_scenes
    }

    output_filename = "scenes.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    src_scenes_path = os.path.join("src", "scenes.json")
    if os.path.isdir("src"):
        with open(src_scenes_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Fichier React mis à jour : {src_scenes_path}")

    js_filename = "data.js"
    with open(js_filename, 'w', encoding='utf-8') as f:
        f.write("window.rpData = ")
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        f.write(";\n")

    print(f"\n✨ Succès total ! Analyse terminée.")
    print(f"📁 Fichiers traités : {len(html_files)}")
    print(f"🎭 Personnages réels identifiés : {len(character_map)}")
    print(f"🎬 Scènes narratives découpées : {len(all_scenes)}")
    print(f"💾 Base de données de la chronologie enregistrée.")

if __name__ == '__main__':
    main()
