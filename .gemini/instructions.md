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

### Étape 3 : Segmentation 100% IA Narrative & Rattachement des Fils
- **Analyse Narrative Pure :** L'IA évalue la continuité du récit, la réponse entre personnages, les entrées/sorties de scène et le rythme du RP Long. (Aucune règle d'heures arbitraires 24h/48h).
- **Marqueurs explicites :** `Scène Terminée`, `Salon libre` $\rightarrow$ Coupure immédiate.
- **Rattachement des Fils RP (Threads) :** Les fils (`↳ Le Rouge et le Noir`, `↳ Le 17`, `↳ Le Bonneteau`, `↳ Le Bras de Fer`) sont rattachés à leur salon parent (`🍻〕𝐋-𝐄picurien`) avec la propriété `"thread_name": "..."`.
- **Titres & Résumés Narratifs :** L'IA génère un titre de chapitre sémantique explicite (ex: *"L'Épreuve d'Alchimie de la Serre de Lune"*) et un aperçu propre.

### Étape 4 : Synchronisation des Fichiers & Compilation Vite
- Mettre à jour simultanément :
  1. `scenes.json` (racine)
  2. `src/scenes.json`
  3. `data.js` (`window.rpData = ...;`)
- Exécuter `npm run build` pour compiler la version de production.
- Confirmer à l'utilisateur la fin du processus avec le nombre de nouvelles scènes ajoutées.
