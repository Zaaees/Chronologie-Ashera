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
    clean = re.sub(r'[^\w\-_]', '_', name).strip('_')
    return clean.lower()

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

    async with aiohttp.ClientSession() as session:
        text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
        print(f"📊 {len(text_channels)} salons textuels trouvés.")

        for channel in text_channels:
            ch_clean = clean_filename(channel.name)
            img_filename = f"{ch_clean}.jpg"
            img_local_path = os.path.join(OUTPUT_DIR, img_filename)
            rel_web_path = f"./channel_images/{img_filename}"

            print(f"\n# Inspection #{channel.name}...")
            found_image = False

            # 1. Epingles
            try:
                async for p in channel.pins():
                    if p.attachments:
                        for att in p.attachments:
                            if any(att.filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                ok = await download_image(att.url, img_local_path, session)
                                if ok:
                                    channel_images_map[channel.name] = rel_web_path
                                    found_image = True
                                    break
                    if found_image:
                        break
            except Exception:
                pass

            # 2. Premiers messages
            if not found_image:
                try:
                    async for msg in channel.history(limit=20, oldest_first=True):
                        if msg.attachments:
                            for att in msg.attachments:
                                if any(att.filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                    ok = await download_image(att.url, img_local_path, session)
                                    if ok:
                                        channel_images_map[channel.name] = rel_web_path
                                        found_image = True
                                        break
                        if found_image:
                            break
                except Exception as e:
                    print(f"  ⚠️ Limite d'accès sur #{channel.name}: {e}")

    print(f"\n✨ {len(channel_images_map)} images de salons téléchargées en local !")

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
