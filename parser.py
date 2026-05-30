import json
import re
from datetime import datetime

# Seuil de coupure par inactivité (en heures)
TIME_GAP_THRESHOLD_HOURS = 12

def parse_character_name(author_name):
    """
    Extrait le nom du personnage. 
    Par exemple : "Alice (Aveline)" -> "Aveline"
    Si aucune parenthèse, retourne le nom d'auteur brut.
    """
    match = re.search(r'\((.*?)\)', author_name)
    if match:
        return match.group(1).strip()
    return author_name.strip()

def parse_iso_time(timestamp_str):
    """Convertit une chaîne ISO 8601 en objet datetime."""
    # Remplacer le Z de fin pour la compatibilité Python plus ancienne si nécessaire,
    # mais datetime.fromisoformat supporte le Z en Python 3.11+. 
    # Pour être robuste, on gère le remplacement manuel.
    clean_ts = timestamp_str.replace('Z', '+00:00')
    return datetime.fromisoformat(clean_ts)

def segment_channel_into_scenes(channel_name, messages):
    """
    Découpe les messages d'un salon en scènes distinctes en utilisant :
    1. Un seuil de temps d'inactivité (ex: 12h)
    2. Un changement complet des personnages actifs (changement de casting)
    """
    if not messages:
        return []

    # Trier par timestamp par sécurité
    sorted_msgs = sorted(messages, key=lambda m: m['timestamp'])
    
    scenes = []
    current_scene_msgs = [sorted_msgs[0]]
    scene_counter = 1
    
    for i in range(1, len(sorted_msgs)):
        prev_msg = sorted_msgs[i - 1]
        curr_msg = sorted_msgs[i]
        
        # 1. Analyse temporelle
        prev_time = parse_iso_time(prev_msg['timestamp'])
        curr_time = parse_iso_time(curr_msg['timestamp'])
        time_diff = (curr_time - prev_time).total_seconds() / 3600.0
        
        # 2. Analyse des participants récents
        recent_actors = {parse_character_name(m['author_name']) for m in current_scene_msgs[-5:]}
        curr_actor = parse_character_name(curr_msg['author_name'])
        
        # Conditions de coupure :
        # - Écart de temps important (> 12h)
        # - OU (le personnage actuel n'était pas dans le groupe récent ET le dernier message remonte à plus de 4h)
        is_new_scene = False
        if time_diff >= TIME_GAP_THRESHOLD_HOURS:
            is_new_scene = True
        elif curr_actor not in recent_actors and time_diff >= 4.0:
            is_new_scene = True
            
        if is_new_scene:
            # Sauvegarder la scène courante
            scenes.append(create_scene_object(channel_name, scene_counter, current_scene_msgs))
            scene_counter += 1
            current_scene_msgs = [curr_msg]
        else:
            current_scene_msgs.append(curr_msg)
            
    # Ne pas oublier la dernière scène en cours
    if current_scene_msgs:
        scenes.append(create_scene_object(channel_name, scene_counter, current_scene_msgs))
        
    return scenes

def create_scene_object(channel_name, scene_index, messages):
    """Formate les messages groupés en un objet Scène structuré."""
    first_msg = messages[0]
    last_msg = messages[-1]
    
    actors = list({parse_character_name(m['author_name']) for m in messages})
    
    # Création d'un aperçu textuel
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
        
    # Trier toutes les scènes par date de début pour la chronologie
    all_scenes.sort(key=lambda s: s['start_time'])
    
    # Enregistrer le résultat pour l'interface frontend
    output_filename = 'scenes.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_scenes, f, indent=2, ensure_ascii=False)

    # Écrire également dans src/scenes.json pour l'application React
    import os
    src_scenes_path = os.path.join('src', 'scenes.json')
    if os.path.isdir('src'):
        # On va envelopper all_scenes de la même manière pour garder la compatibilité si c'est nécessaire,
        # ou juste sérialiser all_scenes directement (le parser.py produit une liste de scènes brute)
        # Mais attendez! Le parser.py d'origine n'avait que scenes, pas de characters!
        # C'est parfait, on écrit la liste de scènes brute.
        # Mais attendez, dans data.ts on s'attend à { characters: ..., scenes: ... }!
        # Si le parser.py produit juste une liste, data.ts pourrait planter car il cherche rawData.characters.
        # Heureusement, le parser principal de l'utilisateur est parser_html.py, pas parser.py
        # (car parser_html.py gère les personnages et génère data.js).
        # Écrivons tout de même scenes.json dans src si besoin.
        # Pour être sûr que data.ts ne plante pas si l'utilisateur utilise parser.py, on peut empaqueter all_scenes dans un format compatible.
        # Mais le parser.py d'origine n'extrait pas les personnages! Il n'écrit que la liste.
        # Donc restons fidèles à l'original et écrivons juste la liste dans src/scenes.json, mais signalons-le.
        with open(src_scenes_path, 'w', encoding='utf-8') as f:
            # Pour la compatibilité du format de scenes.json attendu par React:
            # On conserve le format d'origine qui est une liste, mais on vérifie si data.ts peut le charger.
            # En fait, data.ts s'attend à ce que scenes.json contienne { characters, scenes }.
            # Donc si on utilise parser.py, on doit générer {"characters": {}, "scenes": all_scenes} pour éviter un plantage dans React!
            # C'est extrêmement intelligent !
            output_compatible = {
                "characters": {},
                "scenes": all_scenes
            }
            json.dump(output_compatible, f, indent=2, ensure_ascii=False)
        print(f"💾 Fichier React compatible mis à jour : {src_scenes_path}")
        
    print(f"\nSuccès ! {len(all_scenes)} scènes au total ont été exportées dans '{output_filename}'.")

if __name__ == '__main__':
    main()
