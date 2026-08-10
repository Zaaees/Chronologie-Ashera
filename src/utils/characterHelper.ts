import { CHARACTERS_DATA, SCENES_DATA } from '../data';

// Map of image basenames in public/Personnages
export const KNOWN_CHARACTER_IMAGES: Record<string, string> = {
  "adelina del fuego": "Adelina Del Fuego.jpg",
  "aegnor othar": "Aegnor Othar.jpg",
  "akane tsukishiro": "Akane Tsukishiro.jpg",
  "arun acharya": "Arun Acharya.jpg",
  "aryanna erhendil": "Aryanna Erhendil.jpg",
  "aryana erhendil taurielle": "Aryanna Erhendil.jpg",
  "aryana erhendil": "Aryanna Erhendil.jpg",
  "asior eveus": "Asior Eveus.jpg",
  "bozdag dermirhan": "Bozdag Dermirhan.jpg",
  "brutus redwitch": "Brutus Redwitch.jpg",
  "cassian ortie": "Cassian Ortie.jpg",
  "frey guðfrøðr": "Frey Guðfrøðr.jpg",
  "frey - elear": "Frey Guðfrøðr.jpg",
  "frey elear": "Frey Guðfrøðr.jpg",
  "hedwig von glanzestern": "Hedwig Von Glanzestern.jpg",
  "idelmée cadree": "Idelmée Cadree.jpg",
  "iscarioth": "Iscarioth.jpg",
  "zaes ley vaelric": "Iscarioth.jpg",
  "ley vaelric": "Iscarioth.jpg",
  "zaes": "Iscarioth.jpg",
  "isis faerieth": "Isis Faerieth.jpg",
  "ivara luella": "Ivara Luella.jpg",
  "jasp nah": "Jasp Nah.jpg",
  "junko anarchy": "Junko Anarchy.jpg",
  "katelynn hoffmann": "Katelynn Hoffmann.jpg",
  "yuu katelyn hoffmann": "Katelynn Hoffmann.jpg",
  "katelyn hoffmann": "Katelynn Hoffmann.jpg",
  "kenji takahashi": "Kenji Takahashi.jpg",
  "lewis bamer": "Lewis Bamer.jpg",
  "loyis delacroix": "Loyis Delacroix.jpg",
  "lucia fiorella": "Lucia Fiorella.jpg",
  "lumia faendharts": "Lumia Faendharts.jpg",
  "maëll fol'dun": "Maëll Fol'Dun.jpg",
  "mael fol'dun astyell": "Maëll Fol'Dun.jpg",
  "mael fol'dun": "Maëll Fol'Dun.jpg",
  "myrea m": "Myrea M.jpg",
  "nick sol": "Nick Sol.jpg",
  "ragde umbras": "Ragde Umbras.jpg",
  "red roadman": "Red Roadman.jpg",
  "red": "Red Roadman.jpg",
  "ren urugaki": "Ren Urugaki.jpg",
  "selena moon": "Selena Moon.jpg",
  "septimus kales": "Septimus Kales.jpg",
  "tarrion tombetoile": "Tarrion Tombetoile.jpg",
  "tenebris": "Tenebris.jpg",
  "velka valcyrion": "Velka Valcyrion.jpg",
  "vosk sulyvan": "Vosk Sulyvan.jpg",
  "sulyvan vosk": "Vosk Sulyvan.jpg",
  "sulyvan vosk hussh": "Vosk Sulyvan.jpg",
  "hussh": "Vosk Sulyvan.jpg",
  "hush": "Vosk Sulyvan.jpg"
};

function normalizeStr(str: string): string {
  return str
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/['’\s_-]/g, "");
}

function getTokens(str: string): string[] {
  return str
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]/g, " ")
    .trim()
    .split(/\s+/)
    .filter(t => t.length > 1);
}

// Normalized map for quick lookup
const normalizedImageMap: Record<string, string> = {};
Object.entries(KNOWN_CHARACTER_IMAGES).forEach(([key, filename]) => {
  normalizedImageMap[normalizeStr(key)] = filename;
});

export function getCharacterCardImage(actorName: string): string | null {
  if (!actorName) return null;
  const exact = KNOWN_CHARACTER_IMAGES[actorName.toLowerCase()];
  if (exact) return `./Personnages/${exact}`;

  const normActor = normalizeStr(actorName);
  if (!normActor || normActor.length < 3) return null;

  if (normalizedImageMap[normActor]) {
    return `./Personnages/${normalizedImageMap[normActor]}`;
  }

  // Try substring matching for sufficiently long keys
  for (const [normKey, filename] of Object.entries(normalizedImageMap)) {
    if (normKey.length >= 4 && (normActor.includes(normKey) || normKey.includes(normActor))) {
      return `./Personnages/${filename}`;
    }
  }

  // Try token matching (e.g. Sulyvan Vosk vs Vosk Sulyvan)
  const actorTokens = getTokens(actorName);
  for (const [key, filename] of Object.entries(KNOWN_CHARACTER_IMAGES)) {
    const keyTokens = getTokens(key);
    if (keyTokens.length > 0 && keyTokens.every(kt => actorTokens.includes(kt))) {
      return `./Personnages/${filename}`;
    }
  }

  return null;
}

export interface CharacterStats {
  name: string;
  role: string;
  color: string;
  displayName?: string;
  username?: string;
  cardImage: string | null;
  totalScenes: number;
  totalMessages: number;
  topChannels: { name: string; count: number }[];
  coActors: { name: string; count: number }[];
}

export function getCharacterStats(actorName: string): CharacterStats | null {
  const charInfo = CHARACTERS_DATA[actorName];
  const role = charInfo?.role || 'Sans rôle';
  const color = charInfo?.color || '#94a3b8';
  const displayName = charInfo?.displayName;
  const username = charInfo?.username;

  // Filter scenes for this actor
  const actorScenes = SCENES_DATA.filter(s => s.actors && s.actors.includes(actorName));
  const totalScenes = actorScenes.length;

  if (totalScenes === 0 && !charInfo) return null;

  let totalMessages = 0;
  const channelCounts: Record<string, number> = {};
  const coActorCounts: Record<string, number> = {};

  actorScenes.forEach(scene => {
    // Count messages from this actor if message list exists
    if (scene.messages && scene.messages.length > 0) {
      const actorMsgs = scene.messages.filter(m => m.author === actorName).length;
      totalMessages += actorMsgs > 0 ? actorMsgs : scene.message_count;
    } else {
      totalMessages += scene.message_count;
    }

    // Channel stats
    const ch = scene.channel;
    if (ch) {
      channelCounts[ch] = (channelCounts[ch] || 0) + 1;
    }

    // Co-actor stats (exclut les PNJ)
    if (scene.actors) {
      scene.actors.forEach(co => {
        if (co !== actorName) {
          const coInfo = CHARACTERS_DATA[co];
          const isPnj = coInfo?.role === 'PNJ' || coInfo?.role === 'pnj' || (coInfo as any)?.status === 'SYSTEM' || (coInfo as any)?.status === 'RECURRING_NPC';
          if (!isPnj) {
            coActorCounts[co] = (coActorCounts[co] || 0) + 1;
          }
        }
      });
    }
  });

  const topChannels = Object.entries(channelCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 4);

  const coActors = Object.entries(coActorCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  const cardImage = getCharacterCardImage(actorName);

  return {
    name: actorName,
    role,
    color,
    displayName,
    username,
    cardImage,
    totalScenes,
    totalMessages,
    topChannels,
    coActors
  };
}
