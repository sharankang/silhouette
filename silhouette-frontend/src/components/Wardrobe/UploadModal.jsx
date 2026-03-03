import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, Loader2, Check, ChevronLeft, ChevronRight, Image } from 'lucide-react'
import { Modal } from '../UI'
import clsx from 'clsx'
import api from '../../services/api'

const CATEGORIES = ['tops', 'bottoms', 'dresses', 'outerwear', 'shoes', 'accessories', 'jewellery']
const SEASONS    = ['spring', 'summer', 'autumn', 'winter', 'all-season']
const OCCASIONS  = ['casual', 'formal', 'work', 'party', 'sport', 'loungewear']
const STYLE_TAGS = ['minimalist', 'streetwear', 'bohemian', 'preppy', 'edgy', 'romantic', 'classic', 'sporty']

const emptyTags = () => ({
  name: '', category: '', season: 'all-season',
  occasions: [], styles: [], colors: [],
})

// Auto-tag a single file via the backend /wardrobe/auto-tag endpoint
async function fetchAutoTags(file) {
  try {
    const formData = new FormData()
    formData.append('image', file)
    const result = await api.autoTag(formData)
    return {
      name:      '',
      category:  result.category  || '',
      season:    result.season     || 'all-season',
      styles:    result.styles     || [],
      colors:    result.colors     || [],
      occasions: [],
    }
  } catch {
    return emptyTags()
  }
}

