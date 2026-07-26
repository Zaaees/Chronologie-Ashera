import os
import sys
import re
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
import discord

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID_STR = os.getenv("DISCORD_GUILD_ID")

if not TOKEN or not GUILD_ID_STR:
    print("❌ Token Discord ou GUILD_ID manquant dans le .env")
    sys.exit(1)

GUILD_ID = int(GUILD_ID_STR)

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

OUTPUT_DIR = "public/channel_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

channel_images_map = {}

def clean_filename(name):
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_name = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    clean = re.sub(r'[^\w\-]', '_', ascii_name)
    clean = re.sub(r'_+', '_', clean).strip('_').lower()
    return clean

async def download_image(url, destination_path, session):
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.read()
                with open(destination_path, 'wb') as f:
                    f.write(data)
                print(f"  ✓ Image sauvegardée localement : {destination_path}")
                return True
    except Exception as e:
        print(f"  ❌ Erreur téléchargement : {e}")
    return False

@client.event
async def on_ready():
    print(f"🤖 Bot connecté : {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        try:
            guild = await client.fetch_guild(GUILD_ID)
        except Exception as e:
            print(f"❌ Serveur non trouvé : {e}")
            await client.close()
            return

    print(f"🏰 Extraction sur le serveur : {guild.name}")

    # Récupération des salons RP réellement présents dans scenes.json
    valid_rp_channels = set()
    if os.path.exists("scenes.json"):
        with open("scenes.json", 'r', encoding='utf-8') as f:
            sdata = json.load(f)
            valid_rp_channels = set(s['channel'] for s in sdata.get('scenes', []))

    async with aiohttp.ClientSession() as session:
        text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel) and ch.name in valid_rp_channels]
        print(f"📊 {len(text_channels)} salons textuels RP trouvés sur le serveur Discord.")

        for channel in text_channels:
            ch_clean = clean_filename(channel.name)
            img_filename = f"{ch_clean}.jpg"
            img_local_path = os.path.join(OUTPUT_DIR, img_filename)
            rel_web_path = f"/channel_images/{img_filename}"

            print(f"\n# Inspection #{channel.name}...")
            found_image = False

            # Inspection de la PLUS ANCIENNE ÉPINGLE (Bannière officielle du salon)
            try:
                pins = [p async for p in channel.pins()]
                # On inverse la liste des épingles pour traiter de la PLUS ANCIENNE à la plus récente
                for p in reversed(pins):
                    image_url = None

                    # 1. Vérifier les pièces jointes (attachments)
                    if p.attachments:
                        for att in p.attachments:
                            if any(att.filename.lower().split('?')[0].endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                image_url = att.url
                                break

                    # 2. Vérifier les embeds (images intégrées dans un embed Discord)
                    if not image_url and p.embeds:
                        for emb in p.embeds:
                            if emb.image and emb.image.url:
                                image_url = emb.image.url
                                break
                            elif emb.thumbnail and emb.thumbnail.url:
                                image_url = emb.thumbnail.url
                                break

                    if image_url:
                        ok = await download_image(image_url, img_local_path, session)
                        if ok:
                            channel_images_map[channel.name] = rel_web_path
                            found_image = True
                            break
            except Exception as e:
                print(f"  ⚠️ Erreur lors de l'accès aux épingles de #{channel.name}: {e}")

    print(f"\n✨ {len(channel_images_map)} images de salons RP téléchargées depuis les épingles !")

    # Mise à jour des JSONs
    for json_file in ["scenes.json", "src/scenes.json"]:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                data['channel_images'] = channel_images_map
                for scene in data.get('scenes', []):
                    ch = scene.get('channel')
                    if ch in channel_images_map:
                        scene['location_image'] = channel_images_map[ch]

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                print(f"✅ Mis à jour {json_file}")
            except Exception as e:
                print(f"❌ Erreur sur {json_file}: {e}")

    await client.close()

if __name__ == '__main__':
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"❌ Erreur bot: {e}")
