import { Sidebar } from '@/components/sidebar'
import { Bell, Search } from 'lucide-react'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200">
          <div className="flex items-center gap-4">
            <h1 className="text-slate-900 font-semibold text-lg">Engineering Dashboard</h1>
            <span className="text-slate-400 text-sm">Lisbon · {new Date().toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long' })}</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-500">
              <Search className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
            </button>
          </div>
        </header>
        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}