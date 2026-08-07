import rawData from './scenes.json';

export interface Character {
  role: string;
  color: string;
  colorName?: string;
  username?: string;
  displayName?: string;
  avatarUrl?: string;
}

export interface Message {
  id: string;
  author: string;
  timestamp: string;
  content: string;
  embed_title?: string;
  embed_description?: string;
  avatar_url?: string;
}

export interface Scene {
  id: string;
  channel: string;
  channel_id?: string;
  category?: string;
  title: string;
  actors: string[];
  start_time: string;
  end_time: string;
  preview: string;
  message_count: number;
  discord_url?: string;
  location_image?: string;
  location_description?: string;
  thread_name?: string;
  messages: Message[];
}

interface RawDataType {
  characters: Record<string, Character>;
  scenes: Scene[];
  channel_images?: Record<string, string>;
}

const typedRawData = rawData as unknown as RawDataType;

export const CHARACTERS_DATA: Record<string, Character> = typedRawData.characters;
export const SCENES_DATA: Scene[] = typedRawData.scenes;
export const CHANNEL_IMAGES: Record<string, string> = typedRawData.channel_images || {};

export const CATEGORY_DEFAULT_IMAGE_MAP: Record<string, string> = {
  '| ✦ |  BASSE-VILLE': '🌇〕𝐑uelle-𝐁asse-ville',
  '| ✵ |  LE HEAUME BLANC': '⚪〕𝗖ouloir-Ｂlanc',
  '| ✵ |  GRANDE SALLE PORCELAINE': '⚜️〕𝗚rande-salle-porcelaine',
  '| ✵ |  ATRIUM CANOPUS': '🏛️〕𝗧ribut-des-sages',
  '| ✠ |   LE BASTION ÉCARLATE': '🏮〕𝗖rypte-𝗥ouge',
  '| ۩ |   L\'OBSERVATOIRE CÉRULÉEN': '📚〕Ｂibliothèque-𝗔zure',
  '| ♖ |  LE FORUM ÉBURNÉEN': '♟️〕𝗟e-𝗖afé-des-𝗣hilosophes',
  '𝑼𝒎𝒃𝒓𝒂𝒆𝒍': '🏙️〕𝐄gregore',
  'Demeure du Sabre': '🗡️〕𝗤uartier-des-𝗙orges'
};

export const THREAD_TO_PARENT_CHANNEL_MAP: Record<string, string> = {
  'Rencontre entre reflets': '🌸〕𝗖ours-𝗙leurie',
  'Un début de soirée à la serre de lune': '🍃〕𝗦erre-de-lune'
};

export function getSceneLocationImage(scene?: Scene | null): string | undefined {
  if (!scene) return undefined;

  const ch = scene.channel;
  if (ch && CHANNEL_IMAGES[ch]) return CHANNEL_IMAGES[ch];
  if (scene.thread_name && CHANNEL_IMAGES[scene.thread_name]) return CHANNEL_IMAGES[scene.thread_name];
  if (scene.location_image) return scene.location_image;

  if (ch && THREAD_TO_PARENT_CHANNEL_MAP[ch]) {
    const parent = THREAD_TO_PARENT_CHANNEL_MAP[ch];
    if (parent && CHANNEL_IMAGES[parent]) return CHANNEL_IMAGES[parent];
  }

  if (ch && ch.toLowerCase().includes('chambre')) {
    if (CHANNEL_IMAGES['⚪〕𝗖ouloir-Ｂlanc']) return CHANNEL_IMAGES['⚪〕𝗖ouloir-Ｂlanc'];
  }

  const cleanCh = (ch || '').replace(/[^\w]/g, '').toLowerCase();
  if (cleanCh) {
    const entry = Object.entries(CHANNEL_IMAGES).find(([k, v]) => {
      const cleanK = k.replace(/[^\w]/g, '').toLowerCase();
      return cleanK && (cleanK.includes(cleanCh) || cleanCh.includes(cleanK));
    });
    if (entry && entry[1]) return entry[1];
  }

  const cat = scene.category ? scene.category.trim() : '';
  if (cat) {
    for (const [cKey, cVal] of Object.entries(CATEGORY_DEFAULT_IMAGE_MAP)) {
      if (cat.includes(cKey.trim()) || cKey.trim().includes(cat)) {
        if (CHANNEL_IMAGES[cVal]) return CHANNEL_IMAGES[cVal];
      }
    }
  }

  return undefined;
}


