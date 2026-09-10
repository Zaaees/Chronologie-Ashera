import React, { useMemo, useEffect, useRef } from 'react';
import { Search, X, MessageSquare, Hash } from 'lucide-react';
import { Scene, Message, CHARACTERS_DATA } from '../data';

// ─────────────────────────────────────────────
// 🔧 UTILITAIRES DE NORMALISATION & RECHERCHE
// ─────────────────────────────────────────────

/** Normalise un texte : retire les diacritiques, met en minuscules */
export function normalizeForSearch(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

/**
 * Vérifie si un texte contient tous les mots d'une requête (logique AND).
 * Insensible à la casse et aux accents.
 */
export function textMatchesQuery(text: string, normalizedWords: string[]): boolean {
  if (normalizedWords.length === 0) return false;
  const normalizedText = normalizeForSearch(text);
  return normalizedWords.every(word => normalizedText.includes(word));
}

/**
 * Vérifie si un message (content + embed) contient tous les mots de la requête.
 */
export function messageMatchesQuery(msg: Message, normalizedWords: string[]): boolean {
  if (normalizedWords.length === 0) return false;
  const fields = [
    msg.content ?? '',
    msg.embed_title ?? '',
    msg.embed_description ?? '',
  ].join(' ');
  return textMatchesQuery(fields, normalizedWords);
}

/**
 * Extrait un snippet contextuel autour de la première occurrence d'un mot dans un texte.
 * Retourne ±CONTEXT_CHARS caractères autour du mot.
 */
const CONTEXT_CHARS = 65;

export function extractSnippet(text: string, normalizedWord: string): string {
  if (!text || !normalizedWord) return text.slice(0, CONTEXT_CHARS * 2 + 20);

  const normalizedText = normalizeForSearch(text);
  const idx = normalizedText.indexOf(normalizedWord);

  if (idx === -1) return text.slice(0, CONTEXT_CHARS * 2 + 20);

  const start = Math.max(0, idx - CONTEXT_CHARS);
  const end = Math.min(text.length, idx + normalizedWord.length + CONTEXT_CHARS);

  let snippet = text.slice(start, end);
  if (start > 0) snippet = '…' + snippet;
  if (end < text.length) snippet = snippet + '…';

  return snippet;
}

// ─────────────────────────────────────────────
// 🔍 TYPES
// ─────────────────────────────────────────────

export interface SearchOccurrence {
  scene: Scene;
  messageIndex: number;
  field: 'content' | 'embed_title' | 'embed_description' | 'title' | 'preview';
  snippet: string;
  author: string;
  timestamp: string;
}

// ─────────────────────────────────────────────
// 🎨 SURLIGNAGE INLINE
// ─────────────────────────────────────────────

function HighlightedSnippet({
  text,
  normalizedWords,
}: {
  text: string;
  normalizedWords: string[];
}) {
  if (!text || normalizedWords.length === 0) {
    return <span className="text-slate-300">{text}</span>;
  }

  // On surligne chaque mot individuellement
  const escapedWords = normalizedWords.map(w =>
    w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  );
  // Regex case-insensitive avec diacritiques (on opère sur le texte original)
  // On construit un pattern qui matche les mots en ignorant les accents via normalize
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let keyIdx = 0;

  // Pour chaque morceau, chercher la prochaine occurrence de n'importe quel mot
  while (remaining.length > 0) {
    let earliestIdx = -1;
    let earliestWord = '';
    let earliestOriginalLen = 0;

    const normalizedRemaining = normalizeForSearch(remaining);

    for (const word of normalizedWords) {
      const idx = normalizedRemaining.indexOf(word);
      if (idx !== -1 && (earliestIdx === -1 || idx < earliestIdx)) {
        earliestIdx = idx;
        earliestWord = word;
        earliestOriginalLen = word.length; // longueur approximative
      }
    }

    if (earliestIdx === -1) {
      parts.push(<span key={keyIdx++} className="text-slate-300">{remaining}</span>);
      break;
    }

    // Texte avant l'occurrence
    if (earliestIdx > 0) {
      parts.push(<span key={keyIdx++} className="text-slate-300">{remaining.slice(0, earliestIdx)}</span>);
    }

    // Terme surligné (on prend la portion originale de même longueur)
    const matchedText = remaining.slice(earliestIdx, earliestIdx + earliestOriginalLen);
    parts.push(
      <mark
        key={keyIdx++}
        className="bg-amber-400/40 text-amber-100 font-bold px-0.5 rounded ring-1 ring-amber-400/60 not-italic"
      >
        {matchedText}
      </mark>
    );

    remaining = remaining.slice(earliestIdx + earliestOriginalLen);
  }

  return <>{parts}</>;
}

// ─────────────────────────────────────────────
// 🏷️ BADGE FACTION
// ─────────────────────────────────────────────

const FACTION_TEXT_COLORS: Record<string, string> = {
  'La Garde Pourpre': '#fca5a5',
  "Cercle d'Azur":   '#93c5fd',
  "Voile d'Ivoire":  '#fef08a',
  "L'œil":           '#d8b4fe',
  'JAVUS':           '#ffffff',
  'Sans guilde':     '#fde047',
  'PNJ':             '#d8b4fe',
  'Narrateurs':      '#cbd5e1',
  'Indéfini':        '#94a3b8',
};

function getAuthorColor(authorName: string): string {
  const info = CHARACTERS_DATA[authorName];
  if (!info?.role) return '#cbd5e1';
  return FACTION_TEXT_COLORS[info.role] ?? '#cbd5e1';
}

// ─────────────────────────────────────────────
// 📅 FORMATAGE
// ─────────────────────────────────────────────

function formatShortDate(isoString: string): string {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '';
    const dateStr = d.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
    const timeStr = d.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
    });
    return `${dateStr} à ${timeStr}`;
  } catch {
    return '';
  }
}

