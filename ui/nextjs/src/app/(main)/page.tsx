import Link from 'next/link'
import {
  Users, Rocket, Tag, GitPullRequest, AlertOctagon,
  TrendingUp, TrendingDown, Minus, Activity, ChevronRight,
  RefreshCw
} from 'lucide-react'

interface Project { name: string; score: number; trend: string; open: number; done: number }
interface TeamMember { name: string; role: string; avatar?: string; status?: string; github?: string; email?: string }
interface LogEntry { id: number; action: string; details: string; type: string; timestamp: string; level: string }

interface DashboardData {
  stats: { teamSize: number; activeProjects: number; openIssues: number; prsReviewPending: number; blockedItems: number }
  projects: Project[]
  teamStatus: TeamMember[]
  lastSync: string
}

const API_BASE = process.env.AXENG_API_BASE || 'http://localhost:3457'

const fallbackData: DashboardData = {
  stats: { teamSize: 0, activeProjects: 0, openIssues: 0, prsReviewPending: 0, blockedItems: 0 },
  projects: [],
  teamStatus: [],
  lastSync: '',
}

const statCards = [
  { key: 'teamSize',          label: 'Team Size',      icon: Users,          grad: 'from-violet-500 to-purple-600' },
  { key: 'activeProjects',    label: 'Projects',       icon: Rocket,         grad: 'from-blue-500 to-cyan-600' },
  { key: 'openIssues',        label: 'Open Issues',    icon: Tag,            grad: 'from-amber-500 to-orange-600' },
  { key: 'prsReviewPending',  label: 'PRs Waiting',    icon: GitPullRequest, grad: 'from-emerald-500 to-teal-600' },
  { key: 'blockedItems',      label: 'Blocked',        icon: AlertOctagon,   grad: 'from-rose-500 to-pink-600' },
] as const

const trendIcon  = (t: string) => t === 'up' ? TrendingUp : t === 'down' ? TrendingDown : Minus
const trendColor = (t: string) => t === 'up' ? 'text-emerald-500' : t === 'down' ? 'text-rose-500' : 'text-slate-400'
const scoreColor = (s: number) => s >= 80 ? 'text-emerald-500' : s >= 60 ? 'text-amber-500' : 'text-rose-500'
const scoreBar   = (s: number) => s >= 80 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : s >= 60 ? 'bg-gradient-to-r from-amber-400 to-amber-500' : 'bg-gradient-to-r from-rose-400 to-rose-500'
const statusDot  = (s?: string) => s === 'active' ? 'bg-emerald-500 animate-pulse' : s === 'ooo' ? 'bg-amber-400' : 'bg-slate-400'

function initials(name: string, fallback?: string) {
  if (fallback) return fallback
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('') || '•'
}

async function getJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
    if (!res.ok) return fallback
    return await res.json() as T
  } catch {
    return fallback
  }
}

export default async function DashboardPage() {
  const [data, logData] = await Promise.all([
    getJson<DashboardData>('/api/dashboard', fallbackData),
    getJson<{ logs: LogEntry[] }>('/api/logs?limit=8', { logs: [] }),
  ])
  const logs = logData.logs || []

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {statCards.map(s => {
          const Icon = s.icon
          const value = data.stats[s.key]
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Sprint Health */}
        <div className="lg:col-span-2 glass rounded-2xl border border-border/40 p-5 transition-all">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-foreground">Sprint Health</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                {data.projects.filter(p => p.score >= 80).length}/{data.projects.length} projects on track
              </p>
            </div>
            {data.lastSync && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <RefreshCw className="w-3 h-3" />
                {new Date(data.lastSync).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
          <div className="space-y-3">
            {data.projects.map((p) => {
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
            {data.projects.length === 0 && (
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
            {data.teamStatus.map((m) => (
              <div key={m.name} className="flex items-center gap-3">
                <div className="relative flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[11px] font-bold text-white shadow-md">
                    {initials(m.name, m.avatar)}
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
            {data.teamStatus.length === 0 && (
              <div className="text-center py-6 text-muted-foreground text-sm">Sem estado de equipa.</div>
            )}
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
          {logs.length === 0 && (
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
