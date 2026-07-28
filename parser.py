import os
import sys
import json
import re
from datetime import datetime

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from ai_narrative_segmenter import segment_messages_into_scenes_ai

def parse_character_name(author_name):
    match = re.search(r'\((.*?)\)', author_name)
    if match:
        return match.group(1).strip()
    return author_name.strip()

def segment_channel_into_scenes(channel_name, messages):
    if not messages:
        return []

    sorted_msgs = sorted(messages, key=lambda m: m['timestamp'])

    valid_msgs = []
    for m in sorted_msgs:
        content = m.get('content', '').strip()
        if content:
            valid_msgs.append((m, content))

    if not valid_msgs:
        return []

    def scene_builder(ch_name, ch_id, idx, sub_tuples):
        msgs_list = [t[0] for t in sub_tuples]
        return create_scene_object(ch_name, idx, msgs_list)

    return segment_messages_into_scenes_ai(channel_name, "0", valid_msgs, scene_builder)

def create_scene_object(channel_name, scene_index, messages):
    first_msg = messages[0]
    last_msg = messages[-1]

    actors = list({parse_character_name(m['author_name']) for m in messages})

    preview = first_msg['content']
    if len(preview) > 150:
        preview = preview[:147] + "..."

    return {
        "id": f"scene_{channel_name.replace('-', '_')}_{scene_index}",
        "channel": channel_name,
        "title": f"Scène {scene_index} - {', '.join(actors)}",
        "actors": actors,
        "start_time": first_msg['timestamp'],
        "end_time": last_msg['timestamp'],
        "preview": preview,
        "message_count": len(messages)
    }

def main():
    print("--- Démarrage du parsing des salons Discord RP ---")

    try:
        with open('sample_discord_export.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Erreur : Le fichier 'sample_discord_export.json' est introuvable.")
        return

    all_scenes = []

    for channel_data in data:
        channel_name = channel_data['channel_name']
        messages = channel_data['messages']
        print(f"Analyse du salon : #{channel_name} ({len(messages)} messages)...")

        channel_scenes = segment_channel_into_scenes(channel_name, messages)
        print(f"-> {len(channel_scenes)} scènes détectées.")
        all_scenes.extend(channel_scenes)

    all_scenes.sort(key=lambda s: s['start_time'])

    output_filename = 'scenes.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_scenes, f, indent=2, ensure_ascii=False)

    import unicodedata
    img_dir = "public/channel_images"
    channel_images_map = {}
    if os.path.exists(img_dir):
        img_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
        pub_clean_map = {}
        for f in img_files:
            base = os.path.splitext(f)[0]
            clean = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', base)).lower()
            pub_clean_map[clean] = f'channel_images/{f}'

        fallback_map = {
            'Isis et Astreüs': 'channel_images/serre-de-lune.jpg',
            'Scène Kalès / JAVUS': 'channel_images/arene-hurlante.jpg',
            'Scène Kalès / Kalem': 'channel_images/terrain-d-entrainement.jpg',
            'Scène Lumia | Ivara': 'channel_images/bibliotheque-azure.jpg',
            'TRIPLE A : Asior - Akane - Aryana': 'channel_images/le-bar-des-lions.jpg',
            '☁️〕𝗣ortail-𝗜voire': 'channel_images/couloir-blanc.jpg',
            '️〕Portail-Ivoire': 'channel_images/couloir-blanc.jpg',
            '🛏️  •  Salle de Réveil': 'channel_images/cellules.jpg'
        }

        for scene in all_scenes:
            ch = scene.get('channel')
            thread = scene.get('thread_name')

            img_url = None
            if ch in fallback_map:
                img_url = fallback_map[ch]
            else:
                ch_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', ch or '')).lower()
                for k, url in pub_clean_map.items():
                    if k and (k == ch_c or k in ch_c or ch_c in k):
                        img_url = url
                        break

            if not img_url and thread:
                th_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', thread)).lower()
                for k, url in pub_clean_map.items():
                    if k and (k == th_c or k in th_c or th_c in k):
                        img_url = url
                        break

            if img_url:
                if ch: channel_images_map[ch] = img_url
                if thread: channel_images_map[thread] = img_url
                scene['location_image'] = img_url

    src_scenes_path = os.path.join('src', 'scenes.json')
    if os.path.isdir('src'):
        with open(src_scenes_path, 'w', encoding='utf-8') as f:
            output_compatible = {
                "characters": {},
                "scenes": all_scenes,
                "channel_images": channel_images_map
            }
            json.dump(output_compatible, f, indent=2, ensure_ascii=False)
        print(f"💾 Fichier React compatible mis à jour : {src_scenes_path}")

    print(f"\nSuccès ! {len(all_scenes)} scènes au total ont été exportées dans '{output_filename}'.")

if __name__ == '__main__':
    main()
