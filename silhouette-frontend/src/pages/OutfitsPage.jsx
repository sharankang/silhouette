import { useState, useEffect } from 'react'
import { Sparkles, Star } from 'lucide-react'
import OutfitHistoryCard from '../components/Outfit/OutfitHistoryCard'
import { PageHeader, EmptyState, Skeleton } from '../components/UI'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import clsx from 'clsx'

const SORT_OPTIONS = [
  { value: 'recent',    label: 'Most recent' },
  { value: 'top_rated', label: 'Top rated'   },
]

export default function OutfitsPage() {
  const [outfits,  setOutfits]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [sort,     setSort]     = useState('recent')
  const navigate = useNavigate()

  const fetchOutfits = async () => {
    setLoading(true)
    try {
      const data = await api.getOutfits()
      setOutfits(data.outfits || [])
    } catch {
      setOutfits([]) // empty during dev
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchOutfits() }, [])

  const handleRate = async (id, rating) => {
    try { await api.rateOutfit(id, rating) } catch {}
    setOutfits(prev => prev.map(o => o.id === id ? { ...o, rating } : o))
  }

  const handleDelete = async (id) => {
    try { await api.deleteOutfit(id) } catch {}
    setOutfits(prev => prev.filter(o => o.id !== id))
  }

  const handleRegenerate = async (outfit) => {
    navigate('/chat')
    // In real use, pre-populate the chat with the same query
  }

  const sorted = [...outfits].sort((a, b) => {
    if (sort === 'top_rated') return (b.rating || 0) - (a.rating || 0)
    return new Date(b.created_at) - new Date(a.created_at)
  })

  // Stats
  const avgRating = outfits.length
    ? (outfits.reduce((s, o) => s + (o.rating || 0), 0) / outfits.filter(o => o.rating).length || 0).toFixed(1)
    : '—'
  const topRated = outfits.filter(o => o.rating >= 4).length

  return (
    <div className="p-8">
      <PageHeader
        title="Generated Outfits"
        subtitle={`${outfits.length} outfits saved`}
        action={
          <div className="flex gap-2">
            {SORT_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setSort(opt.value)}
                className={clsx(
                  'btn-outline text-sm',
                  sort === opt.value && 'border-terracotta-500/40 text-terracotta-400'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        }
      />

      {/* Stats bar */}
      {outfits.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Total outfits', value: outfits.length },
            { label: 'Avg rating',    value: avgRating, icon: Star },
            { label: 'Loved looks',   value: topRated },
          ].map(stat => (
            <div key={stat.label} className="glass rounded-xl p-4 text-center">
              <p className="font-display text-2xl text-cream">{stat.value}</p>
              <p className="text-ink-400 text-xs font-mono mt-1 uppercase tracking-wider">{stat.label}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="glass rounded-2xl overflow-hidden">
              <Skeleton className="h-28 rounded-none" />
              <div className="p-4 space-y-2">
                <Skeleton className="h-3 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No outfits yet"
          description="Head to Style Chat and ask for an outfit. Your generated looks will be saved here."
          action={
            <button onClick={() => navigate('/chat')} className="btn-primary flex items-center gap-2">
              <Sparkles size={15} /> Generate your first outfit
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {sorted.map((outfit, i) => (
            <div key={outfit.id} style={{ animationDelay: `${i * 0.05}s` }}>
              <OutfitHistoryCard
                outfit={outfit}
                onRate={handleRate}
                onDelete={handleDelete}
                onRegenerate={handleRegenerate}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
