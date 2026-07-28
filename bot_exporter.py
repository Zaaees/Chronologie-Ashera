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

# Helper pour nettoyer le nom du personnage (issu de parser_html.py)
def clean_character_name(name):
    if not name:
        return "Narrateur"

    name = unicodedata.normalize('NFKD', str(name))
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

# Ordre de priorité des Rôles Faction Discord
FACTION_ROLE_PRIORITY = [
    1327646236760608803, # La Garde Pourpre
    1327646236760608802, # Cercle d'Azur
    1327646236760608801, # Voile d'Ivoire
    1467532532261322813, # L'œil
    1475090340557095003  # Sans guilde
]

FACTION_INFO = {
    1327646236760608803: ("La Garde Pourpre", "#b40000", "char_pourpre"),
    1327646236760608802: ("Cercle d'Azur", "#305ed3", "char_azur"),
    1327646236760608801: ("Voile d'Ivoire", "#ffffd4", "char_ivoire"),
    1467532532261322813: ("L'œil", "#0e0d0d", "char_oeil"),
    1475090340557095003: ("Sans guilde", "#e2ce7d", "char_sans_guilde")
}

detected_member_factions = {}
detected_member_details = {}

def register_member_faction(name_str, faction_info, username="", display_name=""):
    if not name_str:
        return
    cleaned = clean_character_name(name_str)
    if cleaned and len(cleaned) < 50:
        detected_member_factions[cleaned] = faction_info
        if username or display_name:
            detected_member_details[cleaned] = {
                "username": username,
                "displayName": display_name
            }
    
    parts = re.split(r'[\(\)\-\—\•\|]', name_str)
    for p in parts:
        c_part = clean_character_name(p)
        if c_part and len(c_part) < 50:
            detected_member_factions[c_part] = faction_info
            if username or display_name:
                detected_member_details[c_part] = {
                    "username": username,
                    "displayName": display_name
                }

SYSTEM_BOTS = [
    'narrateur', 'narration', 'draftbot', 'ticket tool', 'tupperbox',
    'raidprotect', 'sakuraki', 'jockie', 'liste du rp fr', 'profile', 'koya'
]

LEGITIMATE_PNJ_KEYWORDS = [
    'javus', 'conseiller', 'owl', 'messager', 'missive', 'les missives',
    'monarque', 'infranchissable', 'déesse-mère', 'deesse-mere', 'prince lunaire',
    'prince azur', 'prince du vide', 'roi des rampants', 'nephilim'
]

def get_character_guild_and_color(actor_name):
    clean_name = clean_character_name(actor_name)
    name_lower = clean_name.lower()

    # 1. Ignorer complètement les bots système et utilitaires
    if any(bot_name in name_lower for bot_name in SYSTEM_BOTS):
        return None, None, None

    # 2. PNJ RP officiels
    if any(pnj_kw in name_lower for pnj_kw in LEGITIMATE_PNJ_KEYWORDS) or clean_name in ['JAVUS', 'LE CONSEILLER', 'OWL LE MESSAGER', 'LES MISSIVES', 'LE MONARQUE DU SILENCE', 'L\'Infranchissable', 'La Déesse-Mère']:
        return "PNJ", "#a855f7", "char_pnj"

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

    # 4. Fiches de personnages
    fiche_keywords = ['fiche', 'chambre', 'dortoir', 'effectif', 'profil', 'candidature', 'presentation', 'perso', 'valide']
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

EXPLICIT_START_REGEX = re.compile(
    r'(```ansi.*🎭|#\s+⊱═─────|```\s*🎭|◦\s*─────────────\s*¤)',
    re.IGNORECASE | re.DOTALL
)

from ai_narrative_segmenter import segment_messages_into_scenes_ai

# Segmentation des messages en scènes (100% IA Narrative)
def segment_messages_into_scenes(channel_name, channel_id, messages, guild_id_str):
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
        return create_scene_dict(ch_name, ch_id, idx, sub_tuples, guild_id_str)

    scenes = segment_messages_into_scenes_ai(channel_name, channel_id, valid_msgs, scene_builder)

    clean_scenes = []
    for idx, s in enumerate(scenes, start=1):
        msgs = s.get("messages", [])
        if idx == 1 and len(msgs) == 1:
            first_author = msgs[0].get("author", "").strip().lower()
            if "conseiller" in first_author:
                continue
        clean_scenes.append(s)

    return clean_scenes

