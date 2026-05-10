'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Sunrise, TrendingUp, AlertTriangle, MessageSquare, BarChart3,
  Plus, FileText, Clock, ChevronRight, Users, Copy, Share2, X
} from 'lucide-react'

type ReportType = 'standup' | 'sprint' | 'risk' | 'one-on-one' | 'weekly'

const reports: Array<{
  id: string; type: ReportType; title: string; date: string
  generated_by: string; status: 'ready' | 'pending' | 'draft'
  members?: string[]; member?: string; summary: string; href: string
}> = [
  { id: '1', type: 'standup',     title: 'Daily Standup — 10 Mai',  date: '2026-05-10T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '3 issues bloqueadas · João FCSantos OOO · 4 PRs pendentes', href: '/reports/standup-2026-05-10' },
  { id: '2', type: 'sprint',      title: 'Sprint Health — 09 Mai',  date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 78/100 · Phoenix & Compass em risco · 11 projetos', href: '/reports/sprint-2026-05-09' },
  { id: '3', type: 'risk',        title: 'Risk Radar — 09 Mai',      date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: '0 blockers críticos · 2 warnings · 3 items a resolver esta semana', href: '/reports/risk-2026-05-09' },
  { id: '4', type: 'weekly',      title: 'Weekly Report — 09 Mai',   date: '2026-05-09T17:00:00', generated_by: 'Axemaster', status: 'ready', members: ['Diogo', 'Pedro', 'Daniel', 'Luis', 'João', 'Anastasiia'], summary: '23 tasks completadas · 5 blockers resolvidos · 2 novos risks', href: '/reports/weekly-2026-05-09' },
  { id: '5', type: 'one-on-one',  title: '1:1 Pre-read — Pedro F.',  date: '2026-05-08T10:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Pedro Ferreira', summary: '12 issues ativas · 3 PRs em review · últimas 1:1 notes: 02/05', href: '/reports/1on1-pedro-2026-05-08' },
  { id: '6', type: 'one-on-one',  title: '1:1 Pre-read — Diogo O.',  date: '2026-05-07T09:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Diogo Oliveira', summary: '8 issues ativas · 2 PRs aprovados · blockers: infra costs', href: '/reports/1on1-diogo-2026-05-07' },
  { id: '7', type: 'one-on-one',  title: '1:1 Pre-read — João FCS.', date: '2026-05-06T14:00:00', generated_by: 'Axemaster', status: 'ready', member: 'João FCSantos', summary: '15 issues ativas · PR #844 pendiente · OOO até 16 Mai', href: '/reports/1on1-joao-2026-05-06' },
  { id: '8', type: 'standup',     title: 'Daily Standup — 09 Mai',  date: '2026-05-09T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '2 blockers · 5 PRs mergeados · sprint a 65% completion', href: '/reports/standup-2026-05-09' },
  { id: '9', type: 'sprint',      title: 'Sprint Health — 02 Mai',   date: '2026-05-02T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 82/100 · todos os projetos dentro do prazo', href: '/reports/sprint-2026-05-02' },
]

const typeInfo: Record<ReportType, { label: string; icon: React.ElementType; grad: string; bg: string; dot: string }> = {
  standup:     { label: 'Standup', icon: Sunrise,      grad: 'from-orange-500 to-red-500',    bg: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-300', dot: 'bg-orange-400' },
  sprint:      { label: 'Sprint',   icon: TrendingUp,    grad: 'from-emerald-500 to-teal-600',  bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300', dot: 'bg-emerald-400' },
  risk:        { label: 'Risk',     icon: AlertTriangle, grad: 'from-rose-500 to-pink-600',     bg: 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300', dot: 'bg-rose-400' },
  'one-on-one':{ label: '1:1',     icon: MessageSquare, grad: 'from-violet-500 to-purple-600', bg: 'bg-violet-50 text-violet-700 dark:bg-violet-950/30 dark:text-violet-300', dot: 'bg-violet-400' },
  weekly:      { label: 'Weekly',   icon: BarChart3,     grad: 'from-blue-500 to-indigo-600',   bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-300', dot: 'bg-blue-400' },
}

const filters: Array<{ key: ReportType | 'all'; label: string; icon: React.ElementType }> = [
  { key: 'all',         label: 'Todos',      icon: FileText },
  { key: 'standup',     label: 'Standup',    icon: Sunrise },
  { key: 'sprint',      label: 'Sprint',     icon: TrendingUp },
  { key: 'risk',        label: 'Risk',       icon: AlertTriangle },
  { key: 'one-on-one',  label: '1:1',        icon: MessageSquare },
  { key: 'weekly',      label: 'Weekly',     icon: BarChart3 },
]

export default function ReportsPage() {
  const [tab, setTab] = useState<ReportType | 'all'>('all')
  const [selected, setSelected] = useState<string | null>(null)

  const filtered = tab === 'all' ? reports : reports.filter(r => r.type === tab)
  const selectedReport = reports.find(r => r.id === selected)

  return (
    <div className="space-y-5 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="gradient-text">Reports</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">{filtered.length} relatório{filtered.length !== 1 ? 's' : ''} · histórico completo do Axemaster</p>
        </div>
        <button
          onClick={() => setSelected(reports[0]?.id ?? null)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-indigo-500/25"
        >
          <Plus className="w-4 h-4" /> Gerar Report
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {filters.map(f => {
          const Icon = f.icon
          return (
            <button
              key={f.key}
              onClick={() => { setTab(f.key); setSelected(null) }}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                tab === f.key
                  ? 'nav-active text-white'
                  : 'glass border border-border/40 text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {f.label}
            </button>
          )
        })}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(report => {
          const info = typeInfo[report.type]
          const Icon = info.icon
          return (
            <div
              key={report.id}
              onClick={() => setSelected(selected === report.id ? null : report.id)}
              className={`group relative glass glass-hover border-border/40 rounded-2xl p-5 cursor-pointer transition-all animate-fade-in-up ${
                selected === report.id ? 'ring-2 ring-indigo-500 border-indigo-400/40' : ''
              }`}
            >
              {/* Status dot */}
              {report.status === 'ready' && (
                <span className={`absolute top-4 right-4 w-2 h-2 rounded-full ${info.dot} animate-pulse`} />
              )}

              {/* Type badge */}
              <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold mb-3 ${info.bg}`}>
                <Icon className="w-3.5 h-3.5" />
                {info.label}
              </div>

              {/* Title */}
              <h3 className="text-sm font-semibold text-foreground leading-snug group-hover:text-indigo-600 transition-colors">
                {report.title}
              </h3>

              {/* Summary */}
              <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">{report.summary}</p>

              {/* Footer */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/30">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  {new Date(report.date).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' })}
                </div>
                <Link
                  href={report.href}
                  onClick={e => e.stopPropagation()}
                  className="text-indigo-500"
                >
                  <ChevronRight className="w-4 h-4 text-indigo-400 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
                </Link>
              </div>
            </div>
          )
        })}
      </div>

      {/* Detail drawer */}
      {selectedReport && (
        <div
          className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/40 backdrop-blur-sm p-0 md:p-6"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-card w-full md:max-w-2xl md:rounded-2xl rounded-t-3xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-5 pb-4 border-b border-border/30">
              <div>
                <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold mb-2 ${typeInfo[selectedReport.type].bg}`}>
                  {(() => { const Icon = typeInfo[selectedReport.type].icon; return <Icon className="w-3.5 h-3.5" /> })()}
                  {typeInfo[selectedReport.type].label}
                </div>
                <h2 className="text-base font-semibold text-foreground">{selectedReport.title}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Gerado por {selectedReport.generated_by} · {new Date(selectedReport.date).toLocaleString('pt-PT', { dateStyle: 'medium', timeStyle: 'short' })}
                </p>
              </div>
              <button onClick={() => setSelected(null)} className="p-2 rounded-xl hover:bg-secondary text-muted-foreground transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <div className="bg-secondary/50 rounded-xl p-4 border border-border/30">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Resumo</p>
                <p className="text-sm text-foreground leading-relaxed">{selectedReport.summary}</p>
              </div>

              {selectedReport.members && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Destinatários</p>
                  <div className="flex gap-2 flex-wrap">
                    {selectedReport.members.map(m => (
                      <span key={m} className="inline-flex items-center gap-1.5 text-xs bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300 px-3 py-1.5 rounded-full font-medium">
                        <Users className="w-3 h-3" /> {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedReport.member && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Colaborador</p>
                  <div className="inline-flex items-center gap-2 bg-violet-50 text-violet-700 dark:bg-violet-950/30 dark:text-violet-300 px-3 py-1.5 rounded-full text-sm font-medium">
                    <Users className="w-3.5 h-3.5" /> {selectedReport.member}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 p-4 border-t border-border/30 bg-secondary/30">
              <Link href={selectedReport.href} className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90 text-white text-sm font-medium rounded-xl transition-all shadow-lg">
                <FileText className="w-4 h-4" /> Ver completo
              </Link>
              <button onClick={() => navigator.clipboard.writeText(`📋 ${selectedReport.title}\n\n${selectedReport.summary}`)} className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 glass border border-border/40 hover:bg-secondary text-muted-foreground text-sm font-medium rounded-xl transition-all">
                <Copy className="w-4 h-4" /> Copiar
              </button>
              <button
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({ title: selectedReport.title, text: selectedReport.summary, url: selectedReport.href })
                  } else {
                    navigator.clipboard.writeText(`${location.origin}${selectedReport.href}`)
                    alert('Link copiado')
                  }
                }}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 glass border border-border/40 hover:bg-secondary text-muted-foreground text-sm font-medium rounded-xl transition-all"
              >
                <Share2 className="w-4 h-4" /> Enviar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}