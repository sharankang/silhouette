import { Mic, Image as ImageIcon, Sparkles } from 'lucide-react'
import { StarRating } from '../UI'
import clsx from 'clsx'

function resolveImageUrl(url) {
  if (!url) return null
  return url.startsWith('/wardrobe') ? `/api${url}` : url
}

export default function ChatMessage({ message, onRateOutfit }) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex gap-3 animate-fade-up', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div className={clsx(
        'w-7 h-7 shrink-0 rounded-full flex items-center justify-center mt-1',
        isUser ? 'bg-ink-700 text-dust' : 'bg-terracotta-600/30 text-terracotta-400 border border-terracotta-500/30'
      )}>
        {isUser ? <span className="text-xs font-mono">U</span> : <Sparkles size={13} />}
      </div>

      <div className={clsx('flex flex-col gap-2 max-w-[80%]', isUser ? 'items-end' : 'items-start')}>
        {/* Input indicators (user side) */}
        {isUser && message.hasAudio && (
          <div className="flex items-center gap-1.5 text-[11px] text-ink-400 font-mono">
            <Mic size={11} className="text-terracotta-400" />
            Voice message
          </div>
        )}

        {/* Inspo image (user side) */}
        {isUser && message.imagePreview && (
          <div className="rounded-xl overflow-hidden border border-ink-700/50 w-32">
            <img src={message.imagePreview} alt="inspo" className="w-full object-cover" />
            <div className="px-2 py-1 bg-ink-900/80 flex items-center gap-1">
              <ImageIcon size={10} className="text-ink-400" />
              <span className="text-[10px] text-ink-400 font-mono">inspo</span>
            </div>
          </div>
        )}

        {/* Text bubble */}
        {message.text && (
          <div className={clsx(
            'rounded-2xl px-4 py-3 text-sm font-body leading-relaxed',
            isUser
              ? 'bg-ink-800 text-cream rounded-tr-sm'
              : 'glass text-cream rounded-tl-sm'
          )}>
            {message.text}
          </div>
        )}

        {/* Outfit result */}
        {!isUser && message.outfit && (
          <OutfitCard outfit={message.outfit} onRate={onRateOutfit} />
        )}

        {/* Thinking / loading */}
        {!isUser && message.loading && (
          <div className="glass rounded-2xl rounded-tl-sm px-4 py-3">
            <div className="flex gap-1.5 items-center">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-ink-500 animate-pulse-soft"
                  style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
              <span className="text-ink-400 text-xs font-mono ml-1">Styling...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* Outfit Result Card */
function OutfitCard({ outfit, onRate }) {
  return (
    <div className="glass rounded-2xl rounded-tl-sm overflow-hidden w-full max-w-sm">
      {/* Items grid */}
      <div className="grid grid-cols-3 gap-px bg-ink-800">
        {outfit.items?.slice(0, 6).map((item, i) => (
          <div key={i} className="aspect-square bg-ink-900 overflow-hidden">
            {item.image_url
              ? <img src={resolveImageUrl(item.image_url)} alt={item.name} className="w-full h-full object-cover" />
              : <div className="w-full h-full flex items-center justify-center text-xl">👗</div>
            }
          </div>
        ))}
      </div>

      {/* Explanation */}
      <div className="p-4">
        <p className="text-sm text-cream leading-relaxed">{outfit.explanation}</p>

        {/* Item names */}
        <div className="flex flex-wrap gap-1 mt-3">
          {outfit.items?.map((item, i) => (
            <span key={i} className="tag text-[10px]">{item.name || item.category}</span>
          ))}
        </div>

        {/* Rating */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink-700/50">
          <span className="text-xs font-mono text-ink-400">Rate this look</span>
          <StarRating value={outfit.rating || 0} onChange={rating => onRate?.(outfit.id, rating)} />
        </div>
      </div>
    </div>
  )
}