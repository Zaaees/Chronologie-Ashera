import json, sys, os, re
from datetime import datetime

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

from ai_narrative_segmenter_v2 import segment_messages_into_scenes_v2, parse_timestamp_v2
from unify_characters_v2 import get_canonical_name_v2, build_unified_characters_dict_v2

def main():
    src_path = 'scenes.json'
    with open(src_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    existing_scenes = raw.get('scenes', raw if isinstance(raw, list) else [])

    # Group messages by channel
    channel_groups = {}
    for sc in existing_scenes:
        ch_raw = sc.get('channel_raw', sc.get('channel', 'Salon Inconnu'))
        ch_clean = sc.get('channel_clean', sc.get('channel', 'Salon Inconnu'))
        key = (ch_raw, ch_clean)
        if key not in channel_groups:
            channel_groups[key] = []

        for m in sc.get('messages', []):
            content = m.get('content', '')
            if content and content.strip():
                channel_groups[key].append((m, content))

    def scene_builder(channel_clean, channel_raw, scene_idx, msg_tuples, title_suggested):
        msgs = [t[0] for t in msg_tuples]
        texts = [t[1] for t in msg_tuples]
        actors = list({get_canonical_name_v2(m.get('author_name', m.get('author', ''))) for m in msgs})
        main_actor = actors[0] if actors else "Narrateur"
        is_solo = (len(actors) == 1)

        start_ts = parse_timestamp_v2(msgs[0].get('timestamp'))
        end_ts = parse_timestamp_v2(msgs[-1].get('timestamp'))
        duration_mins = max(1, int((end_ts - start_ts) / 60)) if (end_ts > start_ts and start_ts > 0) else 1

        preview = texts[0]
        if len(preview) > 160:
            preview = preview[:157] + "..."

        sc_id = f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', channel_clean).lower()}_{scene_idx}"

        return {
            "id": sc_id,
            "channel": channel_raw,
            "channel_raw": channel_raw,
            "channel_clean": channel_clean,
            "title": title_suggested if title_suggested else f"{channel_clean} — Scène {scene_idx}",
            "actors": actors,
            "main_actor": main_actor,
            "is_solo": is_solo,
            "scene_type": "Solo / Monologue" if is_solo else "Duo / Groupe",
            "start_time": msgs[0].get('timestamp', ''),
            "end_time": msgs[-1].get('timestamp', ''),
            "duration_minutes": duration_mins,
            "preview": preview,
            "message_count": len(msgs),
            "messages": msgs
        }

    all_scenes = []
    for (ch_raw, ch_clean), msg_tuples in channel_groups.items():
        sorted_tuples = sorted(msg_tuples, key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))
        
        # Deduplicate identical message IDs per channel
        seen_ids = set()
        dedup_tuples = []
        for m, txt in sorted_tuples:
            mid = m.get('id')
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            dedup_tuples.append((m, txt))

        ch_scenes = segment_messages_into_scenes_v2(ch_clean, ch_raw, dedup_tuples, scene_builder)
        all_scenes.extend(ch_scenes)

    all_scenes = [s for s in all_scenes if s.get('message_count', 0) >= 2]
    all_scenes.sort(key=lambda s: parse_timestamp_v2(s.get('start_time', '')))

    # Build character dict
    characters = build_unified_characters_dict_v2(all_scenes)

    output_data = {
        "metadata": {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "total_scenes": len(all_scenes),
            "total_characters": len(characters)
        },
        "characters": characters,
        "scenes": all_scenes
    }

    # Save to scenes.json, src/scenes.json, data.js
    for p in ['scenes.json', 'src/scenes.json']:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write('window.RP_DATA = ' + json.dumps(output_data, ensure_ascii=False, indent=2) + ';')

    print(f"✅ Re-segmentation complète terminée : {len(all_scenes)} scènes générées !")

    porcelaine_scenes = [s for s in all_scenes if 'porcelaine' in s.get('channel_clean', '').lower() or 'porcelaine' in s.get('channel', '').lower()]
    print(f"\n🎭 Scènes générées pour Grande-salle-porcelaine ({len(porcelaine_scenes)} scènes) :")
    for idx, s in enumerate(porcelaine_scenes, 1):
        print(f"  Scène {idx} [{s['id']}] : {s['message_count']} msgs | {s['start_time']} -> {s['end_time']}")
        print(f"    Titre : {s['title']}")
        print(f"    Acteurs : {s['actors']}")

if __name__ == '__main__':
    main()
