import Link from 'next/link'
import {
  Sunrise, TrendingUp, AlertTriangle, MessageSquare, BarChart3,
  ArrowLeft, Clock, Download, Share2, FileText, XCircle, Users
} from 'lucide-react'

type ReportType = 'standup' | 'sprint' | 'risk' | 'one-on-one' | 'weekly'

const reportData: Record<string, {
  type: ReportType; title: string; date: string; generated_by: string
  summary: string; content: string; members?: string[]; member?: string
  metrics?: Array<{ label: string; value: string; icon: string }>
}> = {
  'standup-2026-05-10': {
    type: 'standup', title: 'Daily Standup — 10 Mai', date: '2026-05-10T07:30:00',
    generated_by: 'Axemaster', summary: '3 issues bloqueadas · João FCSantos OOO · 4 PRs pendentes',
    members: ['Daniel', 'Luis', 'Rui', 'Pedro', 'Diogo', 'João FCSantos', 'Anastasiia'],
    metrics: [
      { label: 'Issues bloqueadas', value: '3', icon: '🚧' },
      { label: 'PRs pendentes', value: '4', icon: '🔀' },
      { label: 'Team OOO', value: '1', icon: '🏖️' },
    ],
    content: `## 📋 Daily Standup — 10 de Maio, 2026

### 🚧 Issues Bloqueadas
- **MAI-67** (Orbit) — aguardando review do Diogo
- **MAI-71** (Phoenix) — dependência de API externa
- **MAI-74** (Compass) — blocker: billing layer não pode avanzar sem UAT

### 🔀 PRs em Review
- #848 orbit-health (João FCSantos) — approved, aguardando merge
- #847 orbit-talent (Anastasiia) — 2 reviews, ok
- #412 racoon (Diogo) — needs 1 more approval
- #845 orbit-platform (Rikkarth) — draft, não ready for review

### 🏖️ Team Status
- **João FCSantos** — OOO até 16 Mai (Vacation label Linear)
- Todos os outros — Active

### 📅 Recomendações
1. Priorizar MAI-74 (billing) — blocking de feature crítica
2. Diogo review #412 para fazer merge hoje
3. Agendar daily follow-up para Phoenix blocker`,
  },
  'sprint-2026-05-09': {
    type: 'sprint', title: 'Sprint Health — 09 Mai', date: '2026-05-09T16:00:00',
    generated_by: 'Axemaster', summary: 'Score médio 78/100 · Phoenix & Compass em risco · 11 projetos',
    metrics: [
      { label: 'Score médio', value: '78/100', icon: '📊' },
      { label: 'Projetos em risco', value: '2', icon: '⚠️' },
      { label: 'Issues completadas', value: '12', icon: '✅' },
    ],
    content: `## 📊 Sprint Health — 9 de Maio, 2026

### Visão Geral
**Score médio: 78/100** — Dentro do esperado, com 2 projetos em atenção

### Projetos em Risco
- **Phoenix** (score: 64) — 7 issues abertas, nenhuma completada esta semana
- **Compass** (score: 72) — billing layer bloqueado, depende de MAI-74

### Projetos Bem
- **WareAI** (score: 95) — 8 done, 0 open
- **Orbit** (score: 88) — 9 done, 12 open
- **Brain** (score: 81) — 10 done, 14 open

### Recomendações
1. Daily standup focado em Phoenix — identificar blockers
2. Compass: escalar MAI-74 para o Diogo resolver
3. WareAI manter ritmo, pode servir como benchmark`,
  },
  'risk-2026-05-09': {
    type: 'risk', title: 'Risk Radar — 09 Mai', date: '2026-05-09T16:00:00',
    generated_by: 'Axemaster', summary: '0 blockers críticos · 2 warnings · 3 items a resolver esta semana',
    metrics: [
      { label: 'Blockers críticos', value: '0', icon: '🚨' },
      { label: 'Warnings', value: '2', icon: '⚠️' },
      { label: 'Items a resolver', value: '3', icon: '📌' },
    ],
    content: `## ⚠️ Risk Radar — 9 de Maio, 2026

### 🚨 Blockers Críticos
Nenhum blocker crítico identificado.

### ⚠️ Warnings
1. **Infra costs** (medium) — Cloud costs subiram 18% MTD vs budget. Rikkarth a analisar.
2. **API rate limits** (low) — Linear API a aproximar-se do rate limit (500 req/min). Considerar batching.

### 📌 Items a Resolver Esta Semana
1. Phoenix: identificar root cause do score baixo (64/100)
2. Compass billing: MAI-74 precisa de review urgente
3. João FCSantos OOO: garantir coverage das suas tasks`,
  },
}

