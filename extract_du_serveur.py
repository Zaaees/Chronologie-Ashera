import os
import sys
import re
import json
import asyncio
import datetime
import html
import unicodedata
from dotenv import load_dotenv
import discord

# Force UTF-8 on Windows stdout
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Custom print wrapper to unbuffer stdout
_real_print = print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _real_print(*args, **kwargs)

# Charger les variables d'environnement (.env)
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

if not TOKEN:
    print("❌ Erreur : DISCORD_BOT_TOKEN non trouvé dans le fichier .env")
    sys.exit(1)

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

# Helper pour nettoyer le nom du personnage
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

# Ordre de priorité des Rôles Faction Discord
FACTION_ROLE_PRIORITY = [
    1327646236760608803, # La Garde Pourpre
    1327646236760608802, # Cercle d'Azur
    1327646236760608801, # Voile d'Ivoire
    1467532532261322813, # L'œil
    1525469197935841371, # JAVUS
    1475090340557095003  # Sans guilde
]

FACTION_INFO = {
    1327646236760608803: ("La Garde Pourpre", "#b40000", "char_pourpre"),
    1327646236760608802: ("Cercle d'Azur", "#305ed3", "char_azur"),
    1327646236760608801: ("Voile d'Ivoire", "#ffffd4", "char_ivoire"),
    1467532532261322813: ("L'œil", "#0e0d0d", "char_oeil"),
    1525469197935841371: ("JAVUS", "#ffffff", "char_javus"),
    1475090340557095003: ("Sans guilde", "#e2ce7d", "char_sans_guilde")
}

detected_member_factions = {}
detected_member_details = {}

def register_member_faction(name_str, faction_info, username="", display_name="", avatar_url=""):
    if not name_str:
        return
    cleaned = clean_character_name(name_str)
    if cleaned and len(cleaned) < 50:
        detected_member_factions[cleaned] = faction_info
        if username or display_name or avatar_url:
            detected_member_details[cleaned] = {
                "username": username,
                "displayName": display_name,
                "avatarUrl": avatar_url
            }

SYSTEM_BOTS = [
    'carl-bot', 'dyno', 'mee6', 'ticket tool', 'ticket-tool',
    'disboard', 'raidprotect', 'sakuraki', 'jockie', 'koya', 'draftbot'
]

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


LEGITIMATE_PNJ_KEYWORDS = [
    'javus', 'conseiller', 'owl', 'messager', 'missive', 'les missives',
    'monarque', 'infranchissable', 'déesse-mère', 'deesse-mere', 'prince lunaire',
    'prince azur', 'prince du vide', 'roi des rampants', 'nephilim',
    'oeil', 'l\'oeil', 'l\'œil', 'par-delà le voile', 'que le seigneur ouvre', 'narrateur'
]

def get_character_guild_and_color(actor_name):
    clean_name = clean_character_name(actor_name)
    name_lower = clean_name.lower()

    # 1. Ignorer complètement les bots système et utilitaires
    if any(bot_name in name_lower for bot_name in SYSTEM_BOTS):
        return None, None, None

    # 2. PNJ RP officiels
    if any(pnj_kw in name_lower for pnj_kw in LEGITIMATE_PNJ_KEYWORDS) or clean_name in ['JAVUS', 'LE CONSEILLER', 'OWL LE MESSAGER', 'LES MISSIVES', 'LE MONARQUE DU SILENCE', 'L\'Infranchissable', 'La Déesse-Mère', 'Oeil', 'L\'Oeil']:
        return "PNJ", "#c084fc", "char_pnj"

    # 3. Vérifier si une faction a été détectée via les rôles Discord du membre
    if clean_name in detected_member_factions:
        return detected_member_factions[clean_name]

    return "Sans rôle", "#94a3b8", "char_sans_role"

def is_character_or_fiche_channel(channel):
    ch_name = getattr(channel, 'name', '') if hasattr(channel, 'name') else str(channel)
    cat_name = ""
    if hasattr(channel, 'category') and channel.category:
        cat_name = channel.category.name
    return is_excluded_channel(ch_name, cat_name)

