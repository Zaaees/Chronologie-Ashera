import json
import re
from datetime import datetime

TIME_GAP_THRESHOLD_HOURS = 12

def parse_character_name(author_name):
    match = re.search(r'\((.*?)\)', author_name)
    if match:
        return match.group(1).strip()
    return author_name.strip()

def parse_iso_time(timestamp_str):
    clean_ts = timestamp_str.replace('Z', '+00:00')
    return datetime.fromisoformat(clean_ts)

def segment_channel_into_scenes(channel_name, messages):
    if not messages:
        return []

    sorted_msgs = sorted(messages, key=lambda m: m['timestamp'])

    scenes = []
    current_scene_msgs = [sorted_msgs[0]]
    scene_counter = 1

    for i in range(1, len(sorted_msgs)):
        prev_msg = sorted_msgs[i - 1]
        curr_msg = sorted_msgs[i]

        prev_time = parse_iso_time(prev_msg['timestamp'])
        curr_time = parse_iso_time(curr_msg['timestamp'])
        time_diff = (curr_time - prev_time).total_seconds() / 3600.0

        recent_actors = {parse_character_name(m['author_name']) for m in current_scene_msgs[-5:]}
        curr_actor = parse_character_name(curr_msg['author_name'])

        is_new_scene = False
        if time_diff >= TIME_GAP_THRESHOLD_HOURS:
            is_new_scene = True
        elif curr_actor not in recent_actors and time_diff >= 4.0:
            is_new_scene = True

        if is_new_scene:
            scenes.append(create_scene_object(channel_name, scene_counter, current_scene_msgs))
            scene_counter += 1
            current_scene_msgs = [curr_msg]
        else:
            current_scene_msgs.append(curr_msg)

    if current_scene_msgs:
        scenes.append(create_scene_object(channel_name, scene_counter, current_scene_msgs))

    return scenes

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

    import os
    src_scenes_path = os.path.join('src', 'scenes.json')
    if os.path.isdir('src'):
        with open(src_scenes_path, 'w', encoding='utf-8') as f:
            output_compatible = {
                "characters": {},
                "scenes": all_scenes
            }
            json.dump(output_compatible, f, indent=2, ensure_ascii=False)
        print(f"💾 Fichier React compatible mis à jour : {src_scenes_path}")

    print(f"\nSuccès ! {len(all_scenes)} scènes au total ont été exportées dans '{output_filename}'.")

if __name__ == '__main__':
    main()
