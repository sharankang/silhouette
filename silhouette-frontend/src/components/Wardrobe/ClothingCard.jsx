import { useState } from 'react'
import { Pencil, Trash2, MoreVertical } from 'lucide-react'
import clsx from 'clsx'

const CATEGORY_COLORS = {
  tops:        'tag-accent',
  bottoms:     'tag-sage',
  shoes:       'tag',
  accessories: 'tag',
  outerwear:   'tag-sage',
  dresses:     'tag-accent',
  jewellery:   'tag',
}

function resolveImageUrl(url) {
  if (!url) return null
  if (url.startsWith('/wardrobe')) return `/api${url}`
  return url
}

export default function ClothingCard({ item, onEdit, onDelete, selectable, selected, onSelect }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const imageUrl = resolveImageUrl(item.image_url)

  const handleClick = () => {
    if (selectable) onSelect?.(item)
  }

  return (
    <div
      onClick={handleClick}
      className={clsx(
        'group relative rounded-xl overflow-hidden border transition-all duration-200',
        selectable && 'cursor-pointer',
        selected
          ? 'border-terracotta-400/70 shadow-lg shadow-terracotta-600/10 scale-[1.02]'
          : 'border-ink-800/60 hover:border-ink-600/60',
        'bg-ink-900/40 hover:bg-ink-900/70'
      )}
    >
      {/* Image */}
      <div className="aspect-[3/4] bg-ink-800 overflow-hidden relative">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={item.name}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-ink-600 text-4xl">👗</span>
          </div>
        )}

        {/* Selected indicator */}
        {selected && (
          <div className="absolute inset-0 bg-terracotta-500/10 flex items-center justify-center">
            <div className="w-7 h-7 rounded-full bg-terracotta-500 flex items-center justify-center">
              <span className="text-white text-xs">✓</span>
            </div>
          </div>
        )}

        {/* Action menu — only if not selectable mode */}
        {!selectable && (
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="relative">
              <button
                onClick={e => { e.stopPropagation(); setMenuOpen(v => !v) }}
                className="w-7 h-7 rounded-lg glass flex items-center justify-center text-dust hover:text-cream transition-colors"
              >
                <MoreVertical size={13} />
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-9 glass rounded-lg overflow-hidden shadow-xl z-10 min-w-[130px] animate-fade-in">
                  <button
                    onClick={e => { e.stopPropagation(); setMenuOpen(false); onEdit?.(item) }}
                    className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-dust hover:text-cream hover:bg-ink-700 transition-colors"
                  >
                    <Pencil size={13} /> Edit tags
                  </button>
                  <button
                    onClick={e => { e.stopPropagation(); setMenuOpen(false); onDelete?.(item) }}
                    className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-terracotta-400 hover:text-terracotta-300 hover:bg-ink-700 transition-colors"
                  >
                    <Trash2 size={13} /> Remove
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-sm text-cream font-body font-medium truncate">{item.name || 'Untitled'}</p>
        <div className="flex flex-wrap gap-1 mt-2">
          {item.category && (
            <span className={clsx('tag text-[10px] px-2 py-0.5', CATEGORY_COLORS[item.category] || 'tag')}>
              {item.category}
            </span>
          )}
          {item.season && (
            <span className="tag text-[10px] px-2 py-0.5">{item.season}</span>
          )}
          {item.colors?.[0] && (
            <span className="tag text-[10px] px-2 py-0.5">{item.colors[0]}</span>
          )}
        </div>
      </div>
    </div>
  )
}