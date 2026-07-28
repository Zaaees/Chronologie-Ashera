import React, { useState, useMemo, useEffect, useRef } from 'react';
import { CHARACTERS_DATA, SCENES_DATA, CHANNEL_IMAGES, Scene, Character, Message } from './data';
import { 
  Search, Calendar, Clock, Users, ChevronRight, 
  ExternalLink, Layers, X, ArrowUp, HelpCircle, Shield, Scroll, Eye, Sword, Feather, Sun, Wand2, MessageSquare, Zap, BarChart2, MapPin, ChevronDown
} from 'lucide-react';
import { CharacterSpotlight } from './components/CharacterSpotlight';
import { getCharacterCardImage } from './utils/characterHelper';

export const formatImageUrl = (url?: string | null): string | undefined => {
  if (!url) return undefined;
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  const clean = url.replace(/^\/+/, '');
  return `./${clean}`;
};

const FACTION_INFO: Record<string, { bg: string; text: string; border: string; icon: string; hexColor: string; crest: string; roleName: string }> = {
  "La Garde Pourpre": { 
    roleName: "La Garde Pourpre",
    bg: "rgba(153, 27, 27, 0.4)", 
    text: "#fca5a5", 
    border: "rgba(220, 38, 38, 0.75)", 
    icon: "🗡️", 
    hexColor: "#ef4444",
    crest: "./factions/garde_pourpre.png"
  },
  "Cercle d'Azur": { 
    roleName: "Cercle d'Azur",
    bg: "rgba(30, 58, 138, 0.4)", 
    text: "#93c5fd", 
    border: "rgba(59, 130, 246, 0.75)", 
    icon: "🌙", 
    hexColor: "#3b82f6",
    crest: "./factions/cercle_azur.png"
  },
  "Voile d'Ivoire": { 
    roleName: "Voile d'Ivoire",
    bg: "rgba(254, 240, 138, 0.25)", 
    text: "#fef08a", 
    border: "rgba(254, 240, 138, 0.6)", 
    icon: "⚖️", 
    hexColor: "#fef08a",
    crest: "./factions/voile_ivoire.png"
  },
  "L'œil": { 
    roleName: "L'œil",
    bg: "rgba(30, 41, 59, 0.85)", 
    text: "#e2e8f0", 
    border: "rgba(148, 163, 184, 0.65)", 
    icon: "👁️", 
    hexColor: "#cbd5e1",
    crest: "./factions/oeil.png"
  }
};

const DEFAULT_FACTION_STYLE = {
  roleName: "Sans rôle",
  bg: "rgba(71, 85, 105, 0.4)", 
  text: "#cbd5e1", 
  border: "rgba(100, 116, 139, 0.65)", 
  icon: "🛡️", 
  hexColor: "#94a3b8",
  crest: "./ashera_banner.png"
};

const FACTION_COLORS: Record<string, { bg: string; text: string; border: string; icon: string; hexColor: string; crest: string; roleName: string }> = {
  ...FACTION_INFO,
  "Sans guilde": { bg: "rgba(180, 83, 9, 0.4)", text: "#fde047", border: "rgba(217, 119, 6, 0.75)", icon: "☀️", hexColor: "#eab308", crest: "./ashera_banner.png", roleName: "Sans guilde" },
  "Sans rôle": { bg: "rgba(71, 85, 105, 0.4)", text: "#cbd5e1", border: "rgba(100, 116, 139, 0.65)", icon: "🛡️", hexColor: "#94a3b8", crest: "./ashera_banner.png", roleName: "Sans rôle" },
  "PNJ": { bg: "rgba(126, 34, 206, 0.4)", text: "#d8b4fe", border: "rgba(168, 85, 247, 0.75)", icon: "🔮", hexColor: "#c084fc", crest: "./ashera_banner.png", roleName: "PNJ" }
};

function getFactionStyle(role: string | undefined) {
  if (!role || !FACTION_COLORS[role]) return DEFAULT_FACTION_STYLE;
  return FACTION_COLORS[role];
}

// Formater la date en style Discord
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

function escapeRegExp(string: string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Surlignage du terme de recherche
function highlightSearchQuery(text: string, query: string, baseKey: string | number): React.ReactNode {
  const q = query.trim().toLowerCase();
  if (!q) return text;

  const parts = text.split(new RegExp(`(${escapeRegExp(q)})`, 'gi'));
  return parts.map((part, i) => {
    if (part.toLowerCase() === q) {
      return (
        <mark key={`${baseKey}-${i}`} className="bg-amber-400/45 text-amber-100 font-bold px-1 py-0.5 rounded shadow-sm ring-1 ring-amber-400/70">
          {part}
        </mark>
      );
    }
    return part;
  });
}

// Analyseur Inline Markdown Discord (*, **, ***, __, ~~, ||, `, surbrillance)
function parseInlineDiscord(text: string, searchQuery: string): React.ReactNode {
  if (!text) return null;

  const regex = /(\|\|.+?\|\||`.+?`|\*\*\*.+?\*\*\*|\*\*.+?\*\*|__.+?__|~~.+?~~|\*.+?\*|_.+?_)/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (!part) return null;

    if (part.startsWith('||') && part.endsWith('||')) {
      const inner = part.slice(2, -2);
      return (
        <span key={index} className="bg-slate-700 text-transparent hover:text-slate-200 cursor-pointer rounded px-1 transition-colors select-none">
          {parseInlineDiscord(inner, searchQuery)}
        </span>
      );
    }

    if (part.startsWith('`') && part.endsWith('`')) {
      const inner = part.slice(1, -1);
      return (
        <code key={index} className="bg-[#1e1f22] border border-slate-700/60 px-1.5 py-0.5 rounded text-xs font-mono text-slate-200">
          {inner}
        </code>
      );
    }

    if (part.startsWith('***') && part.endsWith('***')) {
      const inner = part.slice(3, -3);
      return <strong key={index} className="font-bold italic">{parseInlineDiscord(inner, searchQuery)}</strong>;
    }

    if (part.startsWith('**') && part.endsWith('**')) {
      const inner = part.slice(2, -2);
      return <strong key={index} className="font-bold">{parseInlineDiscord(inner, searchQuery)}</strong>;
    }

    if (part.startsWith('__') && part.endsWith('__')) {
      const inner = part.slice(2, -2);
      return <u key={index} className="underline decoration-slate-400">{parseInlineDiscord(inner, searchQuery)}</u>;
    }

    if (part.startsWith('~~') && part.endsWith('~~')) {
      const inner = part.slice(2, -2);
      return <del key={index} className="line-through text-slate-400">{parseInlineDiscord(inner, searchQuery)}</del>;
    }

    if ((part.startsWith('*') && part.endsWith('*')) || (part.startsWith('_') && part.endsWith('_'))) {
      const inner = part.slice(1, -1);
      return <em key={index} className="italic">{parseInlineDiscord(inner, searchQuery)}</em>;
    }

    if (searchQuery && searchQuery.trim().length > 0) {
      return highlightSearchQuery(part, searchQuery, index);
    }

    return part;
  });
}

