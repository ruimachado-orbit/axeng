import Link from 'next/link'
import {
  Sunrise, TrendingUp, AlertTriangle, MessageSquare, BarChart3,
  Plus, FileText, Clock, ChevronRight
} from 'lucide-react'

type ReportType = 'standup' | 'sprint' | 'risk' | 'one-on-one' | 'weekly'

type Report = {
  id: string; type: ReportType; title: string; date: string
  generated_by: string; status: 'ready' | 'pending' | 'draft'
  members?: string[]; member?: string; summary: string; href: string
}

const reports: Report[] = [
  { id: '1', type: 'standup',     title: 'Daily Standup — 10 Mai',  date: '2026-05-10T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '3 issues bloqueadas · João FCSantos OOO · 4 PRs pendentes', href: '/reports/standup-2026-05-10' },
  { id: '2', type: 'sprint',      title: 'Sprint Health — 09 Mai',  date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 78/100 · Phoenix & Compass em risco · 11 projetos', href: '/reports/sprint-2026-05-09' },
  { id: '3', type: 'risk',        title: 'Risk Radar — 09 Mai',      date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: '0 blockers críticos · 2 warnings · 3 items a resolver esta semana', href: '/reports/risk-2026-05-09' },
  { id: '4', type: 'weekly',      title: 'Weekly Report — 09 Mai',   date: '2026-05-09T17:00:00', generated_by: 'Axemaster', status: 'ready', members: ['Diogo', 'Pedro', 'Daniel', 'Luis', 'João', 'Anastasiia'], summary: '23 tasks completadas · 5 blockers resolvidos · 2 novos risks', href: '/reports/weekly-2026-05-09' },
  { id: '5', type: 'one-on-one',  title: '1:1 Pre-read — Pedro F.',  date: '2026-05-08T10:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Pedro Ferreira', summary: '12 issues ativas · 3 PRs em review · últimas 1:1 notes: 02/05', href: '/reports/1on1-pedro-2026-05-08' },
  { id: '6', type: 'one-on-one',  title: '1:1 Pre-read — Diogo O.',  date: '2026-05-07T09:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Diogo Oliveira', summary: '8 issues ativas · 2 PRs aprovados · blockers: infra costs', href: '/reports/1on1-diogo-2026-05-07' },
  { id: '7', type: 'one-on-one',  title: '1:1 Pre-read — João FCS.', date: '2026-05-06T14:00:00', generated_by: 'Axemaster', status: 'ready', member: 'João FCSantos', summary: '15 issues ativas · PR #844 pendente · OOO até 16 Mai', href: '/reports/1on1-joao-2026-05-06' },
  { id: '8', type: 'standup',     title: 'Daily Standup — 09 Mai',  date: '2026-05-09T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '2 blockers · 5 PRs mergeados · sprint a 65% completion', href: '/reports/standup-2026-05-09' },
  { id: '9', type: 'sprint',      title: 'Sprint Health — 02 Mai',   date: '2026-05-02T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 82/100 · todos os projetos dentro do prazo', href: '/reports/sprint-2026-05-02' },
]

const typeInfo: Record<ReportType, { label: string; icon: React.ElementType; bg: string; dot: string }> = {
  standup:     { label: 'Standup', icon: Sunrise,      bg: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-300', dot: 'bg-orange-400' },
  sprint:      { label: 'Sprint',  icon: TrendingUp,   bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300', dot: 'bg-emerald-400' },
  risk:        { label: 'Risk',    icon: AlertTriangle,bg: 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300', dot: 'bg-rose-400' },
  'one-on-one':{ label: '1:1',     icon: MessageSquare,bg: 'bg-violet-50 text-violet-700 dark:bg-violet-950/30 dark:text-violet-300', dot: 'bg-violet-400' },
  weekly:      { label: 'Weekly',  icon: BarChart3,    bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-300', dot: 'bg-blue-400' },
}

const filters: Array<{ key: ReportType | 'all'; label: string; icon: React.ElementType }> = [
  { key: 'all',         label: 'Todos',   icon: FileText },
  { key: 'standup',     label: 'Standup', icon: Sunrise },
  { key: 'sprint',      label: 'Sprint',  icon: TrendingUp },
  { key: 'risk',        label: 'Risk',    icon: AlertTriangle },
  { key: 'one-on-one',  label: '1:1',     icon: MessageSquare },
  { key: 'weekly',      label: 'Weekly',  icon: BarChart3 },
]

function isReportType(value: unknown): value is ReportType | 'all' {
  return typeof value === 'string' && ['all', 'standup', 'sprint', 'risk', 'one-on-one', 'weekly'].includes(value)
}

export default async function ReportsPage({ searchParams }: { searchParams: Promise<{ type?: string }> }) {
  const params = await searchParams
  const active = isReportType(params.type) ? params.type : 'all'
  const filtered = active === 'all' ? reports : reports.filter(r => r.type === active)

  return (
    <div className="space-y-5 animate-fade-in-up">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight"><span className="gradient-text">Reports</span></h1>
          <p className="text-sm text-muted-foreground mt-0.5">{filtered.length} relatório{filtered.length !== 1 ? 's' : ''} · histórico completo do Axemaster</p>
        </div>
        <Link
          href={reports[0].href}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-indigo-500/25"
        >
          <Plus className="w-4 h-4" /> Gerar Report
        </Link>
      </div>

      <div className="flex gap-2 flex-wrap">
        {filters.map(f => {
          const Icon = f.icon
          const selected = active === f.key
          return (
            <Link
              key={f.key}
              href={f.key === 'all' ? '/reports' : `/reports?type=${f.key}`}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                selected ? 'nav-active text-white' : 'glass border border-border/40 text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" /> {f.label}
            </Link>
          )
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(report => {
          const info = typeInfo[report.type]
          const Icon = info.icon
          return (
            <Link
              key={report.id}
              href={report.href}
              className="group relative glass glass-hover border-border/40 rounded-2xl p-5 cursor-pointer transition-all animate-fade-in-up block"
            >
              {report.status === 'ready' && <span className={`absolute top-4 right-4 w-2 h-2 rounded-full ${info.dot} animate-pulse`} />}
              <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold mb-3 ${info.bg}`}>
                <Icon className="w-3.5 h-3.5" /> {info.label}
              </div>
              <h3 className="text-sm font-semibold text-foreground leading-snug group-hover:text-indigo-600 transition-colors">{report.title}</h3>
              <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">{report.summary}</p>
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/30">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" /> {new Date(report.date).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' })}
                </div>
                <ChevronRight className="w-4 h-4 text-indigo-400 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