EXCLUDED_CATEGORIES = [
    'CHANNELS STAFF', 'TICKETS', 'INFORMATIONS HRP', 'INFORMATIONS RP',
    'LE GRIMOIRE D\'URIEL', 'HORS RP', 'FICHES RP', 'GUILDES - HRP',
    'ARC I - LA GALERIE DU PRINCE LUNAIRE', 'NE PAS TOUCHER'
]

EXCLUDED_EXPLICIT_CHANNELS = [
    'le tresor', 'le trésor', 'la folie', 'le marais', 'le sigile', 'la bete', 'la bête',
    'statue d\'icare', 'statue-d-icare', 'statue d icare', 'le mensonge', 'le ciel', 'la force',
    'le voyageur', 'le secret', 'l’orgueil', 'l\'orgueil', 'le guerrier', 'le temps'
]

EXCLUDED_PREFIXES = [
    'hrp', 'ticket', 'logs', 'annonce', 'annonces', 'demande', 'statistiques',
    'réclamations', 'reclamations', 'règlement', 'reglement', 'arrivée', 'arrivee', 'arrivé',
    'to-do', 'moderator', 'formulaire', 'invitation', 'boutique', 'channels-rp', '◦',
    '💬▹', '📸▹', '🎮▹', '💻▹', '🗞️▹', '🔏▹', '♻️▹', '🍂▹', '🗡️▹', '💴▹', '🌕▹', '🎨▹', '🤺▹'
]

def is_excluded_channel(ch_name, cat_name=""):
    norm_ch = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFKD', ch_name)).lower()
    norm_cat = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFKD', cat_name)).lower()

    # 1. Catégories exclues
    if any(ex.lower() in norm_cat for ex in EXCLUDED_CATEGORIES):
        return True

    # 2. Exclusions spécifiques de salons
    if any(ex in norm_ch for ex in EXCLUDED_EXPLICIT_CHANNELS):
        return True

    # 3. Prefixes non-RP
    if norm_ch.startswith(tuple(p.lower() for p in EXCLUDED_PREFIXES)):
        return True

    # 4. Fiches de personnages (seules les fiches/candidatures sont exclues, les chambres et dortoirs RP sont désormais pris en compte)
    fiche_keywords = ['fiche', 'effectif', 'profil', 'candidature', 'presentation', 'perso', 'valide']
    if any(k in norm_ch for k in fiche_keywords) or any(k in norm_cat for k in fiche_keywords):
        return True

    return False

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

from segmenteur_narratif import segment_messages_into_scenes_v2

# Segmentation des messages en scènes (Logique Narrative V2)
def segment_messages_into_scenes(channel_name, channel_id, messages, guild_id_str, category_name="", discord_position=999):
    if not messages:
        return []

    valid_msgs = []
    for m in messages:
        full_text = " ".join([m.get('content', ''), m.get('embed_title', ''), m.get('embed_description', '')]).strip()
        if full_text:
            valid_msgs.append((m, full_text))

    if not valid_msgs:
        return []

    def scene_builder(ch_name, ch_id, idx, sub_tuples, title):
        return create_scene_dict(ch_name, ch_id, idx, sub_tuples, guild_id_str, category_name=category_name, discord_position=discord_position)

    scenes = segment_messages_into_scenes_v2(channel_name, channel_id, valid_msgs, scene_builder)

    return [s for s in scenes if s.get("actors")]

def create_scene_dict(channel_name, channel_id, scene_index, messages_tuples, guild_id_str, category_name="", discord_position=999):
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

    first_msg_id = messages[0]['id']
    discord_url = f"discord://discord.com/channels/{guild_id_str}/{channel_id}/{first_msg_id}"

    formatted_messages = []
    for m in messages:
        formatted_messages.append({
            "id": str(m['id']),
            "author": clean_character_name(m['author']),
            "timestamp": m['timestamp'],
            "content": m['content'],
            "embed_title": m['embed_title'],
            "embed_description": m['embed_description']
        })

    clean_ch_name = re.sub(r'[^\w]', '_', channel_name)
    scene_id = f"scene_{clean_ch_name}_{scene_index}"

    sc_dict = {
        "id": scene_id,
        "channel": parent_channel,
        "channel_id": str(channel_id),
        "category": category_name,
        "discord_position": discord_position,
        "title": f"{', '.join(actors[:3])}{'...' if len(actors) > 3 else ''}" if actors else parent_channel,
        "actors": actors,
        "start_time": messages[0]['timestamp'],
        "end_time": messages[-1]['timestamp'],
        "preview": preview,
        "message_count": len(messages),
        "discord_url": discord_url,
        "messages": formatted_messages
    }

    if channel_name in THREAD_TO_PARENT:
        sc_dict["thread_name"] = channel_name

    return sc_dict

