import React, { useState, useMemo, useEffect } from 'react';
import { CHARACTERS_DATA, SCENES_DATA, Scene, Character, Message } from './data';
import { 
  Search, Calendar, Clock, Users, ChevronRight, 
  ExternalLink, Layers, X, ArrowUp, HelpCircle, Shield, Scroll, Eye, Sword, Feather, Sun, Wand2, MessageSquare, Zap, BarChart2, LayoutGrid
} from 'lucide-react';

const FACTION_COLORS: Record<string, { bg: string; text: string; border: string; icon: string; hexColor: string }> = {
  "La Garde Pourpre": { bg: "rgba(153, 27, 27, 0.4)", text: "#fca5a5", border: "rgba(220, 38, 38, 0.75)", icon: "🗡️", hexColor: "#ef4444" },
  "Cercle d'Azur": { bg: "rgba(30, 58, 138, 0.4)", text: "#93c5fd", border: "rgba(59, 130, 246, 0.75)", icon: "🌙", hexColor: "#3b82f6" },
  "Voile d'Ivoire": { bg: "rgba(254, 240, 138, 0.25)", text: "#fef08a", border: "rgba(254, 240, 138, 0.6)", icon: "⚖️", hexColor: "#fef08a" },
  "L'œil": { bg: "rgba(30, 41, 59, 0.85)", text: "#e2e8f0", border: "rgba(148, 163, 184, 0.65)", icon: "👁️", hexColor: "#cbd5e1" },
  "Sans guilde": { bg: "rgba(180, 83, 9, 0.4)", text: "#fde047", border: "rgba(217, 119, 6, 0.75)", icon: "☀️", hexColor: "#eab308" },
  "Sans rôle": { bg: "rgba(71, 85, 105, 0.4)", text: "#cbd5e1", border: "rgba(100, 116, 139, 0.65)", icon: "🛡️", hexColor: "#94a3b8" },
  "PNJ": { bg: "rgba(126, 34, 206, 0.4)", text: "#d8b4fe", border: "rgba(168, 85, 247, 0.75)", icon: "🔮", hexColor: "#c084fc" }
};

// Formater la date en style Discord (ex: 4 février 2026 à 22:15)
function formatDateDiscord(isoString: string): string {
  if (!isoString) return 'Date inconnue';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const dateStr = d.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
    const timeStr = d.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
    return `${dateStr} à ${timeStr}`;
  } catch (e) {
    return isoString;
  }
}

// Obtenir le mois et l'année pour le groupement
function getMonthYearKey(isoString: string): { key: string; label: string } {
  if (!isoString) return { key: 'inconnu', label: 'Période Indéterminée' };
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return { key: 'inconnu', label: 'Période Indéterminée' };
    const month = d.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    return { key, label: month.charAt(0).toUpperCase() + month.slice(1) };
  } catch (e) {
    return { key: 'inconnu', label: 'Période Indéterminée' };
  }
}

