import rawData from './scenes.json';
import rawDataV2 from './scenes_v2.json';
import { CharacterV2 } from './utils/characterHelperV2';
import { SceneV2 } from './utils/sceneSorterV2';

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

interface RawDataTypeV2 {
  metadata: {
    version: string;
    generated_at: string;
    total_scenes: number;
    total_characters: number;
  };
  characters: Record<string, CharacterV2>;
  scenes: SceneV2[];
}

const typedRawData = rawData as unknown as RawDataType;
const typedRawDataV2 = rawDataV2 as unknown as RawDataTypeV2;

export const CHARACTERS_DATA: Record<string, Character> = typedRawData.characters;
export const SCENES_DATA: Scene[] = typedRawData.scenes;
export const CHANNEL_IMAGES: Record<string, string> = typedRawData.channel_images || {};

export const CHARACTERS_DATA_V2: Record<string, CharacterV2> = typedRawDataV2.characters;
export const SCENES_DATA_V2: SceneV2[] = typedRawDataV2.scenes;
export const METADATA_V2 = typedRawDataV2.metadata;
