'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'

interface DashboardData {
  stats: { teamSize: number; activeProjects: number; openIssues: number; prsReviewPending: number; blockedItems: number }
  projects: Array<{ name: string; score: number; trend: string; open: number; done: number }>
  teamStatus: Array<{ name: string; role: string; avatar: string; status: string }>
  lastSync: string
}

const fallback: DashboardData = {
  stats: { teamSize: 7, activeProjects: 11, openIssues: 38, prsReviewPending: 4, blockedItems: 2 },
  projects: [
    { name: 'Orbit', score: 88, trend: 'up', open: 12, done: 9 },
    { name: 'Compass', score: 72, trend: 'down', open: 18, done: 11 },
    { name: 'WareAI', score: 95, trend: 'stable', open: 6, done: 5 },
    { name: 'Phoenix', score: 64, trend: 'down', open: 9, done: 4 },
    { name: 'Brain', score: 81, trend: 'up', open: 14, done: 10 },
  ],
  teamStatus: [
    { name: 'Pedro Ferreira', role: 'Backend', avatar: 'PF', status: 'active' },
    { name: 'Diogo Oliveira', role: 'DevOps', avatar: 'DO', status: 'active' },
    { name: 'Anastasiia M.', role: 'Frontend', avatar: 'AM', status: 'active' },
    { name: 'João FCSantos', role: 'Engineering', avatar: 'JF', status: 'ooo' },
    { name: 'Rikkarth R.', role: 'ML/AI', avatar: 'RR', status: 'active' },
    { name: 'Daniel Almeida', role: 'CEO', avatar: 'DA', status: 'active' },
    { name: 'Luis Santos', role: 'Co-founder', avatar: 'LS', status: 'active' },
  ],
  lastSync: '',
}

const recentActivity = [
  { time: '09:42', agent: 'Axemaster', action: 'Gerou standup brief para a equipa', type: 'report' },
  { time: '09:38', agent: 'Axemaster', action: 'Sincronizou estado do Linear — 3 issues atualizadas', type: 'sync' },
  { time: '09:30', agent: 'Axemaster', action: 'Detetou João FCSantos em modo OOO até Sexta', type: 'team' },
  { time: '09:15', agent: 'Axemaster', action: 'Enviou briefing para Telegram — 3 items pendentes', type: 'delivery' },
  { time: '08:55', agent: 'Axemaster', action: 'Reviu PR #847 em orbit-health — aprovado', type: 'review' },
]

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/dashboard')
      .then(r => r.ok ? r.json() : null)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => { setData(fallback); setLoading(false) })
  }, [])

  const trendIcon = (t: string) => t === 'up' ? '↑' : t === 'down' ? '↓' : '→'
  const trendColor = (t: string) => t === 'up' ? 'text-green-600' : t === 'down' ? 'text-red-500' : 'text-slate-400'
  const statusColor = (s: string) => s === 'active' ? 'bg-green-500' : s === 'ooo' ? 'bg-amber-400' : 'bg-slate-300'
  const scoreColor = (s: number) => s >= 80 ? 'text-green-600' : s >= 60 ? 'text-amber-600' : 'text-red-600'
  const scoreBar = (s: number) => s >= 80 ? 'bg-green-500' : s >= 60 ? 'bg-amber-400' : 'bg-red-500'

  return (
    <div className="space-y-6">
      {/* Stats row */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i} className="bg-white"><CardContent className="pt-4 pb-3">
              <Skeleton className="h-8 w-12" /><Skeleton className="h-4 w-20 mt-2" />
            </CardContent></Card>
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Team Size', value: data.stats.teamSize, emoji: '👥' },
            { label: 'Projects', value: data.stats.activeProjects, emoji: '🚀' },
            { label: 'Open Issues', value: data.stats.openIssues, emoji: '📌' },
            { label: 'PRs Waiting', value: data.stats.prsReviewPending, emoji: '🔀' },
            { label: 'Blocked', value: data.stats.blockedItems, emoji: '🚧' },
          ].map((stat) => (
            <Card key={stat.label} className="bg-white">
              <CardContent className="pt-4 pb-3">
                <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className="text-base">{stat.emoji}</span>
                  <span className="text-slate-500 text-sm">{stat.label}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sprint Health */}
        <Card className="lg:col-span-2 bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Sprint Health</CardTitle>
              {data?.lastSync && (
                <span className="text-xs text-slate-400">Sincronizado: {new Date(data.lastSync).toLocaleTimeString('pt-PT')}</span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(data?.projects || fallback.projects).map((p) => (
                <div key={p.name} className="flex items-center gap-4">
                  <div className="w-20 text-sm font-medium text-slate-700">{p.name}</div>
                  <div className="flex-1 h-2 rounded-full bg-slate-100">
                    <div className={`h-2 rounded-full transition-all ${scoreBar(p.score)}`} style={{ width: `${p.score}%` }} />
                  </div>
                  <div className={`w-12 text-right text-sm font-semibold ${scoreColor(p.score)}`}>{p.score}</div>
                  <div className={`text-sm ${trendColor(p.trend)}`}>{trendIcon(p.trend)}</div>
                  <div className="text-xs text-slate-400 w-16 text-right">{p.done}/{p.open + p.done || p.open}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Team Status */}
        <Card className="bg-white">
          <CardHeader><CardTitle className="text-base">Team Status</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(data?.teamStatus || fallback.teamStatus).map((m) => (
                <div key={m.name} className="flex items-center gap-3">
                  <div className="relative">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-slate-200 text-slate-600 text-xs">{m.avatar}</AvatarFallback>
                    </Avatar>
                    <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${statusColor(m.status)}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{m.name}</p>
                    <p className="text-xs text-slate-500">{m.role}</p>
                  </div>
                  <Badge variant={m.status === 'ooo' ? 'default' : 'secondary'} className="text-xs">
                    {m.status === 'ooo' ? 'OOO' : 'Active'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Agent Activity */}
      <Card className="bg-white">
        <CardHeader><CardTitle className="text-base">Recent Agent Activity</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {recentActivity.map((a, i) => (
              <div key={i} className="flex items-start gap-3 py-2">
                <span className="text-slate-400 text-xs font-mono w-10">{a.time}</span>
                <div className="w-0.5 h-full min-h-[20px] bg-slate-200 rounded-full self-center mr-2" />
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs font-mono">Axemaster</Badge>
                  <span className="text-xs text-slate-500">{a.action}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}