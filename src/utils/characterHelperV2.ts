import { KNOWN_CHARACTER_IMAGES } from './characterHelper';

export interface CharacterV2 {
  name: string;
  role: string;
  color: string;
  status: 'MAIN_PC' | 'RECURRING_NPC' | 'SYSTEM';
  totalScenes: number;
  totalMessages: number;
}

export interface CharacterStatsV2 {
  name: string;
  role: string;
  color: string;
  status: 'MAIN_PC' | 'RECURRING_NPC' | 'SYSTEM';
  cardImage: string | null;
  totalScenes: number;
  totalMessages: number;
  topChannels: { name: string; count: number }[];
  coActors: { name: string; count: number }[];
}

export function getCharacterCardImageV2(actorName: string): string | null {
  if (!actorName) return null;
  const exact = KNOWN_CHARACTER_IMAGES[actorName.toLowerCase()];
  if (exact) return `./Personnages/${exact}`;

  const normActor = actorName.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "");
  for (const [key, filename] of Object.entries(KNOWN_CHARACTER_IMAGES)) {
    const normKey = key.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "");
    if (normKey && (normActor.includes(normKey) || normKey.includes(normActor))) {
      return `./Personnages/${filename}`;
    }
  }
  return null;
}

export function sortCharactersV2(
  charactersList: CharacterV2[],
  sortBy: 'activity' | 'name' | 'faction' | 'status',
  filterRole?: string,
  searchQuery?: string
): CharacterV2[] {
  let result = [...charactersList];

  if (filterRole && filterRole !== 'all') {
    result = result.filter(c => c.role === filterRole);
  }

  if (searchQuery && searchQuery.trim()) {
    const q = searchQuery.toLowerCase().trim();
    result = result.filter(c => c.name.toLowerCase().includes(q));
  }

  result.sort((a, b) => {
    if (sortBy === 'activity') {
      return (b.totalScenes * 10 + b.totalMessages) - (a.totalScenes * 10 + a.totalMessages);
    }
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name, 'fr');
    }
    if (sortBy === 'faction') {
      return a.role.localeCompare(b.role, 'fr');
    }
    if (sortBy === 'status') {
      const rank = { MAIN_PC: 1, RECURRING_NPC: 2, SYSTEM: 3 };
      return (rank[a.status] || 99) - (rank[b.status] || 99);
    }
    return 0;
  });

  return result;
}
