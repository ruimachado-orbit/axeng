'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Sunrise, TrendingUp, AlertTriangle, MessageSquare, BarChart3,
  Plus, FileText, Clock, ChevronRight, Users, Download, Share2, Copy
} from 'lucide-react'

type ReportType = 'standup' | 'sprint' | 'risk' | 'one-on-one' | 'weekly'

const reports: Array<{
  id: string; type: ReportType; title: string; date: string
  generated_by: string; status: 'ready' | 'pending' | 'draft'
  members?: string[]; member?: string; summary: string; href: string
}> = [
  { id: '1', type: 'standup', title: 'Daily Standup — 10 Mai', date: '2026-05-10T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '3 issues bloqueadas · João FCSantos OOO · 4 PRs pendentes', href: '/reports/standup-2026-05-10' },
  { id: '2', type: 'sprint', title: 'Sprint Health — 09 Mai', date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 78/100 · Phoenix & Compass em risco · 11 projetos', href: '/reports/sprint-2026-05-09' },
  { id: '3', type: 'risk', title: 'Risk Radar — 09 Mai', date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: '0 blockers críticos · 2 warnings · 3 items a resolver esta semana', href: '/reports/risk-2026-05-09' },
  { id: '4', type: 'weekly', title: 'Weekly Report — 09 Mai', date: '2026-05-09T17:00:00', generated_by: 'Axemaster', status: 'ready', members: ['Diogo', 'Pedro', 'Daniel', 'Luis', 'João', 'Anastasiia'], summary: '23 tasks completadas · 5 blockers resolvidos · 2 novos risks', href: '/reports/weekly-2026-05-09' },
  { id: '5', type: 'one-on-one', title: '1:1 Pre-read — Pedro Ferreira', date: '2026-05-08T10:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Pedro Ferreira', summary: '12 issues ativas · 3 PRs em review · últimas 1:1 notes: 02/05', href: '/reports/1on1-pedro-2026-05-08' },
  { id: '6', type: 'one-on-one', title: '1:1 Pre-read — Diogo Oliveira', date: '2026-05-07T09:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Diogo Oliveira', summary: '8 issues ativas · 2 PRs aprovados · blockers: infra costs', href: '/reports/1on1-diogo-2026-05-07' },
  { id: '7', type: 'one-on-one', title: '1:1 Pre-read — João FCSantos', date: '2026-05-06T14:00:00', generated_by: 'Axemaster', status: 'ready', member: 'João FCSantos', summary: '15 issues ativas · PR #844 pendiente · OOO até 16 Mai', href: '/reports/1on1-joao-2026-05-06' },
  { id: '8', type: 'standup', title: 'Daily Standup — 09 Mai', date: '2026-05-09T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '2 blockers · 5 PRs mergeados · sprint a 65% completion', href: '/reports/standup-2026-05-09' },
  { id: '9', type: 'sprint', title: 'Sprint Health — 02 Mai', date: '2026-05-02T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 82/100 · todos os projetos dentro do prazo', href: '/reports/sprint-2026-05-02' },
]

const typeInfo: Record<ReportType, { label: string; icon: React.ReactNode; color: string; bg: string; dot: string }> = {
  standup: { label: 'Standup', icon: <Sunrise className="w-3.5 h-3.5" />, color: 'text-orange-600', bg: 'bg-orange-50', dot: 'bg-orange-400' },
  sprint: { label: 'Sprint', icon: <TrendingUp className="w-3.5 h-3.5" />, color: 'text-emerald-600', bg: 'bg-emerald-50', dot: 'bg-emerald-400' },
  risk: { label: 'Risk', icon: <AlertTriangle className="w-3.5 h-3.5" />, color: 'text-rose-600', bg: 'bg-rose-50', dot: 'bg-rose-400' },
  'one-on-one': { label: '1:1', icon: <MessageSquare className="w-3.5 h-3.5" />, color: 'text-violet-600', bg: 'bg-violet-50', dot: 'bg-violet-400' },
  weekly: { label: 'Weekly', icon: <BarChart3 className="w-3.5 h-3.5" />, color: 'text-blue-600', bg: 'bg-blue-50', dot: 'bg-blue-400' },
}

const filters: Array<{ key: ReportType | 'all'; label: string; icon: React.ReactNode }> = [
  { key: 'all', label: 'Todos', icon: <FileText className="w-3.5 h-3.5" /> },
  { key: 'standup', label: 'Standup', icon: <Sunrise className="w-3.5 h-3.5" /> },
  { key: 'sprint', label: 'Sprint', icon: <TrendingUp className="w-3.5 h-3.5" /> },
  { key: 'risk', label: 'Risk', icon: <AlertTriangle className="w-3.5 h-3.5" /> },
  { key: 'one-on-one', label: '1:1', icon: <MessageSquare className="w-3.5 h-3.5" /> },
  { key: 'weekly', label: 'Weekly', icon: <BarChart3 className="w-3.5 h-3.5" /> },
]

export default function ReportsPage() {
  const [tab, setTab] = useState<ReportType | 'all'>('all')
  const [selected, setSelected] = useState<string | null>(null)

  const filtered = tab === 'all' ? reports : reports.filter(r => r.type === tab)
  const selectedReport = reports.find(r => r.id === selected)

  const copyReport = () => {
    if (selectedReport) {
      navigator.clipboard.writeText(`📋 ${selectedReport.title}\n\n${selectedReport.summary}`)
    }
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">{filtered.length} relatório{filtered.length !== 1 ? 's' : ''} · histórico completo do Axemaster</p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors shadow-sm shadow-blue-200">
          <Plus className="w-4 h-4" />
          Gerar Report
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {filters.map(f => (
          <button
            key={f.key}
            onClick={() => { setTab(f.key); setSelected(null) }}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === f.key
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
            }`}
          >
            {f.icon}
            {f.label}
          </button>
        ))}
      </div>

      {/* Report cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(report => {
          const info = typeInfo[report.type]
          return (
            <Link
              key={report.id}
              href={report.href}
              onClick={(e) => { e.preventDefault(); setSelected(selected === report.id ? null : report.id) }}
              className={`group relative block bg-white rounded-2xl border border-slate-200 p-5 transition-all hover:border-blue-300 hover:shadow-lg hover:shadow-blue-100/50 hover:-translate-y-0.5 cursor-pointer ${
                selected === report.id ? 'ring-2 ring-blue-400 border-blue-300 shadow-lg' : ''
              }`}
            >
              {/* Status dot */}
              {report.status === 'ready' && (
                <span className={`absolute top-4 right-4 w-2 h-2 rounded-full ${info.dot}`} />
              )}

              {/* Type badge */}
              <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium mb-3 ${info.bg} ${info.color}`}>
                {info.icon}
                {info.label}
              </div>

              {/* Title */}
              <h3 className="text-sm font-semibold text-slate-900 leading-snug group-hover:text-blue-700 transition-colors">
                {report.title}
              </h3>

              {/* Summary */}
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{report.summary}</p>

              {/* Footer */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <Clock className="w-3 h-3" />
                  {new Date(report.date).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' })}
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Link>
          )
        })}
      </div>

      {/* Detail panel — slides up as a bottom drawer on mobile, side panel on desktop */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/40 backdrop-blur-sm p-0 md:p-6" onClick={() => setSelected(null)}>
          <div
            className="bg-white w-full md:max-w-2xl md:rounded-2xl rounded-t-3xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            {/* Detail header */}
            <div className="flex items-start justify-between p-5 pb-4 border-b border-slate-100">
              <div>
                <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium mb-2 ${typeInfo[selectedReport.type].bg} ${typeInfo[selectedReport.type].color}`}>
                  {typeInfo[selectedReport.type].icon}
                  {typeInfo[selectedReport.type].label}
                </div>
                <h2 className="text-base font-semibold text-slate-900">{selectedReport.title}</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Gerado por {selectedReport.generated_by} · {new Date(selectedReport.date).toLocaleString('pt-PT', { dateStyle: 'medium', timeStyle: 'short' })}
                </p>
              </div>
              <button onClick={() => setSelected(null)} className="p-2 rounded-xl hover:bg-slate-100 text-slate-400 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Detail content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {/* Summary block */}
              <div className="bg-slate-50 rounded-xl p-4">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Resumo</p>
                <p className="text-sm text-slate-700 leading-relaxed">{selectedReport.summary}</p>
              </div>

              {/* Members for weekly */}
              {selectedReport.members && (
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Destinatários</p>
                  <div className="flex gap-2 flex-wrap">
                    {selectedReport.members.map(m => (
                      <span key={m} className="inline-flex items-center gap-1.5 text-xs bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full font-medium">
                        <Users className="w-3 h-3" />
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Member for 1:1 */}
              {selectedReport.member && (
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Colaborador</p>
                  <div className="inline-flex items-center gap-2 bg-violet-50 text-violet-700 px-3 py-1.5 rounded-full text-sm font-medium">
                    <Users className="w-3.5 h-3.5" />
                    {selectedReport.member}
                  </div>
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 p-4 border-t border-slate-100 bg-slate-50/50">
              <a href={selectedReport.href} className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors">
                <FileText className="w-4 h-4" />
                Ver completo
              </a>
              <button onClick={copyReport} className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 border border-slate-200 hover:bg-slate-100 text-slate-600 text-sm font-medium rounded-xl transition-colors">
                <Copy className="w-4 h-4" />
                Copiar
              </button>
              <button className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 border border-slate-200 hover:bg-slate-100 text-slate-600 text-sm font-medium rounded-xl transition-colors">
                <Share2 className="w-4 h-4" />
                Enviar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}