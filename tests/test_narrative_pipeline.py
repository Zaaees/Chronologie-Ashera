import unittest
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath("."))

from unify_characters_v2 import get_canonical_name_v2
from extract_du_serveur import (
    is_meaningful_rp_content,
    is_excluded_channel,
    clean_character_name,
    is_system_narrator_name,
    SYSTEM_NARRATOR_CANONICAL,
    FACTION_INFO
)
from segmenteur_narratif import (
    GM_BOT_ACTORS,
    is_gm_bot_actor,
    extract_title_from_text,
    parse_timestamp_v2
)

class TestNarrativePipelineAudit(unittest.TestCase):

    def test_chantier_2_canonical_names(self):
        """Chantier 2 : Vérification formelle de la suppression des faux positifs de canonisation."""
        self.assertEqual(get_canonical_name_v2("Dan"), "Dan")
        self.assertNotEqual(get_canonical_name_v2("Dan"), "Tenebris")

        self.assertEqual(get_canonical_name_v2("Law"), "Law")
        self.assertNotEqual(get_canonical_name_v2("Law"), "Markus Law")

        self.assertEqual(get_canonical_name_v2("Gate"), "Gate")
        self.assertNotEqual(get_canonical_name_v2("Gate"), "Eldren Gates")

        self.assertEqual(get_canonical_name_v2("Roi"), "Roi")
        self.assertNotEqual(get_canonical_name_v2("Roi"), "Loyis Delacroix")

        self.assertEqual(get_canonical_name_v2("Lac"), "Lac")
        self.assertNotEqual(get_canonical_name_v2("Lac"), "Loyis Delacroix")

        self.assertEqual(get_canonical_name_v2("Art"), "Art")
        self.assertNotEqual(get_canonical_name_v2("Art"), "Lumia Faendharts")

        # Noms complets canoniques doivent toujours fonctionner
        self.assertEqual(get_canonical_name_v2("Markus Law"), "Markus Law")
        self.assertEqual(get_canonical_name_v2("Eldren Gates"), "Eldren Gates")
        self.assertEqual(get_canonical_name_v2("Tenebris"), "Tenebris")

    def test_chantier_1_security_channel_exclusion(self):
        """Chantier 1 : Vérification de l'exclusion des salons dont le parent est décoratif."""
        # Parent avec séparateur décoratif
        self.assertTrue(is_excluded_channel("fil_prive", "", parent_name="◦─────────────◦"))
        self.assertTrue(is_excluded_channel("discussion_hrp", "", parent_name="━─────────────━"))
        self.assertTrue(is_excluded_channel("autre_fil", "", parent_name="─"))
        self.assertTrue(is_excluded_channel("fil_secret", "", parent_name="·"))

        # Salon normal avec parent valide
        self.assertFalse(is_excluded_channel("🍻〕𝐋-𝐄picurien", "BASSE-VILLE", parent_name="BASSE-VILLE"))

    def test_chantier_1_meaningful_rp_custom_emojis(self):
        """Chantier 1 : Vérification du rejet des pings avec emojis Discord personnalisés."""
        # Faux négatif identifié : ping + custom emoji
        msg1 = "<@178885862644252672> <:gak_azur:1514356539304050708>"
        self.assertFalse(is_meaningful_rp_content(msg1))

        # Ping + phrase courte + custom emoji
        msg2 = "<@184984566673440768> je me permets <:barbarapray:1462403320550260826>"
        self.assertFalse(is_meaningful_rp_content(msg2))

        # Scène vide avec 400 sauts de ligne
        msg3 = ".\n\n\n\n\n\n\n\n\n\n\n\n"
        self.assertFalse(is_meaningful_rp_content(msg3))

        # Vrai contenu RP avec plus de 3 mots et narration
        msg_rp = "Le jeune homme s'avança lentement vers la porte, le regard empreint de détermination."
        self.assertTrue(is_meaningful_rp_content(msg_rp))

    def test_chantier_3_environmental_webhooks(self):
        """Chantier 3 : Vérification de la classification des webhooks d'ambiance et nettoyage du préfixe ⚜ |."""
        env_list = [
            '🌳〕La Forêt', '🦉〕Les Oiseaux', "🎓〕L'Académie", '🗨〕Le Sigile',
            '🪙〕Le Trésor', '🪙〕𝐋e-𝐓résor', '🐺〕La Bête', '💬〕Le Mot', '💬〕𝐋e-𝐌ot',
            '⚔〕Le Guerrier', '🌾〕Le Marais', '🧿〕La Folie', '🌑〕Le Monarque.', 'VICTAE IUSTICIA'
        ]
        for w in env_list:
            self.assertTrue(is_gm_bot_actor(w), f"{w} doit être reconnu par is_gm_bot_actor")
            self.assertTrue(is_system_narrator_name(w), f"{w} doit être reconnu par is_system_narrator_name")

        # Nettoyage du préfixe ⚜ | pour restaurer les acteurs réels
        self.assertEqual(clean_character_name("⚜ | Sha'al Langster"), "Sha'al Langster")
        self.assertEqual(clean_character_name("⚜ | Myrane Jaster"), "Myrane Jaster")

        # Vérification qu'un joueur avec ⚜ | n'est pas classé en narrateur
        self.assertFalse(is_system_narrator_name("⚜ | Sha'al Langster"))
        self.assertFalse(is_system_narrator_name("⚜ | Myrane Jaster"))

    def test_chantier_5_official_palette(self):
        """Chantier 5 : Vérification de la charte chromatique officielle."""
        # FACTION_INFO dans extract_du_serveur
        self.assertEqual(FACTION_INFO[1327646236760608803][1], "#ef4444") # La Garde Pourpre
        self.assertEqual(FACTION_INFO[1327646236760608802][1], "#3b82f6") # Cercle d'Azur
        self.assertEqual(FACTION_INFO[1327646236760608801][1], "#fef08a") # Voile d'Ivoire
        self.assertEqual(FACTION_INFO[1467532532261322813][1], "#cbd5e1") # L'œil (gris argenté)
        self.assertEqual(FACTION_INFO[1475090340557095003][1], "#eab308") # Sans guilde

        # Aucune couleur noire #0e0d0d
        all_colors = [v[1] for v in FACTION_INFO.values()]
        self.assertNotIn("#0e0d0d", all_colors)
        self.assertNotIn("#b40000", all_colors)
        self.assertNotIn("#305ed3", all_colors)
        self.assertNotIn("#ffffd4", all_colors)
        self.assertNotIn("#e2ce7d", all_colors)

    def test_chantier_6_narrative_titles_and_timestamps(self):
        """Chantier 6 : Extraction de titre et sécurisation des timestamps."""
        # Extraction de titre markdown
        text_hash = "# L'Ombre du Passé\nVoici la suite de l'histoire..."
        self.assertEqual(extract_title_from_text(text_hash, "Salon", 1), "L'Ombre du Passé")

        text_bold = "**Le Jugement Dernier**\nTout s'arrêta brusquement."
        self.assertEqual(extract_title_from_text(text_bold, "Salon", 1), "Le Jugement Dernier")

        # Timestamp nul ou vide retourne 0
        self.assertEqual(parse_timestamp_v2(""), 0)
        self.assertEqual(parse_timestamp_v2(None), 0)
        self.assertEqual(parse_timestamp_v2("invalid_date"), 0)

    def test_chantier_7_scenes_json_integrity(self):
        """Chantier 7 : Audit automatisé complet de l'intégrité de src/scenes.json."""
        scenes_file = os.path.join("src", "scenes.json")
        self.assertTrue(os.path.exists(scenes_file), "src/scenes.json doit exister")

        with open(scenes_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        scenes = data.get("scenes", [])
        chars = data.get("characters", {})

        # 1. 0 scène avec du contenu fuité HRP ou pur ping résiduel
        self.assertNotIn("scene_La_sœur_1", [s.get("id") for s in scenes], "scene_La_sœur_1 doit être absente")

        for s in scenes:
            ch = s.get("channel", "")
            self.assertFalse(ch.startswith("◦─────────────◦"), f"Salon décoratif non exclu : {s.get('id')}")
            for m in s.get("messages", []):
                content = m.get("content", "")
                self.assertNotIn("184984566673440768", content, f"Ping 184984566673440768 résiduel dans {s.get('id')}")
                self.assertNotIn("gak_azur:1514356539304050708", content, f"Emoji ping gak_azur résiduel dans {s.get('id')}")
                self.assertNotEqual(content.strip(), "Chambre de (Vide)", f"Scorie Chambre de (Vide) dans {s.get('id')}")

        # 2. Aucun nom de salon environnemental dans scene['actors'] ni dans characters
        env_names = {
            '🌳〕La Forêt', '🦉〕Les Oiseaux', "🎓〕L'Académie", '🗨〕Le Sigile',
            '🪙〕Le Trésor', '🪙〕𝐋e-𝐓résor', '🐺〕La Bête', '💬〕Le Mot', '💬〕𝐋e-𝐌ot',
            '⚔〕Le Guerrier', '🌾〕Le Marais', '🧿〕La Folie', '🌑〕Le Monarque.', 'VICTAE IUSTICIA'
        }
        for s in scenes:
            for actor in s.get("actors", []):
                self.assertNotIn(actor, env_names, f"Webhook de décor trouvé dans actors de {s.get('id')} : {actor}")
                self.assertFalse(actor.startswith("⚜ | "), f"Préfixe résiduel dans actors de {s.get('id')} : {actor}")

        for char_name in chars.keys():
            self.assertNotIn(char_name, env_names, f"Webhook de décor trouvé dans characters : {char_name}")
            self.assertFalse(char_name.startswith("⚜ | "), f"Préfixe résiduel dans characters : {char_name}")

        # 3. Aucun personnage fantôme (0 message, 0 scène) dans characters
        active_entities = set()
        for s in scenes:
            active_entities.update(s.get("actors", []))
            for m in s.get("messages", []):
                if m.get("author"):
                    active_entities.add(m.get("author"))

        official_narrators = {"Oeil", "LE CONSEILLER", "OWL LE MESSAGER", "LES MISSIVES"}
        for char_name in chars.keys():
            if char_name in official_narrators:
                continue
            self.assertIn(char_name, active_entities, f"Personnage fantôme sans scène/message : {char_name}")

        # 4. Cohérence chromatique : 1 seule couleur par rôle, aucune couleur noire #0e0d0d
        forbidden_hex = {"#0e0d0d", "#b40000", "#305ed3", "#ffffd4", "#e2ce7d"}
        role_colors = {}
        for char_name, meta in chars.items():
            col = meta.get("color")
            role = meta.get("role")
            self.assertNotIn(col, forbidden_hex, f"Couleur obsolète/interdite {col} pour {char_name}")
            role_colors.setdefault(role, set()).add(col)

        for role, color_set in role_colors.items():
            self.assertEqual(len(color_set), 1, f"Plusieurs couleurs pour le rôle '{role}' : {color_set}")

        # 5. Présence obligatoire des narrateurs système avec couleurs officielles
        for n_name in official_narrators:
            self.assertIn(n_name, chars, f"Narrateur système absent de characters : {n_name}")
            meta = chars[n_name]
            if n_name == "Oeil":
                self.assertEqual(meta.get("role"), "L'œil")
                self.assertEqual(meta.get("color"), "#cbd5e1")
            else:
                self.assertEqual(meta.get("role"), "PNJ")
                self.assertEqual(meta.get("color"), "#c084fc")

if __name__ == "__main__":
    unittest.main()
