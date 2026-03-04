import { useState, useEffect, useRef } from 'react'
import { ChevronLeft, ChevronRight, Shuffle, Save, X, Sparkles } from 'lucide-react'
import clsx from 'clsx'
import api from '../services/api'

const CATEGORY_LABELS = {
  tops: 'Tops', bottoms: 'Bottoms', dresses: 'Dresses',
  outerwear: 'Outerwear', shoes: 'Shoes', accessories: 'Accessories', jewellery: 'Jewellery',
}

const TEMPLATES = [
  {
    id: 'two',
    label: '2 pieces',
    description: 'Dress + Shoes',
    emoji: '👗',
    slots: ['dresses', 'shoes'],
  },
  {
    id: 'three',
    label: '3 pieces',
    description: 'Top + Bottoms + Shoes',
    emoji: '👚',
    slots: ['tops', 'bottoms', 'shoes'],
  },
  {
    id: 'four',
    label: '4 pieces',
    description: 'Top + Jacket + Bottoms + Shoes',
    emoji: '🧥',
    slots: ['tops', 'outerwear', 'bottoms', 'shoes'],
  },
]

function resolveImageUrl(url) {
  if (!url) return null
  if (url.startsWith('/wardrobe')) return `/api${url}`
  return url
}

function CarouselRow({ category, items, selected, onToggle }) {
  const scrollRef = useRef(null)

  const scroll = (dir) => {
    scrollRef.current?.scrollBy({ left: dir * 220, behavior: 'smooth' })
  }

  if (!items.length) return (
    <div className="mb-8">
      <h3 className="text-sm font-mono uppercase tracking-widest text-ink-400 mb-3 px-1">
        {CATEGORY_LABELS[category]}
      </h3>
      <div className="h-24 rounded-xl border border-dashed border-ink-800 flex items-center justify-center text-ink-600 text-sm">
        No {CATEGORY_LABELS[category].toLowerCase()} in your closet yet
      </div>
    </div>
  )

  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1.5 px-1">
        <h3 className="text-xs font-mono uppercase tracking-widest text-ink-400">
          {CATEGORY_LABELS[category]}
          <span className="ml-1.5 text-ink-600">({items.length})</span>
        </h3>
        <div className="flex gap-1">
          <button onClick={() => scroll(-1)} className="w-6 h-6 rounded-md border border-ink-700 flex items-center justify-center text-ink-400 hover:text-cream hover:border-ink-500 transition-all">
            <ChevronLeft size={12} />
          </button>
          <button onClick={() => scroll(1)} className="w-6 h-6 rounded-md border border-ink-700 flex items-center justify-center text-ink-400 hover:text-cream hover:border-ink-500 transition-all">
            <ChevronRight size={12} />
          </button>
        </div>
      </div>

      <div ref={scrollRef} className="flex gap-2 overflow-x-auto pb-1" style={{ scrollSnapType: 'x mandatory', scrollbarWidth: 'none' }}>
        {items.map(item => {
          const isSelected = selected?.id === item.id
          const imageUrl = resolveImageUrl(item.image_url)
          return (
            <button
              key={item.id}
              onClick={() => onToggle(category, item)}
              style={{ scrollSnapAlign: 'start', minWidth: '100px', maxWidth: '100px' }}
              className={clsx(
                'relative rounded-lg overflow-hidden border transition-all duration-200 shrink-0 group text-left',
                isSelected
                  ? 'border-terracotta-400/80 shadow-lg shadow-terracotta-600/20 scale-[1.03]'
                  : 'border-ink-800/60 hover:border-ink-600 hover:scale-[1.01]'
              )}
            >
              <div className="aspect-square bg-ink-800 overflow-hidden">
                {imageUrl
                  ? <img src={imageUrl} alt={item.name || category} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                  : <div className="w-full h-full flex items-center justify-center text-2xl">👗</div>
                }
              </div>

              {isSelected && (
                <div className="absolute inset-0 bg-terracotta-500/10 flex items-start justify-end p-2">
                  <div className="w-5 h-5 rounded-full bg-terracotta-500 flex items-center justify-center">
                    <span className="text-white text-[10px] font-bold">✓</span>
                  </div>
                </div>
              )}

              <div className="p-1.5 bg-ink-900/80">
                <p className="text-[10px] text-cream truncate">{item.name || 'Untitled'}</p>
                {item.colors?.[0] && <p className="text-[9px] text-ink-400">{item.colors[0]}</p>}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function MixPage() {
  const [wardrobe, setWardrobe]     = useState({})
  const [template, setTemplate]     = useState(null)
  const [selected, setSelected]     = useState({})
  const [saving, setSaving]         = useState(false)
  const [saved, setSaved]           = useState(false)
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    api.getWardrobe().then(res => {
      const grouped = {}
      for (const item of res.items || []) {
        grouped[item.category] = grouped[item.category] || []
        grouped[item.category].push(item)
      }
      setWardrobe(grouped)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const handleSelectTemplate = (t) => {
    setTemplate(t)
    setSelected({})
    setSaved(false)
  }

  const handleToggle = (category, item) => {
    setSelected(prev => ({
      ...prev,
      [category]: prev[category]?.id === item.id ? null : item,
    }))
    setSaved(false)
  }

  const handleRemove = (category) => {
    setSelected(prev => ({ ...prev, [category]: null }))
    setSaved(false)
  }

  const handleShuffle = () => {
    if (!template) return
    const next = {}
    for (const cat of template.slots) {
      const items = wardrobe[cat] || []
      if (items.length) next[cat] = items[Math.floor(Math.random() * items.length)]
    }
    setSelected(next)
    setSaved(false)
  }

  const handleClear = () => {
    setSelected({})
    setSaved(false)
  }

  const handleSave = async () => {
    const items = Object.values(selected).filter(Boolean)
    if (items.length < 2) return
    setSaving(true)
    try {
      await api.saveManualOutfit(items)
      setSaved(true)
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  const selectedItems = template
    ? template.slots.map(cat => selected[cat]).filter(Boolean)
    : []

  const slots = template?.slots || []
  const filledCount = slots.filter(cat => selected[cat]).length

  // Template picker screen
  if (!template) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-8 px-8">
        <div className="text-center">
          <h2 className="font-display text-3xl text-cream mb-2">Mix & Match</h2>
          <p className="text-ink-400 text-sm">How many pieces are you working with today?</p>
        </div>

        <div className="flex gap-4 flex-wrap justify-center max-w-2xl">
          {TEMPLATES.map(t => (
            <button
              key={t.id}
              onClick={() => handleSelectTemplate(t)}
              className="group flex flex-col items-center gap-3 p-6 rounded-2xl border border-ink-700/60 bg-ink-900/40 hover:border-terracotta-500/50 hover:bg-ink-800/60 transition-all duration-200 w-52"
            >
              <span className="text-4xl">{t.emoji}</span>
              <div className="text-center">
                <p className="text-cream font-medium text-base">{t.label}</p>
                <p className="text-ink-400 text-xs mt-1 leading-relaxed">{t.description}</p>
              </div>
              <div className="flex gap-1 mt-1">
                {t.slots.map(s => (
                  <span key={s} className="text-[10px] px-2 py-0.5 rounded-full border border-ink-700 text-ink-400">
                    {CATEGORY_LABELS[s]}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Main mix & match view 
  return (
    <div className="flex h-screen overflow-hidden">

      {/* carousels */}
      <div className="flex-1 overflow-y-auto px-6 pt-5 pb-6">
        <div className="flex items-center gap-3 mb-5">
          <button
            onClick={() => setTemplate(null)}
            className="w-8 h-8 rounded-lg border border-ink-700 flex items-center justify-center text-ink-400 hover:text-cream hover:border-ink-500 transition-all"
          >
            <ChevronLeft size={14} />
          </button>
          <div>
            <h2 className="font-display text-2xl text-cream">{template.label}</h2>
            <p className="text-ink-400 text-xs">{template.description} — pick one from each row</p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64 text-ink-500 text-sm">Loading your closet...</div>
        ) : (
          slots.map(cat => (
            <CarouselRow
              key={cat}
              category={cat}
              items={wardrobe[cat] || []}
              selected={selected[cat]}
              onToggle={handleToggle}
            />
          ))
        )}
      </div>

      {/* outfit panel */}
      <div className="w-72 shrink-0 border-l border-ink-800/60 flex flex-col h-screen">
        <div className="px-5 pt-6 pb-4 border-b border-ink-800/60">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={14} className="text-terracotta-400" />
            <h3 className="text-sm font-mono uppercase tracking-widest text-cream">Your Look</h3>
          </div>
          <p className="text-ink-500 text-xs">
            {filledCount === 0 ? 'Nothing selected yet' : `${filledCount} of ${slots.length} pieces`}
          </p>

          {/* slot progress indicators */}
          <div className="flex gap-1.5 mt-3">
            {slots.map(cat => (
              <div
                key={cat}
                className={clsx(
                  'h-1 flex-1 rounded-full transition-all duration-300',
                  selected[cat] ? 'bg-terracotta-500' : 'bg-ink-700'
                )}
              />
            ))}
          </div>
        </div>

        {/* selected items list */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {slots.map(cat => {
            const item = selected[cat]
            const imageUrl = item ? resolveImageUrl(item.image_url) : null
            return (
              <div key={cat} className={clsx('flex items-center gap-3 group rounded-xl p-2 transition-all', item ? 'bg-ink-900/40' : 'opacity-40')}>
                <div className="w-12 h-12 rounded-lg overflow-hidden border border-ink-700/60 shrink-0 bg-ink-800">
                  {imageUrl
                    ? <img src={imageUrl} alt={item.name} className="w-full h-full object-cover" />
                    : <div className="w-full h-full flex items-center justify-center text-ink-600 text-xs">{CATEGORY_LABELS[cat][0]}</div>
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-ink-400 font-mono uppercase tracking-wider">{CATEGORY_LABELS[cat]}</p>
                  <p className="text-sm text-cream truncate">{item?.name || '—'}</p>
                </div>
                {item && (
                  <button onClick={() => handleRemove(cat)} className="opacity-0 group-hover:opacity-100 text-ink-500 hover:text-terracotta-400 transition-all">
                    <X size={13} />
                  </button>
                )}
              </div>
            )
          })}
        </div>

        {/* actions */}
        <div className="px-5 pb-6 pt-4 border-t border-ink-800/60 space-y-2">
          <button
            onClick={handleShuffle}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-ink-700 text-sm text-dust hover:text-cream hover:border-ink-500 transition-all"
          >
            <Shuffle size={14} />
            Random outfit
          </button>

          {filledCount >= 2 && (
            <button
              onClick={handleSave}
              disabled={saving || saved}
              className={clsx(
                'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all',
                saved
                  ? 'bg-sage-600/30 border border-sage-600/40 text-sage-400 cursor-default'
                  : 'bg-terracotta-600/20 border border-terracotta-500/40 text-terracotta-400 hover:bg-terracotta-600/30'
              )}
            >
              <Save size={14} />
              {saving ? 'Saving...' : saved ? 'Saved to Outfits ✓' : 'Save this look'}
            </button>
          )}

          {filledCount > 0 && (
            <button onClick={handleClear} className="w-full text-xs text-ink-600 hover:text-ink-400 transition-colors py-1">
              Clear all
            </button>
          )}
        </div>
      </div>
    </div>
  )
}