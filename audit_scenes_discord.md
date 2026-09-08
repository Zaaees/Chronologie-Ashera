# Rapport d'Audit : Segmentation Narrative, Chronologie et Attribution des Acteurs (Discord RP)

**Projet :** Ashera Lore / Chronologie-Ashera  
**Rôle :** Auditeur de code et analyste de données  
**Date :** 8 septembre 2026  
**Périmètre audité :**
- Code source : `extract_du_serveur.py`, `segmenteur_narratif.py`, `guild_resolver.py`, `unify_characters_v2.py`
- Base de données de production : `src/scenes.json` (319 scènes, 149 personnages, 11.4 Mo)
- Jeu de données brut : Répertoire `Export/` (60 exports HTML DiscordChatExporter du serveur Discord "Le Conte d'Ashera : Magie & Foi")

---

## 1. Synthèse Exécutive

L'analyse conjointe du code source d'extraction et des 60 exports Discord réels révèle que **le système de segmentation actuel produit d'importantes dégradations narratives et chronologiques**. Sur les 319 scènes répertoriées en production :
- **87 scènes (27,3 %)** comportent des trous d'inactivité intra-scène supérieurs à 7 jours (pouvant atteindre **44,6 jours consécutifs de silence**), causant la fusion aberrante d'intrigues et de personnages sans aucun lien.
- **91 scènes (28,5 %)** intègrent des bots narrateurs (`LE CONSEILLER`, `L'Oeil`, `OWL LE MESSAGER`) dans la liste des personnages joueurs (`actors`).
- **42 scènes** sont des "scènes fantômes" constituées d'un seul message (lignes de tirets décoratifs `_ _ _ _`, messages de lore d'ouverture de salon, ou mentions de clôture de RP orphelines).
- **54 scènes** présentent une distorsion temporelle où la date de début (`start_time`) est postérieure au premier message, avec des décalages chronologiques allant de 15 heures à **4 jours entiers**, causée notamment par l'exclusion arbitraire du compte joueur `Isis Faerieth` dans le calcul d'horodatage.
- **Plusieurs personnages joueurs majeurs** (`Adelina Del Fuego`, `Selena Moon`, `Lewis Bamer`, `Emil Camille Rebenok`) sont rétrogradés au statut de **PNJ** en raison d'une règle punitive classant tout utilisateur de Webhook (Tupperbox/PluralKit) comme non-joueur.

Le présent rapport expose la rétro-ingénierie complète de la logique existante, détaille les failles constatées avec preuves à l'appui tirées de l'export, et fournit les solutions techniques concrètes pour fiabiliser le moteur.

---

## 2. Rétro-Ingénierie de la Logique Actuelle

### 2.1. Pipeline d'Extraction et Cycle de Vie (`extract_du_serveur.py`)

L'extraction quotidienne s'exécute automatiquement via GitHub Actions (`.github/workflows/daily_extract.yml`) selon le flux suivant :
1. **Connexion bot Discord** (`DiscordExporterClient`) via les intents `message_content`, `guilds`, `members`.
2. **Identification des membres & Factions** :
   - Parcourt les membres Discord du serveur cible.
   - Compare leurs rôles à `FACTION_ROLE_PRIORITY` (`La Garde Pourpre`, `Cercle d'Azur`, `Voile d'Ivoire`, `L'œil`, `JAVUS`, `Sans guilde`).
   - Écrit les correspondances dans `discord_member_factions.json`.
3. **Chargement incrémental** :
   - Lit `src/scenes.json`.
   - Mémorise pour chaque salon le dernier message extrait (`last_msg_id_by_channel`). Si `channel.last_message_id <= last_id`, le salon n'est pas réanalysé et conserve ses anciennes scènes (cristallisant ainsi d'anciennes anomalies de découpage).
4. **Découverte des salons et fils (threads)** :
   - Filtre les catégories et salons via `is_excluded_channel()`.
   - Récupère les threads actifs et archivés (`active_threads()`, `archived_threads()`).
   - Rapproche les threads de leur salon parent à l'aide du dictionnaire statique `THREAD_TO_PARENT` (qui ne contient que 4 threads codés en dur pour `🍻〕𝐋-𝐄picurien`).
5. **Extraction des messages** :
   - Parcourt l'historique (`channel.history(limit=history_limit, oldest_first=True)`).
   - Concatène `content`, `embed_title` et `embed_description`.
   - *Anomalie constatée à la ligne 718-740* : La liste `embed_texts` (contenant fields, authors, footers) est construite en mémoire mais n'est jamais injectée dans `raw_messages`, provoquant la perte de contenu pour certains webhooks.
