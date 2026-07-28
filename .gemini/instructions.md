# Consignes de Mise à Jour Automatique 100% IA - Ashera Lore

## 🎯 Commande Unique Master
Lorsque l'utilisateur donne l'instruction :
> **`Antigravity, lance l'extraction et mets à jour le site`**
*(ou toute variante comme "Extrais Discord et segmente les scènes", "Mets à jour le site depuis Discord")*

Antigravity doit exécuter **automatiquement la séquence complète à 100%** sans intervention manuelle :

---

## 📋 Procédure d'Exécution Automatisée (Workflow en 4 Étapes)

### Étape 1 : Extraction Discord Automatique
- Exécuter la commande d'extraction des nouveaux messages du serveur Discord :
  `python bot_exporter.py` (ou script d'export d'API Discord).
- **Salons et catégories strictement exclus de l'extraction :**
  - Toutes les fiches de personnages (fiches, candidatures, effectifs, profils).
  - Toutes les chambres et dortoirs (`#Chambre de...`, `#🛏️ • Chambre...`, `#🛏️〕Dortoirs...`).
  - Salons spécifiques exclus : `Le-Trésor`, `La-Folie`, `Le-Marais`, `Le-Sigile`, `La-Bête`, `Statue-d-Icare`, `Le-Mensonge`, `Le-Ciel`, `La-Force`, `Le-Voyageur`, `Le-Secret`, `L’Orgueil`, `Le-Guerrier`, `Le-Temps`.

### Étape 2 : Filtrage Incrémental des Nouveaux Messages
- Comparer les messages extraits avec le dernier ID enregistré (`last_message_id`) de chaque salon dans `src/scenes.json`.
- Conserver intactes les scènes passées déjà enregistrées.
- Traiter uniquement les nouveaux messages ayant un ID `> last_message_id`.

### Étape 3 : Segmentation Narrative IA & Attribution des Personnages (Tupperbox)
- **Analyse Narrative Pure :** L'IA évalue la continuité du récit, les échanges entre personnages, les entrées/sorties de scène et le rythme du RP Long. (Aucune règle d'heures arbitraires 24h/48h).
- **Attribution & Identification des Personnages (Tupperbox) par l'IA :**
  - L'IA identifie et nettoie automatiquement les noms des personnages RP issus des webhooks/Tuppers (nettoyage des mentions BOT/HRP, extraction du nom du personnage).
  - L'IA associe dynamiquement chaque personnage à son joueur réel (`username`, `displayName`) et à sa Guilde/Faction RP (La Garde Pourpre `#b40000`, Cercle d'Azur `#305ed3`, Voile d'Ivoire `#ffffd4`, L'œil `#0e0d0d`, PNJ `#a855f7`).
  - Aucune liste statique de noms d'acteurs codée en dur dans les scripts Python.
- **Marqueurs explicites :** `Scène Terminée`, `Salon libre` $\rightarrow$ Coupure immédiate.
- **Rattachement des Fils RP (Threads) :** Les fils (`↳ Le Rouge et le Noir`, `↳ Le 17`, `↳ Le Bonneteau`, `↳ Le Bras de Fer`) sont rattachés à leur salon parent (`🍻〕𝐋-𝐄picurien`) avec la propriété `"thread_name": "..."`.
- **Titres & Résumés Narratifs :** L'IA génère un titre de chapitre sémantique explicite (ex: *"L'Épreuve d'Alchimie de la Serre de Lune"*) et un aperçu propre.

### Étape 4 : Synchronisation des Fichiers & Compilation Vite
- Préserver et réattacher automatiquement le dictionnaire `channel_images` ainsi que la propriété `location_image` pour chaque scène depuis `public/channel_images/`.
- Mettre à jour simultanément :
  1. `scenes.json` (racine)
  2. `src/scenes.json`
  3. `data.js` (`window.rpData = ...;`)
- Exécuter `npm run build` pour compiler la version de production.
- Confirmer à l'utilisateur la fin du processus avec le nombre de nouvelles scènes ajoutées.
