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
    'LE CONSEILLER', 'OWL LE MESSAGER', 'LES MISSIVES', 'NARRATEUR', 'HECTOR SWAFT',
    'INZU SRAVEL', 'MILLI ENGA', 'TSUTOMU YAMAMOTO'
}

def resolve_role_from_member_roles(member_role_ids):
    """
    FONCTION DÉTERMINISTE 100% ROBOTIQUE.
    Prend en entrée la liste des IDs de rôles Discord (member.roles) d'un membre/joueur
    et retourne strictement le triplet (nom_guilde, couleur_hex, nom_couleur)
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
    return any(kw in lower for kw in ['pnj', 'narrat', 'bot', 'conseiller', 'messager', 'missive', 'monarque'])
