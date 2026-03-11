import { useState, useEffect } from 'react'
import { Plus, Search, SlidersHorizontal, Shirt } from 'lucide-react'
import ClothingCard from '../components/Wardrobe/ClothingCard'
import UploadModal from '../components/Wardrobe/UploadModal'
import EditModal from '../components/Wardrobe/EditModal'
import { PageHeader, EmptyState, ClothingCardSkeleton } from '../components/UI'
import api from '../services/api'
import clsx from 'clsx'

const FILTER_OPTS = {
  category: ['all', 'tops', 'bottoms', 'dresses', 'outerwear', 'shoes', 'accessories', 'jewellery'],
  season:   ['all', 'spring', 'summer', 'autumn', 'winter', 'all-season'],
  occasion: ['all', 'casual', 'formal', 'work', 'party', 'ethnic', 'lounge', 'outdoor', 'date'],
}



export default function WardrobePage() {
  const [items,        setItems]        = useState([])
  const [loading,      setLoading]      = useState(true)
  const [search,       setSearch]       = useState('')
  const [filters,      setFilters]      = useState({ category: 'all', season: 'all', occasion: 'all' })
  const [uploadOpen,   setUploadOpen]   = useState(false)
  const [editItem,     setEditItem]     = useState(null)
  const [showFilters,  setShowFilters]  = useState(false)

  const fetchItems = async () => {
    setLoading(true)
    try {
      const data = await api.getWardrobe(
        Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== 'all'))
      )
      setItems(data.items || [])
    } catch (err) {
      console.error('Failed to fetch wardrobe:', err)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchItems() }, [filters])

  const handleDelete = async (item) => {
    if (!confirm(`Remove "${item.name}" from your closet?`)) return
    try {
      await api.deleteClothingItem(item.id)
      setItems(prev => prev.filter(i => i.id !== item.id))
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const filtered = items.filter(item =>
    !search || item.name?.toLowerCase().includes(search.toLowerCase()) ||
    item.colors?.some(c => c.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="p-8">
      <PageHeader
        title="My Closet"
        subtitle={`${items.length} items`}
        action={
          <button onClick={() => setUploadOpen(true)} className="btn-primary flex items-center gap-2">
            <Plus size={15} />
            Add items
          </button>
        }
      />

      {/* Search + filter bar */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by name or color..."
            className="input-base w-full pl-9 text-sm"
          />
        </div>
        <button
          onClick={() => setShowFilters(v => !v)}
          className={clsx('btn-outline flex items-center gap-2', showFilters && 'border-terracotta-500/40 text-terracotta-400')}
        >
          <SlidersHorizontal size={15} />
          Filters
        </button>
      </div>

      {/* Filter chips */}
      {showFilters && (
        <div className="glass rounded-xl p-4 mb-6 space-y-3 animate-fade-in">
          {Object.entries(FILTER_OPTS).map(([key, opts]) => (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs font-mono text-ink-400 uppercase tracking-wider w-16 shrink-0">{key}</span>
              <div className="flex flex-wrap gap-1.5">
                {opts.map(opt => (
                  <button
                    key={opt}
                    onClick={() => setFilters(prev => ({ ...prev, [key]: opt }))}
                    className={clsx(
                      'px-3 py-1 rounded-full text-xs capitalize transition-all border',
                      filters[key] === opt
                        ? 'bg-terracotta-600/30 text-terracotta-300 border-terracotta-500/40'
                        : 'bg-ink-800 text-dust border-ink-700/50 hover:border-ink-500'
                    )}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {[...Array(12)].map((_, i) => <ClothingCardSkeleton key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Shirt}
          title="Your closet is empty"
          description="Add photos of your clothes and let Silhouette build outfits from what you already own."
          action={
            <button onClick={() => setUploadOpen(true)} className="btn-primary flex items-center gap-2">
              <Plus size={15} /> Add your first item
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {filtered.map((item, i) => (
            <div key={item.id} style={{ animationDelay: `${i * 0.03}s` }} className="animate-fade-up opacity-0 [animation-fill-mode:forwards]">
              <ClothingCard
                item={item}
                onEdit={setEditItem}
                onDelete={handleDelete}
              />
            </div>
          ))}
        </div>
      )}

      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={fetchItems}
      />

      <EditModal
        open={!!editItem}
        item={editItem}
        onClose={() => setEditItem(null)}
        onSuccess={fetchItems}
      />
    </div>
  )
}