6. **Délégation à la segmentation** :
   - Appelle `segment_messages_into_scenes()`, qui appelle `segmenteur_narratif.py`.

### 2.2. Automate de Segmentation Narrative (`segmenteur_narratif.py`)

La fonction maîtresse `segment_messages_into_scenes_v2` opère séquentiellement sur les messages préalablement triés par horodatage (`parse_timestamp_v2`).

Elle maintient deux ensembles d'acteurs :
- `current_scene_actors` : Acteurs cumulés de la scène en cours.
- `player_scene_actors = current_scene_actors - GM_BOT_ACTORS` : Acteurs joueurs, excluant `{"LE CONSEILLER", "Oeil", "OWL LE MESSAGER", "LES MISSIVES", "Narrateur"}`.

Pour chaque message $i$ (`curr_msg`), l'automate calcule :
- $\Delta t = (t_{\text{curr}} - t_{\text{prev}}) / 86400$ (en jours).
- `has_player_actor_replied` et `has_other_player_actor_replied` : Un parcours prédictif (*lookahead*) sur les messages futurs $[i \dots N]$ dans une fenêtre de `hard_cutoff_days` (45 jours).

L'automate applique alors une cascade de conditions prioritaires :

```
[Message curr_msg]
  │
  ├─ 1. prev_is_sealed (EXPLICIT_END_REGEX sur prev_msg) ──> OUI ──> [ NOUVELLE SCÈNE ]
  │
  ├─ 2. diff_days > 45.0 jours (Hard Cutoff) ──────────────> OUI ──> [ NOUVELLE SCÈNE ]
  │
  ├─ 3. diff_days > 5.0 jours ET curr_actor nouveau ───────> OUI ──> [ NOUVELLE SCÈNE ]
  │     (curr_actor not in current_scene_actors & not in GM)
  │
  ├─ 4. diff_days > 5.0 jours ET curr_is_start (Bannière) ─> OUI ──> [ NOUVELLE SCÈNE ]
  │
  ├─ 4.5 diff_days > 5.0 jours ET curr == prev ────────────> OUI ──> [ NOUVELLE SCÈNE ]
  │      ET non retour des autres (relance orpheline)
  │
  ├─ 5. curr_actor in GM_BOT_ACTORS OU début purement GM ──> OUI ──> [ CONTINUATION ]
  │
  ├─ 6. Continuité "RP Long" (curr in player_scene_actors ─> OUI ──> [ CONTINUATION ]
  │     OU has_player_actor_replied == True)
  │
  ├─ 7. Bannière start par un nouvel acteur ───────────────> OUI ──> [ NOUVELLE SCÈNE ]
  │
  └─ 8. Défaut (fallback) ─────────────────────────────────────────> [ CONTINUATION ]
```

### 2.3. Logique d'Attribution des Acteurs et Factions

L'attribution du nom canonique et de la faction suit une hiérarchie stricte :
1. **Surcharges manuelles** (`Joueurs_Manuels.json` via `guild_resolver.py`).
2. **Webhooks / PNJ** : Si le nom nettoyé a envoyé un message avec `is_webhook = True` ou figure dans `LEGITIMATE_PNJ_NAMES`, le personnage reçoit le rôle `"PNJ"` (couleur violette `#c084fc`).
3. **Factions Discord** : Si le nom figure dans `discord_member_factions.json`, attribution du rôle correspondant.
4. **Fallback** : Dans `extract_du_serveur.py` (ligne 270), tout acteur sans faction devient un `"PNJ"`.

---

## 3. Chasse aux Failles : Analyse Critique et Cas Concrets de l'Extract

### Faille 1 : Le piège du Lookahead et du seuil de 45 jours (Fusion abusive d'intrigues)

#### Mécanisme
La variable `hard_cutoff_days` est fixée à **45.0 jours**. Durant cette période de 1 mois et demi, si un joueur ayant parlé au début de la scène reposte un message (même un simple ping HRP), `has_player_actor_replied` devient `True` pour tous les messages intermédiaires. 
De plus, si un groupe de joueurs complètement nouveau arrive dans le salon 10, 20 ou 40 jours plus tard sans rédiger de bannière formatée avec `EXPLICIT_START_REGEX`, la règle 8 (`else: is_new_scene = False`) maintient la scène ouverte.