// ANALYSEUR DE FORMAT MARKDOWN DISCORD COMPLET
function renderDiscordMarkdown(text: string, searchQuery: string = ''): React.ReactNode {
  if (!text) return null;

  const lines = text.split('\n');
  const renderedElements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeBlockLines: string[] = [];

  lines.forEach((line, lineIdx) => {
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        const codeContent = codeBlockLines.join('\n');
        renderedElements.push(
          <pre key={`code-${lineIdx}`} className="bg-[#1e1f22] border border-slate-700/60 p-2.5 rounded text-xs font-mono text-slate-200 my-1.5 overflow-x-auto whitespace-pre-wrap select-text">
            {codeContent}
          </pre>
        );
        codeBlockLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    if (line.trim().startsWith('-# ')) {
      const subContent = line.trim().slice(3);
      renderedElements.push(
        <div key={`sub-${lineIdx}`} className="text-[11px] text-[#949ba4] font-sans leading-tight my-0.5">
          {parseInlineDiscord(subContent, searchQuery)}
        </div>
      );
      return;
    }

    // Gestion des citations (blockquote)
    const isQuoteLine = line.startsWith('> ') || line === '>' || line.startsWith('>\t');
    if (isQuoteLine) {
      const quoteContent = line === '>' ? '' : line.startsWith('> ') ? line.slice(2) : line.slice(1);
      
      // Si l'élément précédent était un blockquote, on ajoute le contenu à cette citation
      const lastElement = renderedElements[renderedElements.length - 1];
      if (lastElement && React.isValidElement(lastElement) && (lastElement.props as any)?.['data-blockquote']) {
        const existingChildren = (lastElement.props as any).children as React.ReactNode[];
        renderedElements[renderedElements.length - 1] = React.cloneElement(
          lastElement,
          {},
          [
            ...existingChildren,
            <React.Fragment key={`quote-line-${lineIdx}`}>
              <br />
              {parseInlineDiscord(quoteContent, searchQuery)}
            </React.Fragment>
          ]
        );
      } else {
        renderedElements.push(
          <blockquote 
            key={`quote-${lineIdx}`} 
            data-blockquote="true"
            className="border-l-4 border-[#4e5058] pl-3 py-1 my-1 text-[#dbdee1] bg-[#2b2d31]/40 rounded-r select-text"
          >
            {[
              <React.Fragment key={`quote-line-${lineIdx}`}>
                {parseInlineDiscord(quoteContent, searchQuery)}
              </React.Fragment>
            ]}
          </blockquote>
        );
      }
      return;
    }

    renderedElements.push(
      <React.Fragment key={`line-${lineIdx}`}>
        {lineIdx > 0 && <br />}
        {parseInlineDiscord(line, searchQuery)}
      </React.Fragment>
    );
  });

  return <>{renderedElements}</>;
}

