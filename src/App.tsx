import React, { useState, useMemo, useEffect } from 'react';
import { CHARACTERS_DATA, SCENES_DATA, Scene, Character, Message } from './data';
import { 
  Search, Calendar, Clock, Users, ChevronRight, 
  ExternalLink, Layers, X, ArrowUp, HelpCircle, Shield, Scroll, Eye, Sword, Feather, Sun, Wand2
} from 'lucide-react';

const FACTION_COLORS: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  "La Garde Pourpre": { bg: "rgba(153, 27, 27, 0.28)", text: "#fca5a5", border: "rgba(220, 38, 38, 0.55)", icon: "🗡️" },
  "Cercle d'Azur": { bg: "rgba(30, 58, 138, 0.28)", text: "#93c5fd", border: "rgba(59, 130, 246, 0.55)", icon: "🌙" },
  "Voile d'Ivoire": { bg: "rgba(254, 240, 138, 0.14)", text: "#fef08a", border: "rgba(254, 240, 138, 0.4)", icon: "⚖️" },
  "L'œil": { bg: "rgba(30, 41, 59, 0.7)", text: "#e2e8f0", border: "rgba(148, 163, 184, 0.45)", icon: "👁️" },
  "Sans guilde": { bg: "rgba(180, 83, 9, 0.28)", text: "#fde047", border: "rgba(217, 119, 6, 0.55)", icon: "☀️" },
  "Sans rôle": { bg: "rgba(71, 85, 105, 0.28)", text: "#cbd5e1", border: "rgba(100, 116, 139, 0.45)", icon: "🛡️" },
  "PNJ": { bg: "rgba(126, 34, 206, 0.28)", text: "#d8b4fe", border: "rgba(168, 85, 247, 0.55)", icon: "🔮" }
};

