import json
import sys
import re
import unicodedata
import os

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Discord Faction Role IDs mapping rules
FACTION_ROLE_IDS = {
    1467532532261322813: ("L'œil", "#cbd5e1"),
    1327646236760608802: ("Cercle d'Azur", "#3b82f6"),
    1327646236760608803: ("La Garde Pourpre", "#ef4444"),
    1327646236760608801: ("Voile d'Ivoire", "#fef08a"),
    1525469197935841371: ("JAVUS", "#ffffff"),
    1475090340557095003: ("Sans guilde", "#eab308")
}

# Administrative moderation bots to exclude completely from RP
SYSTEM_MODERATION_BOTS = {"carl-bot", "dyno", "mee6", "ticket tool", "ticket-tool", "disboard", "raidprotect", "jockie", "koya"}

# Pure Webhook-based PNJ Classification Rule
# Note: PNJ_NAMES hardcoded dictionary removed as requested.
# Webhook messages are classified as PNJ (Role: PNJ, Color: #c084fc).

# Main canonical mapping rules for names
CANONICAL_MAP = {
    # 35 Main Characters
    "adelina del fuego": "Adelina Del Fuego", "adelina del fuego mari": "Adelina Del Fuego", "marigold": "Adelina Del Fuego", "_marigld": "Adelina Del Fuego",
    "aegnor othar": "Aegnor Othar", "tcizab": "Aegnor Othar", "tcizabaegnor othar": "Aegnor Othar", "tcizab aegnor othar": "Aegnor Othar",
    "akane tsukishiro": "Akane Tsukishiro", "tsukishiro akane": "Akane Tsukishiro", "doppelganger2830": "Akane Tsukishiro",
    "arun acharya": "Arun Acharya", "arun acharya freulonlezouin": "Arun Acharya", "freulonlezouinzouin": "Arun Acharya", "nyson": "Arun Acharya",
    "aryanna erhendil": "Aryanna Erhendil", "aryana erhendil": "Aryanna Erhendil", "aryana erhendil taurielle": "Aryanna Erhendil", "taurielle": "Aryanna Erhendil", "tutaurielle": "Aryanna Erhendil",
    "asior eveus": "Asior Eveus", "eopia asior eveus": "Asior Eveus", "eopia": "Asior Eveus",
    "bozdag dermirhan": "Bozdag Dermirhan", "clipmyr": "Bozdag Dermirhan", "clip demirhan bozdag": "Bozdag Dermirhan",
    "brutus redwitch": "Brutus Redwitch", "kinoru": "Brutus Redwitch",
    "cassian ortie": "Cassian Ortie", "chulakita": "Cassian Ortie", "chulak cassian ortie": "Cassian Ortie", "chulaktm": "Cassian Ortie",
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
    "tenebris": "Tenebris", "___val___": "Tenebris", "_val_": "Tenebris", "lys dandelion": "Tenebris", "lys": "Tenebris", "lys dandelion / tenebris": "Tenebris",
    "okayama": "Okayama", "raien shogo enjaku blacksheep": "Okayama", "raien shogo enjaku": "Okayama", "shogo enjaku": "Okayama", "raien": "Okayama", "vesper": "Okayama", "okayama [ash]": "Okayama", "𝓞𝓴𝓪𝔂𝓪𝓶𝓪 [ASH]": "Okayama",
    "velka valcyrion": "Velka Valcyrion", "norxas": "Velka Valcyrion",
    "magon baldor": "Magon Baldor", "sw dark325": "Magon Baldor", "swdark325": "Magon Baldor",
    "vosk sulyvan": "Vosk Sulyvan", "sulyvan vosk": "Vosk Sulyvan", "sulyvan vosk hussh": "Vosk Sulyvan", "hussh": "Vosk Sulyvan", "hush": "Vosk Sulyvan",
    "aether": "Æther", "æther": "Æther", "miklelait": "Æther", "mikle": "Æther",
    "orla kalem crowley": "Kalem Crowley", "orla": "Kalem Crowley", "orla_": "Kalem Crowley", "eldren gates": "Eldren Gates",
    "yunah aoi enjaku": "Yunah Aoi Enjaku", "jap yunah aoi enjaku": "Yunah Aoi Enjaku", "jaaapaannnnnnnnnnn": "Yunah Aoi Enjaku", "japaaaan": "Yunah Aoi Enjaku", "japan": "Yunah Aoi Enjaku", "jap": "Yunah Aoi Enjaku",


    # Webhook entities & System Narrators
    "par-dela le voile": "Oeil", "par dela le voile": "Oeil", "par-delà le voile": "Oeil", "par delà le voile": "Oeil",
    "que le seigneur ouvre": "Oeil", "le seigneur ouvre": "Oeil",
    "le conseiller": "LE CONSEILLER", "conseiller": "LE CONSEILLER",
    "owl le messager": "OWL LE MESSAGER", "owl": "OWL LE MESSAGER",
    "l'oeil": "Oeil", "l'œil": "Oeil", "loeil": "Oeil", "lœil": "Oeil", "oeil": "Oeil",
    "les missives": "LES MISSIVES", "missive": "LES MISSIVES"
}