// ─────────────────────────────────────────────
// 📦 COMPOSANT PRINCIPAL
// ─────────────────────────────────────────────

interface SearchResultsPanelProps {
  query: string;             // debouncedQuery (déjà normalisé à l'extérieur)
  scenes: Scene[];           // filteredScenes
  onSelectOccurrence: (scene: Scene, msgIndex: number) => void;
  onClose: () => void;
}

export function SearchResultsPanel({
  query,
  scenes,
  onSelectOccurrence,
  onClose,
}: SearchResultsPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Fermeture au clic extérieur
  useEffect(() => {
    const handleMouseDown = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [onClose]);

  // Fermeture à Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // Mots normalisés de la requête
  const normalizedWords = useMemo(() => {
    return query
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map(normalizeForSearch);
  }, [query]);

  // ─── Calcul de toutes les occurrences (sans limite) ───
  const occurrences = useMemo((): SearchOccurrence[] => {
    if (normalizedWords.length === 0) return [];

    const results: SearchOccurrence[] = [];

    for (const scene of scenes) {
      // Occurrences dans les messages
      for (let i = 0; i < scene.messages.length; i++) {
        const msg = scene.messages[i];

        // On teste chaque champ séparément pour trouver le meilleur snippet
        const fieldsToCheck: Array<{
          field: SearchOccurrence['field'];
          text: string;
        }> = [
          { field: 'content', text: msg.content ?? '' },
          { field: 'embed_title', text: msg.embed_title ?? '' },
          { field: 'embed_description', text: msg.embed_description ?? '' },
        ];

        for (const { field, text } of fieldsToCheck) {
          if (!text) continue;
          if (textMatchesQuery(text, normalizedWords)) {
            // Snippet basé sur le premier mot de la requête
            const snippet = extractSnippet(text, normalizedWords[0]);
            results.push({
              scene,
              messageIndex: i,
              field,
              snippet,
              author: msg.author,
              timestamp: msg.timestamp,
            });
            // Un seul résultat par message (le premier champ qui matche)
            break;
          }
        }
      }

      // Occurrences dans le titre ou le preview de la scène (sans message associé)
      const sceneFields: Array<{ field: SearchOccurrence['field']; text: string }> = [
        { field: 'title', text: scene.title ?? '' },
        { field: 'preview', text: scene.preview ?? '' },
      ];

      for (const { field, text } of sceneFields) {
        if (!text) continue;
        if (textMatchesQuery(text, normalizedWords)) {
          const snippet = extractSnippet(text, normalizedWords[0]);
          results.push({
            scene,
            messageIndex: -1, // pas de message ciblé
            field,
            snippet,
            author: '',
            timestamp: scene.start_time,
          });
          break; // un seul résultat par scène pour titre/preview
        }
      }
    }

    // Tri du plus récent au plus ancien (ordre chronologique décroissant)
    return results.sort((a, b) => {
      const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return timeB - timeA;
    });
  }, [scenes, normalizedWords]);

  // Comptages
  const totalOccurrences = occurrences.length;
  const uniqueSceneIds = new Set(occurrences.map(o => o.scene.id));
  const totalScenes = uniqueSceneIds.size;

  if (totalOccurrences === 0) {
    return (
      <div
        ref={panelRef}
        className="absolute top-full left-0 right-0 mt-1.5 z-50 bg-[#08090d] border border-slate-700 shadow-2xl rounded overflow-hidden"
      >
        <div className="px-4 py-5 text-center">
          <Search className="w-5 h-5 text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-400 font-medium">
            Aucune occurrence trouvée pour{' '}
            <span className="text-amber-300 font-bold">«&nbsp;{query}&nbsp;»</span>
          </p>
          <p className="text-[11px] text-slate-600 mt-1">
            Vérifiez l'orthographe ou essayez un autre terme.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={panelRef}
      className="absolute top-full left-0 right-0 mt-1.5 z-50 bg-[#08090d] border border-slate-700 shadow-2xl rounded overflow-hidden flex flex-col"
      style={{ maxHeight: 'min(520px, 60vh)' }}
    >
      {/* En-tête du panneau */}
      <div className="px-4 py-2.5 bg-[#0c0e15] border-b border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          <Search className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span className="text-xs text-slate-200 font-medium">
            <span className="text-amber-300 font-bold">{totalOccurrences}</span>
            {' '}occurrence{totalOccurrences > 1 ? 's' : ''} dans{' '}
            <span className="text-amber-300 font-bold">{totalScenes}</span>
            {' '}scène{totalScenes > 1 ? 's' : ''}
          </span>
          <span className="text-[10px] font-mono text-amber-300/80 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-500/30">
            Du plus récent au plus ancien ▾
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-slate-300 p-1 rounded hover:bg-slate-800/60 transition-colors"
          title="Fermer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Liste des résultats */}
      <div className="overflow-y-auto custom-scrollbar divide-y divide-slate-800/60">
        {occurrences.map((occ, idx) => {
          const isMessageOcc = occ.messageIndex >= 0;
          const authorColor = occ.author ? getAuthorColor(occ.author) : '#94a3b8';

          return (
            <button
              key={`${occ.scene.id}-${occ.messageIndex}-${occ.field}-${idx}`}
              onClick={() => {
                onSelectOccurrence(occ.scene, occ.messageIndex);
                onClose();
              }}
              className="w-full text-left px-4 py-3 hover:bg-slate-800/50 transition-colors group/result flex flex-col gap-1.5"
            >
              {/* Ligne de métadonnées */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Badge salon */}
                <span className="flex items-center gap-0.5 text-[10px] font-mono text-purple-300 bg-purple-950/60 border border-purple-500/30 px-1.5 py-0.5 rounded shrink-0">
                  <Hash className="w-2.5 h-2.5" />
                  <span className="truncate max-w-[120px]">{occ.scene.channel}</span>
                </span>

                {/* Titre de scène */}
                <span className="text-[11px] text-slate-400 font-medium truncate flex-1 min-w-0">
                  {occ.scene.title}
                </span>

                {/* Date */}
                <span className="text-[10px] font-mono text-slate-600 shrink-0">
                  {formatShortDate(occ.timestamp)}
                </span>
              </div>

              {/* Auteur (si message) */}
              {isMessageOcc && occ.author && (
                <div className="flex items-center gap-1.5">
                  <MessageSquare className="w-3 h-3 text-slate-600 shrink-0" />
                  <span
                    className="text-[11px] font-semibold"
                    style={{ color: authorColor }}
                  >
                    {occ.author}
                  </span>
                  <span className="text-[10px] text-slate-600 font-mono">
                    {occ.field === 'embed_title' ? '(embed titre)' : occ.field === 'embed_description' ? '(embed)' : ''}
                  </span>
                </div>
              )}
              {!isMessageOcc && (
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-slate-500 font-mono italic">
                    {occ.field === 'title' ? '✦ Titre de scène' : '✦ Aperçu de scène'}
                  </span>
                </div>
              )}

              {/* Snippet avec surlignage */}
              <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-3 italic">
                <HighlightedSnippet text={occ.snippet} normalizedWords={normalizedWords} />
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
