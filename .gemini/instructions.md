# Consignes de Mise à Jour Automatique 100% Python - Ashera Lore

## 🎯 Commande Unique Master
Lorsque l'utilisateur donne l'instruction :
> **`Antigravity, lance l'extraction et mets à jour le site`**
*(ou toute variante comme "Extrais Discord et segmente les scènes", "Mets à jour le site depuis Discord")*

Antigravity doit exécuter **automatiquement la séquence complète à 100% via des scripts Python fiables** sans intervention manuelle :

---

## 📋 Procédure d'Exécution Automatisée (Workflow en 4 Étapes)

### Étape 1 : Extraction Discord Automatique & Attribution Dynamique des Rôles
- Exécuter la commande d'extraction des nouveaux messages du serveur Discord :
  `python extract_du_serveur.py`
- L'attribution des guildes et personnages se fait **directement à partir des rôles Discord réels des membres** (`member.roles`) lors de l'extraction API.
- **Salons et catégories strictement exclus de l'extraction :**
  - Toutes les fiches de personnages (fiches, candidatures, effectifs, profils). *(Note: Les chambres et dortoirs RP `#Chambre...`, `#Dortoirs...` et leurs posts Forum sont inclus dans l'extraction)*.
  - Salons spécifiques exclus : `Le-Trésor`, `La-Folie`, `Le-Marais`, `Le-Sigile`, `Le-Bête`, `Statue-d-Icare`, `Le-Mensonge`, `Le-Ciel`, `La-Force`, `Le-Voyageur`, `Le-Secret`, `L’Orgueil`, `Le-Guerrier`, `Le-Temps`.

### Étape 2 : Filtrage Incrémental des Nouveaux Messages
- Comparer les messages extraits avec le dernier ID enregistré (`last_message_id`) de chaque salon dans `src/scenes.json`.
- Conserver intactes les scènes passées déjà enregistrées.
- Traiter uniquement les nouveaux messages ayant un ID `> last_message_id`.

### Étape 3 : Segmentation Narrative & Unification des Personnages (Python)
- **Segmentation Déterministe :** Exécutée par `segmenteur_narratif.py` sur la continuité du récit, les échanges entre personnages et les entrées/sorties de scène.
- **Attribution & Identification des Personnages (Tupperbox/Webhooks) :**
  - Le nom des personnages est automatiquement nettoyé et canonisé (`clean_character_name`).
  - Chaque personnage est associé à sa Guilde/Faction RP issue des rôles Discord réels (La Garde Pourpre `#ef4444`, Cercle d'Azur `#3b82f6`, Voile d'Ivoire `#fef08a`, L'œil `#cbd5e1`, Sans guilde `#eab308`, PNJ `#c084fc`).
- **Marqueurs explicites :** `Scène Terminée`, `Salon libre` $\rightarrow$ Coupure immédiate.
- **Rattachement des Fils RP (Threads) :** Les fils (`↳ Le Rouge et le Noir`, `↳ Le 17`, `↳ Le Bonneteau`, `↳ Le Bras de Fer`) sont rattachés à leur salon parent avec la propriété `"thread_name": "..."`.

### Étape 4 : Synchronisation des Fichiers & Compilation Vite
- Préserver et réattacher automatiquement le dictionnaire `channel_images` ainsi que la propriété `location_image` pour chaque scène depuis `public/channel_images/`.
- Mettre à jour simultanément :
  1. `scenes.json` (racine)
  2. `src/scenes.json`
  3. `data.js` (`window.rpData = ...;`)
- Exécuter `npm run build` pour compiler la version de production.
- Confirmer à l'utilisateur la fin du processus avec le nombre de nouvelles scènes ajoutées.
