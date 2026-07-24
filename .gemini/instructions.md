# Consignes d'extraction Discord - Ashera Lore

## 1. Salons et types de canaux exclus de l'extraction
Lors de l'extraction automatique du serveur Discord avec `bot_exporter.py`, ne JAMAIS inclure les salons suivants :

- **Toutes les fiches de personnages** (salons sous les catégories fiches, candidatures, effectifs, profils)
- **Toutes les chambres et dortoirs** (`#Chambre de...`, `#🛏️ • Chambre...`, `#🛏️〕<ctrl42>Dortoirs...`)
- **Salons spécifiques exclus** :
  - `🪎〕<ctrl42>Le-Trésor`
  - `🧿〕<ctrl42>La-Folie`
  - `🌾〕<ctrl42>Le-Marais`
  - `🗨️〕<ctrl42>Le-Sigile`
  - `🐺〕<ctrl42>La-Bête`
  - `👑〕<ctrl42>Statue-d-Icare`
  - `➰〕<ctrl42>Le-Mensonge`
  - `🔻〕<ctrl42>Le-Ciel`
  - `⚔️〕<ctrl42>La-Force`
  - `👁️〕<ctrl42>Le-Voyageur`
  - `📓〕<ctrl42>Le-Secret`
  - `🍎〕<ctrl42>L’Orgueil`
  - `⚔️〕<ctrl42>Le-Guerrier`
  - `⏳〕<ctrl42>Le-Temps`

## 2. Règle d'extraction incrémentale
- Seuls les **nouveaux messages** publiés après le dernier message extrait (`after=last_message_id`) doivent être lus.
- Les scènes déjà générées dans `scenes.json` et `data.js` doivent être préservées si aucune mise à jour n'a eu lieu dans le salon.