export default function UploadModal({ open, onClose, onSuccess }) {
  const [items,      setItems]      = useState([])   // { file, preview, tags, autoTagging }
  const [activeIdx,  setActiveIdx]  = useState(0)
  const [saving,     setSaving]     = useState(false)
  const [saved,      setSaved]      = useState(false)
  const [colorInput, setColorInput] = useState('')
  const [saveError,  setSaveError]  = useState(null)

  // Drop handler: immediately show previews, then auto-tag each in parallel
  const onDrop = useCallback(async (accepted) => {
    if (!accepted.length) return

    const newItems = accepted.map(file => ({
      file,
      preview:     URL.createObjectURL(file),
      tags:        emptyTags(),
      autoTagging: true,
    }))

    setItems(prev => {
      const startIdx = prev.length
      // Jump to first newly added item
      setTimeout(() => setActiveIdx(startIdx), 0)
      return [...prev, ...newItems]
    })

    // Auto-tag all new items in parallel
    const tagResults = await Promise.all(newItems.map(item => fetchAutoTags(item.file)))

    setItems(prev => {
      const updated = [...prev]
      const startIdx = updated.length - newItems.length
      tagResults.forEach((tags, i) => {
        const idx = startIdx + i
        if (updated[idx]) {
          updated[idx] = { ...updated[idx], tags, autoTagging: false }
        }
      })
      return updated
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': [] }, maxFiles: 20,
  })

  // Helpers to update the active item's tags
  const updateTag = (field, value) => {
    setItems(prev => prev.map((item, i) =>
      i === activeIdx ? { ...item, tags: { ...item.tags, [field]: value } } : item
    ))
  }

  const toggleMulti = (field, value) => {
    setItems(prev => prev.map((item, i) => {
      if (i !== activeIdx) return item
      const current = item.tags[field] || []
      return {
        ...item,
        tags: {
          ...item.tags,
          [field]: current.includes(value)
            ? current.filter(v => v !== value)
            : [...current, value],
        },
      }
    }))
  }

  const addColor = (e) => {
    if (e.key === 'Enter' && colorInput.trim()) {
      toggleMulti('colors', colorInput.trim())
      setColorInput('')
    }
  }

  const removeItem = (idx) => {
    setItems(prev => {
      const updated = prev.filter((_, i) => i !== idx)
      setActiveIdx(i => Math.min(i, Math.max(0, updated.length - 1)))
      return updated
    })
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveError(null)
    let successCount = 0

    for (const item of items) {
      try {
        const formData = new FormData()
        formData.append('image', item.file)
        formData.append('tags', JSON.stringify(item.tags))
        await api.addClothingItem(formData)
        successCount++
      } catch (err) {
        console.error('Failed to save item:', err)
      }
    }

    setSaving(false)
    if (successCount > 0) {
      setSaved(true)
      onSuccess?.()
      setTimeout(() => handleClose(), 1400)
    } else {
      setSaveError('All items failed to save. Make sure the backend is running.')
    }
  }

  const handleClose = () => {
    setItems([])
    setActiveIdx(0)
    setSaving(false)
    setSaved(false)
    setSaveError(null)
    setColorInput('')
    onClose()
  }

  const active          = items[activeIdx]
  const taggedCount     = items.filter(i => i.tags.category).length
  const anyAutoTagging  = items.some(i => i.autoTagging)

  return (
    <Modal open={open} onClose={handleClose} title="Add to Closet" wide>

      {/* Success state */}
      {saved && (
        <div className="flex flex-col items-center justify-center py-10 gap-3 animate-fade-up">
          <div className="w-14 h-14 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center">
            <Check size={24} className="text-sage-400" />
          </div>
          <p className="font-display text-lg text-cream">
            {items.length} {items.length === 1 ? 'item' : 'items'} added to your closet
          </p>
        </div>
      )}

      {/* Empty: drop zone */}
      {!saved && items.length === 0 && (
        <div
          {...getRootProps()}
          className={clsx(
            'border-2 border-dashed rounded-xl p-14 text-center cursor-pointer transition-all duration-200',
            isDragActive
              ? 'border-terracotta-400/60 bg-terracotta-600/5'
              : 'border-ink-700 hover:border-ink-500 hover:bg-ink-800/30'
          )}
        >
          <input {...getInputProps()} />
          <Upload size={32} className="mx-auto mb-4 text-ink-500" />
          <p className="text-cream font-display text-lg">Drop your photos here</p>
          <p className="text-dust text-sm mt-2">Up to 20 items — each gets auto-tagged instantly</p>
        </div>
      )}

      {/* Per-item editor */}
      {!saved && items.length > 0 && (
        <>
          <div className="flex gap-5">
            {/* Thumbnail strip */}
            <div className="flex flex-col gap-2 w-[72px] shrink-0">
              {/* Add more button */}
              <div
                {...getRootProps()}
                className="w-full aspect-square rounded-lg border-2 border-dashed border-ink-700 hover:border-ink-500 flex items-center justify-center cursor-pointer transition-colors"
                title="Add more photos"
              >
                <input {...getInputProps()} />
                <Image size={15} className="text-ink-500" />
              </div>

              {/* Thumbnails */}
              <div className="flex flex-col gap-1.5 overflow-y-auto max-h-72">
                {items.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => { setActiveIdx(idx); setColorInput('') }}
                    className={clsx(
                      'relative w-full aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition-all shrink-0 group',
                      activeIdx === idx
                        ? 'border-terracotta-400/80'
                        : 'border-transparent hover:border-ink-600'
                    )}
                  >
                    <img src={item.preview} alt="" className="w-full h-full object-cover" />

                    {/* Tagging spinner */}
                    {item.autoTagging && (
                      <div className="absolute inset-0 bg-ink-950/65 flex items-center justify-center">
                        <Loader2 size={13} className="animate-spin text-terracotta-400" />
                      </div>
                    )}
                    {/* Tagged tick */}
                    {!item.autoTagging && item.tags.category && (
                      <div className="absolute bottom-0.5 right-0.5 w-4 h-4 bg-sage-500 rounded-full flex items-center justify-center">
                        <Check size={9} className="text-white" />
                      </div>
                    )}
                    {/* Remove */}
                    <button
                      onClick={e => { e.stopPropagation(); removeItem(idx) }}
                      className="absolute top-0.5 left-0.5 w-4 h-4 bg-ink-900/80 rounded-full items-center justify-center hidden group-hover:flex"
                    >
                      <X size={9} className="text-dust" />
                    </button>
                  </div>
                ))}
              </div>

              <p className="text-center text-ink-500 text-[10px] font-mono">
                {taggedCount}/{items.length}
              </p>
            </div>

            {/* Tag editor */}
            {active && (
              <div className="flex-1 min-w-0 space-y-3 overflow-y-auto max-h-[420px] pr-1">
                {/* Preview + name row */}
                <div className="flex gap-3 items-start">
                  <div className="relative w-16 h-20 shrink-0 rounded-lg overflow-hidden border border-ink-700">
                    <img src={active.preview} alt="" className="w-full h-full object-cover" />
                    {active.autoTagging && (
                      <div className="absolute inset-0 bg-ink-950/70 flex flex-col items-center justify-center gap-1">
                        <Loader2 size={14} className="animate-spin text-terracotta-400" />
                        <p className="text-[8px] text-terracotta-400 font-mono">tagging</p>
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-mono text-ink-400 uppercase tracking-wider mb-1.5">
                      Name <span className="normal-case text-ink-600">(optional)</span>
                    </p>
                    <input
                      value={active.tags.name}
                      onChange={e => updateTag('name', e.target.value)}
                      placeholder="e.g. Oversized white shirt"
                      className="input-base w-full text-sm"
                    />
                    {active.autoTagging && (
                      <p className="text-[11px] text-terracotta-400/60 font-mono mt-1 flex items-center gap-1">
                        <Loader2 size={9} className="animate-spin" /> Auto-tagging...
                      </p>
                    )}
                  </div>
                </div>

                {/* Category */}
                <Section label="Category *">
                  <Chips options={CATEGORIES} value={active.tags.category}
                    onSelect={v => updateTag('category', v)} single />
                </Section>

                {/* Season */}
                <Section label="Season">
                  <Chips options={SEASONS} value={active.tags.season}
                    onSelect={v => updateTag('season', v)} single />
                </Section>

                {/* Occasion */}
                <Section label="Occasion">
                  <Chips options={OCCASIONS} value={active.tags.occasions || []}
                    onSelect={v => toggleMulti('occasions', v)} />
                </Section>

                {/* Style */}
                <Section label="Style">
                  <Chips options={STYLE_TAGS} value={active.tags.styles || []}
                    onSelect={v => toggleMulti('styles', v)} />
                </Section>

                {/* Colors */}
                <Section label="Colors">
                  <div className="flex flex-wrap gap-1.5 mb-1.5">
                    {(active.tags.colors || []).map(c => (
                      <span key={c} className="tag flex items-center gap-1 text-[11px]">
                        {c}
                        <button onClick={() => toggleMulti('colors', c)}>
                          <X size={9} />
                        </button>
                      </span>
                    ))}
                  </div>
                  <input
                    value={colorInput}
                    onChange={e => setColorInput(e.target.value)}
                    onKeyDown={addColor}
                    placeholder="Type a color, press Enter"
                    className="input-base text-sm w-full"
                  />
                </Section>

                {/* Prev / Next nav */}
                {items.length > 1 && (
                  <div className="flex items-center justify-between pt-1">
                    <button onClick={() => { setActiveIdx(i => Math.max(0, i - 1)); setColorInput('') }}
                      disabled={activeIdx === 0}
                      className="btn-ghost flex items-center gap-1 text-sm disabled:opacity-30">
                      <ChevronLeft size={14} /> Prev
                    </button>
                    <button onClick={() => { setActiveIdx(i => Math.min(items.length - 1, i + 1)); setColorInput('') }}
                      disabled={activeIdx === items.length - 1}
                      className="btn-ghost flex items-center gap-1 text-sm disabled:opacity-30">
                      Next <ChevronRight size={14} />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          {saveError && (
            <p className="text-terracotta-400 text-xs font-mono mt-3 px-1">{saveError}</p>
          )}
          <div className="flex gap-3 mt-3 pt-4 border-t border-ink-800/50">
            <button onClick={handleClose} className="btn-outline flex-1">Cancel</button>
            <button
              onClick={handleSave}
              disabled={saving || items.length === 0}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {saving
                ? <><Loader2 size={14} className="animate-spin" /> Saving...</>
                : `Save ${items.length} ${items.length === 1 ? 'item' : 'items'}`
              }
            </button>
          </div>
        </>
      )}
    </Modal>
  )
}

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs font-mono text-ink-400 uppercase tracking-wider mb-1.5">{label}</p>
      {children}
    </div>
  )
}

function Chips({ options, value, onSelect, single = false }) {
  const isActive = v => single ? value === v : (value || []).includes(v)
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map(o => (
        <button key={o} onClick={() => onSelect(o)}
          className={clsx(
            'px-3 py-1 rounded-full text-xs capitalize transition-all border font-body',
            isActive(o)
              ? 'bg-terracotta-600/30 text-terracotta-300 border-terracotta-500/40'
              : 'bg-ink-800 text-dust border-ink-700/50 hover:border-ink-500 hover:text-cream'
          )}>
          {o}
        </button>
      ))}
    </div>
  )
}