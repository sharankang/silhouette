import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { Modal } from '../UI'
import clsx from 'clsx'
import api from '../../services/api'

const CATEGORIES = ['tops', 'bottoms', 'dresses', 'outerwear', 'shoes', 'accessories', 'jewellery']
const SEASONS    = ['spring', 'summer', 'autumn', 'winter', 'all-season']
const OCCASIONS  = ['casual', 'formal', 'work', 'party', 'ethnic', 'lounge', 'outdoor', 'date']
const STYLE_TAGS = ['minimalist', 'streetwear', 'bohemian', 'preppy', 'edgy', 'romantic', 'classic', 'sporty', 'ethnic', 'quiet-luxury', 'smart-casual', 'cottagecore']

export default function EditModal({ open, onClose, item, onSuccess }) {
  const [tags, setTags] = useState({ category: '', season: '', occasions: [], styles: [], colors: [], name: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (item) setTags({
      name:      item.name      || '',
      category:  item.category  || '',
      season:    item.season    || '',
      occasions: item.occasions || [],
      styles:    item.styles    || [],
      colors:    item.colors    || [],
    })
  }, [item])

  const toggleMulti = (field, value) => {
    setTags(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value]
    }))
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      await api.updateClothingItem(item.id, tags)
      onSuccess?.()
      onClose()
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Edit item" wide>
      <div className="space-y-5">
        {}
        <div className="flex gap-4 items-start">
          {item?.image_url && (
            <img src={item.image_url} alt="" className="w-20 h-24 object-cover rounded-lg border border-ink-700" />
          )}
          <div className="flex-1">
            <label className="text-xs font-mono text-ink-400 uppercase tracking-wider block mb-1.5">Name</label>
            <input
              value={tags.name}
              onChange={e => setTags(prev => ({ ...prev, name: e.target.value }))}
              className="input-base w-full text-sm"
              placeholder="e.g. White linen shirt"
            />
          </div>
        </div>

        {}
        <ChipGroup label="Category" options={CATEGORIES} value={tags.category}
          onChange={v => setTags(p => ({ ...p, category: v }))} single />

        {}
        <ChipGroup label="Season" options={SEASONS} value={tags.season}
          onChange={v => setTags(p => ({ ...p, season: v }))} single />

        {}
        <ChipGroup label="Occasion" options={OCCASIONS} value={tags.occasions}
          onChange={v => toggleMulti('occasions', v)} />

        {}
        <ChipGroup label="Style" options={STYLE_TAGS} value={tags.styles}
          onChange={v => toggleMulti('styles', v)} />

        <div className="flex gap-3 pt-2">
          <button onClick={onClose} className="btn-outline flex-1">Cancel</button>
          <button onClick={handleSave} disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
            {loading && <Loader2 size={14} className="animate-spin" />}
            Save changes
          </button>
        </div>
      </div>
    </Modal>
  )
}

function ChipGroup({ label, options, value, onChange, single = false }) {
  const isActive = v => single ? value === v : value?.includes(v)
  return (
    <div>
      <p className="text-xs font-mono text-ink-400 uppercase tracking-wider mb-2">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {options.map(o => (
          <button key={o} onClick={() => onChange(o)}
            className={clsx(
              'px-3 py-1 rounded-full text-xs capitalize transition-all duration-150 border',
              isActive(o)
                ? 'bg-terracotta-600/30 text-terracotta-300 border-terracotta-500/40'
                : 'bg-ink-800 text-dust border-ink-700/50 hover:border-ink-500 hover:text-cream'
            )}
          >
            {o}
          </button>
        ))}
      </div>
    </div>
  )
}