#### Cas concret A : `scene_💰〕𝐁anque-du-sang_2` (Canal `1467160123108626463` - `🏦〕𝐋ot-𝐃e-𝐌aison`)
- **Scène initiale (Février 2026)** : Du 07/02/2026 au 10/02/2026 (messages 0 à 12). Acteurs : Hector Swaft, Akane Tsukishiro, Isis Faerieth, Magon Baldor. Clôture implicite le 10/02 à 22:02:00Z.
- **Inactivité totale : 28,4 jours consécutifs de silence** (du 10/02/2026 au 11/03/2026).
- **Reprise par un autre groupe (Mars 2026)** : Le 11/03/2026 à 07:18:33Z, Jasp Nah poste un séparateur, LE CONSEILLER pose un cadre narratif, puis Nick Sol, Euros et Lucia Fiorella démarrent une mission d'infiltration.
- **Cause du bug** :
  1. $28,4 \text{ jours} < 45,0 \text{ jours}$ : la règle 2 (hard cutoff) est inopérante.
  2. Jasp Nah avait posté un ping HRP en février (msg 2 : `<@&1327646236760608801> 16h je lance la prochaine narration`). Il était donc enregistré dans `current_scene_actors`.
  3. Lorsque Jasp Nah reposte le 11/03, `curr_actor not in current_scene_actors` est **Faux** (règle 3 ignorée).
  4. Le lookahead détecte que Jasp Nah répond encore plus loin : la règle 6 s'enclenche (`is_new_scene = False`).
- **Résultat dans l'export** : Une méga-scène factice de 50 messages, durant 38 jours, mélangeant 9 acteurs qui ne se sont jamais croisés.

#### Cas concret B : `scene___𝐏lace_𝐕endôme_3` (Canal `1499818405820236017` - `🌃〕𝐏lace-𝐕endôme`)
- **Scène 1 (Juillet 2026)** : Aryanna Erhendil, Ren Urugaki, Jasp Nah et Isis Faerieth mènent un combat et une évasion jusqu'au 14/07/2026 à 23:41:10Z (msg 47).
- **Inactivité record : 44 jours et 15 heures (44,6 jours)** !
- **Scène 2 (Septembre 2026)** : Le 02/09/2026, Kalem Crowley et Lys Ploug-Amar Ruinnard entament une scène civile (des enfants jouant au ballon dans la rue).
- **Cause du bug** : Le délai d'inactivité de 44,6 jours a échoué à franchir le seuil de 45,0 jours à **8 heures près** ! Entre temps, Isis Faerieth a posté un séparateur le 28/08, réactivant son statut d'actrice de la scène et empêchant le découpage lors de l'arrivée de Kalem Crowley le 02/09.
- **Résultat** : Une scène unique de 60,7 jours, 57 messages et 7 acteurs, fusionnant un affrontement dramatique de juillet et un échange poétique de septembre.

---

### Faille 2 : L'effet pervers de la règle 4.5 isolant les messages de fin