// Initiales pour avatar
function getInitials(name: string): string {
  if (!name) return '?';
  const parts = name.trim().split(' ');
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

// Interface pour les pistes Gantt par salon
interface GanttChannelTrack {
  channel: string;
  scenes: {
    scene: Scene;
    leftPercent: number;
    widthPercent: number;
  }[];
}

// COMPOSANT GANTT SWIMLANES DYNAMIQUES PAR MOIS
function GanttMonthView({ monthLabel, scenes, onSelectScene }: { monthLabel: string; scenes: Scene[]; onSelectScene: (s: Scene) => void }) {
  if (scenes.length === 0) return null;

  // Calcul des bornes temporelles min/max du mois
  const timestamps = scenes.flatMap(s => [
    new Date(s.start_time).getTime(),
    new Date(s.end_time || s.start_time).getTime()
  ]).filter(t => !isNaN(t));

  const tMin = Math.min(...timestamps);
  const tMax = Math.max(...timestamps);
  const duration = Math.max(tMax - tMin, 1);

  // Regroupement par salon actif
  const channelMap: Record<string, Scene[]> = {};
  scenes.forEach(s => {
    if (!channelMap[s.channel]) channelMap[s.channel] = [];
    channelMap[s.channel].push(s);
  });

  const tracks: GanttChannelTrack[] = Object.keys(channelMap).map(ch => {
    const chScenes = channelMap[ch];
    return {
      channel: ch,
      scenes: chScenes.map(sc => {
        const sTime = new Date(sc.start_time).getTime();
        const eTime = new Date(sc.end_time || sc.start_time).getTime();
        const left = Math.max(0, ((sTime - tMin) / duration) * 100);
        const rawWidth = Math.max(0.5, ((eTime - sTime) / duration) * 100);
        const width = Math.max(rawWidth, 4.5); // Largeur minimale de 4.5% pour lisibilité et clic
        return {
          scene: sc,
          leftPercent: Math.min(left, 94),
          widthPercent: Math.min(width, 100 - left)
        };
      })
    };
  });

  // 6 Ticks de dates sur la règle supérieure
  const dateTicks = [0, 0.2, 0.4, 0.6, 0.8, 1].map(ratio => {
    const timeAtRatio = tMin + ratio * duration;
    const d = new Date(timeAtRatio);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  });

  return (
    <div className="gothic-corner-box bg-[#0c0e15]/95 border border-slate-700/80 p-5 shadow-2xl space-y-4">
      <div className="gothic-corner gothic-corner-tl" />
      <div className="gothic-corner gothic-corner-tr" />
      <div className="gothic-corner gothic-corner-bl" />
      <div className="gothic-corner gothic-corner-br" />

      {/* En-tête Gantt */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded bg-purple-950/80 border border-purple-500/40 text-purple-300">
            <BarChart2 className="w-4 h-4" />
          </span>
          <div>
            <h3 className="text-xs font-bold font-serif-gothic text-slate-100 tracking-wider uppercase">
              Frise Temporelle des Salons Actifs • {monthLabel}
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">
              {tracks.length} salons actifs en parallèle • {scenes.length} scènes
            </p>
          </div>
        </div>
        <span className="text-[10px] text-slate-400 font-mono bg-slate-950 px-2.5 py-1 border border-slate-800">
          Durée : {dateTicks[0]} → {dateTicks[5]}
        </span>
      </div>

      {/* Conteneur défilable de la Frise Swimlanes */}
      <div className="overflow-x-auto custom-scrollbar">
        <div className="min-w-[950px] space-y-2">
          
          {/* Règle des dates supérieure */}
          <div className="flex items-center mb-2 text-[10px] font-mono text-slate-400 border-b border-slate-800/80 pb-1.5">
            <div className="w-52 shrink-0 font-bold uppercase tracking-wider pl-2 text-slate-300">
              Salons Actifs
            </div>
            <div className="flex-1 flex justify-between px-2">
              {dateTicks.map((t, idx) => (
                <span key={idx} className="text-slate-400 font-semibold">{t}</span>
              ))}
            </div>
          </div>

          {/* Lignes par Salon (Swimlanes) */}
          <div className="space-y-2.5">
            {tracks.map(({ channel, scenes: trackScenes }) => (
              <div key={channel} className="flex items-center h-11 group hover:bg-slate-900/60 rounded transition-colors">
                
                {/* Nom du Salon (Colonne Gauche) */}
                <div className="w-52 shrink-0 pr-3 text-xs font-mono font-medium text-slate-200 flex items-center gap-2 pl-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400 shrink-0" />
                  <span className="truncate" title={`#${channel}`}>#{channel}</span>
                </div>

                {/* Piste Temporelle (Piste Droite) */}
                <div className="flex-1 relative h-9 bg-[#08090d] border border-slate-800 rounded gantt-track-bg overflow-visible">
                  {trackScenes.map(({ scene, leftPercent, widthPercent }) => {
                    const info = CHARACTERS_DATA[scene.actors[0]];
                    const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];
                    const startStr = formatDateDiscord(scene.start_time);
                    const endStr = formatDateDiscord(scene.end_time);
                    const isShort = widthPercent < 10;

                    return (
                      <div
                        key={scene.id}
                        onClick={() => onSelectScene(scene)}
                        style={{
                          left: `${leftPercent}%`,
                          width: `${widthPercent}%`,
                          backgroundColor: style.bg,
                          borderColor: style.border
                        }}
                        className="gantt-bar-item absolute top-0.5 bottom-0.5 border rounded-md px-2 flex items-center justify-between cursor-pointer text-xs select-none group/bar"
                      >
                        {/* CONTENU COMPACT CLAIR SELON LA LARGEUR DE LA BARRE */}
                        <div className="flex items-center gap-1.5 min-w-0 w-full overflow-hidden">
                          <span className="text-xs shrink-0">{style.icon}</span>
                          
                          {/* SI LA BARRE EST RECTANGULAIRE (LARGE) */}
                          {!isShort ? (
                            <div className="flex items-center gap-2 min-w-0 w-full">
                              <span style={{ color: style.text }} className="font-semibold text-xs truncate">
                                {scene.title}
                              </span>
                              {scene.actors.length > 0 && (
                                <span className="text-[10px] text-slate-300/80 font-mono truncate hidden lg:inline">
                                  ({scene.actors.slice(0, 2).join(', ')})
                                </span>
                              )}
                            </div>
                          ) : (
                            /* SI LA BARRE EST ÉTROITE (PETITE SCÈNE) */
                            <span style={{ color: style.text }} className="font-semibold text-[11px] truncate">
                              {scene.actors[0] || scene.title}
                            </span>
                          )}
                        </div>

                        {/* INFO-BULLE RICH DARK FANTASY AU SURVOL (TOOLTIP EXACT) */}
                        <div className="opacity-0 group-hover/bar:opacity-100 pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 bg-[#0c0e15] border border-slate-600 p-3 rounded shadow-2xl z-50 transition-opacity">
                          <div className="flex items-center justify-between gap-2 mb-1.5 pb-1 border-b border-slate-800">
                            <span className="text-[11px] font-mono text-purple-300">#{scene.channel}</span>
                            <span className="text-[10px] font-mono text-slate-400">{scene.messages.length} msg</span>
                          </div>
                          <h4 className="text-xs font-bold text-slate-100 mb-1">{scene.title}</h4>
                          <div className="text-[11px] text-slate-300 font-mono space-y-0.5 mb-2">
                            <div><span className="text-slate-500">Début :</span> {startStr}</div>
                            <div><span className="text-slate-500">Fin :</span> {endStr}</div>
                          </div>
                          <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800">
                            {scene.actors.map(a => (
                              <span key={a} className="px-1.5 py-0.5 bg-slate-900 text-[10px] text-slate-300 rounded border border-slate-700">
                                {a}
                              </span>
                            ))}
                          </div>
                        </div>

                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedActor, setSelectedActor] = useState<string>('all');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [activeMonthKey, setActiveMonthKey] = useState<string>('');
  
  // Scène sélectionnée pour la modale
  const [activeScene, setActiveScene] = useState<Scene | null>(null);

  // Remonter en haut
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Ensemble des acteurs participant au moins à 1 scène
  const activeActorsSet = useMemo(() => {
    const set = new Set<string>();
    SCENES_DATA.forEach(s => s.actors.forEach(a => set.add(a)));
    return set;
  }, []);

  // Groupement des acteurs PAR FACTION (uniquement ceux participant aux scènes)
  const groupedActorsByFaction = useMemo(() => {
    const groups: Record<string, { name: string; displayLabel: string }[]> = {
      "La Garde Pourpre": [],
      "Cercle d'Azur": [],
      "Voile d'Ivoire": [],
      "L'œil": [],
      "Sans guilde": [],
      "Sans rôle": [],
      "PNJ": []
    };

    Object.keys(CHARACTERS_DATA).forEach(actorName => {
      if (!activeActorsSet.has(actorName)) return;

      const charInfo = CHARACTERS_DATA[actorName];
      const role = charInfo?.role || "Sans rôle";
      
      const pseudo = charInfo?.username || charInfo?.displayName;
      const displayLabel = pseudo && pseudo !== actorName 
        ? `${actorName} (${pseudo})` 
        : actorName;

      if (!groups[role]) {
        groups[role] = [];
      }
      groups[role].push({ name: actorName, displayLabel });
    });

    activeActorsSet.forEach(actorName => {
      if (!CHARACTERS_DATA[actorName]) {
        if (!groups["Sans rôle"]) groups["Sans rôle"] = [];
        if (!groups["Sans rôle"].some(x => x.name === actorName)) {
          groups["Sans rôle"].push({ name: actorName, displayLabel: actorName });
        }
      }
    });

    Object.keys(groups).forEach(role => {
      groups[role].sort((a, b) => a.displayLabel.localeCompare(b.displayLabel, 'fr'));
    });

    return groups;
  }, [activeActorsSet]);

  // Groupement des salons par Catégorie Discord
  const groupedChannelsByCategory = useMemo(() => {
    const groups: Record<string, string[]> = {};

    SCENES_DATA.forEach(scene => {
      const cat = scene.category || "Salons Principaux";
      const ch = scene.channel;
      if (!groups[cat]) {
        groups[cat] = [];
      }
      if (!groups[cat].includes(ch)) {
        groups[cat].push(ch);
      }
    });

    Object.keys(groups).forEach(cat => {
      groups[cat].sort((a, b) => a.localeCompare(b, 'fr'));
    });

    return groups;
  }, []);

  // Filtrage des scènes selon les critères
  const filteredScenes = useMemo(() => {
    return SCENES_DATA.filter(scene => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inTitle = scene.title.toLowerCase().includes(q);
        const inChannel = scene.channel.toLowerCase().includes(q);
        const inPreview = scene.preview.toLowerCase().includes(q);
        const inActors = scene.actors.some(a => a.toLowerCase().includes(q));
        if (!inTitle && !inChannel && !inPreview && !inActors) {
          return false;
        }
      }

      if (selectedActor !== 'all') {
        if (!scene.actors.includes(selectedActor)) return false;
      }

      if (selectedChannel !== 'all') {
        if (scene.channel !== selectedChannel) return false;
      }

      return true;
    }).sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
  }, [searchQuery, selectedActor, selectedChannel]);

  // Groupement des scènes par Mois/Année
  const groupedPeriodScenes = useMemo(() => {
    const monthGroups: { key: string; label: string; scenes: Scene[]; totalScenes: number }[] = [];
    const monthMap: Record<string, { label: string; scenes: Scene[] }> = {};

    filteredScenes.forEach(scene => {
      const { key, label } = getMonthYearKey(scene.start_time);
      if (!monthMap[key]) {
        monthMap[key] = { label, scenes: [] };
      }
      monthMap[key].scenes.push(scene);
    });

    Object.keys(monthMap).forEach(mKey => {
      const { label, scenes } = monthMap[mKey];
      monthGroups.push({
        key: mKey,
        label,
        scenes,
        totalScenes: scenes.length
      });
    });

    return monthGroups;
  }, [filteredScenes]);

  const scrollToMonth = (monthKey: string) => {
    setActiveMonthKey(monthKey);
    const element = document.getElementById(`period-${monthKey}`);
    if (element) {
      const yOffset = -100;
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-red-900 selection:text-white relative">
      
      {/* 🖼️ IMAGE DE FOND DARK FANTASY FLOUTÉE */}
      <div className="bg-dark-fantasy-layer" />
      <div className="bg-vignette-overlay" />
      <div className="ember-particles-bg" />

      {/* 🗡️ EN-TÊTE PRINCIPAL AVEC ARTWORK ET FILTRES */}
      <header className="sticky top-0 z-40 bg-[#090b10]/95 backdrop-blur-md border-b border-slate-800/90 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            
            {/* Logo, Artwork & Titre */}
            <div className="flex items-center gap-3.5">
              <div className="relative w-11 h-11 border border-slate-700/80 rounded-lg overflow-hidden shadow-lg shadow-black/80 shrink-0">
                <img 
                  src="./ashera_banner.png" 
                  alt="Ashera Artwork" 
                  className="w-full h-full object-cover object-center"
                />
                <div className="absolute inset-0 ring-1 ring-inset ring-slate-400/20" />
              </div>

              <div>
                <h1 className="text-xl font-bold font-serif-gothic tracking-widest text-slate-100 uppercase flex items-center gap-2">
                  Chronologie d'Ashera
                </h1>
                <p className="text-xs text-slate-400 font-light">
                  {filteredScenes.length} scènes RP répertoriées
                </p>
              </div>
            </div>

            {/* Recherche */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Rechercher une scène, un mot, un extrait..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#0d0f17] border border-slate-800 rounded-none pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-slate-400 transition-colors shadow-inner"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* BARRE DE FILTRES ET BOUTONS DE COMMUTATION DE VUE (GANTT VS CARTES) */}
          <div className="flex flex-wrap items-center justify-between gap-3 mt-3 pt-3 border-t border-slate-800/80 text-xs">
            
            <div className="flex flex-wrap items-center gap-3 flex-1">
              {/* Personnages par Faction */}
              <div className="flex items-center gap-2 bg-[#0d0f17] px-3 py-2 border border-slate-800 shadow-sm flex-1 min-w-[220px]">
                <Users className="w-4 h-4 text-purple-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <select
                    value={selectedActor}
                    onChange={(e) => setSelectedActor(e.target.value)}
                    className="w-full bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs truncate"
                  >
                    <option value="all" className="bg-[#0d0f17] text-slate-200 font-semibold">
                      Tous les personnages
                    </option>
                    
                    {Object.entries(groupedActorsByFaction).map(([roleName, actorList]) => {
                      if (actorList.length === 0) return null;
                      const factionIcon = FACTION_COLORS[roleName]?.icon || "🛡️";
                      return (
                        <optgroup key={roleName} label={`--- ${factionIcon} ${roleName.toUpperCase()} (${actorList.length}) ---`} className="bg-[#08090d] text-slate-400 font-bold">
                          {actorList.map(({ name, displayLabel }) => (
                            <option key={name} value={name} className="bg-[#0d0f17] text-slate-200 font-normal">
                              {displayLabel}
                            </option>
                          ))}
                        </optgroup>
                      );
                    })}
                  </select>
                </div>
              </div>

              {/* Salons par Catégorie */}
              <div className="flex items-center gap-2 bg-[#0d0f17] px-3 py-2 border border-slate-800 shadow-sm flex-1 min-w-[220px]">
                <Layers className="w-4 h-4 text-slate-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <select
                    value={selectedChannel}
                    onChange={(e) => setSelectedChannel(e.target.value)}
                    className="w-full bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs truncate"
                  >
                    <option value="all" className="bg-[#0d0f17] text-slate-200 font-semibold">
                      Tous les salons
                    </option>

                    {Object.entries(groupedChannelsByCategory).map(([catName, channels]) => (
                      <optgroup key={catName} label={`--- ${catName.toUpperCase()} ---`} className="bg-[#08090d] text-slate-400 font-bold">
                        {channels.map(ch => (
                          <option key={ch} value={ch} className="bg-[#0d0f17] text-slate-200 font-normal">
                            #{ch}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              </div>
            </div>

              {(searchQuery || selectedActor !== 'all' || selectedChannel !== 'all') && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedActor('all');
                    setSelectedChannel('all');
                  }}
                  className="px-3 py-2 bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 transition-colors font-medium shrink-0"
                >
                  Réinitialiser les filtres
                </button>
              )}

          </div>
        </div>
      </header>

      {/* 🚀 LAYOUT PRINCIPAL AVEC GANTT SWIMLANES DYNAMIQUES */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex gap-8">
        
        {/* 📌 SAUT TEMPOREL FIGÉ PERMANENT (STICKY TOP-28) */}
        <aside className="hidden lg:block w-64 shrink-0 sticky top-28 h-[calc(100vh-130px)] overflow-y-auto space-y-4 pr-1 text-xs custom-scrollbar">
          
          {/* BANNIÈRE ARTWORK DU PROJET */}
          <div className="gothic-corner-box bg-[#0c0e15]/90 border border-slate-800 p-2 shadow-2xl overflow-hidden">
            <div className="gothic-corner gothic-corner-tl" />
            <div className="gothic-corner gothic-corner-tr" />
            <div className="gothic-corner gothic-corner-bl" />
            <div className="gothic-corner gothic-corner-br" />
            
            <div className="relative h-28 w-full overflow-hidden border border-slate-800">
              <img 
                src="./ashera_banner.png" 
                alt="Conte d'Ashera Artwork" 
                className="w-full h-full object-cover object-center"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0c0e15] via-transparent to-transparent" />
              <div className="absolute bottom-2 left-2 right-2 text-center">
                <span className="text-[11px] font-serif-gothic tracking-widest text-slate-200 uppercase font-bold drop-shadow-md">
                  Le Conte d'Ashera
                </span>
              </div>
            </div>
          </div>

          {/* MENU SAUT TEMPOREL CLAIR & PROPRE */}
          <div className="gothic-corner-box bg-[#0c0e15]/90 border border-slate-800 p-4 shadow-2xl backdrop-blur-md">
            <div className="gothic-corner gothic-corner-tl" />
            <div className="gothic-corner gothic-corner-tr" />
            <div className="gothic-corner gothic-corner-bl" />
            <div className="gothic-corner gothic-corner-br" />

            <div className="flex items-center gap-2 mb-3 pb-2.5 border-b border-slate-800">
              <Calendar className="w-4 h-4 text-slate-400" />
              <h2 className="text-xs font-bold font-serif-gothic tracking-wider uppercase text-slate-300">Saut Temporel</h2>
            </div>
            
            <nav className="space-y-1 text-xs">
              {groupedPeriodScenes.map(({ key, label, totalScenes }) => (
                <button
                  key={key}
                  onClick={() => scrollToMonth(key)}
                  className={`w-full flex items-center justify-between px-3 py-2 transition-all border border-transparent ${
                    activeMonthKey === key
                      ? 'bg-slate-800/80 text-slate-100 font-semibold border-slate-700'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate font-medium">{label}</span>
                  <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-[10px] text-slate-300 font-mono shrink-0 ml-2">
                    {totalScenes} {totalScenes > 1 ? 'scènes' : 'scène'}
                  </span>
                </button>
              ))}

              {groupedPeriodScenes.length === 0 && (
                <p className="text-xs text-slate-500 py-4 text-center">Aucun résultat</p>
              )}
            </nav>
          </div>
        </aside>

        {/* 📜 LA CHRONOLOGIE GANTT SWIMLANES DES SALONS ACTIFS */}
        <main className="flex-1 min-w-0 relative pl-8">
          
          {/* Fil argenté principal de la chronologie */}
          <div className="timeline-spine" />

          {groupedPeriodScenes.length === 0 ? (
            <div className="bg-[#0c0e15] border border-slate-800 p-12 text-center my-8 shadow-xl">
              <HelpCircle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="text-base font-bold font-serif-gothic text-slate-300 mb-1">Aucune scène correspondante</h3>
              <p className="text-xs text-slate-500 mb-6">
                Essayez de modifier vos termes de recherche ou de réinitialiser les filtres.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedActor('all');
                  setSelectedChannel('all');
                }}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 text-xs font-medium transition-colors"
              >
                Réinitialiser les filtres
              </button>
            </div>
          ) : (
            <div className="space-y-12">
              {groupedPeriodScenes.map(({ key, label, scenes, totalScenes }) => (
                <section key={key} id={`period-${key}`} className="scroll-mt-36 relative">
                  
                  {/* ANCRAGE & NOEUD DU MOIS */}
                  <div className="flex items-center gap-4 mb-6 -ml-8">
                    <div className="w-10 h-10 bg-[#08090d] border-2 border-slate-400 flex items-center justify-center shadow-lg shadow-black/80 shrink-0 z-10">
                      <div className="w-3 h-3 bg-slate-300 transform rotate-45" />
                    </div>
                    
                    <div className="px-4 py-2 bg-[#0c0e15] border border-slate-700/80 flex items-center gap-3 shadow-xl">
                      <h2 className="text-sm font-bold font-serif-gothic tracking-widest text-slate-100 uppercase">{label}</h2>
                      <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-mono">
                        {totalScenes} {totalScenes > 1 ? 'SCÈNES' : 'SCÈNE'}
                      </span>
                    </div>
                    
                    <div className="h-[1px] flex-1 bg-gradient-to-r from-slate-700/60 to-transparent" />
                  </div>

                  {/* RENDU EN FRISE GANTT SWIMLANES PAR SALONS ACTIFS */}
                  <GanttMonthView
                    monthLabel={label}
                    scenes={scenes}
                    onSelectScene={(s) => setActiveScene(s)}
                  />
                </section>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* 💬 MODALE LECTEUR DE SCÈNE : FORMAT DISCORD */}
      {activeScene && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
          <div className="gothic-corner-box bg-[#313338] border border-slate-700 w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative text-[#dbdee1]">
            <div className="gothic-corner gothic-corner-tl" />
            <div className="gothic-corner gothic-corner-tr" />
            <div className="gothic-corner gothic-corner-bl" />
            <div className="gothic-corner gothic-corner-br" />

            {/* En-tête Modal Discord */}
            <div className="px-6 py-4 border-b border-[#1e1f22] flex items-center justify-between bg-[#2b2d31]">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-[#1e1f22] border border-slate-700/60 text-[#f2f3f5] font-semibold text-xs rounded">
                  #{activeScene.channel}
                </span>
                <span className="text-xs text-[#949ba4] font-medium flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-[#949ba4]" />
                  {formatDateDiscord(activeScene.start_time)}
                </span>
              </div>
              <button
                onClick={() => setActiveScene(null)}
                className="p-1.5 rounded-full text-[#b5bac1] hover:text-[#f2f3f5] hover:bg-[#35373c] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* En-tête de la Scène */}
            <div className="px-6 py-3 bg-[#2b2d31]/60 border-b border-[#1e1f22]">
              <h2 className="text-base font-bold text-[#f2f3f5] mb-2">{activeScene.title}</h2>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-[#949ba4]">Acteurs présents :</span>
                {activeScene.actors.map(actor => {
                  const info = CHARACTERS_DATA[actor];
                  const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];
                  return (
                    <span
                      key={actor}
                      style={{ backgroundColor: style.bg, color: style.text, borderColor: style.border }}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 border text-xs font-medium rounded"
                    >
                      <span>{style.icon}</span>
                      <span>{actor}</span>
                    </span>
                  );
                })}
              </div>
            </div>

            {/* FLUX DES MESSAGES : FORMAT ET CONFORT DISCORD (BG #313338) */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar bg-[#313338]">
              {activeScene.messages.map((msg, index) => {
                const info = CHARACTERS_DATA[msg.author];
                const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];
                const initials = getInitials(msg.author);

                return (
                  <div key={msg.id || index} className="flex items-start gap-4 hover:bg-[#2e3035] p-2 rounded transition-colors group">
                    
                    {/* AVATAR ROND CONFORT DISCORD */}
                    <div 
                      style={{ backgroundColor: style.hexColor }} 
                      className="w-10 h-10 rounded-full flex items-center justify-center text-slate-950 font-bold text-xs shrink-0 shadow-sm mt-0.5 select-none"
                    >
                      {initials}
                    </div>

                    {/* BLOC MESSAGE DISCORD */}
                    <div className="flex-1 min-w-0">
                      {/* LIGNE AUTEUR & TIMESTAMPS */}
                      <div className="flex items-baseline gap-2 mb-1">
                        <span 
                          style={{ color: style.text }} 
                          className="font-semibold text-[15px] hover:underline cursor-pointer tracking-wide"
                        >
                          {msg.author}
                        </span>
                        <span className="text-[12px] text-[#949ba4] font-normal select-none">
                          {formatDateDiscord(msg.timestamp)}
                        </span>
                      </div>

                      {/* EMBED DISCORD (LE CAS ÉCHÉANT) */}
                      {(msg.embed_title || msg.embed_description) && (
                        <div className="border-l-4 border-purple-500 bg-[#2b2d31] p-3 rounded-r-md mt-1.5 mb-2 max-w-2xl shadow-md">
                          {msg.embed_title && (
                            <h4 className="text-[14px] font-bold text-[#f2f3f5] mb-1">{msg.embed_title}</h4>
                          )}
                          {msg.embed_description && (
                            <p className="text-[14px] text-[#dbdee1] italic whitespace-pre-line leading-relaxed">{msg.embed_description}</p>
                          )}
                        </div>
                      )}

                      {/* CONTENU TEXTE DISCORD LISIBLE */}
                      {msg.content && (
                        <p className="text-[15px] text-[#dbdee1] leading-[1.375rem] font-sans whitespace-pre-wrap select-text">
                          {msg.content}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Footer Modal Discord */}
            <div className="px-6 py-3.5 border-t border-[#1e1f22] bg-[#2b2d31] flex items-center justify-between">
              <span className="text-xs text-[#949ba4] font-medium flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-[#949ba4]" />
                {activeScene.messages.length} message(s) dans cette scène
              </span>
              <a
                href={activeScene.discord_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#5865f2] hover:bg-[#4752c4] text-white rounded text-xs font-semibold transition-colors shadow"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Ouvrir sur Discord
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ⬆️ BOUTON RETOUR EN HAUT */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 p-3 bg-[#2b2d31] hover:bg-[#35373c] text-white border border-slate-700 shadow-2xl transition-all z-40 rounded-full"
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
