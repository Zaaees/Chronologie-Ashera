import os
import re
import sys

# Configure console output encoding to utf-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def parse_html_files(export_folder):
    author_pattern = re.compile(
        r'<span class=chatlog__author\s+'
        r'(?:style=color:rgb\((\d+),(\d+),(\d+)\)\s+)?'
        r'title=(?:"([^"]+)"|([^ >]+))\s+'
        r'data-user-id=(\d+)>'
        r'([^<]+)</span>'
    )
    
    users = {}
    html_files = [f for f in os.listdir(export_folder) if f.endswith('.html')]
    
    for filename in html_files:
        file_path = os.path.join(export_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            matches = author_pattern.findall(content)
            for m in matches:
                r, g, b, t1, t2, user_id, nickname = m
                username = t1 if t1 else t2
                
                if r and g and b:
                    color = (int(r), int(g), int(b))
                else:
                    color = (255, 255, 255)
                    
                nickname = nickname.strip()
                username = username.strip()
                
                # We normalize the nickname to remove emojis and prefixes for cleaner role matching
                clean_nick = re.sub(r'[^\w\s\-\'|]', '', nickname).strip()
                
                if user_id not in users:
                    users[user_id] = {
                        "usernames": {username},
                        "nicknames": {nickname},
                        "clean_nicks": {clean_nick},
                        "color": color
                    }
                else:
                    users[user_id]["usernames"].add(username)
                    users[user_id]["nicknames"].add(nickname)
                    users[user_id]["clean_nicks"].add(clean_nick)
                    if color != (255, 255, 255) and users[user_id]["color"] == (255, 255, 255):
                        users[user_id]["color"] = color
        except Exception as e:
            pass
            
    return users

def main():
    export_folder = "Export"
    users = parse_html_files(export_folder)
    
    # Standard colors
    # Cercle d'Azur: #305ed3 (48, 94, 211)
    # Voile d'Ivoire: #ffffd4 (255, 255, 212)
    # Sans guilde: #e2ce7d (226, 206, 125)
    # Garde Pourpre: #b40000 (180, 0, 0)
    # L'oeil: #0e0d0d (14, 13, 13)
    
    standard_colors = {
        (48, 94, 211),   # Cercle d'Azur
        (255, 255, 212), # Voile d'Ivoire
        (226, 206, 125), # Sans guilde
        (180, 0, 0),     # Garde Pourpre
        (14, 13, 13),     # L'oeil
        (255, 255, 255)  # White / Default
    }
    
    uncategorized = []
    
    for uid, data in users.items():
        color = data["color"]
        if color not in standard_colors:
            # We also filter out Bots or system accounts if any (like "LE CONSEILLER" or "OWL, LE MESSEGER")
            # by checking if nickname contains "CONSEILLER" or "MESSEGER" or "SYSTEM" or "MEMBER" or if it is a known BOT
            is_bot = False
            for nick in data["nicknames"]:
                if "CONSEILLER" in nick.upper() or "MESSEGER" in nick.upper() or "OWL" in nick.upper() or "MISSIVE" in nick.upper() or "SYSTEM" in nick.upper():
                    is_bot = True
                    break
            if not is_bot:
                uncategorized.append((uid, data))
                
    # Sort uncategorized by their primary clean nickname
    uncategorized.sort(key=lambda x: list(x[1]["clean_nicks"])[0])
    
    print(f"Found {len(uncategorized)} players with custom (uncategorized) colors:")
    for uid, data in uncategorized:
        hex_color = '#{:02x}{:02x}{:02x}'.format(*data["color"])
        # Get cleanest nickname
        nicks = [n for n in data["clean_nicks"] if n]
        nick = nicks[0] if nicks else list(data["nicknames"])[0]
        # Remove any leading pipes or symbols
        nick = re.sub(r'^[^\w]+', '', nick).strip()
        print(f"Actor: {nick} (Color: {hex_color}, Username: {list(data['usernames'])[0]})")

if __name__ == "__main__":
    main()
