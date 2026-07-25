import rawData from './scenes.json';

export interface Character {
  role: string;
  color: string;
  colorName?: string;
  username?: string;
  displayName?: string;
}

export interface Message {
  id: string;
  author: string;
  timestamp: string;
  content: string;
  embed_title?: string;
  embed_description?: string;
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
  messages: Message[];
}

interface RawDataType {
  characters: Record<string, Character>;
  scenes: Scene[];
}

const typedRawData = rawData as unknown as RawDataType;

export const CHARACTERS_DATA: Record<string, Character> = typedRawData.characters;
export const SCENES_DATA: Scene[] = typedRawData.scenes;