const typeConfig: Record<ReportType, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  standup: { label: 'Standup', icon: <Sunrise className="w-4 h-4" />, color: 'text-orange-600', bg: 'bg-orange-50' },
  sprint: { label: 'Sprint', icon: <TrendingUp className="w-4 h-4" />, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  risk: { label: 'Risk', icon: <AlertTriangle className="w-4 h-4" />, color: 'text-rose-600', bg: 'bg-rose-50' },
  'one-on-one': { label: '1:1', icon: <MessageSquare className="w-4 h-4" />, color: 'text-violet-600', bg: 'bg-violet-50' },
  weekly: { label: 'Weekly', icon: <BarChart3 className="w-4 h-4" />, color: 'text-blue-600', bg: 'bg-blue-50' },
}

export default async function ReportDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const report = slug ? reportData[slug] : null

  if (!report) {
    return (
      <div className="space-y-6">
        <Link href="/reports" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Voltar aos Reports
        </Link>
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mb-4">
            <XCircle className="w-8 h-8 text-slate-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-700">Report não encontrado</h2>
          <p className="text-sm text-slate-400 mt-1">Este report ainda não foi gerado ou o link expirou.</p>
          <Link href="/reports" className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-colors">
            Voltar aos Reports
          </Link>
        </div>
      </div>
    )
  }

  const cfg = typeConfig[report.type]
  const markdownHref = `data:text/markdown;charset=utf-8,${encodeURIComponent(report.content)}`
  const shareHref = `mailto:?subject=${encodeURIComponent(report.title)}&body=${encodeURIComponent(`${report.summary}\n\n${report.content}`)}`

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Back button */}
      <Link href="/reports" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Voltar aos Reports
      </Link>

      {/* Header card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium mb-3 ${cfg.bg} ${cfg.color}`}>
              {cfg.icon}
              {cfg.label}
            </div>
            <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">{report.title}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
              <span className="inline-flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                {new Date(report.date).toLocaleString('pt-PT', { dateStyle: 'long', timeStyle: 'short' })}
              </span>
              <span>Gerado por {report.generated_by}</span>
            </div>
          </div>
          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <a href="#conteudo" className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 text-sm font-medium rounded-xl transition-colors">
              <FileText className="w-4 h-4" />
              Texto
            </a>
            <a href={shareHref} className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 text-sm font-medium rounded-xl transition-colors">
              <Share2 className="w-4 h-4" />
              Enviar
            </a>
            <a href={markdownHref} download={`${slug || 'report'}.md`} className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors shadow-sm">
              <Download className="w-4 h-4" />
              Markdown
            </a>
          </div>
        </div>
      </div>

      {/* Metrics row */}
      {report.metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {report.metrics.map(m => (
            <div key={m.label} className="bg-white rounded-xl border border-slate-200 p-4 text-center">
              <div className="text-2xl font-bold text-slate-900">{m.value}</div>
              <div className="text-xs text-slate-500 mt-1">{m.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Members row */}
      {report.members && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-700">Destinatários ({report.members.length})</h3>
          </div>
          <div className="flex gap-2 flex-wrap">
            {report.members.map(m => (
              <span key={m} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 text-slate-600 text-xs font-medium rounded-full">
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Main content */}
      <div id="conteudo" className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="prose prose-slate prose-sm max-w-none">
          {report.content.split('\n').map((line, i) => {
            if (line.startsWith('## ')) return <h2 key={i} className="text-lg font-semibold text-slate-900 mt-0 mb-3">{line.replace('## ', '')}</h2>
            if (line.startsWith('### ')) return <h3 key={i} className="text-sm font-semibold text-slate-700 mt-4 mb-2">{line.replace('### ', '')}</h3>
            if (line.startsWith('- ')) return <div key={i} className="pl-3 text-sm text-slate-600 my-0.5">{line}</div>
            if (line.trim() === '') return <div key={i} className="h-2" />
            return <p key={i} className="text-sm text-slate-600 my-0.5 leading-relaxed">{line}</p>
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-slate-400">
        Gerado automaticamente pelo Axemaster · último update {new Date(report.date).toLocaleString('pt-PT')}
      </div>
    </div>
  )
}