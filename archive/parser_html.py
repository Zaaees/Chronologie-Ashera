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

CANONICAL_MAP = {
    "adelina del fuego": "Adelina Del Fuego", "adelina del fuego mari": "Adelina Del Fuego", "marigold": "Adelina Del Fuego", "_marigld": "Adelina Del Fuego",
    "aegnor othar": "Aegnor Othar", "tcizab": "Aegnor Othar", "tcizabaegnor othar": "Aegnor Othar",
    "akane tsukishiro": "Akane Tsukishiro", "tsukishiro akane": "Akane Tsukishiro", "doppelganger2830": "Akane Tsukishiro",
    "arun acharya": "Arun Acharya", "arun acharya freulonlezouin": "Arun Acharya", "freulonlezouinzouin": "Arun Acharya", "nyson": "Arun Acharya",
    "aryanna erhendil": "Aryanna Erhendil", "aryana erhendil": "Aryanna Erhendil", "aryana erhendil taurielle": "Aryanna Erhendil", "taurielle": "Aryanna Erhendil", "tutaurielle": "Aryanna Erhendil",
    "asior eveus": "Asior Eveus", "eopia asior eveus": "Asior Eveus", "eopia": "Asior Eveus",
    "bozdag dermirhan": "Bozdag Dermirhan", "clipmyr": "Bozdag Dermirhan", "clip demirhan bozdag": "Bozdag Dermirhan",
    "brutus redwitch": "Brutus Redwitch", "kinoru": "Brutus Redwitch",
    "cassian ortie": "Cassian Ortie", "chulakita": "Cassian Ortie", "chulaktm": "Cassian Ortie",
    "frey gudfrodur": "Frey Guðfrøðr", "frey guðfrøðr": "Frey Guðfrøðr", "frey elear": "Frey Guðfrøðr", "frey - elear": "Frey Guðfrøðr", "elessai": "Frey Guðfrøðr",
    "hedwig von glanzestern": "Hedwig Von Glanzestern", "twisted_servant": "Hedwig Von Glanzestern",
    "idelmee cadree": "Idelmée Cadree", "idelmee cadere": "Idelmée Cadree", "momo idelmee cadere": "Idelmée Cadree", "momotarie": "Idelmée Cadree", "momo": "Idelmée Cadree",
    "iscarioth": "Iscarioth", "zaes ley vaelric": "Iscarioth", "ley vaelric": "Iscarioth", "zaes": "Iscarioth", "zaaes": "Iscarioth",
    "isis faerieth": "Isis Faerieth", "etoile isis faerieth": "Isis Faerieth", "etoile": "Isis Faerieth", "letoiledeminuit": "Isis Faerieth",
    "ivara luella": "Ivara Luella", "ivara luell": "Ivara Luella", "elisabeeh ivara luell": "Ivara Luella", "elisabeeeeh": "Ivara Luella",
    "jasp nah": "Jasp Nah", "nah jasp": "Jasp Nah",
    "junko anarchy": "Junko Anarchy", "luden junko anarchy": "Junko Anarchy", "luden": "Junko Anarchy", "luden_chan": "Junko Anarchy",
    "katelynn hoffmann": "Katelynn Hoffmann", "katelyn hoffmann": "Katelynn Hoffmann", "yuu katelyn hoffmann": "Katelynn Hoffmann", "its_yuu": "Katelynn Hoffmann", "yuu": "Katelynn Hoffmann",
    "kenji takahashi": "Kenji Takahashi", "kenji takahashi heavil": "Kenji Takahashi", "heavil4444": "Kenji Takahashi", "heavil": "Kenji Takahashi",
    "lewis bamer": "Lewis Bamer", "lewis bamer historious": "Lewis Bamer",
    "loyis delacroix": "Loyis Delacroix", "happy loyis delacroix": "Loyis Delacroix", "happy_is_happy": "Loyis Delacroix", "happy": "Loyis Delacroix",
    "lucia fiorella": "Lucia Fiorella", "ju lucia bunny fiorella": "Lucia Fiorella", "juju_la_best": "Lucia Fiorella",
    "lumia faendharts": "Lumia Faendharts", "lumia lum faendhartslumiere": "Lumia Faendharts", "lueur_": "Lumia Faendharts",
    "maell fol'dun": "Maëll Fol'Dun", "mael fol'dun": "Maëll Fol'Dun", "mael fol'dun astyell": "Maëll Fol'Dun", "astyell": "Maëll Fol'Dun",
    "myrea m": "Myrea M", "khem myrea m": "Myrea M", "khemm": "Myrea M", "khem": "Myrea M",
    "nick sol": "Nick Sol", "prince nick sol": "Nick Sol", "harderbae": "Nick Sol", "_aura_": "Nick Sol",
    "ragde umbras": "Ragde Umbras", "personnes_10": "Ragde Umbras", "personne": "Ragde Umbras",
    "red roadman": "Red Roadman", "red": "Red Roadman", "jivwd": "Red Roadman",
    "ren urugaki": "Ren Urugaki", "noci urugaki ren": "Ren Urugaki", "urugaki ren": "Ren Urugaki", "nociferoce": "Ren Urugaki", "noci": "Ren Urugaki",
    "selena moon": "Selena Moon", "seléna moon": "Selena Moon", "gwenphasehikena": "Selena Moon",
    "septimus kales": "Septimus Kales", "ryo kales septimus": "Septimus Kales",
    "tarrion tombetoile": "Tarrion Tombetoile", "tarrion tombetoile biboon": "Tarrion Tombetoile", "biboon": "Tarrion Tombetoile",
    "tenebris": "Tenebris", "___val___": "Tenebris", "_val_": "Tenebris",
    "velka valcyrion": "Velka Valcyrion", "norxas": "Velka Valcyrion",
    "vosk sulyvan": "Vosk Sulyvan", "sulyvan vosk": "Vosk Sulyvan", "sulyvan vosk hussh": "Vosk Sulyvan", "hussh": "Vosk Sulyvan", "hush": "Vosk Sulyvan",
    "aether": "Æther", "æther": "Æther", "miklelait": "Æther", "mikle": "Æther",
    "jap yunah aoi enjaku": "Yunah Aoi Enjaku", "yunah aoi enjaku": "Yunah Aoi Enjaku", "jaaapaannnnnnnnnnn": "Yunah Aoi Enjaku",
    "kuikui - astreus mylonas": "Astreüs Mylonas", "astreus mylonas": "Astreüs Mylonas", "kuikuito": "Astreüs Mylonas",
    "jin alurantes": "Jin Alurantes", "elouand": "Jin Alurantes",
    "inzu sravel - instructeur de la garde pourpre": "Inzu Sravel", "inzu sravel - garde pourpre": "Inzu Sravel", "inzu sravel": "Inzu Sravel",
    "hector swaft - mage de rang 3": "Hector Swaft", "hector swaft": "Hector Swaft",
    "milli enga - mange de rang 2": "Milli Enga", "milli enga": "Milli Enga",
    "vieux debile tsutomu yamamoto": "Tsutomu Yamamoto", "vieux debile": "Tsutomu Yamamoto", "tsutomu yamamoto": "Tsutomu Yamamoto", "reverse.d": "Tsutomu Yamamoto", "reverse": "Tsutomu Yamamoto",
    "emil camille rebenok": "Emil Camille Rebenok", "emil": "Emil Camille Rebenok", "indominushunter": "Emil Camille Rebenok",
    "rias valdor - cheffe de la famille valdor": "Rias Valdor", "rias valdor": "Rias Valdor",
    "lewis-phoebe d'ashbourne": "Lewis-Phoebe d'Ashbourne", "leonore edelweiss": "Léonore Edelweiss", "ana_non": "Léonore Edelweiss",
    "bourpiff markus law": "Markus Law", "bourpiff": "Markus Law", "markus law": "Markus Law",
    "orla kalem crowley": "Kalem Crowley", "orla": "Kalem Crowley", "orla_": "Kalem Crowley", "eldren gates": "Eldren Gates"
}

