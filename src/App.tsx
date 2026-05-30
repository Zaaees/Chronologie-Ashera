import React, { useState, useMemo, useEffect, useRef } from 'react';
import { CHARACTERS_DATA, SCENES_DATA, Scene, Character, Message } from './data';
import { Search, ZoomIn, ZoomOut, Maximize2, ShieldAlert, Award, Compass, Music, Palette, BookOpen, Star, HelpCircle, ArrowRightLeft } from 'lucide-react';

const ROLE_ORDER: Record<string, number> = {
  "cercle d'azur": 1,
  "la garde pourpre": 2,
  "voile d'ivoire": 3,
  "l'œil": 4,
  "l'oeil": 4,
  "sans guilde": 5,
  "autre": 6,
  "pnj": 7
};

export default function App() {
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [charSearch, setCharSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [hoveredScene, setHoveredScene] = useState<Scene | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const wrapperRef = useRef<HTMLDivElement>(null);
  const boardRef = useRef<HTMLDivElement>(null);
  
  const baseWidth = useRef(0);
  const baseHeight = useRef(0);

  const channels = useMemo(() => {
    return Array.from(new Set(SCENES_DATA.map(s => s.channel)));
  }, []);

  const characterStats = useMemo(() => {
    const stats: Record<string, number> = {};
    Object.keys(CHARACTERS_DATA).forEach(actor => {
      stats[actor] = SCENES_DATA.filter(scene => scene.actors.includes(actor)).length;
    });
    return stats;
  }, []);

  const distinctRoles = useMemo(() => {
    const roles = Array.from(new Set(Object.values(CHARACTERS_DATA).map(c => c.role)));
    return roles.sort((a, b) => {
      const orderA = ROLE_ORDER[a.toLowerCase()] || 99;
      const orderB = ROLE_ORDER[b.toLowerCase()] || 99;
      return orderA - orderB;
    });
  }, []);

  const filteredActors = useMemo(() => {
    const list = Object.keys(CHARACTERS_DATA).filter(actor => {
      const meta = CHARACTERS_DATA[actor];
      const matchesSearch = actor.toLowerCase().includes(charSearch.toLowerCase()) || 
                            meta.role.toLowerCase().includes(charSearch.toLowerCase());
      const matchesRole = roleFilter === '' || meta.role === roleFilter;
      return matchesSearch && matchesRole;
    });
    
    return list.sort((a, b) => {
      const roleA = CHARACTERS_DATA[a]?.role?.toLowerCase() || '';
      const roleB = CHARACTERS_DATA[b]?.role?.toLowerCase() || '';
      
      const orderA = ROLE_ORDER[roleA] || 99;
      const orderB = ROLE_ORDER[roleB] || 99;
      
      if (orderA !== orderB) {
        return orderA - orderB;
      }
      return a.localeCompare(b, 'fr');
    });
  }, [charSearch, roleFilter]);

  const { colMap, totalCols } = useMemo(() => {
    const sortedScenes = [...SCENES_DATA].sort(
      (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
    const mapping: Record<string, number> = {};
    let currentColumn = 1;

    if (sortedScenes.length > 0) {
      mapping[sortedScenes[0].id] = currentColumn;

      for (let i = 1; i < sortedScenes.length; i++) {
        const prev = sortedScenes[i - 1];
        const curr = sortedScenes[i];
        
        const prevDate = prev.start_time.split("T")[0];
        const currDate = curr.start_time.split("T")[0];

        if (prevDate !== currDate) {
          currentColumn++;
        }
        mapping[curr.id] = currentColumn;
      }
    }
    return { colMap: mapping, totalCols: currentColumn };
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (boardRef.current) {
        const prevTransform = boardRef.current.style.transform;
        const prevWidth = boardRef.current.style.width;
        const prevHeight = boardRef.current.style.height;

        boardRef.current.style.transform = "none";
        boardRef.current.style.width = "max-content";
        boardRef.current.style.height = "auto";
        
        baseWidth.current = boardRef.current.scrollWidth || 3000;
        baseHeight.current = boardRef.current.scrollHeight || 1000;

        boardRef.current.style.transform = prevTransform;
        boardRef.current.style.width = prevWidth;
        boardRef.current.style.height = prevHeight;

        const wrapper = wrapperRef.current;
        if (wrapper && baseWidth.current > 0) {
          const fitZoom = (wrapper.clientWidth - 40) / baseWidth.current;
          setZoomLevel(Math.max(0.15, Math.min(1.0, fitZoom)));
        }
      }
    }, 450);
    return () => clearTimeout(timer);
  }, []);

  const applyZoomCentering = (targetZoom: number) => {
    const oldZoom = zoomLevel;
    const nextZoom = Math.max(0.15, Math.min(2.0, targetZoom));
    setZoomLevel(nextZoom);

    const wrapper = wrapperRef.current;
    if (wrapper && baseWidth.current > 0) {
      const viewportWidth = wrapper.clientWidth;
      const viewportHeight = wrapper.clientHeight;
      const centerX = (wrapper.scrollLeft + viewportWidth / 2) / oldZoom;
      const centerY = (wrapper.scrollTop + viewportHeight / 2) / oldZoom;

      setTimeout(() => {
        wrapper.scrollLeft = centerX * nextZoom - viewportWidth / 2;
        wrapper.scrollTop = centerY * nextZoom - viewportHeight / 2;
      }, 10);
    }
  };

  const fitGlobalView = () => {
    const wrapper = wrapperRef.current;
    if (wrapper && baseWidth.current > 0) {
      const fitZoom = (wrapper.clientWidth - 40) / baseWidth.current;
      setZoomLevel(Math.max(0.15, Math.min(1.0, fitZoom)));
    } else {
      setZoomLevel(0.35);
    }
  };

  useEffect(() => {
    const handleWrapperWheel = (e: WheelEvent) => {
      if (e.ctrlKey) {
        e.preventDefault();
        const zoomFactor = 0.05;
        const delta = e.deltaY < 0 ? zoomFactor : -zoomFactor;
        const targetZoom = zoomLevel + delta;
        const nextZoom = Math.max(0.15, Math.min(2.0, targetZoom));

        const wrapper = wrapperRef.current;
        const board = boardRef.current;
        if (!wrapper || !board || baseWidth.current === 0) return;

        const rect = wrapper.getBoundingClientRect();
        const mouseViewportX = e.clientX - rect.left;
        const mouseViewportY = e.clientY - rect.top;

        const boardX = (wrapper.scrollLeft + mouseViewportX) / zoomLevel;
        const boardY = (wrapper.scrollTop + mouseViewportY) / zoomLevel;

        setZoomLevel(nextZoom);

        wrapper.scrollLeft = boardX * nextZoom - mouseViewportX;
        wrapper.scrollTop = boardY * nextZoom - mouseViewportY;
      }
    };

    const wrapper = wrapperRef.current;
    if (wrapper) {
      wrapper.addEventListener('wheel', handleWrapperWheel, { passive: false });
    }
    return () => {
      if (wrapper) {
        wrapper.removeEventListener('wheel', handleWrapperWheel);
      }
    };
  }, [zoomLevel]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedSceneId(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const renderRoleIcon = (role: string, color: string) => {
    const style = { color: color, flexShrink: 0 };
    switch (role?.toLowerCase()) {
      case 'cercle d\'azur':
        return <BookOpen size={16} style={style} />;
      case 'la garde pourpre':
        return <ShieldAlert size={16} style={style} />;
      case 'voile d\'ivoire':
        return <Star size={16} style={style} />;
      case 'l\'œil':
      case "l'oeil":
        return <Compass size={16} style={style} />;
      case 'sans guilde':
        return <Music size={16} style={style} />;
      case 'pnj':
        return <HelpCircle size={16} style={style} />;
      default:
        return <Palette size={16} style={style} />;
    }
  };

  const parseMarkdown = (text: string) => {
    if (!text) return "";
    return text.split("\n").map((line, lineIdx) => {
      let formatted = line;
      formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");
      return (
        <span 
          key={lineIdx} 
          style={{ display: 'block', minHeight: '1.2em' }} 
          dangerouslySetInnerHTML={{ __html: formatted }} 
        />
      );
    });
  };

  const connectors = useMemo(() => {
    let sortedConnectorScenes = [...SCENES_DATA];
    let isGlobal = true;

    if (selectedCharacter !== null) {
      sortedConnectorScenes = SCENES_DATA.filter(s => s.actors.includes(selectedCharacter));
      isGlobal = false;
    }

    sortedConnectorScenes.sort(
      (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );

    if (sortedConnectorScenes.length < 2) return { paths: [], dots: [] };

    const points = sortedConnectorScenes.map(scene => {
      const colIndex = colMap[scene.id] || 1;
      const leftOffset = (colIndex - 1) * 360 + 30;
      const laneIndex = channels.indexOf(scene.channel);
      
      const x = 220 + leftOffset + 160;
      const y = laneIndex * 242 + 110;
      return { x, y, sceneId: scene.id };
    });

    const paths: string[] = [];
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];

      const cp1x = prev.x + (curr.x - prev.x) * 0.45;
      const cp1y = prev.y;
      const cp2x = prev.x + (curr.x - prev.x) * 0.55;
      const cp2y = curr.y;

      const d = `M ${prev.x} ${prev.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
      paths.push(d);
    }

    const lineColor = selectedCharacter 
      ? (CHARACTERS_DATA[selectedCharacter]?.color || '#8b5cf6')
      : 'rgba(234, 179, 8, 0.45)';

    return { paths, dots: points, lineColor, isGlobal };
  }, [selectedCharacter, colMap, channels]);

  const handleCardDoubleClick = (scene: Scene) => {
    const colIndex = colMap[scene.id] || 1;
    const leftOffsetVal = (colIndex - 1) * 360 + 30;
    const laneIndex = channels.indexOf(scene.channel);
    
    const cardCenterX = 220 + leftOffsetVal + 160;
    const cardCenterY = laneIndex * 242 + 110;

    setZoomLevel(1.0);

    setTimeout(() => {
      if (wrapperRef.current) {
        wrapperRef.current.scrollTo({
          left: cardCenterX - wrapperRef.current.clientWidth / 2,
          top: cardCenterY - wrapperRef.current.clientHeight / 2,
          behavior: 'smooth'
        });
      }
    }, 50);
  };

  const activeModalScene = useMemo(() => {
    return SCENES_DATA.find(s => s.id === selectedSceneId) || null;
  }, [selectedSceneId]);

  return (
    <>
      <div className="glow-orb orb-1" id="orb-1"></div>
      <div className="glow-orb orb-2" id="orb-2"></div>
      <div className="glow-orb orb-3" id="orb-3"></div>

      <div className="app-container">
        
        <aside className="sidebar" id="character-list-sidebar">
          
          <div className="sidebar-header">
            <h1 className="app-title">Chronologie d'Ashera</h1>
          </div>

          <div className="section-title">Recherche & Filtres</div>
          
          {/* Quick search input and role selectors */}
          <div className="search-container">
            <input 
              type="text" 
              id="char-search" 
              placeholder="Rechercher un personnage..." 
              className="char-search-input"
              value={charSearch}
              onChange={(e) => setCharSearch(e.target.value)}
            />

            <div className="flex gap-2">
              <select 
                className="char-search-input py-2 text-xs flex-grow cursor-pointer"
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                style={{ background: 'rgba(10, 10, 20, 0.9)', minWidth: 120 }}
              >
                <option value="">Tous les rôles</option>
                {distinctRoles.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>

              {roleFilter !== '' && (
                <button 
                  className="btn-reset-top py-1.5 px-3 select-none text-xs flex items-center justify-center"
                  onClick={() => setRoleFilter('')}
                >
                  ✕
                </button>
              )}
            </div>

            {selectedCharacter !== null && (
              <button 
                className="btn-reset-top active:scale-95 duration-100" 
                id="btn-reset-top"
                onClick={() => setSelectedCharacter(null)}
              >
                ✕ Effacer le fil d'Ariane
              </button>
            )}
          </div>

          <div className="section-title">
            Personnages ({filteredActors.length})
          </div>

          <div className="character-list" id="character-list">
            {filteredActors.length === 0 ? (
              <div className="loading-text text-center py-6">Aucun personnage trouvé</div>
            ) : (
              filteredActors.map(actor => {
                const meta = CHARACTERS_DATA[actor];
                const isActive = selectedCharacter === actor;
                const scenesCount = characterStats[actor] || 0;

                return (
                  <div 
                    key={actor}
                    className={`character-card group ${isActive ? 'active' : ''}`}
                    onClick={() => setSelectedCharacter(isActive ? null : actor)}
                    style={{ 
                      color: meta.color,
                      borderColor: isActive ? meta.color : undefined,
                      boxShadow: isActive ? `0 0 15px ${meta.color}35` : undefined
                    }}
                    data-char={actor}
                  >
                    <div className="absolute left-0 top-0 h-full w-1 rounded-l-md" style={{ backgroundColor: meta.color }} />
                    <div className="char-avatar" style={{ backgroundColor: meta.color }} />
                    
                    <div className="char-info flex-grow">
                      <div className="flex items-center gap-2">
                        <span className="char-name text-slate-100 group-hover:text-white transition-colors">{actor}</span>
                        {renderRoleIcon(meta.role, meta.color)}
                      </div>
                      <span className="char-role block text-xs">{meta.role}</span>
                      
                      <span className="char-stats-indicator">
                        {scenesCount} {scenesCount > 1 ? 'scènes' : 'scène'}
                      </span>
                    </div>

                    <div className="opacity-0 group-hover:opacity-100 duration-200 text-xs font-mono ml-auto" style={{ color: meta.color }}>
                      {isActive ? 'Actif' : 'Sélectionner'}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="sidebar-footer">
            <p className="mb-2">
              <span className="inline-block w-2.5 h-1.5 bg-yellow-500 rounded-sm mr-1"></span>
              <strong>Fil Directeur :</strong> Ligne dorée en pointillés reliant toutes les scènes du scénario principal d'écriture.
            </p>
            <p>
              <span className="inline-block w-2.5 h-1.5 bg-indigo-500 rounded-sm mr-1"></span>
              <strong>Fil d'Ariane :</strong> Sélectionnez un personnage ci-dessus pour isoler son parcours à travers les différents salons.
            </p>
          </div>
        </aside>

        <main className="timeline-container">
          
          <header className="timeline-header flex justify-between items-center">
            
            <div className="header-info">
              <h2 className="text-2xl font-serif text-white flex items-center gap-3">
                <Compass className="text-indigo-400" />
                Scènes par ordre chronologique
              </h2>
            </div>

            <div className="zoom-controls">
              <button 
                className="btn-zoom" 
                id="btn-zoom-out" 
                title="Dézoomer"
                onClick={() => applyZoomCentering(zoomLevel - 0.1)}
              >
                ➖
              </button>
              
              <span className="zoom-badge" id="zoom-percent">
                {Math.round(zoomLevel * 100)}%
              </span>
              
              <button 
                className="btn-zoom" 
                id="btn-zoom-in" 
                title="Zoomer"
                onClick={() => applyZoomCentering(zoomLevel + 0.1)}
              >
                ➕
              </button>
              
              <button 
                className="btn-zoom-reset text-white" 
                id="btn-zoom-reset"
                onClick={fitGlobalView}
              >
                Vue Globale
              </button>
            </div>

            <div className="legend flex items-center gap-4">
              <div className="legend-item">
                <span className="legend-dot main-timeline"></span>
                <span>Scène RP</span>
              </div>
              <div className="legend-item flex items-center gap-1">
                <svg width="24" height="6">
                  <line x1="0" y1="3" x2="24" y2="3" stroke="#eab308" strokeWidth="2" strokeDasharray="4 3" />
                </svg>
                <span>Fil Directeur Principal</span>
              </div>
              <div className="legend-item flex items-center gap-1">
                <svg width="24" height="6">
                  <line x1="0" y1="3" x2="24" y2="3" stroke="#8b5cf6" strokeWidth="2.5" />
                </svg>
                <span>Parcours Personnage</span>
              </div>
            </div>
          </header>

          <div 
            className="lanes-wrapper" 
            id="lanes-wrapper"
            ref={wrapperRef}
            onClick={() => setSelectedCharacter(null)}
            onDoubleClick={(e) => {
              if (e.target === e.currentTarget) {
                fitGlobalView();
              }
            }}
          >
            <div 
              className={`timeline-board ${zoomLevel < 0.65 ? 'zoom-out-mode' : ''}`}
              id="timeline-board"
              ref={boardRef}
              style={{
                width: baseWidth.current ? `${baseWidth.current * zoomLevel}px` : 'max-content',
                height: baseHeight.current ? `${baseHeight.current * zoomLevel}px` : 'auto',
                transform: `scale(${zoomLevel})`,
                '--total-cols': totalCols
              } as React.CSSProperties}
            >
              
              <svg 
                className="absolute inset-x-0 inset-y-0 h-full w-full pointer-events-none z-10" 
                style={{ overflow: 'visible' }}
              >
                {connectors.paths.map((d, index) => (
                  <g key={`connect-path-${index}`}>
                    <path 
                      d={d}
                      className="ariane-line"
                      stroke={connectors.lineColor}
                      strokeWidth={connectors.isGlobal ? 3.5 : 6}
                      opacity={connectors.isGlobal ? 0.18 : 0.35}
                      style={{ filter: 'blur(3px)' }}
                      fill="none"
                    />
                    <path 
                      d={d}
                      className={`ariane-line ${connectors.isGlobal ? 'global-thread' : ''}`}
                      stroke={connectors.isGlobal ? connectors.lineColor : '#ffffff'}
                      strokeWidth={connectors.isGlobal ? 1.8 : 2.5}
                      opacity={connectors.isGlobal ? 0.55 : 0.95}
                      fill="none"
                    />
                  </g>
                ))}

                {connectors.dots.map((dot, index) => (
                  <g key={`connect-node-${index}-${dot.sceneId}`}>
                    <circle 
                      cx={dot.x} 
                      cy={dot.y} 
                      r={connectors.isGlobal ? 6 : 8} 
                      fill={connectors.lineColor} 
                      opacity={connectors.isGlobal ? 0.3 : 0.45}
                      style={{ filter: connectors.isGlobal ? undefined : 'blur(2.5px)' }}
                    />
                    <circle 
                      cx={dot.x} 
                      cy={dot.y} 
                      r={connectors.isGlobal ? 2.5 : 4} 
                      fill={connectors.isGlobal ? connectors.lineColor : '#ffffff'} 
                    />
                  </g>
                ))}
              </svg>

              {channels.map((channel, laneIndex) => {
                const laneScenes = SCENES_DATA.filter(s => s.channel === channel);
                const displayTitle = channel.replace(/_/g, ' ').replace(/-/g, ' ');

                return (
                  <div 
                    key={channel} 
                    className="lane flex"
                    id={`lane-${channel.replace(/\s+/g, "_")}`}
                  >
                    <div className="lane-title select-none sticky left-0">
                      <h3 title={displayTitle}>#{displayTitle}</h3>
                      <span>{laneScenes.length} scène{laneScenes.length > 1 ? 's' : ''} RP</span>
                    </div>

                    <div className="lane-cards" id={`cards-${channel.replace(/\s+/g, "_")}`}>
                      {laneScenes.map(scene => {
                        const colIdx = colMap[scene.id] || 1;
                        const leftOffset = (colIdx - 1) * 360 + 30;
                        
                        const hasActiveSelection = selectedCharacter !== null;
                        const actorParticipating = selectedCharacter !== null && scene.actors.includes(selectedCharacter);
                        const isCardDimmed = hasActiveSelection && !actorParticipating;
                        const isCardHighlighted = hasActiveSelection && actorParticipating;

                        const start = new Date(scene.start_time);
                        const end = new Date(scene.end_time);

                        const dateStr = start.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
                        const timeStartStr = start.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
                        const timeEndStr = end.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

                        const charHighlightColor = selectedCharacter && CHARACTERS_DATA[selectedCharacter]?.color;

                        return (
                          <div 
                            key={scene.id}
                            className={`scene-card ${isCardDimmed ? 'dimmed' : ''} ${isCardHighlighted ? 'highlighted text-white' : ''}`}
                            id={scene.id}
                            style={{ 
                              left: `${leftOffset}px`,
                              borderColor: isCardHighlighted ? charHighlightColor || undefined : undefined,
                              boxShadow: isCardHighlighted ? `0 0 20px ${charHighlightColor}25` : undefined
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedSceneId(scene.id);
                            }}
                            onDoubleClick={(e) => {
                              e.stopPropagation();
                              handleCardDoubleClick(scene);
                            }}
                            onMouseEnter={(e) => {
                              if (zoomLevel < 0.65) {
                                const rect = e.currentTarget.getBoundingClientRect();
                                setTooltipPos({
                                  x: rect.left + rect.width / 2,
                                  y: rect.top - 10
                                });
                                setHoveredScene(scene);
                              }
                            }}
                            onMouseLeave={() => setHoveredScene(null)}
                          >
                            <div className="card-header">
                              <span className="scene-number">
                                {scene.id.replace("scene_", "").replace(/_/g, " ").toUpperCase()}
                              </span>
                              <span className="scene-date">
                                {dateStr} • {timeStartStr} - {timeEndStr}
                              </span>
                            </div>

                            <h4 
                              className="scene-title-text" 
                              title={scene.title}
                              style={{ borderBottom: isCardHighlighted ? `1px solid ${charHighlightColor}44` : undefined }}
                            >
                              {scene.title}
                            </h4>

                            <p className="scene-preview">
                              "{scene.preview}"
                            </p>

                            <div className="card-footer flex justify-between items-center">
                              <div className="card-actors flex gap-1 items-center">
                                {scene.actors.slice(0, 3).map(act => {
                                  const c = CHARACTERS_DATA[act]?.color || '#94a3b8';
                                  const isMatchedActor = selectedCharacter === act;
                                  return (
                                    <span 
                                      key={act}
                                      className={`actor-pill text-[10px] ${isMatchedActor ? 'active-char font-bold text-white' : ''}`}
                                      style={{ 
                                        color: isMatchedActor ? '#000000' : c,
                                        backgroundColor: isMatchedActor ? c : undefined,
                                        border: !isMatchedActor ? `1px solid ${c}35` : undefined
                                      }}
                                    >
                                      {act.split(" ")[0]}
                                    </span>
                                  );
                                })}
                                {scene.actors.length > 3 && (
                                  <span className="actor-pill text-[10px] text-slate-400">
                                    +{scene.actors.length - 3}
                                  </span>
                                )}
                              </div>

                              <span className="msg-count">
                                {scene.message_count} posts
                              </span>
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
        </main>
      </div>

      {hoveredScene && (
        <div 
          className="hover-tooltip active"
          style={{
            left: `${Math.max(10, Math.min(window.innerWidth - 330, tooltipPos.x - 160))}px`,
            top: `${Math.max(10, tooltipPos.y - 190)}px`,
            position: 'fixed'
          }}
        >
          <div className="card-header">
            <span className="scene-number">
              {hoveredScene.id.replace("scene_", "").replace(/_/g, " ").toUpperCase()}
            </span>
            <span className="scene-date">
              {new Date(hoveredScene.start_time).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
            </span>
          </div>

          <h4>{hoveredScene.title}</h4>
          
          <p className="text-slate-300">
            "{hoveredScene.preview}"
          </p>

          <div className="card-footer">
            <div className="card-actors">
              {hoveredScene.actors.slice(0, 4).map(act => {
                const col = CHARACTERS_DATA[act]?.color || 'rgba(255,255,255,0.2)';
                return (
                  <span 
                    key={act} 
                    className="actor-pill" 
                    style={{ border: `1.5px solid ${col}35`, color: col }}
                  >
                    {act.split(" ")[0]}
                  </span>
                );
              })}
            </div>
            <span className="msg-count">{hoveredScene.message_count} posts</span>
          </div>
        </div>
      )}

      <div className={`reader-modal ${selectedSceneId ? 'active' : ''}`} id="reader-modal">
        <div className="modal-backdrop" id="modal-backdrop" onClick={() => setSelectedSceneId(null)}></div>
        
        {activeModalScene && (
          <div className="modal-content">
            
            <header className="modal-header">
              <div className="modal-title-area">
                <span className="modal-scene-number" id="modal-scene-number">
                  {activeModalScene.id.replace("scene_", "").replace(/_/g, " ").toUpperCase()}
                </span>
                
                <h2 className="modal-title text-white font-serif" id="modal-title" title={activeModalScene.title}>
                  {activeModalScene.title}
                </h2>
                
                <span className="modal-channel font-mono text-indigo-300" id="modal-channel">
                  #{activeModalScene.channel.replace(/_/g, ' ').replace(/-/g, ' ')}
                </span>
              </div>

              <div className="modal-header-actions">
                {activeModalScene.discord_url && (
                  <a 
                    href={activeModalScene.discord_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-discord-link flex items-center gap-2" 
                    id="btn-discord-link"
                  >
                    <svg className="discord-svg-icon fill-white" viewBox="0 0 127.14 96.36" width="16" height="16">
                      <path d="M107.7,8.07A105.15,105.15,0,0,0,77.26,0a77.19,77.19,0,0,0-3.3,6.83A96.67,96.67,0,0,0,52.8,6.83,77.19,77.19,0,0,0,49.5,0,105.15,105.15,0,0,0,19.06,8.07C3.58,31.21-1,53.7,1,75.8a107.84,107.84,0,0,0,32,16.15,80.39,80.39,0,0,0,6.83-11.1,68.43,68.43,0,0,1-10.75-5.18c.91-.66,1.8-1.34,2.65-2a76.08,76.08,0,0,0,62.77,0c.85.69,1.74,1.37,2.65,2a68.43,68.43,0,0,1-10.75,5.18,80.39,80.39,0,0,0,6.83,11.1,107.84,107.84,0,0,0,32-16.15C129.27,53.7,124.69,31.21,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53S36.18,40.36,42.45,40.36,53.9,46,53.9,53,48.72,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.24,60,73.24,53S78.41,40.36,84.69,40.36,96.14,46,96.14,53,91,65.69,84.69,65.69Z"/>
                    </svg>
                    Ouvrir sur Discord
                  </a>
                )}
                
                <button 
                  className="btn-close-modal" 
                  id="btn-close-modal"
                  onClick={() => setSelectedSceneId(null)}
                >
                  ✕
                </button>
              </div>
            </header>

            <div className="modal-body" id="modal-body">
              {activeModalScene.messages.length === 0 ? (
                <p className="loading-text text-center text-slate-400">
                  Aucun message enregistré dans cette scène.
                </p>
              ) : (
                activeModalScene.messages.map((m) => {
                  const authorColor = CHARACTERS_DATA[m.author]?.color || "#e2e8f0";
                  const date = new Date(m.timestamp);
                  
                  const formattedTitle = m.embed_title ? m.embed_title : "";
                  const formattedDesc = m.embed_description ? m.embed_description : "";

                  return (
                    <div 
                      key={m.id} 
                      className="modal-message"
                      style={{ '--msg-char-color': authorColor } as React.CSSProperties}
                    >
                      <div className="msg-header">
                        <span className="msg-author cursor-pointer hover:underline" onClick={() => {
                          setSelectedCharacter(m.author);
                          setSelectedSceneId(null);
                        }}>
                          {m.author}
                        </span>
                        
                        <span className="msg-timestamp">
                          {date.toLocaleString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>

                      {m.content && (
                        <div className="msg-text mb-2">
                          {parseMarkdown(m.content)}
                        </div>
                      )}

                      {(m.embed_title || m.embed_description) && (
                        <div 
                          className="msg-embed"
                          style={{ '--msg-char-color': authorColor } as React.CSSProperties}
                        >
                          {m.embed_title && (
                            <span className="embed-title-text font-serif text-slate-100 flex items-center gap-2">
                              {formattedTitle}
                            </span>
                          )}
                          {m.embed_description && (
                            <div className="embed-desc-text text-slate-300">
                              {parseMarkdown(m.embed_description)}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
