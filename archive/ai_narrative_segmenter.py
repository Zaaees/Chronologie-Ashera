import re

# Marqueurs explicites de fermeture et d'ouverture de RP
EXPLICIT_END_REGEX = re.compile(
    r'(sc[èe]ne\s+termin[eé]|salon\s+libre|fin\s+de\s+sc[èe]ne|mission\s+termin[eé]|fin\s+du\s+rp)',
    re.IGNORECASE
)

EXPLICIT_START_REGEX = re.compile(
    r'(```ansi.*🎭|#\s+⊱═─────|```\s*🎭|◦\s*─────────────\s*¤)',
    re.IGNORECASE | re.DOTALL
)

SYSTEM_BOTS = {"koya", "profile", "carl-bot", "dyno", "mee6"}


def segment_messages_into_scenes_ai(channel_name, channel_id, valid_msgs, create_scene_func):
    """
    Segmentation Narrative des messages RP (Exécutée dans le workflow Antigravity).
    Analyse la continuité du récit, les répliques entre personnages, et les ouvertures/fermetures de RP.
    Aucune règle d'heures arbitraires (pas de 24h, 48h ou 30j).
    """
    if not valid_msgs:
        return []

    scenes = []
    current_scene_msgs = [valid_msgs[0]]
    scene_counter = 1

    for i in range(1, len(valid_msgs)):
        prev_msg, prev_text = valid_msgs[i - 1]
        curr_msg, curr_text = valid_msgs[i]

        current_scene_actors = {m[0].get('author_name', m[0].get('author', '')) for m in current_scene_msgs}
        curr_actor = curr_msg.get('author_name', curr_msg.get('author', ''))

        prev_is_sealed = bool(EXPLICIT_END_REGEX.search(prev_text))
        curr_is_start = bool(EXPLICIT_START_REGEX.search(curr_text))

        # Vérifie si l'un des acteurs de la scène en cours répond plus loin dans le salon
        has_previous_actor_replied = False
        for nm, _ in valid_msgs[i:]:
            act = nm.get('author_name', nm.get('author', ''))
            if act in current_scene_actors:
                has_previous_actor_replied = True
                break

        is_new_scene = False

        # 1. Marqueur explicite de fin de RP dans le message précédent -> Fermeture de la scène
        if prev_is_sealed:
            is_new_scene = True

        # 2. Bannière/Bloc d'ouverture RP démarré par un intervenant externe sans fil de réponse en attente
        elif curr_is_start and curr_actor not in current_scene_actors and not has_previous_actor_replied:
            is_new_scene = True

        # 3. Continuité narrative : si l'acteur participe à la scène ou que les participants précédents répondent -> Continuer la scène
        elif curr_actor in current_scene_actors or has_previous_actor_replied:
            is_new_scene = False

        # 4. Nouveau fil d'interaction sans lien avec la scène précédente
        else:
            is_new_scene = True

        if is_new_scene:
            scenes.append(create_scene_func(channel_name, channel_id, scene_counter, current_scene_msgs))
            scene_counter += 1
            current_scene_msgs = [valid_msgs[i]]
        else:
            current_scene_msgs.append(valid_msgs[i])

    if current_scene_msgs:
        scenes.append(create_scene_func(channel_name, channel_id, scene_counter, current_scene_msgs))

    return scenes
