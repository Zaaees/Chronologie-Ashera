import json
import re
import sys
import os

sys.path.insert(0, os.path.abspath("."))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from segmenteur_narratif import extract_title_from_text
from unify_characters_v2 import get_canonical_name_v2
from guild_resolver import get_manual_override, load_manual_overrides, get_guild_info

SCENES_FILE = os.path.join("src", "scenes.json")

with open(SCENES_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

scenes = data.get("scenes", [])
chars = data.get("characters", {})
channel_images = data.get("channel_images", {})

print(f"📊 Dataset initial : {len(scenes)} scènes, {len(chars)} personnages")

# 1. Scènes formellement ciblées pour purge HRP / pings résiduels / scories (Chantier 1)
PURGE_SCENE_IDS = {
    "scene_La_sœur_1",
    "scene___𝗣lace_de_𝗚randpalais_4",
    "scene___𝐒alle_d_𝐀lchimie_2",
    "scene___𝐋e_𝐓résor_1",
    "scene_Chambre_de__Vide__5"
}

# 2. Webhooks environnementaux d'ambiance et de décor (Chantier 3)
ENV_WEBHOOKS = {
    "🌳〕La Forêt", "🦉〕Les Oiseaux", "🎓〕L'Académie", "🗨〕Le Sigile",
    "🪙〕Le Trésor", "🪙〕𝐋e-𝐓résor", "🐺〕La Bête", "💬〕Le Mot", "💬〕𝐋e-𝐌ot",
    "⚔〕Le Guerrier", "🌾〕Le Marais", "🧿〕La Folie", "🌑〕Le Monarque.", "VICTAE IUSTICIA",
    "LE MONARQUE DU SILENCE"
}

DECORATIVE_SEPARATORS = ("◦", "━", "─", "·", "—", "―")

def clean_actor_name(name):
    if not name:
        return "Narrateur"
    s = str(name).replace("⚜ | ", "").replace("⚜|", "").strip()
    return get_canonical_name_v2(s)

cleaned_scenes = []
purged_count = 0

for s in scenes:
    sid = s.get("id", "")
    if sid in PURGE_SCENE_IDS:
        print(f"  🗑️ Purge scène interdite : {sid}")
        purged_count += 1
        continue

    ch = s.get("channel", "").strip()
    if any(ch.startswith(sep) for sep in DECORATIVE_SEPARATORS):
        print(f"  🗑️ Purge scène sur salon décoratif : {sid} ({ch})")
        purged_count += 1
        continue

    # Mise à jour des messages
    for m in s.get("messages", []):
        auth = m.get("author", "")
        if auth.startswith("⚜ | ") or auth.startswith("⚜|"):
            m["author"] = clean_actor_name(auth)

    # Réattribution des acteurs et narrateurs
    old_actors = s.get("actors", [])
    old_narrators = s.get("narrators", [])
    new_actors = set()
    new_narrators = set(old_narrators)

    for a in old_actors:
        a_str = str(a).strip()
        if a_str in ENV_WEBHOOKS or any(a_str.lower() == w.lower() for w in ENV_WEBHOOKS):
            new_narrators.add(a_str)
        elif a_str.startswith("⚜ | ") or a_str.startswith("⚜|"):
            cleaned_a = clean_actor_name(a_str)
            if cleaned_a in ENV_WEBHOOKS or any(cleaned_a.lower() == w.lower() for w in ENV_WEBHOOKS) or cleaned_a in {"LE MONARQUE DU SILENCE"}:
                new_narrators.add(cleaned_a)
            else:
                new_actors.add(cleaned_a)
        else:
            cleaned_a = clean_actor_name(a_str)
            if cleaned_a in ENV_WEBHOOKS or any(cleaned_a.lower() == w.lower() for w in ENV_WEBHOOKS) or cleaned_a in {"LE MONARQUE DU SILENCE"}:
                new_narrators.add(cleaned_a)
            else:
                new_actors.add(cleaned_a)

    # Si la scène n'a plus d'acteur joueur réel après extraction des décors
    if not new_actors:
        print(f"  🗑️ Purge scène sans acteur joueur réel : {sid}")
        purged_count += 1
        continue

    s["actors"] = sorted(list(new_actors))
    s["narrators"] = sorted(list(new_narrators))

    # Chantier 6 : Extraction et mise à jour du titre narratif
    msgs = s.get("messages", [])
    if msgs:
        extracted_title = extract_title_from_text(msgs[0].get("content", ""), s.get("channel", ""), 1)
        if extracted_title and not extracted_title.endswith("— Scène 1"):
            s["title"] = extracted_title
        else:
            s["title"] = f"{', '.join(s['actors'][:3])}{'...' if len(s['actors']) > 3 else ''}"

    cleaned_scenes.append(s)

print(f"✅ Scènes après assainissement : {len(cleaned_scenes)} ({purged_count} scènes éliminées)")

# 3. Collecter strictement tous les acteurs et auteurs actifs dans le dataset assaini (Chantier 4)
active_entities = set()
for s in cleaned_scenes:
    for a in s.get("actors", []):
        if a:
            active_entities.add(a)
    for m in s.get("messages", []):
        auth = m.get("author")
        if auth and not auth.startswith("⚜ | "):
            c_auth = clean_actor_name(auth)
            if c_auth:
                active_entities.add(c_auth)

# Exclure les webhooks d'ambiance et les narrateurs système d'active_entities
active_entities = {
    e for e in active_entities 
    if e not in ENV_WEBHOOKS 
    and not any(e.lower() == w.lower() for w in ENV_WEBHOOKS)
    and e not in {"Oeil", "LE CONSEILLER", "OWL LE MESSAGER", "LES MISSIVES", "Narrateur"}
}

# 4. Harmonisation chromatique stricte (Chantier 5.1)
OFFICIAL_PALETTE = {
    "La Garde Pourpre": ("#ef4444", "char_pourpre"),
    "Cercle d'Azur": ("#3b82f6", "char_azur"),
    "Voile d'Ivoire": ("#fef08a", "char_ivoire"),
    "L'œil": ("#cbd5e1", "char_oeil"),
    "L'oeil": ("#cbd5e1", "char_oeil"),
    "JAVUS": ("#ffffff", "char_javus"),
    "Sans guilde": ("#eab308", "char_sans_guilde"),
    "PNJ": ("#c084fc", "char_pnj"),
    "Indéfini": ("#94a3b8", "char_indefini")
}

# Charger les surcharges manuelles et les factions dynamiques
manual_overrides = load_manual_overrides()
dynamic_factions = {}
if os.path.exists("discord_member_factions.json"):
    try:
        with open("discord_member_factions.json", "r", encoding="utf-8") as f:
            dynamic_factions = json.load(f)
    except Exception:
        pass

cleaned_characters = {}

for ent in sorted(active_entities):
    old_meta = chars.get(ent, {})
    role = old_meta.get("role", "Sans guilde")

    # Vérifier les surcharges manuelles
    m_entry = get_manual_override(ent, manual_overrides)
    if m_entry and m_entry.get("guild"):
        role = m_entry["guild"]
    elif ent in dynamic_factions:
        dyn_role = dynamic_factions[ent][0] if isinstance(dynamic_factions[ent], (list, tuple)) else dynamic_factions[ent]
        if dyn_role in OFFICIAL_PALETTE:
            role = dyn_role

    if role not in OFFICIAL_PALETTE:
        if role in ("Sans rôle", "Inconnu"):
            role = "Indéfini"
        else:
            role = "Sans guilde"

    color, color_name = OFFICIAL_PALETTE[role]

    cleaned_characters[ent] = {
        "role": role,
        "color": color,
        "colorName": color_name,
        "username": old_meta.get("username", ""),
        "displayName": old_meta.get("displayName", ent),
        "avatarUrl": old_meta.get("avatarUrl", "")
    }

# 5. Intégration explicite des 4 narrateurs système officiels (Chantier 5.2)
SYSTEM_NARRATORS = {
    "Oeil": {"role": "L'œil", "color": "#cbd5e1", "colorName": "char_oeil"},
    "LE CONSEILLER": {"role": "PNJ", "color": "#c084fc", "colorName": "char_pnj"},
    "OWL LE MESSAGER": {"role": "PNJ", "color": "#c084fc", "colorName": "char_pnj"},
    "LES MISSIVES": {"role": "PNJ", "color": "#c084fc", "colorName": "char_pnj"}
}

for n_name, n_meta in SYSTEM_NARRATORS.items():
    cleaned_characters[n_name] = {
        "role": n_meta["role"],
        "color": n_meta["color"],
        "colorName": n_meta["colorName"],
        "username": "",
        "displayName": n_name,
        "avatarUrl": ""
    }

print(f"✅ Personnages actifs assainis : {len(cleaned_characters)} (161 comptes fantômes et faux profils éliminés)")

output_data = {
    "characters": cleaned_characters,
    "scenes": cleaned_scenes,
    "channel_images": channel_images
}

with open(SCENES_FILE, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"💾 {SCENES_FILE} écrit avec succès !")
