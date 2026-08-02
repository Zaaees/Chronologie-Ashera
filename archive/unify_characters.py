import json, sys, re, unicodedata, os, shutil

sys.stdout.reconfigure(encoding='utf-8')

# Canonical mapping rules (maps any nickname, raw username, or Discord display variant to EXACTLY 1 Canonical Character Name)
CANONICAL_MAP = {
    # 35 Main Characters with Images
    "adelina del fuego": "Adelina Del Fuego",
    "adelina del fuego mari": "Adelina Del Fuego",
    "marigold": "Adelina Del Fuego",
    "_marigld": "Adelina Del Fuego",
    
    "aegnor othar": "Aegnor Othar",
    "tcizab": "Aegnor Othar",
    "tcizabaegnor othar": "Aegnor Othar",
    "tcizab aegnor othar": "Aegnor Othar",
    
    "akane tsukishiro": "Akane Tsukishiro",
    "tsukishiro akane": "Akane Tsukishiro",
    "doppelganger2830": "Akane Tsukishiro",
    
    "arun acharya": "Arun Acharya",
    "arun acharya freulonlezouin": "Arun Acharya",
    "freulonlezouinzouin": "Arun Acharya",
    "nyson": "Arun Acharya",
    
    "aryanna erhendil": "Aryanna Erhendil",
    "aryana erhendil": "Aryanna Erhendil",
    "aryana erhendil taurielle": "Aryanna Erhendil",
    "taurielle": "Aryanna Erhendil",
    "tutaurielle": "Aryanna Erhendil",
    
    "asior eveus": "Asior Eveus",
    "eopia asior eveus": "Asior Eveus",
    "eopia": "Asior Eveus",
    
    "bozdag dermirhan": "Bozdag Dermirhan",
    "clipmyr": "Bozdag Dermirhan",
    "clip demirhan bozdag": "Bozdag Dermirhan",
    
    "brutus redwitch": "Brutus Redwitch",
    "kinoru": "Brutus Redwitch",
    
    "cassian ortie": "Cassian Ortie",
    "chulakita": "Cassian Ortie",
    "chulak cassian ortie": "Cassian Ortie",
    "chulaktm": "Cassian Ortie",
    
    "frey gudfrodur": "Frey Guðfrøðr",
    "frey guðfrøðr": "Frey Guðfrøðr",
    "frey elear": "Frey Guðfrøðr",
    "frey - elear": "Frey Guðfrøðr",
    "elessai": "Frey Guðfrøðr",
    
    "hedwig von glanzestern": "Hedwig Von Glanzestern",
    "twisted_servant": "Hedwig Von Glanzestern",
    
    "idelmee cadree": "Idelmée Cadree",
    "idelmee cadere": "Idelmée Cadree",
    "momo idelmee cadere": "Idelmée Cadree",
    "momotarie": "Idelmée Cadree",
    "momo": "Idelmée Cadree",
    
    "iscarioth": "Iscarioth",
    "zaes ley vaelric": "Iscarioth",
    "ley vaelric": "Iscarioth",
    "zaes": "Iscarioth",
    "zaaes": "Iscarioth",
    
    "isis faerieth": "Isis Faerieth",
    "etoile isis faerieth": "Isis Faerieth",
    "etoile": "Isis Faerieth",
    "letoiledeminuit": "Isis Faerieth",
    
    "ivara luella": "Ivara Luella",
    "ivara luell": "Ivara Luella",
    "elisabeeh ivara luell": "Ivara Luella",
    "elisabeeeeh": "Ivara Luella",
    
    "jasp nah": "Jasp Nah",
    "nah jasp": "Jasp Nah",
    
    "junko anarchy": "Junko Anarchy",
    "luden junko anarchy": "Junko Anarchy",
    "luden": "Junko Anarchy",
    "luden_chan": "Junko Anarchy",
    
    "katelynn hoffmann": "Katelynn Hoffmann",
    "katelyn hoffmann": "Katelynn Hoffmann",
    "yuu katelyn hoffmann": "Katelynn Hoffmann",
    "its_yuu": "Katelynn Hoffmann",
    "yuu": "Katelynn Hoffmann",
    
    "kenji takahashi": "Kenji Takahashi",
    "kenji takahashi heavil": "Kenji Takahashi",
    "heavil4444": "Kenji Takahashi",
    "heavil": "Kenji Takahashi",
    
    "lewis bamer": "Lewis Bamer",
    "lewis bamer historious": "Lewis Bamer",
    
    "loyis delacroix": "Loyis Delacroix",
    "happy loyis delacroix": "Loyis Delacroix",
    "happy_is_happy": "Loyis Delacroix",
    "happy": "Loyis Delacroix",
    
    "lucia fiorella": "Lucia Fiorella",
    "ju lucia bunny fiorella": "Lucia Fiorella",
    "juju_la_best": "Lucia Fiorella",
    
    "lumia faendharts": "Lumia Faendharts",
    "lumia lum faendhartslumiere": "Lumia Faendharts",
    "lueur_": "Lumia Faendharts",
    
    "maell fol'dun": "Maëll Fol'Dun",
    "mael fol'dun": "Maëll Fol'Dun",
    "mael fol'dun astyell": "Maëll Fol'Dun",
    "astyell": "Maëll Fol'Dun",
    
    "myrea m": "Myrea M",
    "khem myrea m": "Myrea M",
    "khemm": "Myrea M",
    "khem": "Myrea M",
    
    "nick sol": "Nick Sol",
    "prince nick sol": "Nick Sol",
    "harderbae": "Nick Sol",
    "_aura_": "Nick Sol",
    
    "ragde umbras": "Ragde Umbras",
    "personnes_10": "Ragde Umbras",
    "personne": "Ragde Umbras",
    
    "red roadman": "Red Roadman",
    "red": "Red Roadman",
    "jivwd": "Red Roadman",
    
    "ren urugaki": "Ren Urugaki",
    "noci urugaki ren": "Ren Urugaki",
    "urugaki ren": "Ren Urugaki",
    "nociferoce": "Ren Urugaki",
    "noci": "Ren Urugaki",
    
    "selena moon": "Selena Moon",
    "seléna moon": "Selena Moon",
    "gwenphasehikena": "Selena Moon",
    
    "septimus kales": "Septimus Kales",
    "ryo kales septimus": "Septimus Kales",
    
    "tarrion tombetoile": "Tarrion Tombetoile",
    "tarrion tombetoile biboon": "Tarrion Tombetoile",
    "biboon": "Tarrion Tombetoile",
    
    "tenebris": "Tenebris",
    "___val___": "Tenebris",
    "_val_": "Tenebris",
    
    "velka valcyrion": "Velka Valcyrion",
    "norxas": "Velka Valcyrion",
    
    "vosk sulyvan": "Vosk Sulyvan",
    "sulyvan vosk": "Vosk Sulyvan",
    "sulyvan vosk hussh": "Vosk Sulyvan",
    "hussh": "Vosk Sulyvan",
    "hush": "Vosk Sulyvan",
    
    # Additional Characters
    "aether": "Æther",
    "æther": "Æther",
    "miklelait": "Æther",
    "mikle": "Æther",
    
    "jap yunah aoi enjaku": "Yunah Aoi Enjaku",
    "yunah aoi enjaku": "Yunah Aoi Enjaku",
    "jaaapaannnnnnnnnnn": "Yunah Aoi Enjaku",
    "jaaaaaaaaaapaaaaaaaaaaaaan": "Yunah Aoi Enjaku",
    
    "kuikui - astreus mylonas": "Astreüs Mylonas",
    "kuikui - astreüs mylonas": "Astreüs Mylonas",
    "astreus mylonas": "Astreüs Mylonas",
    "kuikuito": "Astreüs Mylonas",
    
    "jin alurantes": "Jin Alurantes",
    "elouand": "Jin Alurantes",
    
    "inzu sravel - instructeur de la garde pourpre": "Inzu Sravel",
    "inzu sravel - garde pourpre": "Inzu Sravel",
    "inzu sravel": "Inzu Sravel",
    
    "hector swaft - mage de rang 3": "Hector Swaft",
    "hector swaft": "Hector Swaft",
    
    "milli enga - mange de rang 2": "Milli Enga",
    "milli enga": "Milli Enga",
    
    "vieux debile tsutomu yamamoto": "Tsutomu Yamamoto",
    "vieux debile": "Tsutomu Yamamoto",
    "tsutomu yamamoto": "Tsutomu Yamamoto",
    "reverse.d": "Tsutomu Yamamoto",
    "reverse": "Tsutomu Yamamoto",
    "reversed": "Tsutomu Yamamoto",

    "emil camille rebenok": "Emil Camille Rebenok",
    "emil": "Emil Camille Rebenok",
    "indominushunter": "Emil Camille Rebenok",
    
    "rias valdor - cheffe de la famille valdor": "Rias Valdor",
    "rias valdor": "Rias Valdor",
    
    "lewis-phoebe d'ashbourne": "Lewis-Phoebe d'Ashbourne",
    "lewis phoebe ashbourne": "Lewis-Phoebe d'Ashbourne",

    "leonore edelweiss": "Léonore Edelweiss",
    "leonore edelweiss ana": "Léonore Edelweiss",
    "ana_non": "Léonore Edelweiss",

    "bourpiff markus law": "Markus Law",
    "bourpiff": "Markus Law",
    "markus law": "Markus Law",

    "orla kalem crowley": "Kalem Crowley",
    "orla": "Kalem Crowley",
    "orla_": "Kalem Crowley",

    "eldren gates": "Eldren Gates"
}

