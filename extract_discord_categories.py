from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot connecte en tant que {client.user}")
    
    mapping = {}
    
    for guild in client.guilds:
        print(f"Guilde : {guild.name} (ID: {guild.id})")
        
        guild_data = {}
        for category in guild.categories:
            cat_name = category.name
            guild_data[cat_name] = []
            print(f"\nCategorie : [{cat_name}]")
            
            for channel in category.channels:
                guild_data[cat_name].append({
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": str(channel.type)
                })
                print(f"   # {channel.name} (ID: {channel.id})")

        # Salons sans catégorie
        uncategorized = [ch for ch in guild.channels if ch.category is None]
        if uncategorized:
            guild_data["Sans Categorie"] = []
            print(f"\nCategorie : [Sans Categorie]")
            for ch in uncategorized:
                guild_data["Sans Categorie"].append({
                    "id": str(ch.id),
                    "name": ch.name,
                    "type": str(ch.type)
                })
                print(f"   # {ch.name} (ID: {ch.id})")

        mapping[guild.name] = guild_data

    with open("discord_server_structure.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        
    print("\nStructure des categories et salons sauvegardee dans discord_server_structure.json")
    await client.close()

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"Erreur lors de la connexion : {e}")