# Roles strictly assigned based on Discord Role IDs (Webhooks are classified dynamically as PNJ)
CHARACTER_METADATA_V2 = {
    # Main Guilds
    "Adelina Del Fuego": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Aegnor Othar": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Akane Tsukishiro": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Arun Acharya": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Aryanna Erhendil": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Astreüs Mylonas": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Bozdag Dermirhan": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Brutus Redwitch": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Cassian Ortie": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "MAIN_PC"},
    "Emil Camille Rebenok": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Frey Guðfrøðr": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Hector Swaft": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "PNJ"},
    "Hedwig Von Glanzestern": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "MAIN_PC"},
    "Inzu Sravel": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "PNJ"},
    "Iscarioth": {"role": "L'œil", "color": "#cbd5e1", "status": "MAIN_PC"},
    "Isis Faerieth": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Ivara Luella": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "MAIN_PC"},
    "Jasp Nah": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Jin Alurantes": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Kalem Crowley": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Katelynn Hoffmann": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},

    "Lewis Bamer": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Lumia Faendharts": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Maëll Fol'Dun": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Milli Enga": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "PNJ"},
    "Myrea M": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "MAIN_PC"},
    "Nick Sol": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Ren Urugaki": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Selena Moon": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Septimus Kales": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Tarrion Tombetoile": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Tenebris": {"role": "L'œil", "color": "#cbd5e1", "status": "MAIN_PC"},
    "Tsutomu Yamamoto": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "PNJ"},
    "Velka Valcyrion": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Æther": {"role": "L'œil", "color": "#cbd5e1", "status": "MAIN_PC"},

    # Faction Roles (Real Player Discord Roles)
    "Asior Eveus": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Idelmée Cadree": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "MAIN_PC"},
    "Junko Anarchy": {"role": "Voile d'Ivoire", "color": "#fef08a", "status": "MAIN_PC"},
    "Kenji Takahashi": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Loyis Delacroix": {"role": "La Garde Pourpre", "color": "#ef4444", "status": "MAIN_PC"},
    "Lucia Fiorella": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Okayama": {"role": "Sans guilde", "color": "#eab308", "status": "MAIN_PC"},
    "Red Roadman": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Vosk Sulyvan": {"role": "Sans guilde", "color": "#eab308", "status": "MAIN_PC"},
    "Ragde Umbras": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Yunah Aoi Enjaku": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},
    "Eldren Gates": {"role": "Cercle d'Azur", "color": "#3b82f6", "status": "MAIN_PC"},

    # Webhooks (System & PNJ entities)
    "Rias Valdor": {"role": "PNJ", "color": "#c084fc", "status": "PNJ"},
    "Captain Hook": {"role": "PNJ", "color": "#c084fc", "status": "PNJ"},
    "L'Ost du Sang": {"role": "PNJ", "color": "#c084fc", "status": "PNJ"},
    "LE MONARQUE DU SILENCE": {"role": "PNJ", "color": "#c084fc", "status": "PNJ"},
    "Regisseur du Centre de l'Histoire": {"role": "PNJ", "color": "#c084fc", "status": "PNJ"},
    "Oeil": {"role": "PNJ", "color": "#c084fc", "status": "SYSTEM"},
    "L'Oeil": {"role": "PNJ", "color": "#c084fc", "status": "SYSTEM"},
    "LE CONSEILLER": {"role": "PNJ", "color": "#c084fc", "status": "SYSTEM"},
    "OWL LE MESSAGER": {"role": "PNJ", "color": "#c084fc", "status": "SYSTEM"},
    "LES MISSIVES": {"role": "PNJ", "color": "#c084fc", "status": "SYSTEM"},
    "Narrateur": {"role": "PNJ", "color": "#c084fc", "status": "SYSTEM"}
}