class DiscordExporterClient(discord.Client):
    async def on_ready(self):
        print(f"🤖 Bot connecté en tant que : {self.user} (ID: {self.user.id})")
        
        target_guild = None
        if GUILD_ID:
            target_guild = self.get_guild(int(GUILD_ID))
            if not target_guild:
                try:
                    target_guild = await self.fetch_guild(int(GUILD_ID))
                except Exception as e:
                    print(f"⚠️ Impossible d'obtenir la guilde {GUILD_ID}: {e}")

        if not target_guild:
            if self.guilds:
                target_guild = self.guilds[0]
                print(f"ℹ️ Aucun GUILD_ID valide spécifié, utilisation du premier serveur disponible : {target_guild.name}")
            else:
                print("❌ Le bot n'est présent sur aucun serveur Discord.")
                await self.close()
                return

        print(f"\n🏰 Extraction du serveur : {target_guild.name} (ID: {target_guild.id})")

        # Analyse des rôles des membres du serveur Discord
        try:
            print("👥 Analyse intelligente des membres du serveur et attribution des factions par priorité...")
            gm_role_id = 1327646236798353535
            detected_gm_names = set()
            if os.path.exists("discord_gm_members.json"):
                try:
                    with open("discord_gm_members.json", "r", encoding="utf-8") as f:
                        old_gms = json.load(f)
                        if isinstance(old_gms, list): detected_gm_names.update(old_gms)
                except Exception:
                    pass

            async for member in target_guild.fetch_members(limit=None):
                member_role_ids = [r.id for r in member.roles]

                if gm_role_id in member_role_ids:
                    for n_candidate in [member.display_name, member.name, getattr(member, 'global_name', None)]:
                        if n_candidate:
                            c_name = clean_character_name(n_candidate)
                            if c_name:
                                detected_gm_names.add(c_name)

                best_role = None
                for pid in FACTION_ROLE_PRIORITY:
                    if pid in member_role_ids:
                        best_role = pid
                        break
                
                if best_role:
                    faction_info = FACTION_INFO[best_role]
                    av_url = str(member.display_avatar.url) if hasattr(member, 'display_avatar') and member.display_avatar else ""
                    register_member_faction(member.display_name, faction_info, username=member.name, display_name=member.display_name, avatar_url=av_url)
                    if member.name:
                        register_member_faction(member.name, faction_info, username=member.name, display_name=member.display_name, avatar_url=av_url)
                    global_name = getattr(member, 'global_name', None)
                    if global_name:
                        register_member_faction(global_name, faction_info, username=member.name, display_name=member.display_name, avatar_url=av_url)
            
            with open("discord_gm_members.json", "w", encoding="utf-8") as f:
                json.dump(sorted(list(detected_gm_names)), f, ensure_ascii=False, indent=2)

            print(f"✅ {len(detected_member_factions)} correspondances nom/pseudo -> faction et {len(detected_gm_names)} membres avec le rôle MJ enregistrés.")
            with open("discord_member_factions.json", "w", encoding="utf-8") as f:
                json.dump(detected_member_factions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Analyse des membres restreinte : {e}")

        # 1. Charger d'abord les scènes existantes pour l'extraction incrémentale instantanée
        existing_scenes_data = {}
        existing_scenes_by_channel = {}
        last_msg_id_by_channel = {}
        if os.path.exists("scenes.json"):
            try:
                with open("scenes.json", "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    scenes_list = existing_data.get("scenes", [])
                    for s in scenes_list:
                        ch_name = s.get("channel", "")
                        cat_name = s.get("category", "")
                        if is_excluded_channel(ch_name, cat_name):
                            continue

                        if 'messages' in s:
                            msg_authors = set()
                            for m in s['messages']:
                                if 'author' in m:
                                    cleaned_a = clean_character_name(m['author'])
                                    m['author'] = cleaned_a
                                    if cleaned_a and not any(b in cleaned_a.lower() for b in SYSTEM_BOTS):
                                        if is_meaningful_rp_content(m.get('content', ''), m.get('embed_title', ''), m.get('embed_description', '')):
                                            msg_authors.add(cleaned_a)
                            s['actors'] = list(msg_authors)
                            if not s['actors']:
                                continue
                            parent_ch = s.get("channel", "")
                            s['title'] = f"{', '.join(s['actors'][:3])}{'...' if len(s['actors']) > 3 else ''}" if s['actors'] else parent_ch

                        ch_key = s.get("channel_id") or s.get("channel")
                        if ch_key not in existing_scenes_by_channel:
                            existing_scenes_by_channel[ch_key] = []

                        if len(existing_scenes_by_channel[ch_key]) == 0 and len(s.get("messages", [])) == 1:
                            first_author = s["messages"][0].get("author", "").strip().lower()
                            if "conseiller" in first_author:
                                continue

                        existing_scenes_by_channel[ch_key].append(s)
                        
                        msgs = s.get("messages", [])
                        if msgs:
                            last_id = msgs[-1].get("id")
                            if last_id and last_id.isdigit():
                                if ch_key not in last_msg_id_by_channel or int(last_id) > int(last_msg_id_by_channel[ch_key]):
                                    last_msg_id_by_channel[ch_key] = last_id
                print("📦 Base de scènes existantes nettoyée et chargée pour l'extraction incrémentale.")
            except Exception as e:
                print(f"⚠️ Erreur chargement scenes.json existant : {e}")

        # 2. Récupérer la liste complète des salons via l'API REST
        try:
            fetched_channels = await target_guild.fetch_channels()
        except Exception as e:
            print(f"⚠️ Impossible de fetch les salons : {e}")
            fetched_channels = target_guild.channels

        # Filtrer TOUT DE SUITE les salons HRP / Non-RP
        rp_channels = [ch for ch in fetched_channels if isinstance(ch, (discord.TextChannel, discord.ForumChannel)) and not is_character_or_fiche_channel(ch)]

        channels_to_process = list(rp_channels)

        # 3. Récupérer les fils (threads) actifs pour les salons RP uniquement
        try:
            active_threads = await target_guild.active_threads()
            for thread in active_threads:
                if not is_character_or_fiche_channel(thread) and thread not in channels_to_process:
                    channels_to_process.append(thread)
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les threads actifs : {e}")

        # 4. Recherche complète des fils/posts archivés (actifs et inactifs/archivés) pour TOUS les salons et forums RP
        my_permissions = target_guild.me.guild_permissions if target_guild.me else None
        
        for ch in rp_channels:
            if hasattr(ch, 'archived_threads'):
                if my_permissions and not ch.permissions_for(target_guild.me).read_message_history:
                    continue
                try:
                    async def fetch_archived_for_channel(channel_obj):
                        threads_found = []
                        # Threads/posts archivés publics
                        try:
                            async for arch_thread in channel_obj.archived_threads(limit=None, private=False):
                                if not is_character_or_fiche_channel(arch_thread):
                                    threads_found.append(arch_thread)
                        except Exception as e_pub:
                            pass
                        # Threads/posts archivés privés (si accessibles)
                        try:
                            async for arch_thread in channel_obj.archived_threads(limit=None, private=True):
                                if not is_character_or_fiche_channel(arch_thread):
                                    threads_found.append(arch_thread)
                        except Exception as e_priv:
                            pass
                        return threads_found

                    arch_threads = await asyncio.wait_for(fetch_archived_for_channel(ch), timeout=15.0)
                    for arch_thread in arch_threads:
                        if arch_thread not in channels_to_process:
                            channels_to_process.append(arch_thread)
                except Exception as e_arch:
                    print(f"⚠️ Note recherche archivés sur #{ch.name} : {e_arch}")

        all_scenes = []
        all_actors = set()

        for idx, channel in enumerate(channels_to_process):
            ch_name = channel.name
            ch_id = str(channel.id)

            print(f"[{idx+1}/{len(channels_to_process)}] Extraction : #{ch_name} (ID: {ch_id})...")

            # Ignorer les salons de fiches personnages et chambres
            if is_character_or_fiche_channel(channel):
                print(f"  -> ⏭️ Salon de fiche/personnage ignoré.")
                continue

            # Ignorer les ForumChannel directement (leurs threads/postes sont traités séparément)
            if not hasattr(channel, 'history'):
                continue

            # Vérifier si un salon a eu de nouveaux messages depuis le dernier export
            last_id = last_msg_id_by_channel.get(ch_id) or last_msg_id_by_channel.get(ch_name)
            ch_last_msg_id = getattr(channel, 'last_message_id', None)
            
            if last_id and ch_last_msg_id and ch_last_msg_id <= int(last_id):
                old_scenes = existing_scenes_by_channel.get(ch_id) or existing_scenes_by_channel.get(ch_name) or []
                print(f"  -> ⚡ Aucun changement depuis l'export précédent ({len(old_scenes)} scènes conservées).")
                all_scenes.extend(old_scenes)
                continue

            after_obj = None  # Extraction complète depuis l'origine pour ne rater aucun message/description

            # Limiter l'historique sur les salons HRP/Généraux/Staff/Jeux/Bots/Demandes
            history_limit = None
            ch_normalized = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFKD', ch_name)).lower()
            if any(x in ch_normalized for x in ["general", "staff", "medias", "commandes", "logs", "bot", "ticket", "jeux", "jeu", "hrp", "demande", "question", "spoil", "suggestion"]):
                history_limit = 100

            raw_messages = []
            try:
                # Extraire tous les messages sans filtre after_obj pour capturer les messages de description
                async for msg in channel.history(limit=history_limit, oldest_first=True):
                    # Déterminer le nom de l'auteur (affichage/surnom si disponible)
                    author_name = msg.author.display_name if hasattr(msg.author, 'display_name') else msg.author.name
                    author_avatar_url = str(msg.author.display_avatar.url) if hasattr(msg.author, 'display_avatar') and msg.author.display_avatar else ""
                    
                    # Contenu texte + pièces jointes (ex: images)
                    content = msg.content or ""
                    if msg.attachments:
                        att_urls = [f"[Image: {att.url}]" for att in msg.attachments]
                        if content:
                            content += "\n" + "\n".join(att_urls)
                        else:
                            content = "\n".join(att_urls)

                    embed_title = ""
                    embed_desc = ""
                    embed_texts = []
                    if msg.embeds:
                        titles = [e.title for e in msg.embeds if e.title]
                        descs = [e.description for e in msg.embeds if e.description]
                        embed_title = " | ".join(titles)
                        embed_desc = " | ".join(descs)

                        for e in msg.embeds:
                            if e.title:
                                embed_texts.append(e.title)
                            if hasattr(e, 'author') and e.author and hasattr(e.author, 'name') and e.author.name:
                                embed_texts.append(e.author.name)
                            if e.description:
                                embed_texts.append(e.description)
                            if hasattr(e, 'fields') and e.fields:
                                for f in e.fields:
                                    field_str = f"{f.name}\n{f.value}" if hasattr(f, 'name') and f.name else f.value
                                    embed_texts.append(field_str)
                            if hasattr(e, 'footer') and e.footer and hasattr(e.footer, 'text') and e.footer.text:
                                embed_texts.append(e.footer.text)
                            if hasattr(e, 'image') and e.image and hasattr(e.image, 'url') and e.image.url:
                                embed_texts.append(f"[Image: {e.image.url}]")

                        if embed_texts:
                            embed_full = "\n".join(embed_texts)
                            if content:
                                content = content + "\n\n" + embed_full
                            else:
                                content = embed_full

                    # Format du timestamp ISO
                    ts_iso = msg.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                    is_wh = getattr(msg, 'webhook_id', None) is not None or (hasattr(msg.author, 'bot') and msg.author.bot)

                    raw_messages.append({
                        "id": str(msg.id),
                        "author": author_name,
                        "timestamp": ts_iso,
                        "content": content,
                        "embed_title": embed_title,
                        "embed_description": embed_desc,
                        "avatar_url": author_avatar_url,
                        "is_webhook": is_wh
                    })

                cat_name = channel.category.name if hasattr(channel, 'category') and channel.category else ""
                pos = channel.position if hasattr(channel, 'position') else 999
                channel_scenes = segment_messages_into_scenes(ch_name, ch_id, raw_messages, str(target_guild.id), category_name=cat_name, discord_position=pos)
                print(f"  -> {len(raw_messages)} message(s) lu(s) ({len(channel_scenes)} scène(s) au total).")
                all_scenes.extend(channel_scenes)

            except Exception as e:
                print(f"  -> ⚠️ ERREUR lors de la lecture du salon #{ch_name}: {e}")

        # conserver tous les messages sans filtrer l'année 2025
        def get_start_time(scene):
            return scene.get('start_time', '0000-00-00')

        all_scenes.sort(key=get_start_time)

        # Collecter tous les acteurs de l'ENSEMBLE des scènes (y compris conservées)
        all_actors = set()
        for scene in all_scenes:
            for actor in scene.get('actors', []):
                if actor:
                    all_actors.add(actor)

        # Générer la carte des personnages (à partir des scènes ET des membres identifiés sur Discord)
        character_map = {}
        valid_actors = set()

        # 1. Ajouter d'abord les acteurs des scènes RP en évaluant get_character_guild_and_color
        for actor in sorted(all_actors):
            if not actor or len(actor) >= 50 or any(b in actor.lower() for b in SYSTEM_BOTS):
                continue
            role, color, color_name = get_character_guild_and_color(actor)
            if role is not None:
                details = detected_member_details.get(actor, {})
                character_map[actor] = {
                    "role": role,
                    "color": color,
                    "colorName": color_name,
                    "username": details.get('username', ''),
                    "displayName": details.get('displayName', ''),
                    "avatarUrl": details.get('avatarUrl', '')
                }
                valid_actors.add(actor)

        # 2. Compléter avec les membres Discord identifiés qui ne sont pas déjà dans character_map
        for char_name, faction_info in detected_member_factions.items():
            if char_name and len(char_name) < 50 and char_name not in character_map:
                if any(b in char_name.lower() for b in SYSTEM_BOTS):
                    continue
                role, color, color_name = faction_info
                details = detected_member_details.get(char_name, {})
                character_map[char_name] = {
                    "role": role,
                    "color": color,
                    "colorName": color_name,
                    "username": details.get('username', ''),
                    "displayName": details.get('displayName', ''),
                    "avatarUrl": details.get('avatarUrl', '')
                }
                valid_actors.add(char_name)

        img_dir = "public/channel_images"
        channel_images_map = {}
        if os.path.exists(img_dir):
            img_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
            pub_clean_map = {}
            for f in img_files:
                base = os.path.splitext(f)[0]
                clean = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', base)).lower()
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
                'ilsnesouhaitentquuneseulechoselapaix': 'channel_images/egregore.jpg',
                'planétarium': 'channel_images/planetarium.png',
                'planetarium': 'channel_images/planetarium.png',
                'Planétarium': 'channel_images/planetarium.png'
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

        output_data = {
            "characters": character_map,
            "scenes": all_scenes,
            "channel_images": channel_images_map
        }

        # Sauvegarder dans src/scenes.json
        output_file = os.path.join('src', 'scenes.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n✨ Extraction et mise à jour terminées avec succès !")
        print(f"📁 Salons/Fils traités : {len(channels_to_process)}")
        print(f"🎭 Personnages identifiés : {len(character_map)}")
        print(f"🎬 Scènes générées : {len(all_scenes)}")

        await self.close()

async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.members = True

    client = DiscordExporterClient(intents=intents)
    await client.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt du bot.")
