import { Star, RefreshCw, Trash2 } from 'lucide-react'
import { StarRating } from '../UI'
import clsx from 'clsx'

function resolveImageUrl(url) {
  if (!url) return null
  return url.startsWith('/wardrobe') ? `/api${url}` : url
}

export default function OutfitHistoryCard({ outfit, onRegenerate, onDelete, onRate }) {
  return (
    <div className="glass rounded-2xl overflow-hidden border border-ink-800/60 hover:border-ink-600/60 transition-all duration-200 group animate-fade-up">
      {/* Items strip */}
      <div className="flex h-28 bg-ink-900">
        {outfit.items?.slice(0, 4).map((item, i) => (
          <div key={i} className="flex-1 overflow-hidden relative">
            {item.image_url
              ? <img src={resolveImageUrl(item.image_url)} alt={item.name} className="w-full h-full object-cover" />
              : <div className="w-full h-full flex items-center justify-center bg-ink-800 text-2xl">👗</div>
            }
            {i < (outfit.items.length - 1) && (
              <div className="absolute right-0 top-0 bottom-0 w-px bg-ink-700/50" />
            )}
          </div>
        ))}
        {outfit.items?.length > 4 && (
          <div className="flex-1 bg-ink-800 flex items-center justify-center">
            <span className="text-ink-400 text-sm font-mono">+{outfit.items.length - 4}</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm text-cream font-body line-clamp-2 leading-relaxed">
              {outfit.explanation}
            </p>
            <p className="text-xs text-ink-500 font-mono mt-1">
              {new Date(outfit.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </p>
          </div>
        </div>

        {/* Tags */}
        {outfit.query_text && (
          <div className="mt-2">
            <span className="tag text-[10px] italic text-ink-400">"{outfit.query_text}"</span>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink-800/60">
          <StarRating value={outfit.rating || 0} onChange={r => onRate?.(outfit.id, r)} />
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => onRegenerate?.(outfit)}
              className="w-7 h-7 rounded-lg hover:bg-ink-700 flex items-center justify-center text-ink-500 hover:text-dust transition-colors"
              title="Regenerate similar outfit"
            >
              <RefreshCw size={13} />
            </button>
            <button
              onClick={() => onDelete?.(outfit.id)}
              className="w-7 h-7 rounded-lg hover:bg-ink-700 flex items-center justify-center text-ink-500 hover:text-terracotta-400 transition-colors"
              title="Delete"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}