// 🔍 COMPOSANT INTERACTIF : SÉLECTEUR DE PERSONNAGES AVEC RECHERCHE PAR SAISIE MANUELLE
function SearchableCharacterSelect({
  selectedActor,
  setSelectedActor,
  groupedActorsByFaction
}: {
  selectedActor: string;
  setSelectedActor: (name: string) => void;
  groupedActorsByFaction: Record<string, { name: string; displayLabel: string }[]>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentDisplayLabel = useMemo(() => {
    if (selectedActor === 'all') return 'Tous les personnages';
    const charInfo = CHARACTERS_DATA[selectedActor];
    const serverNick = charInfo?.displayName || charInfo?.username;
    return serverNick && serverNick !== selectedActor 
      ? `${selectedActor} (${serverNick})` 
      : selectedActor;
  }, [selectedActor]);

  const filteredGroupedActors = useMemo(() => {
    const q = filterQuery.toLowerCase().trim();
    if (!q) return groupedActorsByFaction;

    const result: Record<string, { name: string; displayLabel: string }[]> = {};
    Object.entries(groupedActorsByFaction).forEach(([role, actors]) => {
      const matching = actors.filter(a => 
        a.name.toLowerCase().includes(q) || a.displayLabel.toLowerCase().includes(q)
      );
      if (matching.length > 0) {
        result[role] = matching;
      }
    });
    return result;
  }, [filterQuery, groupedActorsByFaction]);

  return (
    <div ref={containerRef} className="relative flex-1 min-w-[240px]">
      <div className="flex items-center gap-2 bg-[#0d0f17] px-3 py-1.5 border border-slate-800 shadow-sm">
        <Users className="w-4 h-4 text-purple-400 shrink-0" />
        
        <input
          type="text"
          placeholder="Taper un nom de personnage..."
          value={isOpen ? filterQuery : (selectedActor === 'all' ? '' : currentDisplayLabel)}
          onFocus={() => {
            setIsOpen(true);
            setFilterQuery('');
          }}
          onChange={(e) => {
            setFilterQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          className="w-full bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none text-xs truncate"
        />

        {selectedActor !== 'all' && (
          <button 
            onClick={() => {
              setSelectedActor('all');
              setFilterQuery('');
            }}
            className="text-slate-500 hover:text-slate-300 p-0.5"
            title="Effacer le personnage"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}

        <button 
          onClick={() => setIsOpen(!isOpen)}
          className="text-slate-500 hover:text-slate-300"
        >
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 max-h-72 overflow-y-auto bg-[#08090d] border border-slate-700 shadow-2xl z-50 rounded custom-scrollbar py-1">
          <button
            onClick={() => {
              setSelectedActor('all');
              setIsOpen(false);
              setFilterQuery('');
            }}
            className={`w-full text-left px-3 py-1.5 text-xs font-semibold hover:bg-slate-800 transition-colors ${
              selectedActor === 'all' ? 'bg-purple-950/80 text-purple-200' : 'text-slate-300'
            }`}
          >
            Tous les personnages
          </button>

          {(Object.entries(filteredGroupedActors) as [string, { name: string; displayLabel: string }[]][]).map(([roleName, actorList]) => {
            const factionStyle = getFactionStyle(roleName);
            return (
              <div key={roleName} className="border-t border-slate-800/80 pt-1">
                <div style={{ color: factionStyle.text }} className="px-3 py-1 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 bg-slate-950/80">
                  <span>{factionStyle.icon}</span>
                  <span>{roleName} ({actorList.length})</span>
                </div>
                {actorList.map(({ name, displayLabel }) => (
                  <button
                    key={name}
                    onClick={() => {
                      setSelectedActor(name);
                      setIsOpen(false);
                      setFilterQuery('');
                    }}
                    className={`w-full text-left px-4 py-1.5 text-xs hover:bg-slate-800/80 transition-colors truncate ${
                      selectedActor === name ? 'bg-slate-800 text-purple-300 font-semibold' : 'text-slate-300'
                    }`}
                  >
                    {displayLabel}
                  </button>
                ))}
              </div>
            );
          })}

          {Object.keys(filteredGroupedActors).length === 0 && (
            <div className="px-4 py-3 text-xs text-slate-500 text-center">
              Aucun personnage trouvé pour "{filterQuery}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Interface pour les pistes Gantt par salon
interface GanttChannelTrack {
  channel: string;
  locationImage?: string;
  maxLanes: number;
  scenes: {
    scene: Scene;
    leftPercent: number;
    widthPercent: number;
    lane: number;
  }[];
}

// COMPOSANT GANTT SWIMLANES DYNAMIQUES AVEC IMAGES LOCALES EXTRAITES DE DISCORD
function GanttMonthView({ 
  monthLabel, 
  scenes, 
  onSelectScene,
  onSelectChannel
}: { 
  monthLabel: string; 
  scenes: Scene[]; 
  onSelectScene: (s: Scene) => void;
  onSelectChannel?: (ch: string) => void;
}) {
  const [hoveredTooltip, setHoveredTooltip] = useState<{
    scene: Scene;
    channel: string;
    locationImage?: string;
    rect: DOMRect;
  } | null>(null);

  useEffect(() => {
    const handleScrollOrResize = () => setHoveredTooltip(null);
    window.addEventListener('scroll', handleScrollOrResize, true);
    window.addEventListener('resize', handleScrollOrResize);
    return () => {
      window.removeEventListener('scroll', handleScrollOrResize, true);
      window.removeEventListener('resize', handleScrollOrResize);
    };
  }, []);

  if (scenes.length === 0) return null;

  const timestamps = scenes.flatMap(s => [
    new Date(s.start_time).getTime(),
    new Date(s.end_time || s.start_time).getTime()
  ]).filter(t => !isNaN(t));

  const tMin = Math.min(...timestamps);
  const tMax = Math.max(...timestamps);
  const duration = Math.max(tMax - tMin, 1);

  const channelMap: Record<string, Scene[]> = {};
  scenes.forEach(s => {
    if (!channelMap[s.channel]) channelMap[s.channel] = [];
    channelMap[s.channel].push(s);
  });

  const getLocationImage = (ch: string, chScenes?: Scene[]) => {
    if (CHANNEL_IMAGES[ch]) return formatImageUrl(CHANNEL_IMAGES[ch]);
    const fromScene = chScenes?.find(s => s.location_image)?.location_image;
    if (fromScene) return formatImageUrl(fromScene);

    const parentCh = chScenes?.[0]?.channel;
    if (parentCh && CHANNEL_IMAGES[parentCh]) return formatImageUrl(CHANNEL_IMAGES[parentCh]);

    const cleanCh = ch.replace(/[^\w]/g, '').toLowerCase();
    const cleanParent = parentCh ? parentCh.replace(/[^\w]/g, '').toLowerCase() : '';

    const entry = Object.entries(CHANNEL_IMAGES).find(([k, v]) => {
      const cleanK = k.replace(/[^\w]/g, '').toLowerCase();
      if (!cleanK || !v) return false;
      return (cleanCh && (cleanK.includes(cleanCh) || cleanCh.includes(cleanK))) ||
             (cleanParent && (cleanK.includes(cleanParent) || cleanParent.includes(cleanK)));
    });
    const rawResult = entry ? entry[1] : undefined;
    return formatImageUrl(rawResult);
  };

  const tracks: GanttChannelTrack[] = Object.keys(channelMap).map(ch => {
    const chScenes = channelMap[ch];
    const locationImg = getLocationImage(ch, chScenes);

    const sortedWithPos = chScenes.map(sc => {
      const sTime = new Date(sc.start_time).getTime();
      const eTime = new Date(sc.end_time || sc.start_time).getTime();
      const left = Math.max(0, ((sTime - tMin) / duration) * 100);
      const rawWidth = Math.max(0.5, ((eTime - sTime) / duration) * 100);
      const width = Math.max(rawWidth, 4.5);
      return {
        scene: sc,
        leftPercent: Math.min(left, 94),
        widthPercent: Math.min(width, 100 - left)
      };
    }).sort((a, b) => a.leftPercent - b.leftPercent);

    const laneRightEdges: number[] = [];
    const itemsWithLanes = sortedWithPos.map(item => {
      let lane = 0;
      const itemRight = item.leftPercent + item.widthPercent;

      for (let l = 0; l < laneRightEdges.length; l++) {
        if (laneRightEdges[l] + 0.5 <= item.leftPercent) {
          lane = l;
          break;
        }
        lane = l + 1;
      }

      laneRightEdges[lane] = itemRight;
      return { ...item, lane };
    });

    const maxLanes = Math.max(1, laneRightEdges.length);

    return {
      channel: ch,
      locationImage: locationImg,
      maxLanes,
      scenes: itemsWithLanes
    };
  });

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
      <div className="overflow-x-auto custom-scrollbar py-6">
        <div className="min-w-[950px] space-y-3">
          
          {/* Règle des dates supérieure */}
          <div className="flex items-center mb-2 text-[10px] font-mono text-slate-400 border-b border-slate-800/80 pb-1.5">
            <div className="w-56 shrink-0 font-bold uppercase tracking-wider pl-2 text-slate-300 flex items-center gap-1">
              <MapPin className="w-3 h-3 text-purple-400" />
              <span>Salons & Lieux</span>
            </div>
            <div className="flex-1 flex justify-between px-2">
              {dateTicks.map((t, idx) => (
                <span key={idx} className="text-slate-400 font-semibold">{t}</span>
              ))}
            </div>
          </div>

          {/* Lignes par Salon avec Arrière-plan Immersif et Hover Effect */}
          <div className="space-y-3">
            {tracks.map(({ channel, locationImage, maxLanes, scenes: trackScenes }) => {
              const trackHeight = maxLanes * 36 + 12;

              return (
                <div 
                  key={channel} 
                  style={{ minHeight: `${trackHeight + 12}px` }}
                  className="group/track relative flex items-center bg-[#0a0c12]/90 hover:bg-[#0f121d] border border-slate-800 hover:border-slate-700 rounded-lg p-1.5 transition-all shadow-md"
                >
                  {/* 🏰 BLOC SALON : Nom du salon avec Filtre au Clic */}
                  <div 
                    onClick={() => onSelectChannel && onSelectChannel(channel)}
                    className="w-52 shrink-0 pr-3 text-xs font-mono font-medium text-slate-200 flex items-center gap-2 pl-2 z-10 cursor-pointer group/chan"
                    title={`Cliquer pour filtrer par #${channel}`}
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-400/90 group-hover/chan:bg-purple-300 group-hover/chan:scale-125 transition-all shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-semibold text-slate-200 group-hover/chan:text-purple-300 transition-colors flex items-center gap-1">
                        <span className="text-purple-400 font-bold text-[13px]">#</span>
                        <span className="truncate">{channel}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {trackScenes.length} {trackScenes.length > 1 ? 'scènes' : 'scène'}
                        {maxLanes > 1 && ` • ${maxLanes} fils/pistes`}
                      </div>
                    </div>
                  </div>

                  {/* 📊 PISTE TEMPORELLE AVEC IMAGE DE FOND INTÉGRÉE & VISIBLE */}
                  <div 
                    style={{ height: `${trackHeight}px` }}
                    className="flex-1 relative border border-slate-700/80 rounded-md gantt-track-bg z-10"
                  >
                    
                    {/* 🖼️ IMAGE DE FOND DU SALON SUR LA PISTE */}
                    {locationImage ? (
                      <div className="absolute inset-0 overflow-hidden pointer-events-none rounded-md select-none">
                        <img 
                          src={locationImage} 
                          alt="" 
                          className="w-full h-full object-cover object-center opacity-45 group-hover/track:opacity-75 group-hover/track:scale-105 transition-all duration-500" 
                        />
                        <div className="absolute inset-0 bg-gradient-to-r from-[#06070a]/90 via-[#06070a]/35 to-[#06070a]/80" />
                      </div>
                    ) : (
                      <div className="absolute inset-0 bg-[#08090d]/60 rounded-md" />
                    )}

                    {trackScenes.map(({ scene, leftPercent, widthPercent, lane }) => {
                      const mainActor = scene.actors[0];
                      const info = CHARACTERS_DATA[mainActor];
                      const style = getFactionStyle(info?.role);
                      const isShort = widthPercent < 10;
                      const mainActorDisplayName = info?.displayName || mainActor;

                      return (
                        <div
                          key={scene.id}
                          onClick={() => onSelectScene(scene)}
                          onMouseEnter={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect();
                            setHoveredTooltip({ scene, channel, locationImage, rect });
                          }}
                          onMouseLeave={() => {
                            setHoveredTooltip(null);
                          }}
                          style={{
                            left: `${leftPercent}%`,
                            width: `${widthPercent}%`,
                            top: `${lane * 36 + 4}px`,
                            height: '28px',
                            backgroundColor: style.bg,
                            borderColor: style.border
                          }}
                          className="gantt-bar-item absolute border rounded-md px-2 flex items-center justify-between cursor-pointer text-xs select-none group/bar z-20 shadow-md"
                        >
                          <div className="flex items-center gap-1.5 min-w-0 w-full overflow-hidden">
                            {scene.thread_name && (
                              <span className="px-1.5 py-0.5 bg-purple-950/90 text-purple-200 border border-purple-500/50 text-[10px] rounded shrink-0 font-bold font-mono shadow">
                                {scene.thread_name}
                              </span>
                            )}

                            <span className="text-xs shrink-0">{style.icon}</span>
                            
                            {!isShort ? (
                              <div className="flex items-center gap-2 min-w-0 w-full">
                                <span style={{ color: style.text }} className="font-semibold text-xs truncate">
                                  {scene.title}
                                </span>
                                {scene.actors.length > 0 && (
                                  <span className="text-[10px] text-slate-300/80 font-mono truncate hidden lg:inline">
                                    ({mainActorDisplayName})
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span style={{ color: style.text }} className="font-semibold text-[11px] truncate">
                                {mainActorDisplayName || scene.title}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 🚀 INFOBULLE FLOTTANTE UNIVERSELLE : TOUJOURS ORIENTÉE VERS LE HAUT ET AU-DESSUS DE TOUT (FIXED POSITION Z-99999) */}
      {hoveredTooltip && (() => {
        const { scene: hScene, channel: hChannel, locationImage: hLocImg, rect } = hoveredTooltip;
        const startStr = formatDateDiscord(hScene.start_time);
        const endStr = formatDateDiscord(hScene.end_time);

        // Toujours orientée vers le haut au-dessus de la barre de scène
        const bottomPx = window.innerHeight - rect.top + 8;
        const targetLeft = rect.left + rect.width / 2 - 144;
        const clampedLeft = Math.max(16, Math.min(window.innerWidth - 304, targetLeft));

        return (
          <div 
            style={{
              position: 'fixed',
              left: `${clampedLeft}px`,
              bottom: `${bottomPx}px`,
              zIndex: 99999,
            }}
            className="pointer-events-none w-72 bg-[#0c0e15]/98 border border-slate-600 p-3 rounded-lg shadow-2xl drop-shadow-[0_20px_40px_rgba(0,0,0,0.95)] backdrop-blur-md transition-all duration-150"
          >
            {hLocImg && (
              <div className="h-20 w-full overflow-hidden rounded mb-2 border border-slate-700/80 bg-slate-900 shadow">
                <img 
                  src={hLocImg} 
                  alt={hChannel} 
                  className="w-full h-full object-cover object-center" 
                />
              </div>
            )}

            <div className="flex items-center justify-between gap-2 mb-1.5 pb-1 border-b border-slate-800">
              <span className="text-[11px] font-mono text-purple-300">#{hScene.channel}</span>
              <span className="text-[10px] font-mono text-[#949ba4]">{hScene.messages.length} msg</span>
            </div>
            <h4 className="text-xs font-bold text-slate-100 mb-1">{hScene.title}</h4>
            <div className="text-[11px] text-slate-300 font-mono space-y-0.5 mb-2">
              <div><span className="text-slate-500">Début :</span> {startStr}</div>
              <div><span className="text-slate-500">Fin :</span> {endStr}</div>
            </div>
            <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800">
              {hScene.actors.map(a => {
                const aInfo = CHARACTERS_DATA[a];
                const nameDisp = aInfo?.displayName || a;
                return (
                  <span key={a} className="px-1.5 py-0.5 bg-slate-900 text-[10px] text-slate-300 rounded border border-slate-700">
                    {nameDisp}
                  </span>
                );
              })}
            </div>
          </div>
        );
      })()}
    </div>
  );
}

const FACTION_THEMES: Record<string, { accent: string; border: string; glow: string; motto: string; mottoAuthor: string }> = {
  "La Garde Pourpre": {
    accent: "#ef4444",
    border: "rgba(220, 38, 38, 0.8)",
    glow: "rgba(239, 68, 68, 0.5)",
    motto: "L’inconnu et l’irrégulier sont dangereux, ils sont les outils du Mal que nous devons rayer de notre monde.",
    mottoAuthor: "Félina Cravagant"
  },
  "Cercle d'Azur": {
    accent: "#3b82f6",
    border: "rgba(59, 130, 246, 0.8)",
    glow: "rgba(59, 130, 246, 0.5)",
    motto: "L’inconnu et l’irrégulier sont deux phénomènes que nous devons élucider, analyser et classifier. Ils sont l’outil du progrès que nous devons comprendre pour bâtir un monde meilleur.",
    mottoAuthor: "Serena VIII"
  },
  "Voile d'Ivoire": {
    accent: "#eab308",
    border: "rgba(234, 179, 8, 0.8)",
    glow: "rgba(234, 179, 8, 0.5)",
    motto: "L'avarice empêche le partage. Le plus riche des hommes est pauvre s'il n'a plus personne avec qui partager.",
    mottoAuthor: "Rias Valdor"
  },
  "L'œil": {
    accent: "#a855f7",
    border: "rgba(147, 51, 234, 0.8)",
    glow: "rgba(147, 51, 234, 0.5)",
    motto: "Oculus videt",
    mottoAuthor: "Maël Legarde"
  }
};

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedActor, setSelectedActor] = useState<string>('all');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [selectedFaction, setSelectedFaction] = useState<string | null>(null);
  const [activeMonthKey, setActiveMonthKey] = useState<string>('');
  
  const headerRef = useRef<HTMLElement>(null);
  const [sidebarTopOffset, setSidebarTopOffset] = useState<number>(220);

  useEffect(() => {
    if (selectedFaction && FACTION_THEMES[selectedFaction]) {
      const theme = FACTION_THEMES[selectedFaction];
      document.documentElement.style.setProperty('--theme-accent', theme.accent);
      document.documentElement.style.setProperty('--theme-border', theme.border);
      document.documentElement.style.setProperty('--theme-glow', theme.glow);
    } else {
      document.documentElement.style.removeProperty('--theme-accent');
      document.documentElement.style.removeProperty('--theme-border');
      document.documentElement.style.removeProperty('--theme-glow');
    }
  }, [selectedFaction]);

  useEffect(() => {
    const updateOffset = () => {
      if (headerRef.current) {
        setSidebarTopOffset(headerRef.current.offsetHeight + 32);
      }
    };
    updateOffset();
    window.addEventListener('resize', updateOffset);
    return () => window.removeEventListener('resize', updateOffset);
  }, []);

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

  const activeActorsSet = useMemo(() => {
    const set = new Set<string>();
    SCENES_DATA.forEach(s => s.actors.forEach(a => set.add(a)));
    return set;
  }, []);

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
      const charInfo = CHARACTERS_DATA[actorName];
      const role = charInfo?.role || "Sans rôle";
      
      const serverNickname = charInfo?.displayName || charInfo?.username;
      const displayLabel = serverNickname && serverNickname !== actorName 
        ? `${actorName} (${serverNickname})` 
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

  // Filtrage des scènes selon Personnage, Salon et Recherche
  const filteredScenes = useMemo(() => {
    return SCENES_DATA.filter(scene => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inTitle = scene.title.toLowerCase().includes(q);
        const inChannel = scene.channel.toLowerCase().includes(q);
        const inPreview = scene.preview.toLowerCase().includes(q);
        const inActors = scene.actors.some(a => {
          const info = CHARACTERS_DATA[a];
          const serverNick = info?.displayName || info?.username || '';
          return a.toLowerCase().includes(q) || serverNick.toLowerCase().includes(q);
        });
        const inMessages = scene.messages.some(m => 
          (m.content && m.content.toLowerCase().includes(q)) || 
          (m.embed_description && m.embed_description.toLowerCase().includes(q)) ||
          (m.embed_title && m.embed_title.toLowerCase().includes(q))
        );
        if (!inTitle && !inChannel && !inPreview && !inActors && !inMessages) {
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

  const activeSceneLocationImage = useMemo(() => {
    if (!activeScene) return null;

    if (activeScene.thread_name && CHANNEL_IMAGES[activeScene.thread_name]) {
      return formatImageUrl(CHANNEL_IMAGES[activeScene.thread_name]);
    }

    const ch = activeScene.channel;
    if (CHANNEL_IMAGES[ch]) return formatImageUrl(CHANNEL_IMAGES[ch]);
    if (activeScene.location_image) return formatImageUrl(activeScene.location_image);

    const cleanTh = activeScene.thread_name ? activeScene.thread_name.replace(/[^\w]/g, '').toLowerCase() : '';
    const cleanCh = ch.replace(/[^\w]/g, '').toLowerCase();

    const entry = Object.entries(CHANNEL_IMAGES).find(([k, v]) => {
      const cleanK = k.replace(/[^\w]/g, '').toLowerCase();
      if (!cleanK || !v) return false;
      return (cleanTh && (cleanK.includes(cleanTh) || cleanTh.includes(cleanK))) ||
             (cleanCh && (cleanK.includes(cleanCh) || cleanCh.includes(cleanK)));
    });
    const rawResult = entry ? entry[1] : null;
    return formatImageUrl(rawResult);
  }, [activeScene]);

  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-red-900 selection:text-white relative">
      
      {/* 🖼️ IMAGE DE FOND DARK FANTASY FLOUTÉE */}
      <div 
        className="bg-dark-fantasy-layer" 
        style={{ backgroundImage: "url('./dark_fantasy_bg.png')" }}
      />
      <div className="bg-vignette-overlay" />
      <div className="ember-particles-bg" />

      {/* 🗡️ EN-TÊTE PRINCIPAL AVEC ARTWORK ET FILTRES */}
      <header ref={headerRef} className="sticky top-0 z-40 bg-[#090b10]/95 backdrop-blur-md border-b border-slate-800/90 shadow-2xl">
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

            {/* Recherche globale */}
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

          {/* 🛡️ BANNIÈRES INTERACTIVES DES 4 FACTIONS D'ASHERA (CHANGEMENT DE THÈME) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3.5 pt-3 border-t border-slate-800/80">
            {Object.entries(FACTION_INFO).map(([factionName, info]) => {
              const isSelected = selectedFaction === factionName;
              const memberCount = groupedActorsByFaction[factionName]?.length || 0;

              return (
                <div
                  key={factionName}
                  onClick={() => setSelectedFaction(isSelected ? null : factionName)}
                  style={{ 
                    borderColor: isSelected ? info.hexColor : 'rgba(226, 232, 240, 0.15)',
                    boxShadow: isSelected ? `0 0 20px ${info.hexColor}60` : undefined,
                    backgroundColor: isSelected ? `${info.hexColor}25` : '#0c0e1590'
                  }}
                  className={`faction-crest-card relative p-2.5 rounded flex items-center gap-2.5 border text-left select-none cursor-pointer transition-all duration-300 transform hover:scale-[1.02] ${
                    isSelected ? 'ring-2 ring-white/50 shadow-xl' : 'hover:border-slate-600'
                  }`}
                  title={`Cliquer pour appliquer le thème ${factionName}`}
                >
                  {/* Blason Image du Dossier Images */}
                  <div 
                    style={{ borderColor: info.hexColor }}
                    className="w-8 h-8 rounded-full overflow-hidden border-2 shrink-0 bg-black/80 shadow flex items-center justify-center p-0.5"
                  >
                    <img src={info.crest} alt={factionName} className="w-full h-full object-cover object-center rounded-full" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div style={{ color: isSelected ? '#ffffff' : info.text }} className="text-xs font-bold font-serif-gothic truncate flex items-center gap-1">
                      <span>{info.icon}</span>
                      <span className="truncate">{factionName}</span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-400 flex items-center justify-between gap-1 mt-0.5">
                      <span>{memberCount} membres</span>
                      {isSelected && (
                        <span style={{ backgroundColor: info.hexColor }} className="px-1.5 py-0.2 text-[9px] font-bold text-black rounded font-sans">
                          THÈME ACTIF
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* BARRE DE FILTRES SÉLECTEURS AVEC RECHERCHE INTERACTIVE DE PERSONNAGES */}
          <div className="flex flex-wrap items-center justify-between gap-3 mt-3 text-xs">
            <div className="flex flex-wrap items-center gap-3 flex-1">
              
              {/* 🔍 SÉLECTEUR DE PERSONNAGES AVEC RECHERCHE PAR SAISIE MANUELLE */}
              <SearchableCharacterSelect
                selectedActor={selectedActor}
                setSelectedActor={setSelectedActor}
                groupedActorsByFaction={groupedActorsByFaction}
              />

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

                    {(Object.entries(groupedChannelsByCategory) as [string, string[]][]).map(([catName, channels]) => (
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
      <div className={`${selectedActor !== 'all' ? 'max-w-[1600px]' : 'max-w-7xl'} mx-auto px-4 sm:px-6 lg:px-8 py-6 flex gap-6 lg:gap-8 transition-all duration-300`}>
        
        {/* 📌 SAUT TEMPOREL FIGÉ PERMANENT */}
        <aside 
          style={{ 
            top: `${sidebarTopOffset}px`, 
            height: `calc(100vh - ${sidebarTopOffset + 20}px)` 
          }}
          className="hidden lg:block w-64 shrink-0 sticky overflow-y-auto space-y-4 pr-1 text-xs custom-scrollbar"
        >
          
          {/* BANNIÈRE ARTWORK DU PROJET / DOCTRINE DE FACTION (CASE AU-DESSUS DE SAUT TEMPOREL) */}
          <div 
            style={{ 
              borderColor: selectedFaction && FACTION_THEMES[selectedFaction] ? FACTION_THEMES[selectedFaction].border : undefined,
              boxShadow: selectedFaction && FACTION_THEMES[selectedFaction] ? `0 0 15px ${FACTION_THEMES[selectedFaction].glow}` : undefined
            }}
            className="gothic-corner-box bg-[#0c0e15]/90 border border-slate-800 p-2.5 shadow-2xl overflow-hidden transition-all"
          >
            <div className="gothic-corner gothic-corner-tl" />
            <div className="gothic-corner gothic-corner-tr" />
            <div className="gothic-corner gothic-corner-bl" />
            <div className="gothic-corner gothic-corner-br" />
            
            {selectedFaction && FACTION_THEMES[selectedFaction] ? (
              <div className="relative min-h-[7.5rem] w-full overflow-hidden border border-slate-800/80 rounded p-2.5 flex flex-col justify-between bg-black/60">
                {/* Artwork Blason en fond semi-transparent */}
                {FACTION_INFO[selectedFaction]?.crest && (
                  <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
                    <img 
                      src={FACTION_INFO[selectedFaction].crest} 
                      alt={selectedFaction} 
                      className="w-full h-full object-cover opacity-25 scale-110" 
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0c0e15] via-[#0c0e15]/80 to-transparent" />
                  </div>
                )}

                {/* Titre de la Faction */}
                <div className="relative z-10 flex items-center gap-2 pb-1.5 border-b border-slate-800/80">
                  <div 
                    style={{ borderColor: FACTION_THEMES[selectedFaction].accent }}
                    className="w-6 h-6 rounded-full border shrink-0 overflow-hidden p-0.5 bg-black"
                  >
                    <img src={FACTION_INFO[selectedFaction]?.crest} alt="" className="w-full h-full object-cover rounded-full" />
                  </div>
                  <span style={{ color: FACTION_THEMES[selectedFaction].accent }} className="text-xs font-bold font-serif-gothic uppercase tracking-wider truncate">
                    {selectedFaction}
                  </span>
                </div>

                {/* Quote & Auteur */}
                <div className="relative z-10 mt-2">
                  <p className="text-[11px] italic font-serif text-slate-100 leading-snug line-clamp-4">
                    « {FACTION_THEMES[selectedFaction].motto} »
                  </p>
                  <p style={{ color: FACTION_THEMES[selectedFaction].accent }} className="text-[10px] font-mono font-semibold mt-1.5 text-right">
                    — {FACTION_THEMES[selectedFaction].mottoAuthor}
                  </p>
                </div>
              </div>
            ) : (
              <div className="relative h-28 w-full overflow-hidden border border-slate-800 rounded">
                <img 
                  src="./default_guild_banner.png" 
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
            )}
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

          {/* 👤 FICHE PERSONNAGE VISUELLE SI UN PERSONNAGE EST SÉLECTIONNÉ (MOBILE/TABLETTE) */}
          {selectedActor !== 'all' && (
            <div className="block xl:hidden mb-8">
              <CharacterSpotlight
                selectedActor={selectedActor}
                onReset={() => setSelectedActor('all')}
                onSelectActor={(actorName) => setSelectedActor(actorName)}
                onSelectChannel={(channelName) => setSelectedChannel(channelName)}
              />
            </div>
          )}

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
                    <div 
                      style={{ borderColor: selectedFaction ? FACTION_THEMES[selectedFaction]?.accent : undefined }}
                      className="w-10 h-10 bg-[#08090d] border-2 border-slate-400 flex items-center justify-center shadow-lg shadow-black/80 shrink-0 z-10 transition-colors"
                    >
                      <div 
                        style={{ backgroundColor: selectedFaction ? FACTION_THEMES[selectedFaction]?.accent : undefined }}
                        className="w-3 h-3 bg-slate-300 transform rotate-45 transition-colors" 
                      />
                    </div>
                    
                    <div 
                      style={{ borderColor: selectedFaction ? FACTION_THEMES[selectedFaction]?.border : undefined }}
                      className="px-4 py-2 bg-[#0c0e15] border border-slate-700/80 flex items-center gap-3 shadow-xl transition-colors"
                    >
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
                    onSelectChannel={(ch) => setSelectedChannel(ch)}
                  />
                </section>
              ))}
            </div>
          )}
        </main>

        {/* 👤 FICHE PERSONNAGE STICKY DROITE SUR ÉCRANS DESKTOP (>= xl) */}
        {selectedActor !== 'all' && (
          <aside 
            style={{ 
              top: `${sidebarTopOffset}px`, 
              height: `calc(100vh - ${sidebarTopOffset + 20}px)` 
            }}
            className="hidden xl:block w-72 lg:w-80 shrink-0 sticky overflow-y-auto pr-1 text-xs custom-scrollbar z-20"
          >
            <CharacterSpotlight
              selectedActor={selectedActor}
              onReset={() => setSelectedActor('all')}
              onSelectActor={(actorName) => setSelectedActor(actorName)}
              onSelectChannel={(channelName) => setSelectedChannel(channelName)}
            />
          </aside>
        )}
      </div>

      {/* 💬 MODALE LECTEUR DE SCÈNE : FORMAT DISCORD AVEC BANNIÈRE DU LIEU */}
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

            {/* BANNIÈRE DE LIEU DU SALON (SI DISPONIBLE) */}
            {activeSceneLocationImage && (
              <div className="h-32 w-full relative overflow-hidden border-b border-[#1e1f22] bg-slate-950 shrink-0">
                <img 
                  src={activeSceneLocationImage} 
                  alt={activeScene.channel} 
                  className="w-full h-full object-cover object-center"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#2b2d31] via-transparent to-black/30" />
                <div className="absolute bottom-2 left-6 right-6 flex items-center justify-between">
                  <span className="text-xs font-serif-gothic font-bold text-slate-100 drop-shadow-md">
                    Lieu : #{activeScene.channel}
                  </span>
                </div>
              </div>
            )}

            {/* En-tête de la Scène */}
            <div className="px-6 py-3 bg-[#2b2d31]/60 border-b border-[#1e1f22]">
              <h2 className="text-base font-bold text-[#f2f3f5] mb-2">
                {highlightSearchQuery(activeScene.title, searchQuery, 'title')}
              </h2>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-[#949ba4]">Acteurs présents :</span>
                {activeScene.actors.map(actor => {
                  const info = CHARACTERS_DATA[actor];
                  const style = getFactionStyle(info?.role);
                  const serverNick = info?.displayName || actor;

                  return (
                    <button
                      key={actor}
                      onClick={() => {
                        setSelectedActor(actor);
                        setActiveScene(null);
                      }}
                      style={{ backgroundColor: style.bg, color: style.text, borderColor: style.border }}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 border text-xs font-medium rounded cursor-pointer hover:opacity-85 hover:scale-105 transition-all shadow-sm"
                      title={`Voir la fiche visuelle de ${actor}`}
                    >
                      <span>{style.icon}</span>
                      <span>{highlightSearchQuery(serverNick, searchQuery, `act-${actor}`)}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* FLUX DES MESSAGES : FORMAT DISCORD */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar bg-[#313338]">
              {activeScene.messages.map((msg, index) => {
                const info = CHARACTERS_DATA[msg.author];
                const style = getFactionStyle(info?.role);
                const serverNick = info?.displayName || msg.author;
                const initials = getInitials(serverNick);
                const avatarImg = msg.avatar_url || info?.avatarUrl || getCharacterCardImage(msg.author);

                return (
                  <div key={msg.id || index} className="flex items-start gap-4 hover:bg-[#2e3035] p-2 rounded transition-colors group">
                    
                    {/* AVATAR ROND DISCORD */}
                    {avatarImg ? (
                      <img
                        src={avatarImg}
                        alt={serverNick}
                        style={{ borderColor: style.hexColor }}
                        className="w-10 h-10 rounded-full object-cover shrink-0 shadow-sm mt-0.5 border border-slate-700 select-none cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => setSelectedActor(msg.author)}
                        title={`Voir le profil de ${serverNick}`}
                      />
                    ) : (
                      <div 
                        style={{ backgroundColor: style.hexColor }} 
                        className="w-10 h-10 rounded-full flex items-center justify-center text-slate-950 font-bold text-xs shrink-0 shadow-sm mt-0.5 select-none"
                      >
                        {initials}
                      </div>
                    )}

                    {/* BLOC MESSAGE DISCORD */}
                    <div className="flex-1 min-w-0">
                      {/* LIGNE AUTEUR */}
                      <div className="flex items-baseline gap-2 mb-1">
                        <span 
                          style={{ color: style.text }} 
                          className="font-semibold text-[15px] hover:underline cursor-pointer tracking-wide"
                        >
                          {highlightSearchQuery(serverNick, searchQuery, `msg-author-${index}`)}
                        </span>
                        <span className="text-[12px] text-[#949ba4] font-normal select-none">
                          {formatDateDiscord(msg.timestamp)}
                        </span>
                      </div>

                      {/* EMBED DISCORD */}
                      {(msg.embed_title || msg.embed_description) && (
                        <div className="border-l-4 border-purple-500 bg-[#2b2d31] p-3 rounded-r-md mt-1.5 mb-2 max-w-2xl shadow-md">
                          {msg.embed_title && (
                            <h4 className="text-[14px] font-bold text-[#f2f3f5] mb-1">
                              {renderDiscordMarkdown(msg.embed_title, searchQuery)}
                            </h4>
                          )}
                          {msg.embed_description && (
                            <div className="text-[14px] text-[#dbdee1] italic whitespace-pre-wrap leading-relaxed">
                              {renderDiscordMarkdown(msg.embed_description, searchQuery)}
                            </div>
                          )}
                        </div>
                      )}

                      {/* CONTENU TEXTE DISCORD LISIBLE */}
                      {msg.content && (
                        <div className="text-[15px] text-[#dbdee1] leading-[1.375rem] font-sans whitespace-pre-wrap select-text">
                          {renderDiscordMarkdown(msg.content, searchQuery)}
                        </div>
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
