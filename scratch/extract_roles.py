import os
import re
import sys
from collections import defaultdict

# Reconfigure console output encoding to utf-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def parse_html_files(export_folder):
    # Regex designed to extract authors, supporting color styled names
    author_pattern = re.compile(
        r'<span class=chatlog__author\s+'
        r'(?:style=color:rgb\((\d+),(\d+),(\d+)\)\s+)?'
        r'title=(?:"([^"]+)"|([^ >]+))\s+'
        r'data-user-id=(\d+)>'
        r'([^<]+)</span>'
    )
    
    users = {}
    
    html_files = [f for f in os.listdir(export_folder) if f.endswith('.html')]
    print(f"Analyzing {len(html_files)} HTML export files...")
    
    for filename in html_files:
        file_path = os.path.join(export_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            matches = author_pattern.findall(content)
            for m in matches:
                r, g, b, t1, t2, user_id, nickname = m
                username = t1 if t1 else t2
                
                # Normalize color
                if r and g and b:
                    color = (int(r), int(g), int(b))
                else:
                    color = (255, 255, 255) # default white
                    
                nickname = nickname.strip()
                username = username.strip()
                
                if user_id not in users:
                    users[user_id] = {
                        "usernames": {username},
                        "nicknames": {nickname},
                        "color": color
                    }
                else:
                    users[user_id]["usernames"].add(username)
                    users[user_id]["nicknames"].add(nickname)
                    if color != (255, 255, 255) and users[user_id]["color"] == (255, 255, 255):
                        users[user_id]["color"] = color
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return users

def main():
    export_folder = "Export"
    users = parse_html_files(export_folder)
    
    print(f"\nFound {len(users)} unique participants in the logs!")
    
    # Group by color
    color_groups = defaultdict(list)
    for uid, data in users.items():
        color_groups[data["color"]].append((uid, data))
        
    print(f"\n--- GROUPS BY ROLE COLOR ---")
    
    # Sort groups by size
    sorted_colors = sorted(color_groups.keys(), key=lambda c: len(color_groups[c]), reverse=True)
    
    for color in sorted_colors:
        members = color_groups[color]
        if color == (255, 255, 255):
            color_name = "Default/White (No custom role color)"
        else:
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            color_name = f"RGB{color} / Hex {hex_color}"
            
        print(f"\n[Color Group: {color_name} ({len(members)} member(s))]")
        for uid, m in members:
            nicknames_str = ", ".join(m["nicknames"])
            usernames_str = ", ".join(m["usernames"])
            print(f"  - Nickname(s): {nicknames_str} (Username: {usernames_str}, ID: {uid})")

if __name__ == "__main__":
    main()
