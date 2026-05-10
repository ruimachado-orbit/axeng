'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Users, Rocket, Tag, GitPullRequest, AlertOctagon,
  TrendingUp, TrendingDown, Minus, Clock, Activity, ChevronRight,
  RefreshCw, CheckCircle2, XCircle, ArrowUpRight
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

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
  { key: 'teamSize', label: 'Team Size', icon: Users, color: 'text-violet-600', bg: 'bg-violet-50' },
  { key: 'activeProjects', label: 'Projects', icon: Rocket, color: 'text-blue-600', bg: 'bg-blue-50' },
  { key: 'openIssues', label: 'Open Issues', icon: Tag, color: 'text-amber-600', bg: 'bg-amber-50' },
  { key: 'prsReviewPending', label: 'PRs Waiting', icon: GitPullRequest, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  { key: 'blockedItems', label: 'Blocked', icon: AlertOctagon, color: 'text-rose-600', bg: 'bg-rose-50' },
]

const trendIcon = (t: string) => t === 'up' ? TrendingUp : t === 'down' ? TrendingDown : Minus
const trendColor = (t: string) => t === 'up' ? 'text-emerald-600' : t === 'down' ? 'text-rose-600' : 'text-slate-400'
const scoreColor = (s: number) => s >= 80 ? 'text-emerald-600' : s >= 60 ? 'text-amber-600' : 'text-rose-600'
const scoreBar = (s: number) => s >= 80 ? 'bg-emerald-500' : s >= 60 ? 'bg-amber-400' : 'bg-rose-500'
const statusDot = (s: string) => s === 'active' ? 'bg-emerald-500' : s === 'ooo' ? 'bg-amber-400' : 'bg-slate-300'
const logTypeColor = (t: string) => t === 'report' ? 'text-blue-600' : t === 'sync' ? 'text-emerald-600' : t === 'delivery' ? 'text-violet-600' : t === 'review' ? 'text-amber-600' : 'text-slate-500'

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
    <div className="space-y-6">
      {/* Stats row */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-slate-200 p-4">
              <Skeleton className="h-8 w-10" />
              <Skeleton className="h-4 w-16 mt-2" />
            </div>
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {statCards.map(s => {
            const Icon = s.icon
            const value = (data.stats as any)[s.key]
            return (
              <div key={s.key} className="bg-white rounded-2xl border border-slate-200 p-4 hover:border-slate-300 transition-colors">
                <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl ${s.bg} mb-3`}>
                  <Icon className={`w-5 h-5 ${s.color}`} />
                </div>
                <div className="text-2xl font-bold text-slate-900">{value}</div>
                <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
              </div>
            )
          })}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Sprint Health */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Sprint Health</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {data?.projects.filter(p => p.score >= 80).length}/{data?.projects.length || 0} projects on track
              </p>
            </div>
            {data?.lastSync && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
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
                  <span className="text-sm font-medium text-slate-700 w-24 truncate">{p.name}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${scoreBar(p.score)}`} style={{ width: `${p.score}%` }} />
                  </div>
                  <span className={`text-sm font-semibold w-10 text-right ${scoreColor(p.score)}`}>{p.score}</span>
                  <TrendIcon className={`w-4 h-4 flex-shrink-0 ${trendColor(p.trend)}`} />
                  <span className="text-xs text-slate-400 w-16 text-right">{p.done}/{p.open + p.done || '—'}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Team Status */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-900">Team Status</h2>
            <Link href="/team" className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
              Ver todos <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {(data?.teamStatus || []).map((m) => (
              <div key={m.name} className="flex items-center gap-3">
                <div className="relative flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-semibold text-slate-600">
                    {m.avatar}
                  </div>
                  <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${statusDot(m.status)}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{m.name}</p>
                  <p className="text-xs text-slate-500">{m.role}</p>
                </div>
                {m.status === 'ooo' && (
                  <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">OOO</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-400" />
            <h2 className="text-base font-semibold text-slate-900">Agent Activity</h2>
          </div>
          <Link href="/logs" className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            Ver logs <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="space-y-0">
          {logs.length === 0 && !loading && (
            <div className="text-center py-8 text-slate-400 text-sm">Nenhuma atividade registada ainda.</div>
          )}
          {logs.map((l, i) => (
            <div key={l.id} className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
              <div className={`w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-slate-300`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-700">{l.action}</p>
                {l.details && <p className="text-xs text-slate-400 mt-0.5 truncate">{l.details}</p>}
              </div>
              <span className="text-xs text-slate-400 flex-shrink-0">
                {new Date(l.timestamp).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}