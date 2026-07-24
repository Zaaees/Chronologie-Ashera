import React, { useState, useMemo, useRef, useEffect } from 'react';
import { CHARACTERS_DATA, SCENES_DATA, Scene, Character, Message } from './data';
import { 
  Search, Calendar, Clock, Filter, User, Users, ChevronRight, 
  ExternalLink, Sparkles, BookOpen, Layers, X, Shield, Eye, Feather, 
  Bot, HelpCircle, ArrowUp
} from 'lucide-react';

const ROLE_ORDER: Record<string, number> = {
  "la garde pourpre": 1,
  "cercle d'azur": 2,
  "voile d'ivoire": 3,
  "l'œil": 4,
  "l'oeil": 4,
  "sans guilde": 5,
  "sans rôle": 6,
  "pnj": 7
};

const FACTION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  "La Garde Pourpre": { bg: "rgba(180, 0, 0, 0.15)", text: "#ff6b6b", border: "rgba(180, 0, 0, 0.4)" },
  "Cercle d'Azur": { bg: "rgba(48, 94, 211, 0.15)", text: "#60a5fa", border: "rgba(48, 94, 211, 0.4)" },
  "Voile d'Ivoire": { bg: "rgba(255, 255, 212, 0.12)", text: "#fef08a", border: "rgba(255, 255, 212, 0.3)" },
  "L'œil": { bg: "rgba(30, 30, 30, 0.6)", text: "#cbd5e1", border: "rgba(100, 116, 139, 0.4)" },
  "Sans guilde": { bg: "rgba(226, 206, 125, 0.15)", text: "#fde047", border: "rgba(226, 206, 125, 0.4)" },
  "Sans rôle": { bg: "rgba(148, 163, 184, 0.12)", text: "#94a3b8", border: "rgba(148, 163, 184, 0.3)" },
  "PNJ": { bg: "rgba(168, 85, 247, 0.15)", text: "#c084fc", border: "rgba(168, 85, 247, 0.4)" }
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
  const [selectedRole, setSelectedRole] = useState<string>('all');
  const [selectedActor, setSelectedActor] = useState<string>('all');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [activeMonthKey, setActiveMonthKey] = useState<string>('');
  
  // Scène sélectionnée pour la modale de lecture
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

  // Liste de tous les salons uniques
  const allChannels = useMemo(() => {
    return Array.from(new Set(SCENES_DATA.map(s => s.channel))).sort((a, b) => a.localeCompare(b, 'fr'));
  }, []);

  // Liste des acteurs filtrés
  const sortedActors = useMemo(() => {
    return Object.keys(CHARACTERS_DATA).sort((a, b) => {
      const roleA = CHARACTERS_DATA[a]?.role?.toLowerCase() || '';
      const roleB = CHARACTERS_DATA[b]?.role?.toLowerCase() || '';
      const orderA = ROLE_ORDER[roleA] || 99;
      const orderB = ROLE_ORDER[roleB] || 99;
      if (orderA !== orderB) return orderA - orderB;
      return a.localeCompare(b, 'fr');
    });
  }, []);

  // Filtrage des scènes par critères
  const filteredScenes = useMemo(() => {
    return SCENES_DATA.filter(scene => {
      // 1. Recherche textuelle
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

      // 2. Filtre par Rôle / Faction
      if (selectedRole !== 'all') {
        const hasMatchingActor = scene.actors.some(actorName => {
          const charInfo = CHARACTERS_DATA[actorName];
          return charInfo && charInfo.role === selectedRole;
        });
        if (!hasMatchingActor) return false;
      }

      // 3. Filtre par Acteur spécifique
      if (selectedActor !== 'all') {
        if (!scene.actors.includes(selectedActor)) return false;
      }

      // 4. Filtre par Salon
      if (selectedChannel !== 'all') {
        if (scene.channel !== selectedChannel) return false;
      }

      return true;
    }).sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
  }, [searchQuery, selectedRole, selectedActor, selectedChannel]);

  // Groupement des scènes par Mois/Année
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
      const yOffset = -90; 
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 font-sans selection:bg-purple-600 selection:text-white">
      {/* 🌟 EN-TÊTE PRINCIPALE */}
      <header className="sticky top-0 z-40 bg-[#0f172a]/90 backdrop-blur-md border-b border-slate-800 shadow-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            
            {/* Logo & Titre */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-purple-300">
                  Chronologie d'Ashera
                </h1>
                <p className="text-xs text-slate-400">
                  Magie & Foi • {filteredScenes.length} scènes en ordre chronologique
                </p>
              </div>
            </div>

            {/* Barre de Recherche Globale */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Rechercher une scène, un mot, un lieu..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
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

          {/* BARRE DE FILTRES SECONDAIRE */}
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-slate-800/80 text-xs">
            
            {/* Filtre Faction */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800">
              <Shield className="w-3.5 h-3.5 text-purple-400" />
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="bg-transparent text-slate-300 focus:outline-none cursor-pointer"
              >
                <option value="all" className="bg-slate-900 text-slate-200">Toutes les Factions</option>
                <option value="La Garde Pourpre" className="bg-slate-900 text-red-400">🔴 La Garde Pourpre</option>
                <option value="Cercle d'Azur" className="bg-slate-900 text-blue-400">🔵 Cercle d'Azur</option>
                <option value="Voile d'Ivoire" className="bg-slate-900 text-yellow-200">⚪ Voile d'Ivoire</option>
                <option value="L'œil" className="bg-slate-900 text-slate-400">👁️ L'œil</option>
                <option value="Sans guilde" className="bg-slate-900 text-yellow-500">🟡 Sans Guilde (Officiel)</option>
                <option value="Sans rôle" className="bg-slate-900 text-slate-500">⚪ Sans Rôle</option>
                <option value="PNJ" className="bg-slate-900 text-purple-400">🔮 PNJ / Système</option>
              </select>
            </div>

            {/* Filtre Personnage */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800">
              <User className="w-3.5 h-3.5 text-indigo-400" />
              <select
                value={selectedActor}
                onChange={(e) => setSelectedActor(e.target.value)}
                className="bg-transparent text-slate-300 focus:outline-none cursor-pointer max-w-[160px] truncate"
              >
                <option value="all" className="bg-slate-900 text-slate-200">Tous les Personnages</option>
                {sortedActors.map(actor => (
                  <option key={actor} value={actor} className="bg-slate-900 text-slate-300">
                    {actor}
                  </option>
                ))}
              </select>
            </div>

            {/* Filtre Salon */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              <select
                value={selectedChannel}
                onChange={(e) => setSelectedChannel(e.target.value)}
                className="bg-transparent text-slate-300 focus:outline-none cursor-pointer max-w-[180px] truncate"
              >
                <option value="all" className="bg-slate-900 text-slate-200">Tous les Salons ({allChannels.length})</option>
                {allChannels.map(ch => (
                  <option key={ch} value={ch} className="bg-slate-900 text-slate-300">
                    #{ch}
                  </option>
                ))}
              </select>
            </div>

            {/* Bouton Réinitialiser */}
            {(searchQuery || selectedRole !== 'all' || selectedActor !== 'all' || selectedChannel !== 'all') && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedRole('all');
                  setSelectedActor('all');
                  setSelectedChannel('all');
                }}
                className="px-2.5 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30 rounded-lg transition-colors"
              >
                Réinitialiser les filtres
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 🚀 LAYOUT PRINCIPAL */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex gap-8">
        
        {/* 📌 NAVIGATEUR CHRONOLOGIQUE PAR MOIS (MINI-MAP SIDEBAR) */}
        <aside className="hidden lg:block w-64 shrink-0">
          <div className="sticky top-32 bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4 shadow-xl backdrop-blur-md">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <Calendar className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-semibold text-slate-200">Fil Temporel</h2>
            </div>
            
            <nav className="space-y-1 max-h-[calc(100vh-220px)] overflow-y-auto pr-1 custom-scrollbar text-xs">
              {groupedPeriodScenes.map(({ key, label, scenes }) => (
                <button
                  key={key}
                  onClick={() => scrollToMonth(key)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl transition-all ${
                    activeMonthKey === key
                      ? 'bg-purple-600/30 text-purple-200 font-medium border border-purple-500/40 shadow-sm'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate">{label}</span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-400 font-mono">
                    {scenes.length}
                  </span>
                </button>
              ))}

              {groupedPeriodScenes.length === 0 && (
                <p className="text-xs text-slate-500 py-4 text-center">Aucune période disponible</p>
              )}
            </nav>
          </div>
        </aside>

        {/* 📜 FLUX DU LORE CHRONOLOGIQUE */}
        <main className="flex-1 min-w-0">
          
          {groupedPeriodScenes.length === 0 ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center my-8">
              <HelpCircle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-300 mb-1">Aucune scène trouvée</h3>
              <p className="text-sm text-slate-500 mb-6">
                Aucun résultat ne correspond aux filtres sélectionnés.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedRole('all');
                  setSelectedActor('all');
                  setSelectedChannel('all');
                }}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-medium transition-colors"
              >
                Effacer tous les filtres
              </button>
            </div>
          ) : (
            <div className="space-y-12">
              {groupedPeriodScenes.map(({ key, label, scenes }) => (
                <section key={key} id={`period-${key}`} className="scroll-mt-32">
                  
                  {/* EN-TÊTE DU MOIS / PÉRIODE */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className="px-4 py-2 bg-gradient-to-r from-purple-900/40 to-slate-900/60 border border-purple-500/30 rounded-2xl flex items-center gap-3 shadow-lg">
                      <Calendar className="w-4 h-4 text-purple-400" />
                      <h2 className="text-base font-bold text-slate-100 tracking-wide">{label}</h2>
                      <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-xs font-semibold">
                        {scenes.length} {scenes.length > 1 ? 'scènes' : 'scène'}
                      </span>
                    </div>
                    <div className="h-[1px] flex-1 bg-gradient-to-r from-purple-500/20 to-transparent" />
                  </div>

                  {/* GRILLE DES SCÈNES DU MOIS */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {scenes.map(scene => {
                      const firstDate = formatDateFr(scene.start_time);

                      return (
                        <div
                          key={scene.id}
                          onClick={() => setActiveScene(scene)}
                          className="group relative bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 hover:border-purple-500/50 rounded-2xl p-4 transition-all duration-200 cursor-pointer shadow-lg hover:shadow-purple-500/10 flex flex-col justify-between"
                        >
                          <div>
                            {/* Ligne d'En-tête de la Carte */}
                            <div className="flex items-center justify-between gap-2 mb-3">
                              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/60 text-xs font-medium text-purple-300 truncate max-w-[70%]">
                                #{scene.channel}
                              </span>
                              <span className="text-[11px] text-slate-400 flex items-center gap-1 shrink-0">
                                <Clock className="w-3 h-3 text-slate-500" />
                                {firstDate}
                              </span>
                            </div>

                            {/* Titre & Aperçu */}
                            <h3 className="text-sm font-semibold text-slate-100 group-hover:text-purple-300 transition-colors line-clamp-1 mb-2">
                              {scene.title}
                            </h3>
                            
                            <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed font-light">
                              {scene.preview}
                            </p>
                          </div>

                          {/* Acteurs & Bouton de Lecture */}
                          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-1.5 max-w-[80%]">
                              {scene.actors.slice(0, 4).map(actor => {
                                const info = CHARACTERS_DATA[actor];
                                const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];

                                return (
                                  <span
                                    key={actor}
                                    style={{ backgroundColor: style.bg, color: style.text, borderColor: style.border }}
                                    className="px-2 py-0.5 rounded-md border text-[10px] font-medium truncate max-w-[120px]"
                                  >
                                    {actor}
                                  </span>
                                );
                              })}
                              {scene.actors.length > 4 && (
                                <span className="text-[10px] text-slate-500 font-mono">
                                  +{scene.actors.length - 4}
                                </span>
                              )}
                            </div>

                            <span className="text-slate-500 group-hover:text-purple-400 transition-colors">
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

      {/* 🔮 MODAL DE LECTURE D'UNE SCÈNE */}
      {activeScene && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            
            {/* Header Modal */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 text-purple-300 rounded-xl text-xs font-semibold">
                  #{activeScene.channel}
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {formatDateFr(activeScene.start_time)}
                </span>
              </div>
              <button
                onClick={() => setActiveScene(null)}
                className="p-1.5 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Corps Modal */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 custom-scrollbar">
              
              {/* Entête de Scène */}
              <div>
                <h2 className="text-lg font-bold text-slate-100 mb-2">{activeScene.title}</h2>
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <span className="text-xs text-slate-400">Acteurs présents :</span>
                  {activeScene.actors.map(actor => {
                    const info = CHARACTERS_DATA[actor];
                    const style = info ? FACTION_COLORS[info.role] || FACTION_COLORS["Sans rôle"] : FACTION_COLORS["Sans rôle"];
                    return (
                      <span
                        key={actor}
                        style={{ backgroundColor: style.bg, color: style.text, borderColor: style.border }}
                        className="px-2.5 py-0.5 rounded-lg border text-xs font-medium"
                      >
                        {actor}
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
                    <div key={msg.id || index} className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4 space-y-2">
                      <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                        <span style={{ color: style.text }} className="text-xs font-bold">
                          {msg.author}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {formatDateFr(msg.timestamp)}
                        </span>
                      </div>

                      {msg.embed_title && (
                        <h4 className="text-xs font-semibold text-purple-300">{msg.embed_title}</h4>
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
            <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {activeScene.messages.length} message(s) dans cette scène
              </span>
              <a
                href={activeScene.discord_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-colors shadow-lg shadow-indigo-600/20"
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
          className="fixed bottom-6 right-6 p-3 bg-purple-600 hover:bg-purple-500 text-white rounded-full shadow-2xl transition-all transform hover:scale-110 z-40"
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