#### Mécanisme
La règle 4.5 a été conçue pour couper si un joueur relance seul après 5 jours :
```python
elif diff_days > max_inactivity_days and curr_actor == prev_actor and not has_other_player_actor_replied and not current_scene_actors.issubset(GM_BOT_ACTORS):
    is_new_scene = True
```
Cependant, dans un jeu de rôle, lorsqu'un joueur attend son partenaire sans réponse pendant plus de 5 jours et décide d'officialiser la fermeture du salon en postant ````Scène close.```` ou ````Scène abrégée par accord mutuel```` :
1. `curr_actor == prev_actor` est **Vrai** (le joueur parle après lui-même).
2. `diff_days > 5.0` est **Vrai**.
3. `has_other_player_actor_replied` est **Faux** (le partenaire n'a jamais répondu).
4. Cette règle 4.5 est positionnée **avant** le traitement de fin de scène !

Le message de fermeture est donc **séparé de la scène qu'il clôture** et devient le premier (et unique) message d'une nouvelle scène fantôme.

#### Cas concrets tirés de l'extract
1. **`scene___𝗣ont_des_𝗗eux_5` (Canal `1328038693902094357`)** :
   - Le 16/04/2026 à 22:04, Lucia Fiorella envoie sa dernière réplique de RP face à Myrea M.
   - Le 29/04/2026 à 20:54 (13 jours plus tard), Lucia poste : ````Scène close.````
   - **Résultat** : La scène 4 s'arrête le 16/04, et `scene___𝗣ont_des_𝗗eux_5` est créée avec 1 seul message, 1 seul acteur (Lucia Fiorella) et un contenu réduit à "Scène close.".
2. **`scene_🌸〕𝗖ours-𝗙leurie_4` (Canal `1334878212110549033`)** :
   - Le 07/07/2026 à 17:42, Ivara Luella poste en RP face à Cassian Ortie.
   - Le 13/07/2026 à 16:32 (6 jours plus tard), Ivara poste : ````Scène abrégée par accord mutuel C:````
   - **Résultat** : Création de la scène fantôme `scene_🌸〕𝗖ours-𝗙leurie_4` (1 message).
3. **`scene_L_équilibre_est_le_contraire_du_chaos_2`** :
   - Message unique d'Aryanna Erhendil : ```` Scène interrompue ````. En prime, le mot "interrompue" est absent de `EXPLICIT_END_REGEX`.

---

### Faille 3 : Traitement des séparateurs décoratifs (`_ _ _ _`) et des pings HRP

#### Mécanisme
Dans `is_meaningful_rp_content` :
```python
text = re.sub(r'<@[!&]?\d+>', '', full_text)
cleaned = re.sub(r'[^\w]', '', text, flags=re.UNICODE).strip()
```
En syntaxe regex, la classe `\w` inclut les lettres, les chiffres ET le caractère souligné `_`. Par conséquent, une suite de tirets bas comme `_ _ _ _ _ _ _ _ _ _ _ _` n'est pas nettoyée par `[^\w]` ; sa longueur dépasse le seuil minimal de 3 caractères et le script la qualifie de **vrai contenu RP**.

De surcroît, `is_meaningful_rp_content` n'est pas appelée lors de la constitution de `valid_msgs` dans `extract_du_serveur.py`. Tous les pings de relance HRP (ex: `||<@374571976645148693> pense à relancer frangin||`) pénètrent l'historique et faussent la liste des participants.

#### Cas concrets tirés de l'extract
- **9 scènes mono-message constituées uniquement de séparateurs** :
  - `scene_💰〕𝐁anque-du-sang_3` : `_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _` (Jasp Nah)
  - `scene_🕋〕𝐆uet-apens_4` : `_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _` (Jasp Nah)
  - `scene_🚬〕𝐏etit-𝐒alon_3` : `_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ ...` (Isis Faerieth)
  - `scene_🛋️〕𝐁ureau-de-𝐒haal_3` : `_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ ...` (Isis Faerieth)
  - `scene___𝐋e_𝐌ot_2` et `scene____𝐋e_𝐆uerrier_2` : Séparateurs postés par Loyis Delacroix.
  - `scene___𝐋e_17_2`, `scene___𝐋e_𝗣assage_2`, `scene___𝐌arché_𝐍oir_2` : Séparateurs postés par Isis Faerieth.
- **Attribution d'acteur indue dans `scene____𝗟e_𝗖afé_des_𝗣hilosophes_3`** :
  - L'acteur `Vosk Sulyvan` est crédité comme personnage joueur de la scène alors qu'il n'a posté que 3 messages strictement hors-RP :
    - `[0] 2026-05-31` : ```` ```` (bloc de code vide)
    - `[8] 2026-07-03` : `||<@374571976645148693> pense à relancer ou, au moins, à clore frangin||`
    - `[15] 2026-07-12` : `||<@374571976645148693><@249497144698863617>||`

---

### Faille 4 : Pollution des acteurs par les Bots MJ et messages de description

#### Mécanisme
Dans `create_scene_dict()` (`extract_du_serveur.py`) :
```python
actors = list({
    clean_character_name(m['author']) 
    for m in messages 
    if m.get('author') 
    and not any(b in m['author'].lower() for b in SYSTEM_BOTS)
    and is_meaningful_rp_content(...)
})
```
La variable `SYSTEM_BOTS` ne contient que les bots d'administration Discord (`carl-bot`, `dyno`, `mee6`). Les bots de narration et de MJ (`LE CONSEILLER`, `L'Oeil`, `OWL LE MESSAGER`, `LES MISSIVES`) en sont absents. Par conséquent, dès qu'un bot MJ intervient dans une scène, son nom est injecté dans le tableau `actors` et affiché sur l'interface du site comme un personnage joueur participant.

Pire, lors de l'ouverture d'un nouveau salon, le bot `LE CONSEILLER` y dépose un embed décrivant le lieu. Si les joueurs ne rejoignent le salon que plusieurs semaines après, ce message forme une scène isolée dont l'unique acteur est le bot MJ.

#### Cas concrets tirés de l'extract
- **91 scènes sur 319 (28,5 % de la base)** comportent un bot MJ dans leurs `actors` :
  - `scene___𝗔uditorium_2` : Acteurs : `[..., 'OWL LE MESSAGER', ...]`.
  - `scene___𝗔rène_𝗛urlante_2` : Acteurs : `['LE CONSEILLER', 'Loyis Delacroix', 'Nick Sol', ...]`.
  - `scene___𝗦erre_de_lune_2` : Acteurs : `['OWL LE MESSAGER', 'Emil Camille Rebenok', ...]`.
- **Scènes fantômes de description pure** :
  - `scene___𝗣arc_des_𝗖ardinaux_1` : Acteurs : `['LE CONSEILLER']`, 1 message (description du parc).
  - `scene____𝗖our_des_alchimistes_1` : Acteurs : `['LE CONSEILLER']`, 1 message (description de la cour).
  - `scene___𝗣ort_du_𝗟evant_1` : Acteurs : `['LE CONSEILLER']`, 1 message (description du port).

---

### Faille 5 : Distorsion temporelle du `start_time` et cas `'isis faerieth'`

#### Mécanisme
Dans `extract_du_serveur.py` (l. 394-404) :
```python
SYSTEM_AUTHORS_LOWER = {
    'le conseiller', 'oeil', "l'oeil", 'owl le messager', 'les missives',
    'narrateur', 'isis faerieth', 'carl-bot', 'dyno', 'mee6', 'ticket tool', 'ticket-tool', 'disboard'
}

first_player_msg = next((
    m for m in formatted_messages 
    if m.get('author') and m.get('author').lower().strip() not in SYSTEM_AUTHORS_LOWER
), formatted_messages[0] if formatted_messages else {"timestamp": "0000-00-00"})

start_time = first_player_msg.get('timestamp') or ...
```
Le pseudonyme du compte joueur `'isis faerieth'` a été hardcodé par erreur dans `SYSTEM_AUTHORS_LOWER`. Dès lors, chaque fois qu'Isis Faerieth rédige le premier message d'une scène, son message est ignoré et le `start_time` de la scène est calé sur le message du joueur suivant.

#### Cas concrets tirés de l'extract (54 scènes affectées)
- **`scene___𝗣ont_des_𝗗eux_6`** :
  - Message 0 par Isis Faerieth le **10/06/2026 à 22:12:31Z**.
  - `start_time` enregistré pour la scène : **11/06/2026 à 18:44:29Z** (soit **20 heures de décalage**).
- **`scene___𝗣arc_des_𝗖ardinaux_4`** :
  - Message 0 par Isis Faerieth le **08/04/2026 à 16:25:43Z**.
  - `start_time` enregistré pour la scène : **11/04/2026 à 11:13:48Z** (soit **près de 3 jours de retard**).
- **`scene_🏙️〕𝐄gregore_1`** :
  - Message 0 par LE CONSEILLER le **31/01/2026 à 14:26:34Z**.
  - `start_time` enregistré : **04/02/2026 à 22:10:01Z** (**4 jours de discordance** entre le début réel affiché et l'index chronologique).

Ces distorsions brisent le classement chronologique du site puisque les scènes sont triées selon leur `start_time`.

---

### Faille 6 : Désynchronisation des mappings et classification erronée "PNJ"

#### Mécanisme
Il existe deux tables de canonicalisation non synchronisées :
- `CANONICAL_MAP` dans `extract_du_serveur.py` (contient 15 entrées absentes de l'autre, ex: *Astreüs Mylonas, Jin Alurantes, Inzu Sravel, Hector Swaft, Emil Camille Rebenok, Rias Valdor, Lewis-Phoebe d'Ashbourne*).
- `CANONICAL_MAP` dans `unify_characters_v2.py` (contient des variantes différentes pour *Okayama, Velka, Euros, Tenebris*).

De plus, l'algorithme de classification de faction dans `extract_du_serveur.py` applique une règle éliminatoire :
1. Si un joueur a utilisé un Webhook (Tupperbox/PluralKit) ne serait-ce qu'une fois, son nom est enregistré dans `detected_webhooks`.
2. La règle 3 évalue `if clean_name in detected_webhooks: return "PNJ"` **avant** de regarder si la personne a un rôle dans `detected_member_factions`.
3. Enfin, la règle 5 assigne le statut `"PNJ"` (`#c084fc`) à quiconque n'a pas de rôle actif dans `detected_member_factions`.

#### Cas concrets tirés de l'extract
- **Personnages joueurs majeurs étiquetés PNJ** :
  - `Adelina Del Fuego` : 100 % Personnage Joueur, créditée avec rôle **PNJ** et couleur violette dans `scenes.json`.
  - `Selena Moon` : Personnage Joueur créditée en **PNJ**.
  - `Lewis Bamer` : Personnage Joueur crédité en **PNJ**.
  - `Emil Camille Rebenok` : Personnage Joueur crédité en **PNJ**.
- **Doublons non unifiés dans la liste des acteurs** :
  - `Brutas Greenwitch de la GP` et `Brutus Redwitch` coexistent comme deux acteurs distincts dans la Garde Pourpre.
  - `Thumb Hedwig Von G 12` et `Hedwig Von Glanzestern` coexistent comme deux acteurs distincts.
  - `CʜᴜʟᴀᴋTM` et `Cassian Ortie` coexistent dans le Voile d'Ivoire.
  - `Sous son Oeil` et `Sous son oeil` coexistent avec `L'Oeil`.
- **Noms de salons Discord devenus des acteurs PNJ** :
  Des messages postés par des webhooks portant le nom du salon ont généré des acteurs fictifs : `Le Mot`, `Le-Mot`, `Le Guerrier`, `Le Tresor`, `Le-Tresor`, `Le Penitancier`, `Le Voyageur`, `Le Marais`, `Le Sigile`, `La Bete`, `La Folie`, `La Foret`, `L'Academie`.

---

### Faille 7 : Recyclage et renommage des salons lors des Événements

#### Mécanisme
Pour les animations et quêtes majeures (Évent "Soupçons Morbides", Évent "De la Rage & du Sang"), l'équipe administrative réutilise les salons existants en changeant leur titre Discord. 
Comme le script d'extraction extrait l'historique d'un `channel_id` en lui associant le nom actuel du salon renvoyé par l'API Discord au moment du crawl, toutes les anciennes scènes passées voient leur nom écrasé rétroactivement.

#### Cas concrets (Exports HTML vs `scenes.json`)
| Channel ID | Nom dans l'Export HTML (Événement) | Nom dans `scenes.json` (Production) |
| :--- | :--- | :--- |
| `1480943398218109100` | `🐦‍⬛〕𝐑uelle-𝐏arallèle` | `💬〕𝐋e-𝐌ot` |
| `1483819969174310952` | `🦡〕𝐋a-𝐁elette-à-𝐃eux-𝐐ueues` | `⚔️〕𝐋e-𝐆uerrier` |
| `1480168703403495516` | `🎢〕𝐄tage` | `🛑〕𝐀rène` |
| `1480168496141697127` | `🏫〕𝐑ez-de-𝐂haussé` | `🌆〕𝐏lace` |
| `1480167606580150272` | `💞〕𝐌aison-de-𝐕elours` | `🌇〕𝐑uelle-𝐁asse-ville` |
| `1467160123108626463` | `🏦〕𝐋ot-𝐃e-𝐌aison` | `💰〕𝐁anque-du-sang` |
| `1467160167488684074` | `🕋〕𝐁outique` | `🕋〕𝐆uet-apens` |

Les scènes d'un événement se retrouvent ainsi rattachées à des lieux qui n'existaient pas ou qui portaient un tout autre rôle diégétique lors de leur écriture.

---

## 4. Recommandations et Correctifs Techniques

### 4.1. Refonte du Moteur de Segmentation (`segmenteur_narratif.py`)

#### 1. Remplacement du seuil de 45 jours et encadrement du Lookahead
- Abaisser `hard_cutoff_days` de 45.0 jours à **7.0 jours**. Dans un jeu de rôle Discord, une pause de 7 jours consécutifs sans aucune interaction entre les personnages doit sceller la scène.
- Restreindre le *lookahead* (`has_player_actor_replied`) à une fenêtre maximale de **3 jours**.
- Interdire au lookahead de maintenir une scène active si le nouveau message est émis par un joueur n'ayant jamais participé à la scène en cours.

#### 2. Priorité absolue aux marqueurs de fin (Correction de la règle 4.5)
Le test d'un marqueur de clôture sur le message courant doit s'exécuter **avant** toute décision de coupure pour inactivité ou relance par le même auteur. Si `curr_msg` contient une formule de fin, il doit rejoindre la scène active pour la sceller, sans créer de scène orpheline.

```python
# Correction de la gestion de clôture dans segmenteur_narratif.py
curr_is_end = bool(EXPLICIT_END_REGEX.search(curr_text))

# Si le message courant est un marqueur explicite de fin, on l'absorbe et on clôt la scène
if curr_is_end:
    current_scene_msgs.append(valid_msgs_sorted[i])
    scenes.append(create_scene_func(...))
    current_scene_msgs = []
    continue
```

#### 3. Enrichissement des Expressions Régulières
```python
EXPLICIT_END_REGEX = re.compile(
    r'(\bsc[èe]ne\s+(?:termin[eé]e?|close?|finie?|abr[eé]g[eé]e?|interrompue?)\b|'
    r'\bsalon\s+libre\b|'
    r'\bfin\s+de\s+(?:sc[èe]ne|mission|rp)\b|'
    r'\brp\s+(?:clos?|fini|termin[eé]e?)\b|'
    r'\baccord\s+mutuel\b)',
    re.IGNORECASE
)

# Regex pour éliminer les séparateurs décoratifs purs
SEPARATOR_LINE_REGEX = re.compile(r'^[\s\-_=*~•◦¤♅\.\/]+$')
```

---

### 4.2. Épuration du Filtrage et des Rôles (`extract_du_serveur.py`)

#### 1. Filtrage strict en amont dans `segment_messages_into_scenes`
Ne pas insérer dans `valid_msgs` les messages qui ne constituent pas du RP légitime :
```python
valid_msgs = []
for m in messages:
    full_text = " ".join([m.get('content', ''), m.get('embed_title', ''), m.get('embed_description', '')]).strip()
    # Ignorer les séparateurs décoratifs purs (_ _ _ _)
    if SEPARATOR_LINE_REGEX.match(full_text):
        continue
    # Appliquer le filtre RP signifiant dès l'ingestion
    if is_meaningful_rp_content(m.get('content', ''), m.get('embed_title', ''), m.get('embed_description', '')):
        valid_msgs.append((m, full_text))
```

#### 2. Séparation des Narrateurs / MJ et des Joueurs
- Dans `create_scene_dict`, exclure formellement les entités de `GM_BOT_ACTORS` de la liste finale des `actors`.
- Stocker les narrateurs dans une propriété dédiée : `scene["narrators"]`.
- Si une scène ne comporte aucun joueur (ex: embeds de lore du Conseiller), ne pas créer de scène RP ; stocker ces messages dans un champ `channel_description` rattaché au salon.

```python
SYSTEM_NARRATOR_NAMES = {
    'LE CONSEILLER', 'Le Conseiller', 'Oeil', "L'Oeil", "L'œil",
    'OWL LE MESSAGER', 'LES MISSIVES', 'Missive De la Rage et du Sang',
    'Sous son Oeil', 'Sous son oeil', 'Narrateur'
}

# Dans create_scene_dict
player_actors = [a for a in actors if a not in SYSTEM_NARRATOR_NAMES]
if not player_actors:
    # Scène purement administrative / descriptive : à écarter des scènes RP
    return None
```

#### 3. Correction de l'Horodatage (`start_time`)
- Retirer immédiatement `'isis faerieth'` de `SYSTEM_AUTHORS_LOWER`.
- Définir `start_time` comme étant l'horodatage exact du premier message réel de la scène (ou du premier message joueur si la scène commence par une courte amorce du MJ).

---

### 4.3. Unification du Référentiel des Personnages (`unify_characters_v2.py`)

#### 1. Fusion dans un dictionnaire unique et suppression des divergences
Centraliser `CANONICAL_MAP` dans un fichier unique importé par `extract_du_serveur.py` et `segmenteur_narratif.py`. Y adjoindre les alias constatés :
```python
CANONICAL_MAP.update({
    "brutas greenwitch de la gp": "Brutus Redwitch",
    "thumb hedwig von g 12": "Hedwig Von Glanzestern",
    "cʜᴜʟᴀᴋtm": "Cassian Ortie",
    "sw darker": "Magon Baldor",
    "sw dark325": "Magon Baldor",
    "kanta": "Euros",
    "sous son oeil": "Oeil",
    "sous son œil": "Oeil",
    "le mot": "Narrateur",
    "le guerrier": "Narrateur",
    "le tresor": "Narrateur"
})
```

#### 2. Correction de la règle Webhook / PNJ
Ne pas déclasser un joueur en PNJ sous prétexte qu'il a émis via un webhook. La vérification du rôle dans `discord_member_factions.json` ou `CANONICAL_MAP` doit prévaloir sur `detected_webhooks`.

```python
def get_character_guild_and_color(actor_name):
    clean_name = clean_character_name(actor_name)
    
    # 1. Bots de modération système exclus
    if any(b in clean_name.lower() for b in SYSTEM_MODERATION_BOTS):
        return None, None, None

    # 2. Surcharges manuelles
    manual = get_manual_override(clean_name)
    if manual and manual.get("guild"):
        return get_guild_info(manual["guild"])

    # 3. Vérifier d'abord si c'est un joueur identifié dans les factions
    if clean_name in detected_member_factions:
        return detected_member_factions[clean_name]

    # 4. Vérifier s'il figure dans la liste des PNJ légitimes connus
    if is_pnj_character(clean_name):
        return "PNJ", "#c084fc", "char_pnj"

    # 5. Webhook non identifié comme joueur -> PNJ
    if clean_name in detected_webhooks:
        return "PNJ", "#c084fc", "char_pnj"

    # 6. Joueur réel sans rôle attribué sur Discord -> "Sans guilde" ou "Indéfini" (MAIN_PC)
    return "Indéfini", "#94a3b8", "char_indefini"
```

---

### 4.4. Gestion Dynamique des Salons, Threads et Événements

1. **Rattachement dynamique des fils de discussion** :
   Remplacer le dictionnaire statique `THREAD_TO_PARENT` par l'attribut natif Discord :
   ```python
   if isinstance(channel, discord.Thread) and channel.parent:
       parent_channel = channel.parent.name
       thread_name = channel.name
   ```
2. **Gestion de l'historique des noms de salons** :
   Pour éviter d'écraser les salons d'événements, stocker dans chaque scène :
   - `channel_id` : Identifiant immuable du salon Discord.
   - `channel_title_at_time` : Nom du salon au moment où les messages ont été écrits (détecté via les balises de titre d'export ou les bannières d'événements).

---

## 5. Matrice Récapitulative des Anomalies et Correctifs

| Problème identifié | Cause racine dans le code | Impact sur les données | Solution recommandée |
| :--- | :--- | :--- | :--- |
| **Fusion de scènes après 20 à 44 jours** | `hard_cutoff_days = 45.0` + Lookahead non borné | Scènes de 50+ messages mélangeant des intrigues différentes (`Place Vendôme`, `Banque du sang`) | Réduire le seuil à **7 jours** et borner le lookahead à **3 jours** |
| **Messages "Scène close" orphelins** | Règle 4.5 exécutée avant le scellement de fin | Scènes de 1 message contenant uniquement "Scène close." (`Pont des Deux`) | Traiter `curr_is_end` en priorité pour absorber le message dans la scène en cours |
| **Scènes de tirets `_ _ _ _`** | Regex `\w` acceptant les underscores dans `is_meaningful_rp_content` | 9 scènes parasites d'un seul message | Pré-filtrer avec `SEPARATOR_LINE_REGEX` avant segmentation |
| **Bots MJ comptés comme acteurs** | `SYSTEM_BOTS` restreint aux bots d'administration Discord | 91 scènes affichant `LE CONSEILLER` ou `L'Oeil` comme joueurs | Exclure `SYSTEM_NARRATOR_NAMES` de `actors` ; créer un champ `narrators` |
| **Décalage temporel (`start_time`)** | `'isis faerieth'` hardcodée dans `SYSTEM_AUTHORS_LOWER` | Décalages de 15h à 4 jours sur 54 scènes ; ordre chronologique faussé | Supprimer `'isis faerieth'` ; baser `start_time` sur le message 0 |
| **Joueurs majeurs classés "PNJ"** | Priorité absolue de `detected_webhooks` sur les factions | `Adelina`, `Selena`, `Lewis`, `Emil` en PNJ violet | Vérifier `detected_member_factions` avant `detected_webhooks` |
| **Divergence des noms canoniques** | Deux `CANONICAL_MAP` distinctes dans 2 fichiers | Incohérence de nommage et doublons d'acteurs | Fusionner dans un module unique partagé |
| **Renommage destructif des salons** | Utilisation exclusive du nom Discord courant | Scènes d'événements renommées avec des noms génériques | Conserver le nom historique du salon au moment de la scène |

---

## 6. Conclusion et Plan de Déploiement Conseillé

L'infrastructure actuelle dispose d'une excellente base (automatisation GitHub Actions, typage, structuration React/Vite). Toutefois, l'empilement de règles heuristiques permissives (seuil de 45 jours, lookahead sans garde-fous, confusion entre bots MJ et joueurs) a dégradé la fidélité de la chronologie.

Le déploiement des correctifs peut être réalisé en **3 étapes sans interruption de service** :
1. **Étape 1 (Correctif immédiat)** : Suppression d'`isis faerieth` de `SYSTEM_AUTHORS_LOWER`, nettoyage des séparateurs `_ _ _ _`, et correction de la priorité de clôture (Règle 4.5).
2. **Étape 2 (Refonte de segmentation)** : Remplacement du seuil de 45 jours par 7 jours et exclusion des narrateurs de la liste des acteurs.
3. **Étape 3 (Re-génération complète)** : Forcer une ré-extraction complète de tous les salons pour régénérer un `scenes.json` assaini et cohérent de bout en bout.