// Formater la date en français clair
function formatDateFr(isoString: string): string {
  if (!isoString) return 'Date inconnue';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

export default function App() {
  // États de filtres et recherche
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedActor, setSelectedActor] = useState<string>('all');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [activeMonthKey, setActiveMonthKey] = useState<string>('');
  
  // Scène sélectionnée pour la modale de lecture (Codex)
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

  // Filtrage des scènes par critères
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

  // Groupement complet des scènes par Mois/Année
  const groupedPeriodScenes = useMemo(() => {
    const groups: { key: string; label: string; scenes: Scene[] }[] = [];
    const groupMap: Record<string, { label: string; scenes: Scene[] }> = {};

    filteredScenes.forEach(scene => {
      const { key, label } = getMonthYearKey(scene.start_time);
      if (!groupMap[key]) {
        groupMap[key] = { label, scenes: [] };
        groups.push({ key, label, scenes: groupMap[key].scenes });
      }
      groupMap[key].scenes.push(scene);
    });

    return groups;
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
      
      {/* 🖼️ IMAGE DE FOND DARK FANTASY DU PROJET FLOUTÉE */}
      <div className="bg-dark-fantasy-layer" />
      <div className="bg-vignette-overlay" />
      <div className="ember-particles-bg" />

      {/* 🗡️ EN-TÊTE GOTHIQUE ÉPURÉE */}
      <header className="sticky top-0 z-40 bg-[#090b10]/95 backdrop-blur-md border-b border-slate-800/90 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            
            {/* Logo & Titre Cinzel */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 border border-slate-700 bg-slate-950 flex items-center justify-center shadow-lg shadow-black/80">
                <Scroll className="w-5 h-5 text-slate-300" />
              </div>
              <div>
                <h1 className="text-xl font-bold font-serif-gothic tracking-widest text-slate-100 uppercase">
                  Chronologie d'Ashera
                </h1>
                <p className="text-xs text-slate-400 font-light">
                  {filteredScenes.length} scènes RP répertoriées
                </p>
              </div>
            </div>

            {/* Barre de Recherche Tranchée */}
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

          {/* FILTRES ERGONOMIQUES STYLE SOMBRE */}
          <div className="flex flex-wrap items-center gap-3 mt-3 pt-3 border-t border-slate-800/80 text-xs">
            
            {/* Personnages par Faction */}
            <div className="flex items-center gap-2 bg-[#0d0f17] px-3 py-2 border border-slate-800 shadow-sm flex-1 min-w-[240px]">
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
            <div className="flex items-center gap-2 bg-[#0d0f17] px-3 py-2 border border-slate-800 shadow-sm flex-1 min-w-[240px]">
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

            {/* Réinitialiser */}
            {(searchQuery || selectedActor !== 'all' || selectedChannel !== 'all') && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedActor('all');
                  setSelectedChannel('all');
                }}
                className="px-3 py-2 bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 transition-colors shrink-0 font-medium"
              >
                Réinitialiser les filtres
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 🚀 LAYOUT GOTHIQUE AVEC SIDEBAR & LA CHRONOLOGIE VERTICALE */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex gap-8">
        
        {/* 📌 SAUT TEMPOREL (SIDEBAR MINIMALISTE AVEC CORNIÈRES) */}
        <aside className="hidden lg:block w-64 shrink-0">
          <div className="sticky top-36 gothic-corner-box bg-[#0c0e15]/90 border border-slate-800 p-4 shadow-2xl backdrop-blur-md">
            <div className="gothic-corner gothic-corner-tl" />
            <div className="gothic-corner gothic-corner-tr" />
            <div className="gothic-corner gothic-corner-bl" />
            <div className="gothic-corner gothic-corner-br" />

            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <Calendar className="w-4 h-4 text-slate-400" />
              <h2 className="text-xs font-bold font-serif-gothic tracking-wider uppercase text-slate-300">Saut Temporel</h2>
            </div>
            
            <nav className="space-y-1 max-h-[calc(100vh-230px)] overflow-y-auto pr-1 text-xs">
              {groupedPeriodScenes.map(({ key, label, scenes }) => (
                <button
                  key={key}
                  onClick={() => scrollToMonth(key)}
                  className={`w-full flex items-center justify-between px-3 py-2 transition-all ${
                    activeMonthKey === key
                      ? 'bg-slate-800/80 text-slate-100 font-semibold border-l-2 border-slate-300'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate">{label}</span>
                  <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-[10px] text-slate-400 font-mono">
                    {scenes.length}
                  </span>
                </button>
              ))}

              {groupedPeriodScenes.length === 0 && (
                <p className="text-xs text-slate-500 py-4 text-center">Aucun résultat</p>
              )}
            </nav>
          </div>
        </aside>

        {/* 📜 LA CHRONOLOGIE (FIL VERTICAL ARGENTÉ) */}
        <main className="flex-1 min-w-0 relative pl-8">
          
          {/* Ligne verticale de la chronologie (Spine argentée) */}
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
              {groupedPeriodScenes.map(({ key, label, scenes }) => (
                <section key={key} id={`period-${key}`} className="scroll-mt-36 relative">
                  
                  {/* ANCRAGE & NOEUD DE PÉRIODE (Nœud Métallique Argenté) */}
                  <div className="flex items-center gap-4 mb-6 -ml-8">
                    <div className="w-10 h-10 bg-[#08090d] border-2 border-slate-400 flex items-center justify-center shadow-lg shadow-black/80 shrink-0 z-10">
                      <div className="w-3 h-3 bg-slate-300 transform rotate-45" />
                    </div>
                    
                    <div className="px-4 py-2 bg-[#0c0e15] border border-slate-700/80 flex items-center gap-3 shadow-xl">
                      <h2 className="text-sm font-bold font-serif-gothic tracking-widest text-slate-100 uppercase">{label}</h2>
                      <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-mono">
                        {scenes.length} {scenes.length > 1 ? 'SCÈNES' : 'SCÈNE'}
                      </span>
                    </div>
                    
                    <div className="h-[1px] flex-1 bg-gradient-to-r from-slate-700/60 to-transparent" />
                  </div>

                  {/* GRILLE DES CARTE GOTHIQUES DE SCÈNES AVEC CORNIÈRES */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {scenes.map(scene => {
                      const firstDate = formatDateFr(scene.start_time);

                      return (
                        <div
                          key={scene.id}
                          onClick={() => setActiveScene(scene)}
                          className="gothic-card gothic-corner-box relative p-4.5 cursor-pointer flex flex-col justify-between"
                        >
                          <div className="gothic-corner gothic-corner-tl" />
                          <div className="gothic-corner gothic-corner-tr" />
                          <div className="gothic-corner gothic-corner-bl" />
                          <div className="gothic-corner gothic-corner-br" />

                          <div>
                            {/* En-tête de la carte */}
                            <div className="flex items-center justify-between gap-2 mb-3">
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 truncate max-w-[70%]">
                                #{scene.channel}
                              </span>
                              <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1 shrink-0">
                                <Clock className="w-3 h-3 text-slate-500" />
                                {firstDate}
                              </span>
                            </div>

                            {/* Titre & Résumé */}
                            <h3 className="text-sm font-semibold text-slate-100 group-hover:text-slate-300 transition-colors line-clamp-1 mb-2">
                              {scene.title}
                            </h3>
                            
                            <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed font-light">
                              {scene.preview}
                            </p>
                          </div>

                          {/* Acteurs & Sceaux de Faction */}
                          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-1.5 max-w-[85%]">
                              {scene.actors.slice(0, 4).map(actor => {
                                const info = CHARACTERS_DATA[actor];
                                const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];

                                return (
                                  <span
                                    key={actor}
                                    style={{ backgroundColor: style.bg, color: style.text, borderColor: style.border }}
                                    className="inline-flex items-center gap-1 px-2 py-0.5 border text-[10px] font-medium truncate max-w-[130px]"
                                  >
                                    <span className="text-[10px]">{style.icon}</span>
                                    <span className="truncate">{actor}</span>
                                  </span>
                                );
                              })}
                              {scene.actors.length > 4 && (
                                <span className="text-[10px] text-slate-500 font-mono">
                                  +{scene.actors.length - 4}
                                </span>
                              )}
                            </div>

                            <span className="text-slate-500 hover:text-slate-200 transition-colors">
                              <ChevronRight className="w-4 h-4" />
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* 🔮 MODALE CODEX LECTURE DE SCÈNE GOTHIQUE */}
      {activeScene && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
          <div className="gothic-corner-box bg-[#0c0e15] border border-slate-700 w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative">
            <div className="gothic-corner gothic-corner-tl" />
            <div className="gothic-corner gothic-corner-tr" />
            <div className="gothic-corner gothic-corner-bl" />
            <div className="gothic-corner gothic-corner-br" />

            {/* Header Modal */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#080a0f]">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-1 bg-slate-900 border border-slate-700 text-slate-200 font-mono text-xs">
                  #{activeScene.channel}
                </span>
                <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {formatDateFr(activeScene.start_time)}
                </span>
              </div>
              <button
                onClick={() => setActiveScene(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Corps Modal */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 custom-scrollbar">
              
              <div>
                <h2 className="text-lg font-bold font-serif-gothic tracking-wide text-slate-100 mb-2">{activeScene.title}</h2>
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <span className="text-xs text-slate-400">Acteurs présents :</span>
                  {activeScene.actors.map(actor => {
                    const info = CHARACTERS_DATA[actor];
                    const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];
                    return (
                      <span
                        key={actor}
                        style={{ backgroundColor: style.bg, color: style.text, borderColor: style.border }}
                        className="inline-flex items-center gap-1 px-2.5 py-0.5 border text-xs font-medium"
                      >
                        <span>{style.icon}</span>
                        <span>{actor}</span>
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Messages de la Scène */}
              <div className="space-y-4">
                {activeScene.messages.map((msg, index) => {
                  const info = CHARACTERS_DATA[msg.author];
                  const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];

                  return (
                    <div key={msg.id || index} className="bg-[#08090d] border border-slate-800/90 p-4 space-y-2">
                      <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                        <span style={{ color: style.text }} className="text-xs font-bold font-serif-gothic tracking-wider inline-flex items-center gap-1.5">
                          <span>{style.icon}</span>
                          <span>{msg.author}</span>
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {formatDateFr(msg.timestamp)}
                        </span>
                      </div>

                      {msg.embed_title && (
                        <h4 className="text-xs font-semibold text-slate-300 font-serif-gothic">{msg.embed_title}</h4>
                      )}

                      {msg.embed_description && (
                        <p className="text-xs text-slate-300 italic whitespace-pre-line leading-relaxed">{msg.embed_description}</p>
                      )}

                      {msg.content && (
                        <p className="text-xs text-slate-200 whitespace-pre-line leading-relaxed">{msg.content}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Footer Modal avec Lien Discord */}
            <div className="px-6 py-4 border-t border-slate-800 bg-[#080a0f] flex items-center justify-between">
              <span className="text-xs text-slate-500 font-mono">
                {activeScene.messages.length} message(s) dans cette scène
              </span>
              <a
                href={activeScene.discord_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 text-xs font-semibold transition-colors"
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
          className="fixed bottom-6 right-6 p-3 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 shadow-2xl transition-all z-40"
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
