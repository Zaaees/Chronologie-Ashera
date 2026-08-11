import json
import re
import unicodedata
import os

# Ordre déterministe de priorité des Rôles Faction Discord
FACTION_ROLE_PRIORITY = [
    1327646236760608803, # La Garde Pourpre
    1327646236760608802, # Cercle d'Azur
    1327646236760608801, # Voile d'Ivoire
    1467532532261322813, # L'œil
    1525469197935841371, # JAVUS
    1475090340557095003  # Sans guilde
]

FACTION_INFO = {
    1327646236760608803: ("La Garde Pourpre", "#ef4444", "char_pourpre"),
    1327646236760608802: ("Cercle d'Azur", "#3b82f6", "char_azur"),
    1327646236760608801: ("Voile d'Ivoire", "#fef08a", "char_ivoire"),
    1467532532261322813: ("L'œil", "#cbd5e1", "char_oeil"),
    1525469197935841371: ("JAVUS", "#ffffff", "char_javus"),
    1475090340557095003: ("Sans guilde", "#eab308", "char_sans_guilde")
}

LEGITIMATE_PNJ_NAMES = {
    'RIAS VALDOR', 'CAPTAIN HOOK', "L'OST DU SANG", 'LE MONARQUE DU SILENCE',
    "REGISSEUR DU CENTRE DE L'HISTOIRE", 'OEIL', "L'OEIL", "L'ŒIL",
    'LE CONSEILLER', 'LE CONSEILLER', 'OWL LE MESSAGER', 'LES MISSIVES', 'NARRATEUR', 'HECTOR SWAFT',
    'HECTOR', 'INZU SRAVEL', 'MILLI ENGA', 'TSUTOMU YAMAMOTO'
}

MANUAL_OVERRIDES_FILES = ["Joueurs_Manuels.json", "joueurs_manuels.json", "manual_player_overrides.json"]

GUILD_COLOR_MAP = {
    "La Garde Pourpre": ("La Garde Pourpre", "#ef4444", "char_pourpre"),
    "Cercle d'Azur": ("Cercle d'Azur", "#3b82f6", "char_azur"),
    "Voile d'Ivoire": ("Voile d'Ivoire", "#fef08a", "char_ivoire"),
    "L'œil": ("L'œil", "#cbd5e1", "char_oeil"),
    "L'oeil": ("L'œil", "#cbd5e1", "char_oeil"),
    "L'œil": ("L'œil", "#cbd5e1", "char_oeil"),
    "JAVUS": ("JAVUS", "#ffffff", "char_javus"),
    "Sans guilde": ("Sans guilde", "#eab308", "char_sans_guilde"),
    "PNJ": ("PNJ", "#c084fc", "char_pnj"),
    "Indéfini": ("Indéfini", "#94a3b8", "char_indefini")
}

def get_guild_info(guild_name):
    """
    Retourne le triplet (nom_guilde, couleur_hex, nom_couleur) à partir du nom d'une guilde.
    """
    if not guild_name:
        return ("Indéfini", "#94a3b8", "char_indefini")
    
    g_strip = str(guild_name).strip()
    for key, info in GUILD_COLOR_MAP.items():
        if key.lower() == g_strip.lower():
            return info
            
    return (g_strip, "#94a3b8", "char_indefini")

def load_manual_overrides():
    """
    Charge le fichier Joueurs_Manuels.json.
    """
    for filepath in MANUAL_OVERRIDES_FILES:
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data.get("overrides", data)
            except Exception as e:
                print(f"⚠️ Erreur lors de la lecture de {filepath}: {e}")
    return {}


def clean_key_simple(s):
    if not s: return ""
    s = unicodedata.normalize('NFD', str(s).lower())
    s = re.sub(r'[\u0300-\u036f]', '', s)
    return re.sub(r'[^a-z0-9]', '', s)

def get_manual_override(identifier, manual_overrides=None):
    """
    Recherche si l'identifiant (pseudo, nom) existe dans les surcharges manuelles.
    Retourne le dictionnaire de surcharge ou None.
    """
    if manual_overrides is None:
        manual_overrides = load_manual_overrides()
    if not manual_overrides or not identifier:
        return None

    ident_str = str(identifier).strip()
    ck_ident = clean_key_simple(ident_str)
    if not ck_ident:
        return None

    # 1. Correspondance exacte ou par clé nettoyée (pseudo ou nom)
    if ident_str in manual_overrides:
        return manual_overrides[ident_str]

    for k, v in manual_overrides.items():
        if k == "__comment__":
            continue
        if clean_key_simple(k) == ck_ident:
            return v

    # 2. Correspondance sur le character_name contenu dans la surcharge
    for k, v in manual_overrides.items():
        if k == "__comment__":
            continue
        if isinstance(v, dict) and v.get("character_name"):
            c_name = v.get("character_name")
            if clean_key_simple(c_name) == ck_ident:
                return v

    return None

def resolve_role_from_member_roles(member_role_ids):
    """
    FONCTION DÉTERMINISTE 100% ROBOTIQUE.
    Prend en entrée la liste des IDs de rôles Discord (member.roles) d'un membre/joueur
    et retourne strictly le triplet (nom_guilde, couleur_hex, nom_couleur)
    d'après l'ordre de priorité strict. Sans aucune interprétation ni IA.
    """
    if not member_role_ids:
        return "Indéfini", "#94a3b8", "char_indefini"

    for role_id in FACTION_ROLE_PRIORITY:
        if role_id in member_role_ids:
            return FACTION_INFO[role_id]

    return "Indéfini", "#94a3b8", "char_indefini"

def is_pnj_character(character_name):
    if not character_name:
        return True
    up = character_name.upper().strip()
    if up in LEGITIMATE_PNJ_NAMES:
        return True
    lower = character_name.lower()
    return any(kw in lower for kw in ['pnj', 'narrat', 'bot', 'webhook', 'conseiller', 'swaft', 'monarque', 'regisseur'])