def create_scene_dict(channel_name, channel_id, scene_index, messages_tuples, guild_id_str, category_name=""):
    messages = [t[0] for t in messages_tuples]
    texts = [t[1] for t in messages_tuples]

    actors = list({clean_character_name(m['author']) for m in messages if m.get('author') and not any(b in m['author'].lower() for b in SYSTEM_BOTS)})
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
            async for member in target_guild.fetch_members(limit=None):
                member_role_ids = [r.id for r in member.roles]
                best_role = None
                for pid in FACTION_ROLE_PRIORITY:
                    if pid in member_role_ids:
                        best_role = pid
                        break
                
                if best_role:
                    faction_info = FACTION_INFO[best_role]
                    register_member_faction(member.display_name, faction_info, username=member.name, display_name=member.display_name)
                    if member.name:
                        register_member_faction(member.name, faction_info, username=member.name, display_name=member.display_name)
                    global_name = getattr(member, 'global_name', None)
                    if global_name:
                        register_member_faction(global_name, faction_info, username=member.name, display_name=member.display_name)
            print(f"✅ {len(detected_member_factions)} correspondances nom/pseudo -> faction identifiées.")
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
                                        msg_authors.add(cleaned_a)
                            s['actors'] = list(msg_authors)

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

        # 4. Recherche ciblée des fils archivés uniquement pour les salons RP modifiés
        my_permissions = target_guild.me.guild_permissions if target_guild.me else None
        
        for ch in rp_channels:
            ch_id = str(ch.id)
            ch_name = ch.name
            last_id = last_msg_id_by_channel.get(ch_id) or last_msg_id_by_channel.get(ch_name)
            ch_last_msg_id = getattr(ch, 'last_message_id', None)

            # Si le salon n'a aucun nouveau message depuis le dernier export, sauter la recherche de threads archivés !
            if last_id and ch_last_msg_id and ch_last_msg_id <= int(last_id):
                continue

            if hasattr(ch, 'archived_threads'):
                if my_permissions and not ch.permissions_for(target_guild.me).read_message_history:
                    continue
                try:
                    async def fetch_archived_for_channel(channel_obj):
                        threads_found = []
                        try:
                            async for arch_thread in channel_obj.archived_threads(limit=100):
                                if not is_character_or_fiche_channel(arch_thread):
                                    threads_found.append(arch_thread)
                        except Exception:
                            pass
                        return threads_found

                    arch_threads = await asyncio.wait_for(fetch_archived_for_channel(ch), timeout=2.0)
                    for arch_thread in arch_threads:
                        if arch_thread not in channels_to_process:
                            channels_to_process.append(arch_thread)
                except Exception:
                    pass

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

            after_obj = discord.Object(id=int(last_id)) if last_id else None

            # Limiter l'historique sur les salons HRP/Généraux/Staff/Jeux/Bots/Demandes
            history_limit = None
            ch_normalized = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFKD', ch_name)).lower()
            if any(x in ch_normalized for x in ["general", "staff", "medias", "commandes", "logs", "bot", "ticket", "jeux", "jeu", "hrp", "demande", "question", "spoil", "suggestion"]):
                history_limit = 100

            raw_messages = []
            try:
                # Si after est spécifié, n'extraire que les nouveaux messages
                async for msg in channel.history(limit=history_limit, after=after_obj, oldest_first=True):
                    # Déterminer le nom de l'auteur (affichage/surnom si disponible)
                    author_name = msg.author.display_name if hasattr(msg.author, 'display_name') else msg.author.name
                    
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
                    if msg.embeds:
                        titles = [e.title for e in msg.embeds if e.title]
                        descs = [e.description for e in msg.embeds if e.description]
                        embed_title = " | ".join(titles)
                        embed_desc = " | ".join(descs)

                    # Format du timestamp ISO
                    ts_iso = msg.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

                    raw_messages.append({
                        "id": str(msg.id),
                        "author": author_name,
                        "timestamp": ts_iso,
                        "content": content,
                        "embed_title": embed_title,
                        "embed_description": embed_desc
                    })

                if after_obj and len(raw_messages) == 0:
                    old_scenes = existing_scenes_by_channel.get(ch_id) or existing_scenes_by_channel.get(ch_name) or []
                    print(f"  -> ⏩ Aucune nouveauté ({len(old_scenes)} scènes conservées).")
                    all_scenes.extend(old_scenes)
                else:
                    channel_scenes = segment_messages_into_scenes(ch_name, ch_id, raw_messages, str(target_guild.id))
                    old_scenes = existing_scenes_by_channel.get(ch_id) or existing_scenes_by_channel.get(ch_name) or [] if after_obj else []
                    merged_scenes = old_scenes + channel_scenes
                    print(f"  -> {len(raw_messages)} message(s) lu(s) ({len(merged_scenes)} scène(s) au total).")
                    all_scenes.extend(merged_scenes)

            except Exception as e:
                print(f"  -> ⚠️ ERREUR lors de la lecture du salon #{ch_name}: {e}")

        # Trier les scènes par date de début
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
                    "displayName": details.get('displayName', '')
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
                    "displayName": details.get('displayName', '')
                }
                valid_actors.add(char_name)

        for scene in all_scenes:
            scene['actors'] = [a for a in scene['actors'] if a in valid_actors]

        output_data = {
            "characters": character_map,
            "scenes": all_scenes
        }

        # Sauvegarder dans scenes.json
        output_filename = "scenes.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Sauvegarder dans src/scenes.json
        src_scenes_path = os.path.join("src", "scenes.json")
        if os.path.isdir("src"):
            with open(src_scenes_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Fichier React mis à jour : {src_scenes_path}")

        # Sauvegarder dans data.js
        js_filename = "data.js"
        with open(js_filename, 'w', encoding='utf-8') as f:
            f.write("window.rpData = ")
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            f.write(";\n")

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