def clean_key_lookup(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = re.sub(r'[\u0300-\u036f]', '', s)
    return re.sub(r'[^a-z0-9]', '', s)

CANONICAL_LOOKUP = {clean_key_lookup(k): v for k, v in CANONICAL_MAP.items()}

def clean_character_name(name):
    if not name:
        return "Narrateur"

    name_str = unicodedata.normalize('NFKD', str(name))
    name_str = re.sub(r'[^\w\s\-\']', '', name_str)
    name_str = re.sub(r'\s+', ' ', name_str).strip()
    name_str = re.sub(r'\s+BOT$', '', name_str, flags=re.IGNORECASE)
    name_lower = name_str.lower()

    if 'conseiller' in name_lower:
        return "LE CONSEILLER"
    elif 'owl' in name_lower or 'messager' in name_lower:
        return "OWL LE MESSAGER"
    elif name_lower in ["l'oeil", "l'œil", "oeil", "œil", "loeil", "lœil"]:
        return "L'Oeil"
    elif 'missive' in name_lower:
        return "LES MISSIVES"

    ck = clean_key_lookup(name_str)
    if ck in CANONICAL_LOOKUP:
        return CANONICAL_LOOKUP[ck]
    for k, v in CANONICAL_LOOKUP.items():
        if len(k) >= 4 and (k in ck or ck in k):
            return v

    return name_str if name_str else "Narrateur"

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

def is_meaningful_rp_content(content, embed_title='', embed_description=''):
    full_text = ' '.join([content or '', embed_title or '', embed_description or '']).strip()
    if not full_text:
        return False

    has_mentions = ('<' in full_text and '@' in full_text) or ('@' in full_text)
    has_image = '[Image:' in full_text or 'http://' in full_text or 'https://' in full_text
    
    text = re.sub(r'<@[!&]?\d+>', '', full_text)
    text = re.sub(r'<#\d+>', '', text)
    text = re.sub(r'\[Image:\s*https?://\S+\]', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@[^\n@]+?(?=\s+@|\n|$)', '', text)
    text = re.sub(r'@\S+', '', text)
    
    cleaned = re.sub(r'[^\w]', '', text, flags=re.UNICODE).strip()
    
    if has_mentions and not has_image:
        if len(cleaned) < 15:
            return False
        lower = cleaned.lower()
        ping_phrases = ['ping', 'up', 'relance', 'atoai', 'atois', 'avous', 'hrp', 'inrp', 'repondez', 'edited', 'prochainenarration', 'lajournee']
        if any(lower == p for p in ping_phrases):
            return False

    if has_image and not has_mentions:
        return True

    if len(cleaned) < 3 and not has_image:
        return False
        
    return True

SYSTEM_BOTS = [
    'carl-bot', 'dyno', 'mee6', 'ticket tool', 'ticket-tool',
    'disboard', 'raidprotect', 'sakuraki', 'jockie', 'koya', 'draftbot'
]

from ai_narrative_segmenter import segment_messages_into_scenes_ai

def segment_messages_into_scenes(channel_name, channel_id, messages):
    if not messages:
        return []

    valid_msgs = []
    for m in messages:
        full_text = " ".join([m.get('content', ''), m.get('embed_title', ''), m.get('embed_description', '')]).strip()
        if full_text:
            valid_msgs.append((m, full_text))

    if not valid_msgs:
        return []

    def scene_builder(ch_name, ch_id, idx, sub_tuples):
        return create_scene_dict(ch_name, ch_id, idx, sub_tuples)

    scenes = segment_messages_into_scenes_ai(channel_name, channel_id, valid_msgs, scene_builder)
    return [s for s in scenes if s.get("actors")]

def create_scene_dict(channel_name, channel_id, scene_index, messages_tuples):
    global GLOBAL_GUILD_ID
    messages = [t[0] for t in messages_tuples]
    texts = [t[1] for t in messages_tuples]

    actors = list({
        clean_character_name(m['author']) 
        for m in messages 
        if m.get('author') 
        and not any(b in m['author'].lower() for b in SYSTEM_BOTS)
        and is_meaningful_rp_content(m.get('content', ''), m.get('embed_title', ''), m.get('embed_description', ''))
    })
    parent_channel = THREAD_TO_PARENT.get(channel_name, channel_name)

    preview = texts[0]
    if len(preview) > 160:
        preview = preview[:157] + "..."

    first_msg_id = messages[0].get('id', '0')
    discord_url = f"discord://discord.com/channels/{GLOBAL_GUILD_ID}/{channel_id}/{first_msg_id}"

    sc_dict = {
        "id": f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', channel_name)}_{scene_index}",
        "channel": parent_channel,
        "channel_id": str(channel_id),
        "category": "",
        "title": f"Scène {scene_index} - {', '.join(actors[:3])}{'...' if len(actors)>3 else ''}",
        "actors": actors,
        "start_time": parse_html_timestamp(messages[0]['timestamp']),
        "end_time": parse_html_timestamp(messages[-1]['timestamp']),
        "preview": preview,
        "message_count": len(messages),
        "discord_url": discord_url,
        "messages": messages
    }

    if channel_name in THREAD_TO_PARENT:
        sc_dict["thread_name"] = channel_name

    return sc_dict

def get_character_guild_and_color(actor_name):
    clean_name = clean_character_name(actor_name)
    name_lower = clean_name.lower()

    if any(x in name_lower for x in ["koya", "profile", "carl-bot", "dyno"]):
        return None, None, None

    if any(x in name_lower for x in ["conseiller", "owl", "messager", "missive", "les missives"]) or name_lower in ["l'oeil", "l'oeil", "l'œil", "oeil", "loeil", "lœil"]:
        return "PNJ", "#a855f7", "char_pnj"

    return "Sans rôle", "#94a3b8", "char_sans_role"

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
            channel_scenes = [s for s in channel_scenes if not s.get("start_time", "").startswith("2025")]
            print(f"  -> {len(messages)} messages lus, divisés en {len(channel_scenes)} scène(s) (2026+).")

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

    existing_character_map = {}
    if os.path.exists("scenes.json"):
        try:
            with open("scenes.json", "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_character_map = existing_data.get("characters", {})
        except Exception:
            pass

    character_map = dict(existing_character_map)
    valid_actors = set(existing_character_map.keys())
    for actor in all_actors:
        if not actor or len(actor) >= 50:
            continue
        role, color, color_name = get_character_guild_and_color(actor)
        if role is not None:
            # Preserve existing rich role info if available
            existing = existing_character_map.get(actor, {})
            if existing and existing.get("role") and existing["role"] != "Sans rôle":
                role = existing.get("role", role)
                color = existing.get("color", color)
                color_name = existing.get("colorName", color_name)

            char_entry = {
                "role": role,
                "color": color,
                "colorName": color_name
            }
            if existing.get("avatarUrl"): char_entry["avatarUrl"] = existing["avatarUrl"]
            if existing.get("displayName"): char_entry["displayName"] = existing["displayName"]
            if existing.get("username"): char_entry["username"] = existing["username"]

            character_map[actor] = char_entry
            valid_actors.add(actor)

    for scene in all_scenes:
        scene['actors'] = [a for a in scene['actors'] if a in valid_actors]

    img_dir = "public/channel_images"
    channel_images_map = {}
    if os.path.exists(img_dir):
        img_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
        img_word_sets = []
        for f in img_files:
            base = os.path.splitext(f)[0]
            words = set(re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKD', base)).lower().split())
            img_word_sets.append((f, words))

        def get_best_image(name):
            if not name: return None
            ch_words = set(re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKD', name)).lower().split())
            if not ch_words: return None
            best_img, best_score = None, 0
            for f, words in img_word_sets:
                if not words: continue
                intersection = ch_words.intersection(words)
                if not intersection: continue
                score = len(intersection) / float(len(words))
                if words.issubset(ch_words):
                    score += 2.0
                if score > best_score and score >= 0.7:
                    best_score, best_img = score, f
            return f'channel_images/{best_img}' if best_img else None

        for scene in all_scenes:
            ch = scene.get('channel')
            thread = scene.get('thread_name')
            img = get_best_image(ch)
            if img:
                channel_images_map[ch] = img
                scene['location_image'] = img
            elif thread:
                th_img = get_best_image(thread)
                if th_img:
                    channel_images_map[thread] = th_img
                    scene['location_image'] = th_img

    output_data = {
        "characters": character_map,
        "scenes": all_scenes,
        "channel_images": channel_images_map
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
