import React, { useState } from 'react';
import { X, Film, MessageSquare, MapPin, Users, ZoomIn, Shield, Sparkles } from 'lucide-react';
import { getCharacterStats, CharacterStats } from '../utils/characterHelper';

interface CharacterSpotlightProps {
  selectedActor: string;
  onReset: () => void;
  onSelectActor: (actorName: string) => void;
  onSelectChannel?: (channelName: string) => void;
}

export const CharacterSpotlight: React.FC<CharacterSpotlightProps> = ({
  selectedActor,
  onReset,
  onSelectActor,
  onSelectChannel,
}) => {
  const [showLightbox, setShowLightbox] = useState(false);
  const stats: CharacterStats | null = getCharacterStats(selectedActor);

  if (!stats) return null;

  return (
    <>
      <div 
        style={{ borderColor: `${stats.color}50` }}
        className="relative gothic-corner-box bg-[#0c0e15]/95 border p-5 sm:p-6 mb-8 shadow-2xl backdrop-blur-md overflow-hidden transition-all duration-300 animate-fadeIn"
      >
        <div className="gothic-corner gothic-corner-tl" />
        <div className="gothic-corner gothic-corner-tr" />
        <div className="gothic-corner gothic-corner-bl" />
        <div className="gothic-corner gothic-corner-br" />

        {/* Ambient background glow matching guild color */}
        <div 
          style={{ background: `radial-gradient(circle at 10% 20%, ${stats.color}25 0%, transparent 60%)` }}
          className="absolute inset-0 pointer-events-none"
        />

        {/* Close Button */}
        <button
          onClick={onReset}
          className="absolute top-4 right-4 p-1.5 bg-slate-900/80 hover:bg-red-950/80 text-slate-400 hover:text-red-300 border border-slate-700/60 transition-colors z-20"
          title="Fermer la fiche personnage"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="relative z-10 flex flex-col gap-4 items-stretch">
          
          {/* Header Title & Close Button */}
          <div className="pr-8">
            <div className="flex flex-col gap-0.5">
              <h2 className="text-lg sm:text-xl font-bold font-serif-gothic tracking-wide text-slate-100 leading-tight">
                {stats.name}
              </h2>
              {stats.displayName && stats.displayName !== stats.name && (
                <span className="text-xs text-slate-400 font-mono">
                  ({stats.displayName})
                </span>
              )}
            </div>
          </div>

          {/* Character Card Image / Avatar */}
          <div className="w-full shrink-0 flex flex-col items-center">
            {stats.cardImage ? (
              <div 
                onClick={() => setShowLightbox(true)}
                className="relative group cursor-pointer w-full overflow-hidden border-2 shadow-2xl transition-all duration-300 transform hover:scale-[1.01]"
                style={{ borderColor: stats.color }}
              >
                <img 
                  src={stats.cardImage} 
                  alt={stats.name}
                  className="w-full h-72 sm:h-80 object-cover object-top transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center p-3">
                  <span className="flex items-center gap-1.5 text-xs text-white bg-black/70 px-3 py-1 border border-white/20 backdrop-blur-sm">
                    <ZoomIn className="w-3.5 h-3.5" />
                    Agrandir la carte
                  </span>
                </div>
              </div>
            ) : (
              <div 
                style={{ borderColor: stats.color, backgroundColor: `${stats.color}15` }}
                className="w-full h-56 border-2 flex flex-col items-center justify-center p-4 text-center shadow-xl"
              >
                <div 
                  style={{ backgroundColor: stats.color }}
                  className="w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold font-serif-gothic text-slate-950 mb-2 shadow-lg"
                >
                  {stats.name.substring(0, 2).toUpperCase()}
                </div>
                <span className="text-xs text-slate-400 font-medium mt-1">Aucune image</span>
              </div>
            )}

            {/* Guild Role Badge */}
            <div 
              style={{ borderColor: `${stats.color}60`, color: stats.color }}
              className="mt-2.5 w-full text-center px-3 py-1.5 bg-[#08090d] border text-xs font-bold font-serif-gothic tracking-wider uppercase flex items-center justify-center gap-1.5 shadow-sm"
            >
              <Shield className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">{stats.role}</span>
            </div>
          </div>

          {/* Detailed Stats */}
          <div className="space-y-3.5 w-full">
            
            {/* Main Stats Grid */}
            <div className="grid grid-cols-2 gap-2">
              
              <div className="bg-[#08090d]/80 border border-slate-800 p-2.5 shadow-sm">
                <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1">
                  <Film className="w-3 h-3 text-purple-400 shrink-0" />
                  <span className="truncate">Scènes Jouées</span>
                </div>
                <div className="text-base font-bold font-mono text-purple-300">
                  {stats.totalScenes} <span className="text-[10px] font-normal text-slate-400">{stats.totalScenes > 1 ? 'scènes' : 'scène'}</span>
                </div>
              </div>

              <div className="bg-[#08090d]/80 border border-slate-800 p-2.5 shadow-sm">
                <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1">
                  <MessageSquare className="w-3 h-3 text-blue-400 shrink-0" />
                  <span className="truncate">Actions postées</span>
                </div>
                <div className="text-base font-bold font-mono text-blue-300">
                  {stats.totalMessages} <span className="text-[10px] font-normal text-slate-400">msgs</span>
                </div>
              </div>

            </div>

            {/* Top Channels / Lieux de RP */}
            {stats.topChannels.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-emerald-400 shrink-0" />
                  Salons & Lieux principaux :
                </span>
                <div className="flex flex-wrap gap-1">
                  {stats.topChannels.map(ch => (
                    <button
                      key={ch.name}
                      onClick={() => onSelectChannel && onSelectChannel(ch.name)}
                      className="px-2 py-0.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-[11px] text-slate-300 transition-colors flex items-center gap-1"
                    >
                      <span className="text-slate-500">#</span>
                      <span className="truncate max-w-[140px]">{ch.name}</span>
                      <span className="text-[9px] bg-slate-950 px-1 py-0.2 text-emerald-400 font-mono ml-0.5">
                        {ch.count}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Frequent Co-Actors / Partenaires */}
            {stats.coActors.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                  <Users className="w-3 h-3 text-amber-400 shrink-0" />
                  Partenaires de scènes :
                </span>
                <div className="flex flex-wrap gap-1">
                  {stats.coActors.map(co => (
                    <button
                      key={co.name}
                      onClick={() => onSelectActor(co.name)}
                      className="px-2 py-0.5 bg-[#08090d] hover:bg-purple-950/40 border border-slate-800 hover:border-purple-800 text-[11px] text-slate-300 hover:text-purple-200 transition-all flex items-center gap-1 group"
                    >
                      <span className="group-hover:text-purple-300 truncate max-w-[120px]">{co.name}</span>
                      <span className="text-[9px] bg-slate-900 text-amber-300 font-mono px-1">
                        {co.count}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* Lightbox Modal for Full Resolution Character Card */}
      {showLightbox && stats.cardImage && (
        <div 
          onClick={() => setShowLightbox(false)}
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 cursor-pointer animate-fadeIn"
        >
          <div className="relative max-w-2xl max-h-[90vh] flex flex-col items-center">
            <button
              onClick={() => setShowLightbox(false)}
              className="absolute -top-10 right-0 p-2 text-white/80 hover:text-white text-sm font-semibold flex items-center gap-1 bg-slate-900/80 px-3 py-1 border border-slate-700"
            >
              <X className="w-4 h-4" /> Fermer
            </button>
            <img 
              src={stats.cardImage} 
              alt={stats.name} 
              className="max-w-full max-h-[85vh] object-contain border-2 shadow-2xl"
              style={{ borderColor: stats.color }}
            />
            <div className="mt-3 text-center text-sm font-serif-gothic text-slate-200 bg-slate-950/80 px-4 py-1.5 border border-slate-800">
              {stats.name} — {stats.role}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
