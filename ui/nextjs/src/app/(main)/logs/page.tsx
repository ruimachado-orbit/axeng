import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import Link from 'next/link'
import {
  Activity, ScrollText, AlertTriangle, XCircle,
  Search, RefreshCw, Bot, Send, Zap
} from 'lucide-react'

type LogType  = 'tool_call' | 'report' | 'delivery' | 'sync' | 'review' | 'error' | 'decision'
type LogLevel = 'info' | 'warning' | 'error' | 'success'

interface LogEntry {
  id: string
  timestamp: string
  agent: string
  type: LogType
  level: LogLevel
  action: string
  details?: string
  duration_ms?: number
  tool?: string
  target?: string
}

const API_BASE = process.env.AXENG_API_BASE || 'http://localhost:3457'

const typeColors: Record<LogType, string> = {
  tool_call: 'from-slate-400 to-slate-500', report: 'from-blue-500 to-indigo-600', delivery: 'from-emerald-500 to-teal-600', sync: 'from-purple-500 to-violet-600', review: 'from-amber-500 to-orange-600', error: 'from-rose-500 to-pink-600', decision: 'from-indigo-500 to-violet-700',
}
const typeBgColors: Record<LogType, string> = {
  tool_call: 'bg-slate-100 text-slate-700 dark:bg-slate-800/50 dark:text-slate-300', report: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-300', delivery: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300', sync: 'bg-purple-50 text-purple-700 dark:bg-purple-950/30 dark:text-purple-300', review: 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300', error: 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300', decision: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300',
}
const levelColors: Record<LogLevel, string> = { info: 'border-l-indigo-400', success: 'border-l-emerald-400', warning: 'border-l-amber-400', error: 'border-l-rose-400' }
const levelDot: Record<LogLevel, string> = { info: 'bg-indigo-400', success: 'bg-emerald-400', warning: 'bg-amber-400', error: 'bg-rose-400' }
const typeLabels: Record<LogType, string> = { tool_call: 'Tool', report: 'Report', delivery: 'Delivery', sync: 'Sync', review: 'Review', error: 'Error', decision: 'Decision' }
const typeIcons: Record<LogType, React.ElementType> = { tool_call: Zap, report: ScrollText, delivery: Send, sync: RefreshCw, review: Activity, error: XCircle, decision: Bot }
const filterTypes = ['all', 'tool_call', 'report', 'delivery', 'sync', 'review', 'error', 'decision'] as const

function formatTime(ts: string) { return new Date(ts).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }
function formatDate(ts: string) { return new Date(ts).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' }) }
function formatDuration(ms?: number) { if (!ms) return null; return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s` }
function groupByDate(logs: LogEntry[]) { const groups: Record<string, LogEntry[]> = {}; for (const log of logs) { const date = formatDate(log.timestamp); if (!groups[date]) groups[date] = []; groups[date].push(log) } return groups }
function validType(value?: string): LogType | 'all' { return filterTypes.includes(value as any) ? value as LogType | 'all' : 'all' }

async function getLogs(): Promise<LogEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/logs?limit=100`, { cache: 'no-store' })
    if (!res.ok) return []
    const data = await res.json()
    return data?.logs || []
  } catch { return [] }
}

