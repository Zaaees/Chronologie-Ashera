export interface SceneMessageV2 {
  author: string;
  timestamp: string;
  content: string;
}

export interface SceneV2 {
  id: string;
  channel_raw: string;
  channel_clean: string;
  title: string;
  actors: string[];
  main_actor: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  preview: string;
  message_count: number;
  word_count: number;
  location_image?: string | null;
  faction_distribution?: Record<string, number>;
  messages?: SceneMessageV2[];
}

export type SceneSortOptionV2 = 
  | 'date_desc' 
  | 'date_asc' 
  | 'messages_desc' 
  | 'words_desc' 
  | 'duration_desc' 
  | 'title_asc';

export interface SceneFilterOptionsV2 {
  searchQuery?: string;
  selectedFaction?: string;
  selectedActor?: string;
  selectedChannel?: string;
  minMessages?: number;
}

export function filterScenesV2(scenes: SceneV2[], filters: SceneFilterOptionsV2): SceneV2[] {
  return scenes.filter(scene => {
    // 1. Text Search (title, actors, preview, channel)
    if (filters.searchQuery && filters.searchQuery.trim()) {
      const q = filters.searchQuery.toLowerCase().trim();
      const titleMatch = scene.title.toLowerCase().includes(q);
      const actorMatch = scene.actors.some(a => a.toLowerCase().includes(q));
      const channelMatch = (scene.channel_clean || scene.channel_raw || '').toLowerCase().includes(q);
      const previewMatch = scene.preview.toLowerCase().includes(q);

      if (!titleMatch && !actorMatch && !channelMatch && !previewMatch) {
        return false;
      }
    }

    // 2. Faction filter
    if (filters.selectedFaction && filters.selectedFaction !== 'all') {
      if (!scene.faction_distribution || !scene.faction_distribution[filters.selectedFaction]) {
        return false;
      }
    }

    // 3. Actor filter
    if (filters.selectedActor && filters.selectedActor !== 'all') {
      if (!scene.actors.includes(filters.selectedActor)) {
        return false;
      }
    }

    // 4. Channel filter
    if (filters.selectedChannel && filters.selectedChannel !== 'all') {
      if (scene.channel_clean !== filters.selectedChannel && scene.channel_raw !== filters.selectedChannel) {
        return false;
      }
    }

    // 5. Min messages filter
    if (filters.minMessages && filters.minMessages > 0) {
      if (scene.message_count < filters.minMessages) {
        return false;
      }
    }

    return true;
  });
}

export function sortScenesV2(scenes: SceneV2[], sortBy: SceneSortOptionV2): SceneV2[] {
  const result = [...scenes];

  result.sort((a, b) => {
    switch (sortBy) {
      case 'date_desc':
        return new Date(b.start_time).getTime() - new Date(a.start_time).getTime();
      case 'date_asc':
        return new Date(a.start_time).getTime() - new Date(b.start_time).getTime();
      case 'messages_desc':
        return b.message_count - a.message_count;
      case 'words_desc':
        return b.word_count - a.word_count;
      case 'duration_desc':
        return b.duration_minutes - a.duration_minutes;
      case 'title_asc':
        return a.title.localeCompare(b.title, 'fr');
      default:
        return 0;
    }
  });

  return result;
}

export function groupScenesByMonthV2(scenes: SceneV2[]): { key: string; label: string; scenes: SceneV2[] }[] {
  const groups: Record<string, { label: string; scenes: SceneV2[] }> = {};

  scenes.forEach(scene => {
    let key = 'inconnu';
    let label = 'Période Indéterminée';

    if (scene.start_time) {
      try {
        const d = new Date(scene.start_time);
        if (!isNaN(d.getTime())) {
          key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
          const monthStr = d.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
          label = monthStr.charAt(0).toUpperCase() + monthStr.slice(1);
        }
      } catch (e) {
        // ignore
      }
    }

    if (!groups[key]) {
      groups[key] = { label, scenes: [] };
    }
    groups[key].scenes.push(scene);
  });

  return Object.entries(groups)
    .sort(([keyA], [keyB]) => keyB.localeCompare(keyA))
    .map(([key, data]) => ({
      key,
      label: data.label,
      scenes: data.scenes
    }));
}
