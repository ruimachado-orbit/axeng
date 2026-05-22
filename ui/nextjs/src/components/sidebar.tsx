'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

import {
  LayoutDashboard,
  ScrollText,
  FileText,
  Users,
  Settings,
  Menu,
  Zap,
} from 'lucide-react'

const navItems = [
  { label: 'Dashboard',   href: '/',       icon: LayoutDashboard },
  { label: 'Agent Logs', href: '/logs',   icon: ScrollText },
  { label: 'Reports',    href: '/reports', icon: FileText },
  { label: 'Team',       href: '/team',   icon: Users },
  { label: 'Settings',   href: '/settings', icon: Settings },
]

function NavLink({ item, onNavigate }: { item: typeof navItems[0]; onNavigate?: () => void }) {
  const pathname = usePathname()
  const active = pathname === item.href
  const Icon = item.icon

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative overflow-hidden',
        active
          ? 'nav-active text-white'
          : 'text-slate-400 hover:text-white hover:bg-white/5'
      )}
    >
      {/* Active shimmer */}
      {active && (
        <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-gradient" />
      )}
      <Icon className={cn(
        'w-[18px] h-[18px] shrink-0 transition-colors',
        active ? 'text-white' : 'text-slate-500 group-hover:text-indigo-300'
      )} />
      <span className="relative z-10">{item.label}</span>
      {active && (
        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-white/80" />
      )}
    </Link>
  )
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/8">
        <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold text-sm shadow-lg shadow-indigo-500/30">
          A
        </div>
        <div>
          <p className="text-white font-semibold text-sm leading-tight">Axeng</p>
          <p className="text-slate-400 text-xs flex items-center gap-1">
            <Zap className="w-2.5 h-2.5 text-indigo-400" /> EM Accelerator
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink key={item.href} item={item} onNavigate={onNavigate} />
        ))}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-white/8">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-default">
          <Avatar className="w-8 h-8 ring-2 ring-indigo-500/50 ring-offset-2 ring-offset-slate-900">
            <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-xs font-bold">
              AX
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="text-white text-sm font-medium truncate">Axeng Admin</p>
            <p className="text-slate-400 text-xs truncate">Admin</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-64 min-h-screen bg-sidebar sidebar-gradient border-r border-white/8 shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile: CSS-only drawer — works even if mobile WebView drops React click handlers */}
      <input id="mobile-menu-toggle" type="checkbox" className="peer sr-only md:hidden" aria-hidden="true" />
      <label
        htmlFor="mobile-menu-toggle"
        aria-label="Abrir menu"
        className="md:hidden fixed top-0 left-0 z-[80] m-3 flex items-center justify-center w-10 h-10 rounded-xl bg-sidebar border border-white/10 shadow-lg active:scale-95 transition-transform cursor-pointer"
      >
        <Menu className="w-5 h-5 text-white" />
      </label>

      <div className="md:hidden fixed inset-0 z-[90] hidden peer-checked:block">
        <label
          htmlFor="mobile-menu-toggle"
          aria-label="Fechar menu"
          className="absolute inset-0 block bg-black/30 backdrop-blur-[1px] cursor-pointer"
        />
        <aside className="absolute inset-y-0 left-0 w-64 bg-sidebar sidebar-gradient border-r border-white/8 shadow-2xl">
          <SidebarContent />
        </aside>
      </div>
    </>
  )
}