export default async function LogsPage({ searchParams }: { searchParams: Promise<{ type?: string; q?: string }> }) {
  const params = await searchParams
  const allLogs = await getLogs()
  const filter = validType(params.type)
  const search = params.q || ''
  const filtered = allLogs.filter(l => {
    const matchType = filter === 'all' || l.type === filter
    const q = search.toLowerCase()
    const matchSearch = !q || l.action.toLowerCase().includes(q) || l.details?.toLowerCase().includes(q)
    return matchType && matchSearch
  })
  const grouped = groupByDate(filtered)
  const stats = [
    { label: 'Total', value: allLogs.length, color: 'text-foreground', icon: Activity },
    { label: 'Reports', value: allLogs.filter(l => l.type === 'report').length, color: 'text-blue-600', icon: ScrollText },
    { label: 'Syncs', value: allLogs.filter(l => l.type === 'sync').length, color: 'text-purple-600', icon: RefreshCw },
    { label: 'Warnings', value: allLogs.filter(l => l.level === 'warning').length, color: 'text-amber-600', icon: AlertTriangle },
  ]

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div><h1 className="text-2xl font-bold tracking-tight"><span className="gradient-text">Agent Logs</span></h1><p className="text-muted-foreground text-sm mt-1">Timeline completa de todas as ações do Axemaster</p></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{stats.map(s => { const Icon = s.icon; return <Card key={s.label} className="glass border-border/40 overflow-hidden"><CardContent className="p-4 flex items-center gap-3"><div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${s.label === 'Total' ? 'from-slate-400 to-slate-500' : s.label === 'Reports' ? 'from-blue-500 to-indigo-600' : s.label === 'Syncs' ? 'from-purple-500 to-violet-600' : 'from-amber-500 to-orange-600'} flex items-center justify-center shadow-md shrink-0`}><Icon className="w-4 h-4 text-white" /></div><div><div className={`text-xl font-bold ${s.color}`}>{s.value}</div><div className="text-xs text-muted-foreground">{s.label}</div></div></CardContent></Card> })}</div>

      <div className="flex flex-wrap items-center gap-3">
        <form action="/logs" className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          {filter !== 'all' && <input type="hidden" name="type" value={filter} />}
          <input type="text" name="q" defaultValue={search} placeholder="Pesquisar..." className="pl-9 pr-3 py-2 glass border border-border/40 rounded-xl text-sm w-44 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400/40 bg-transparent" />
        </form>
        <div className="flex gap-1.5 flex-wrap">{filterTypes.map(type => { const Icon = type !== 'all' ? typeIcons[type] : Activity; const href = `/logs${type === 'all' ? '' : `?type=${type}`}${search ? `${type === 'all' ? '?' : '&'}q=${encodeURIComponent(search)}` : ''}`; return <Link key={type} href={href} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filter === type ? 'nav-active text-white' : 'glass border border-border/40 text-muted-foreground hover:text-foreground hover:bg-secondary/50'}`}><Icon className="w-3 h-3" />{type === 'all' ? 'Todos' : typeLabels[type]}</Link> })}</div>
      </div>

      <Card className="glass border-border/40 overflow-hidden"><CardContent className="p-5">{Object.entries(grouped).map(([date, entries]) => <div key={date}><div className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3 mt-2 first:mt-0 flex items-center gap-2"><span>{date}</span><div className="h-px flex-1 bg-border/50" /></div><div className="space-y-0">{entries.map(entry => { const TypeIcon = typeIcons[entry.type]; return <div key={entry.id} className={`flex gap-4 border-l-2 ml-1 pl-4 py-3 ${levelColors[entry.level]}`}><div className="w-16 shrink-0 pt-0.5"><span className="text-xs font-mono text-muted-foreground">{formatTime(entry.timestamp)}</span></div><div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${typeColors[entry.type]} flex items-center justify-center shrink-0 shadow-md`}><TypeIcon className="w-3.5 h-3.5 text-white" /></div><div className="flex-1 min-w-0"><div className="flex flex-wrap items-center gap-2 mb-1"><Badge className={`text-[10px] font-semibold ${typeBgColors[entry.type]}`}>{typeLabels[entry.type]}</Badge><span className="text-xs font-mono text-muted-foreground">{entry.agent}</span>{entry.duration_ms && <span className="text-[10px] text-muted-foreground font-mono bg-secondary px-1.5 py-0.5 rounded">{formatDuration(entry.duration_ms)}</span>}{entry.level !== 'info' && <span className={`w-1.5 h-1.5 rounded-full ${levelDot[entry.level]}`} />}</div><p className="text-sm font-medium text-foreground">{entry.action}</p>{entry.details && <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{entry.details}</p>}<div className="flex gap-2 mt-1.5 flex-wrap">{entry.tool && <span className="text-[10px] font-mono bg-secondary text-muted-foreground px-1.5 py-0.5 rounded border border-border/40">{entry.tool}</span>}{entry.target && <span className="text-[10px] font-mono bg-indigo-50 text-indigo-600 dark:bg-indigo-950/30 dark:text-indigo-400 px-1.5 py-0.5 rounded border border-indigo-200/30 dark:border-indigo-800/30">{entry.target}</span>}</div></div></div> })}</div><Separator className="mt-2 mb-1" /></div>)}{filtered.length === 0 && <div className="text-center py-12 text-muted-foreground text-sm">Nenhum log encontrado</div>}</CardContent></Card>
    </div>
  )
}