def clean_key(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = re.sub(r'[\u0300-\u036f]', '', s)
    return re.sub(r'[^a-z0-9]', '', s)

LOOKUP = {}
for k, v in CANONICAL_MAP.items():
    LOOKUP[clean_key(k)] = v

def get_canonical_name(raw_name):
    if not raw_name: return "Narrateur"
    ck = clean_key(raw_name)
    if ck in LOOKUP:
        return LOOKUP[ck]
    
    for k, v in LOOKUP.items():
        if len(k) >= 4 and (k in ck or ck in k):
            return v
            
    return raw_name.strip()

# Process scenes.json
with open('scenes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

old_chars = data.get('characters', {})
scenes = data.get('scenes', [])

# Collect all active scene actors
scene_actors_set = set()
for s in scenes:
    new_actors = []
    for a in s.get('actors', []):
        ca = get_canonical_name(a)
        if ca not in new_actors:
            new_actors.append(ca)
        scene_actors_set.add(ca)
    s['actors'] = new_actors
    
    for msg in s.get('messages', []):
        if msg.get('author'):
            msg['author'] = get_canonical_name(msg['author'])

# Canonical values set
CANONICAL_VALUES_SET = set(CANONICAL_MAP.values())

new_chars = {}

for name, info in old_chars.items():
    canon = get_canonical_name(name)
    
    # Retain ONLY if it's an active scene actor OR a recognized Canonical RP Character
    if canon in scene_actors_set or canon in CANONICAL_VALUES_SET:
        if canon not in new_chars:
            new_chars[canon] = dict(info)
        else:
            if new_chars[canon].get('role') == 'Sans rôle' and info.get('role') != 'Sans rôle':
                new_chars[canon]['role'] = info['role']
                new_chars[canon]['color'] = info.get('color', new_chars[canon].get('color'))
                new_chars[canon]['colorName'] = info.get('colorName', new_chars[canon].get('colorName'))
            if info.get('avatarUrl') and not new_chars[canon].get('avatarUrl'):
                new_chars[canon]['avatarUrl'] = info['avatarUrl']

# Ensure all scene actors exist in new_chars
for a in scene_actors_set:
    if a not in new_chars:
        new_chars[a] = {'role': 'Sans rôle', 'color': '#94a3b8', 'colorName': 'char_sans_role'}

data['characters'] = new_chars

print(f"Total clean canonical characters: {len(new_chars)}")

roles_dist = {}
for name, c in new_chars.items():
    r = c.get('role', 'Sans rôle')
    roles_dist[r] = roles_dist.get(r, 0) + 1

print("Clean roles distribution:", roles_dist)
print("\n=== CLEAN CANONICAL CHARACTER LIST BY FACTION ===")
for r in ["La Garde Pourpre", "Cercle d'Azur", "Voile d'Ivoire", "L'œil", "Sans guilde", "PNJ", "Sans rôle"]:
    chars_in_r = [k for k, v in new_chars.items() if v.get('role') == r]
    print(f"\n--- {r} ({len(chars_in_r)}) ---")
    for name in sorted(chars_in_r):
        print("  -", name)

# Save updated files
with open('scenes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

if os.path.exists('src/scenes.json'):
    with open('src/scenes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

with open('data.js', 'w', encoding='utf-8') as f:
    f.write('window.rpData = ')
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write(';\n')

if os.path.exists('Ancien_site/data.js'):
    shutil.copy('data.js', 'Ancien_site/data.js')

print('\nCanonical unification completed!')
