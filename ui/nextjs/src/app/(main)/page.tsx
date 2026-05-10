'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Users, Rocket, Tag, GitPullRequest, AlertOctagon,
  TrendingUp, TrendingDown, Minus, Clock, Activity, ChevronRight,
  RefreshCw, CheckCircle2, XCircle, ArrowUpRight, ArrowUp
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'

interface Project { name: string; score: number; trend: string; open: number; done: number }
interface TeamMember { name: string; role: string; avatar: string; status: string }
interface LogEntry { id: number; action: string; details: string; type: string; timestamp: string; level: string }

interface DashboardData {
  stats: { teamSize: number; activeProjects: number; openIssues: number; prsReviewPending: number; blockedItems: number }
  projects: Project[]
  teamStatus: TeamMember[]
  lastSync: string
}

const statCards = [
  { key: 'teamSize',          label: 'Team Size',      icon: Users,         grad: 'from-violet-500 to-purple-600',   bg: 'bg-violet-50 dark:bg-violet-950/30' },
  { key: 'activeProjects',    label: 'Projects',        icon: Rocket,        grad: 'from-blue-500 to-cyan-600',       bg: 'bg-blue-50 dark:bg-blue-950/30' },
  { key: 'openIssues',        label: 'Open Issues',     icon: Tag,           grad: 'from-amber-500 to-orange-600',    bg: 'bg-amber-50 dark:bg-amber-950/30' },
  { key: 'prsReviewPending',  label: 'PRs Waiting',     icon: GitPullRequest, grad: 'from-emerald-500 to-teal-600',   bg: 'bg-emerald-50 dark:bg-emerald-950/30' },
  { key: 'blockedItems',      label: 'Blocked',         icon: AlertOctagon,  grad: 'from-rose-500 to-pink-600',      bg: 'bg-rose-50 dark:bg-rose-950/30' },
]

const trendIcon  = (t: string) => t === 'up' ? TrendingUp : t === 'down' ? TrendingDown : Minus
const trendColor = (t: string) => t === 'up' ? 'text-emerald-500' : t === 'down' ? 'text-rose-500' : 'text-slate-400'
const scoreColor = (s: number) => s >= 80 ? 'text-emerald-500' : s >= 60 ? 'text-amber-500' : 'text-rose-500'
const scoreBar   = (s: number) => s >= 80 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : s >= 60 ? 'bg-gradient-to-r from-amber-400 to-amber-500' : 'bg-gradient-to-r from-rose-400 to-rose-500'
const statusDot  = (s: string) => s === 'active' ? 'bg-emerald-500 animate-pulse' : s === 'ooo' ? 'bg-amber-400' : 'bg-slate-400'

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/dashboard').then(r => r.ok ? r.json() : null),
      fetch('/api/logs?limit=8').then(r => r.ok ? r.json() : null),
    ]).then(([d, l]) => {
      setData(d)
      setLogs(l?.logs || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Stats row */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass rounded-2xl border border-border/40 p-4">
              <Skeleton className="h-10 w-10 rounded-xl" />
              <Skeleton className="h-6 w-16 mt-3" />
              <Skeleton className="h-4 w-20 mt-1" />
            </div>
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {statCards.map(s => {
            const Icon = s.icon
            const value = (data.stats as any)[s.key]
            return (
              <div key={s.key} className="glass glass-hover rounded-2xl border border-border/40 p-4 transition-all">
                <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br ${s.grad} mb-3 shadow-lg`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div className="text-2xl font-bold text-foreground">{value ?? 0}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{s.label}</div>
              </div>
            )
          })}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Sprint Health */}
        <div className="lg:col-span-2 glass rounded-2xl border border-border/40 p-5 transition-all">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-foreground">Sprint Health</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                {data?.projects.filter(p => p.score >= 80).length}/{data?.projects.length || 0} projects on track
              </p>
            </div>
            {data?.lastSync && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <RefreshCw className="w-3 h-3" />
                {new Date(data.lastSync).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
          <div className="space-y-3">
            {(data?.projects || []).map((p) => {
              const TrendIcon = trendIcon(p.trend)
              return (
                <div key={p.name} className="flex items-center gap-3 py-1">
                  <span className="text-sm font-medium text-foreground w-24 truncate">{p.name}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${scoreBar(p.score)}`} style={{ width: `${p.score}%` }} />
                  </div>
                  <span className={`text-sm font-bold w-9 text-right ${scoreColor(p.score)}`}>{p.score}</span>
                  <TrendIcon className={`w-4 h-4 flex-shrink-0 ${trendColor(p.trend)}`} />
                  <span className="text-xs text-muted-foreground w-14 text-right">{p.done}/{p.open + p.done || '—'}</span>
                </div>
              )
            })}
            {(!data?.projects || data.projects.length === 0) && (
              <div className="text-center py-6 text-muted-foreground text-sm">Nenhum projeto encontrado</div>
            )}
          </div>
        </div>

        {/* Team Status */}
        <div className="glass rounded-2xl border border-border/40 p-5 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-foreground">Team Status</h2>
            <Link href="/team" className="text-xs text-indigo-500 hover:text-indigo-600 font-medium flex items-center gap-1 transition-colors">
              Ver todos <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {(data?.teamStatus || []).map((m) => (
              <div key={m.name} className="flex items-center gap-3">
                <div className="relative flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[11px] font-bold text-white shadow-md">
                    {m.avatar}
                  </div>
                  <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-card ${statusDot(m.status)}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{m.name}</p>
                  <p className="text-xs text-muted-foreground">{m.role}</p>
                </div>
                {m.status === 'ooo' && (
                  <span className="text-xs font-medium text-amber-600 bg-amber-50 dark:bg-amber-950/30 px-2 py-0.5 rounded-full">OOO</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="glass rounded-2xl border border-border/40 p-5 transition-all">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center">
              <Activity className="w-4 h-4 text-indigo-500" />
            </div>
            <h2 className="text-base font-semibold text-foreground">Agent Activity</h2>
          </div>
          <Link href="/logs" className="text-xs text-indigo-500 hover:text-indigo-600 font-medium flex items-center gap-1 transition-colors">
            Ver logs <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="space-y-0">
          {logs.length === 0 && !loading && (
            <div className="text-center py-8 text-muted-foreground text-sm">Nenhuma atividade registada ainda.</div>
          )}
          {logs.map((l) => (
            <div key={l.id} className="flex items-start gap-3 py-3 border-b border-border/30 last:border-0">
              <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-indigo-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground">{l.action}</p>
                {l.details && <p className="text-xs text-muted-foreground mt-0.5 truncate">{l.details}</p>}
              </div>
              <span className="text-xs text-muted-foreground flex-shrink-0">
                {new Date(l.timestamp).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}