'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

const navItems = [
  { label: 'Dashboard', href: '/', icon: '📊' },
  { label: 'Agent Logs', href: '/logs', icon: '🕐' },
  { label: 'Reports', href: '/reports', icon: '📋' },
  { label: 'Team', href: '/team', icon: '👥' },
  { label: 'Settings', href: '/settings', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="flex flex-col w-64 min-h-screen bg-slate-900 border-r border-slate-800">
      {/* Logo / Header */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-600 text-white font-bold text-sm">
          A
        </div>
        <div>
          <p className="text-white font-semibold text-sm">Axeng</p>
          <p className="text-slate-400 text-xs">EM Accelerator</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-blue-600 text-white text-xs">RM</AvatarFallback>
          </Avatar>
          <div>
            <p className="text-white text-sm font-medium">Rui Machado</p>
            <p className="text-slate-400 text-xs">CTPO · Maio Labs</p>
          </div>
        </div>
      </div>
    </aside>
  )
}