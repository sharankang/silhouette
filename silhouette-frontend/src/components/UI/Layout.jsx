import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { Shirt, MessageSquare, Sparkles, Shuffle } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/wardrobe', icon: Shirt,         label: 'Closet'      },
  { to: '/chat',     icon: MessageSquare, label: 'Style Chat'  },
  { to: '/mix',      icon: Shuffle,       label: 'Mix & Match' },
  { to: '/outfits',  icon: Sparkles,      label: 'Outfits'     },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="flex min-h-screen">
      {}
      <aside className="w-56 shrink-0 flex flex-col glass border-r border-ink-800/60 sticky top-0 h-screen">
        {}
        <div className="px-6 pt-8 pb-6 border-b border-ink-800/60">
          <h1 className="font-display text-xl text-cream leading-tight">
            Silhou
            <span className="text-terracotta-400 italic">ette</span>
          </h1>
          <p className="text-ink-400 text-xs font-mono mt-1 tracking-wider uppercase">
            Your AI Stylist
          </p>
        </div>

        {}
        <nav className="flex-1 px-3 py-6 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group',
                  isActive
                    ? 'bg-terracotta-600/20 text-terracotta-400 border border-terracotta-600/30'
                    : 'text-dust hover:text-cream hover:bg-ink-800'
                )
              }
            >
              <Icon size={16} className="shrink-0" />
              <span className="font-body">{label}</span>
            </NavLink>
          ))}
        </nav>

        {}
        <div className="px-6 pb-6">
          <div className="p-3 rounded-lg bg-ink-900/60 border border-ink-800/50">
            <p className="text-ink-400 text-xs font-mono leading-relaxed">
              Hybrid mode<br />
              <span className="text-sage-400">Ollama</span> + <span className="text-terracotta-400">Groq</span>
            </p>
          </div>
        </div>
      </aside>

      {}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}