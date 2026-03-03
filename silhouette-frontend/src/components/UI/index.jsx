import { X, Star } from 'lucide-react'
import { useEffect } from 'react'
import clsx from 'clsx'

/* Modal */
export function Modal({ open, onClose, title, children, wide = false }) {
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-ink-950/80 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />
      <div className={clsx(
        'relative glass rounded-2xl p-6 animate-fade-up shadow-2xl shadow-ink-950/50',
        wide ? 'w-full max-w-2xl' : 'w-full max-w-md'
      )}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-lg text-cream">{title}</h3>
          <button onClick={onClose} className="btn-ghost p-1.5 rounded-lg">
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function StarRating({ value, onChange, readonly = false }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          onClick={() => !readonly && onChange?.(star)}
          disabled={readonly}
          className={clsx(
            'transition-all duration-150',
            readonly ? 'cursor-default' : 'hover:scale-110 cursor-pointer'
          )}
        >
          <Star
            size={16}
            className={star <= value ? 'fill-terracotta-400 text-terracotta-400' : 'text-ink-600'}
          />
        </button>
      ))}
    </div>
  )
}

/* Skeleton */
export function Skeleton({ className }) {
  return <div className={clsx('shimmer-bg rounded-lg', className)} />
}

export function ClothingCardSkeleton() {
  return (
    <div className="rounded-xl overflow-hidden border border-ink-800/50">
      <Skeleton className="aspect-[3/4] w-full rounded-none" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-3 w-2/3" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  )
}

/* Empty State */
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-14 h-14 rounded-2xl bg-ink-800 border border-ink-700/50 flex items-center justify-center mb-4">
        <Icon size={24} className="text-ink-500" />
      </div>
      <h3 className="font-display text-lg text-cream mb-2">{title}</h3>
      <p className="text-dust text-sm max-w-xs leading-relaxed mb-6">{description}</p>
      {action}
    </div>
  )
}

/* Page Header  */
export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <h2 className="font-display text-3xl text-cream leading-tight">{title}</h2>
        {subtitle && <p className="text-dust mt-1 text-sm">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