VALID_FACTION_ROLES = {"L'œil", "Cercle d'Azur", "La Garde Pourpre", "Voile d'Ivoire", "JAVUS", "Sans guilde", "PNJ", "Indéfini"}

def clean_key_v2(s):
    if not s: return ""
    s = unicodedata.normalize('NFD', str(s).lower())
    s = re.sub(r'[\u0300-\u036f]', '', s)
    return re.sub(r'[^a-z0-9]', '', s)

LOOKUP_V2 = {clean_key_v2(k): v for k, v in CANONICAL_MAP.items()}

from guild_resolver import resolve_role_from_member_roles, is_pnj_character, load_manual_overrides, get_manual_override, get_guild_info

def get_canonical_name_v2(raw_name):
    if not raw_name:
        return "Narrateur"

    raw_str = str(raw_name).strip()
    raw_lower = raw_str.lower()

    if any(m_bot in raw_lower for m_bot in SYSTEM_MODERATION_BOTS):
        return "Narrateur"

    # Vérification Prioritaire des surcharges manuelles (ID Discord, pseudo ou nom RP brut)
    override = get_manual_override(raw_str)
    if override and override.get("character_name"):
        return override["character_name"]
    
    match = re.search(r'\((.*?)\)', raw_str)
    if match and len(match.group(1).strip()) >= 3:
        inside = match.group(1).strip()
        ck_inside = clean_key_v2(inside)
        if ck_inside in LOOKUP_V2:
            return LOOKUP_V2[ck_inside]

    name_clean = re.sub(r'\[.*?\]', '', raw_str).strip()
    ck = clean_key_v2(name_clean)

    if ck in LOOKUP_V2:
        return LOOKUP_V2[ck]

    if re.match(r'^j+a+p+a+n+.*$|^j+a+p+$', ck):
        return "Yunah Aoi Enjaku"

    for k, v in LOOKUP_V2.items():
        if len(k) >= 4 and (k in ck or ck in k):
            return v

    return name_clean if name_clean else "Narrateur"

def build_unified_characters_dict_v2(all_scenes):
    scene_actors_counts = {}
    scene_messages_counts = {}

    for scene in all_scenes:
        actors = scene.get('actors', [])
        for act in actors:
            scene_actors_counts[act] = scene_actors_counts.get(act, 0) + 1

        for msg in scene.get('messages', []):
            author = msg.get('author')
            if author:
                scene_messages_counts[author] = scene_messages_counts.get(author, 0) + 1

    dynamic_factions = {}
    if os.path.exists("discord_member_factions.json"):
        try:
            with open("discord_member_factions.json", "r", encoding="utf-8") as f:
                dynamic_factions = json.load(f)
        except Exception:
            pass

    manual_overrides = load_manual_overrides()
    chars_dict = {}

    for act, s_count in scene_actors_counts.items():
        manual_entry = get_manual_override(act, manual_overrides)

        if manual_entry and manual_entry.get("guild"):
            role = manual_entry["guild"]
            _, color, _ = get_guild_info(role)
            status = "MAIN_PC"
        elif is_pnj_character(act):
            role = "PNJ"
            color = "#c084fc"
            status = "PNJ"
        elif act in dynamic_factions:
            dyn_info = dynamic_factions[act]
            if isinstance(dyn_info, (list, tuple)):
                role, color = dyn_info[0], dyn_info[1]
            elif isinstance(dyn_info, dict):
                role, color = dyn_info.get("role", "Indéfini"), dyn_info.get("color", "#94a3b8")
            else:
                role, color = "Indéfini", "#94a3b8"
            status = "MAIN_PC"
        elif act in CHARACTER_METADATA_V2:
            meta = CHARACTER_METADATA_V2[act]
            role = meta["role"]
            color = meta["color"]
            status = meta["status"]
        else:
            role = "Indéfini"
            color = "#94a3b8"
            status = "MAIN_PC"

        chars_dict[act] = {
            "name": act,
            "role": role,
            "color": color,
            "status": status,
            "totalScenes": s_count,
            "totalMessages": scene_messages_counts.get(act, 0)
        }

    return chars_dict

