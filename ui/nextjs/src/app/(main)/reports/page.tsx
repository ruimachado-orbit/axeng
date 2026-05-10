'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

type ReportType = 'standup' | 'sprint' | 'risk' | 'one-on-one' | 'weekly'

const reports: Array<{
  id: string
  type: ReportType
  title: string
  date: string
  generated_by: string
  status: 'ready' | 'pending' | 'draft'
  members?: string[]
  member?: string
  summary: string
}> = [
  { id: '1', type: 'standup', title: 'Daily Standup — 10 Mai', date: '2026-05-10T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '3 issues bloqueadas · João FCSantos OOO · 4 PRs pendentes' },
  { id: '2', type: 'sprint', title: 'Sprint Health — 09 Mai', date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 78/100 · Phoenix & Compass em risco · 11 projetos' },
  { id: '3', type: 'risk', title: 'Risk Radar — 09 Mai', date: '2026-05-09T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: '0 blockers críticos · 2 warnings · 3 items a resolver esta semana' },
  { id: '4', type: 'weekly', title: 'Weekly Report — 09 Mai', date: '2026-05-09T17:00:00', generated_by: 'Axemaster', status: 'ready', members: ['Diogo', 'Pedro', 'Daniel', 'Luis', 'João', 'Anastasiia'], summary: '23 tasks completadas · 5 blockers resolvidos · 2 novos risks' },
  { id: '5', type: 'one-on-one', title: '1:1 Pre-read — Pedro Ferreira', date: '2026-05-08T10:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Pedro Ferreira', summary: '12 issues ativas · 3 PRs em review · últimas 1:1 notes: 02/05' },
  { id: '6', type: 'one-on-one', title: '1:1 Pre-read — Diogo Oliveira', date: '2026-05-07T09:00:00', generated_by: 'Axemaster', status: 'ready', member: 'Diogo Oliveira', summary: '8 issues ativas · 2 PRs aprovados · blockers: infra costs' },
  { id: '7', type: 'one-on-one', title: '1:1 Pre-read — João FCSantos', date: '2026-05-06T14:00:00', generated_by: 'Axemaster', status: 'ready', member: 'João FCSantos', summary: '15 issues ativas · PR #844 pendiente · OOO até 16 Mai' },
  { id: '8', type: 'standup', title: 'Daily Standup — 09 Mai', date: '2026-05-09T07:30:00', generated_by: 'Axemaster', status: 'ready', summary: '2 blockers · 5 PRs mergeados · sprint a 65% completion' },
  { id: '9', type: 'sprint', title: 'Sprint Health — 02 Mai', date: '2026-05-02T16:00:00', generated_by: 'Axemaster', status: 'ready', summary: 'Score médio 82/100 · todos os projetos dentro do prazo' },
]

const typeInfo: Record<ReportType, { label: string; color: string; bgColor: string; icon: string }> = {
  standup: { label: 'Standup', color: 'text-blue-700', bgColor: 'bg-blue-100', icon: '🌅' },
  sprint: { label: 'Sprint', color: 'text-green-700', bgColor: 'bg-green-100', icon: '📈' },
  risk: { label: 'Risk', color: 'text-red-700', bgColor: 'bg-red-100', icon: '🚨' },
  'one-on-one': { label: '1:1', color: 'text-purple-700', bgColor: 'bg-purple-100', icon: '💬' },
  weekly: { label: 'Weekly', color: 'text-indigo-700', bgColor: 'bg-indigo-100', icon: '📊' },
}

const typeFilterLabels: Record<ReportType, string> = {
  standup: '🌅 Standup',
  sprint: '📈 Sprint',
  risk: '🚨 Risk',
  'one-on-one': '💬 1:1',
  weekly: '📊 Weekly',
}

export default function ReportsPage() {
  const [tab, setTab] = useState<ReportType | 'all'>('all')
  const [selected, setSelected] = useState<string | null>(null)

  const filtered = tab === 'all' ? reports : reports.filter(r => r.type === tab)
  const selectedReport = reports.find(r => r.id === selected)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Reports</h1>
          <p className="text-slate-500 text-sm mt-1">Histórico de todos os reports gerados pelo Axemaster</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white text-sm">
          + Gerar Report
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {(['all', 'standup', 'sprint', 'risk', 'one-on-one', 'weekly'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {t === 'all' ? 'Todos' : typeFilterLabels[t as ReportType]}
          </button>
        ))}
      </div>

      {/* Report list */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map(report => {
          const info = typeInfo[report.type]
          return (
            <Card
              key={report.id}
              className={`bg-white cursor-pointer transition-all hover:ring-2 hover:ring-blue-400 ${
                selected === report.id ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => setSelected(selected === report.id ? null : report.id)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{info.icon}</span>
                    <Badge className={`${info.bgColor} ${info.color} text-xs font-medium border-0`}>
                      {info.label}
                    </Badge>
                    {report.status === 'ready' && (
                      <span className="w-2 h-2 rounded-full bg-green-500" />
                    )}
                  </div>
                  <span className="text-xs text-slate-400">
                    {new Date(report.date).toLocaleDateString('pt-PT')}
                  </span>
                </div>
                <CardTitle className="text-sm mt-2">{report.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-500">{report.summary}</p>
                {report.members && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {report.members.map(m => (
                      <span key={m} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{m}</span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Detail panel */}
      {selectedReport && (
        <Card className="bg-white border-blue-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{selectedReport.title}</CardTitle>
                <CardDescription className="mt-1">
                  Gerado por {selectedReport.generated_by} · {new Date(selectedReport.date).toLocaleString('pt-PT')}
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="text-xs">Ver completo</Button>
                <Button variant="outline" size="sm" className="text-xs">Enviar</Button>
                <Button variant="outline" size="sm" className="text-xs">Copiar</Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-700 leading-relaxed">
              <p className="font-medium text-slate-900 mb-2">📋 Resumo:</p>
              <p>{selectedReport.summary}</p>
              {selectedReport.type === 'weekly' && (
                <>
                  <Separator className="my-3" />
                  <p className="font-medium text-slate-900 mb-2">📬 Destinatários:</p>
                  <div className="flex gap-1 flex-wrap">
                    {selectedReport.members?.map(m => (
                      <span key={m} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{m}</span>
                    ))}
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}