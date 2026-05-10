import { Sidebar } from '@/components/sidebar'
import { Bell, Search } from 'lucide-react'
import Link from 'next/link'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const now = new Date()
  const dateStr = now.toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long' })

  return (
    <div className="flex min-h-screen bg-background gradient-bg">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between h-16 px-6 bg-white/60 glass border-b border-white/20 sticky top-0 z-40">
          <div className="flex items-center gap-4 min-w-0">
            <h1 className="text-slate-900 font-bold text-lg tracking-tight hidden sm:block">
              Engineering Dashboard
            </h1>
            <span className="text-slate-400 text-sm hidden md:block">
              Lisbon · {dateStr}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/logs" className="p-2 rounded-xl hover:bg-white/60 glass-hover text-slate-500 hover:text-indigo-600 transition-all duration-200">
              <Search className="w-4 h-4" />
            </Link>
            <Link href="/logs" className="p-2 rounded-xl hover:bg-white/60 glass-hover text-slate-500 hover:text-indigo-600 transition-all duration-200 relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 sm:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}