import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Bot, Link2, Clock, Key, CheckCircle2, AlertTriangle,
  ChevronRight, ExternalLink, RefreshCw, Shield,
} from 'lucide-react'

const llmProviders = [
  { id: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-4-20250514', status: 'connected', color: 'from-orange-500 to-red-500' },
  { id: 'openrouter', name: 'OpenRouter', model: 'anthropic/claude-sonnet-4', status: 'connected', color: 'from-blue-500 to-indigo-500' },
  { id: 'openai', name: 'OpenAI', model: 'gpt-4o', status: 'not_configured', color: 'from-green-400 to-emerald-500' },
  { id: 'google', name: 'Google AI', model: 'gemini-2.0-flash', status: 'not_configured', color: 'from-yellow-400 to-orange-500' },
]

const integrations = [
  { name: 'Linear', desc: 'Issue tracking & project management', status: 'connected', icon: '●', color: 'text-blue-500', lastSync: '2026-05-10T09:38:00' },
  { name: 'GitHub', desc: 'PRs, repos, contributors', status: 'connected', icon: '◆', color: 'text-slate-700', lastSync: '2026-05-10T09:30:00' },
  { name: 'Telegram', desc: 'Briefings & notifications', status: 'connected', icon: '▶', color: 'text-sky-500', lastSync: '2026-05-10T09:42:00' },
  { name: 'Google Calendar', desc: 'Events & OOO detection', status: 'connected', icon: '◻', color: 'text-rose-500', lastSync: '2026-05-10T09:00:00' },
  { name: 'Obsidian', desc: 'Session logs & team notes', status: 'connected', icon: '◈', color: 'text-purple-500', lastSync: '2026-05-10T09:45:00' },
  { name: 'Google Chat', desc: 'Team notifications', status: 'warning', icon: '◉', color: 'text-amber-500', lastSync: '2026-05-09T17:00:00' },
]

const cronJobs = [
  { name: 'Daily Standup Brief', schedule: '07:30 Mon–Fri', lastRun: '2026-05-09T07:30:00', status: 'active' },
  { name: 'Team Intel Daily Sync', schedule: '07:00 daily', lastRun: '2026-05-10T07:01:00', status: 'active' },
  { name: 'Sprint Health', schedule: '16:00 Fridays', lastRun: '2026-05-09T16:00:00', status: 'active' },
  { name: 'Risk Radar', schedule: '16:00 Fridays', lastRun: '2026-05-09T16:00:00', status: 'active' },
  { name: 'Weekly Team Report', schedule: '07:00 Fridays', lastRun: '2026-05-09T07:00:00', status: 'active' },
  { name: "Sir's Daily Briefing", schedule: '08:00 daily', lastRun: null, status: 'paused' },
]

function formatLastSync(ts: string) {
  const d = new Date(ts)
  return d.toLocaleString('pt-PT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

const tabs = [
  { value: 'llm', label: 'LLM', icon: Bot },
  { value: 'integrations', label: 'Integrações', icon: Link2 },
  { value: 'cron', label: 'Cron Jobs', icon: Clock },
  { value: 'api', label: 'API Keys', icon: Key },
]

function activeStatus(name: string, fallback: string, toggled?: string) {
  return toggled === name ? (fallback === 'active' ? 'paused' : 'active') : fallback
}

export default async function SettingsPage({ searchParams }: { searchParams: Promise<{ tab?: string; toggle?: string }> }) {
  const params = await searchParams
  const activeTab = tabs.some(t => t.value === params.tab) ? params.tab! : 'llm'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight"><span className="gradient-text">Settings</span></h1>
        <p className="text-muted-foreground text-sm mt-1">Configuração do Axeng · integrações · cron jobs</p>
      </div>

      <div className="glass inline-flex flex-wrap gap-1 p-1 h-auto bg-transparent border border-border/40 rounded-xl">
        {tabs.map(t => { const Icon = t.icon; const selected = activeTab === t.value; return (
          <Link key={t.value} href={`/settings?tab=${t.value}`} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${selected ? 'glass nav-active text-white border-indigo-400/30' : 'text-muted-foreground hover:text-foreground'}`}>
            <Icon className="w-3.5 h-3.5" /><span className="hidden sm:inline">{t.label}</span>
          </Link>
        )})}
      </div>

      {activeTab === 'llm' && <div className="grid gap-3 sm:grid-cols-2">{llmProviders.map(p => <Card key={p.id} className="glass glass-hover border-border/40 overflow-hidden"><CardContent className="p-4"><div className="flex items-start justify-between gap-3"><div className="flex items-center gap-3 min-w-0"><div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${p.color} flex items-center justify-center shadow-lg shrink-0`}><Bot className="w-5 h-5 text-white" /></div><div className="min-w-0"><p className="font-semibold text-sm truncate">{p.name}</p><p className="text-xs text-muted-foreground font-mono truncate">{p.model}</p></div></div><Badge className={`text-xs font-medium ${p.status === 'connected' ? 'badge-glow text-white border-0' : 'bg-secondary text-muted-foreground border-border'}`}>{p.status === 'connected' ? <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Connected</span> : 'Not configured'}</Badge></div>{p.status === 'connected' && <div className="mt-3 flex items-center justify-between"><span className="text-xs text-muted-foreground">Provider active</span><Link href="/settings?tab=api" className="inline-flex items-center h-7 text-xs gap-1 text-indigo-600 hover:text-indigo-700">Configure <ChevronRight className="w-3 h-3" /></Link></div>}</CardContent></Card>)}</div>}

      {activeTab === 'integrations' && <div className="space-y-3">{integrations.map(i => <Card key={i.name} className="glass glass-hover border-border/40 overflow-hidden"><CardContent className="p-4"><div className="flex items-center justify-between gap-3"><div className="flex items-center gap-3 min-w-0"><div className={`w-9 h-9 rounded-lg bg-secondary flex items-center justify-center ${i.color}`}><span className="text-sm font-bold">{i.icon}</span></div><div className="min-w-0"><p className="font-medium text-sm">{i.name}</p><p className="text-xs text-muted-foreground">{i.desc}</p></div></div><div className="flex items-center gap-3 shrink-0"><div className="text-right hidden sm:block">{i.status === 'connected' ? <div className="flex items-center gap-1.5 text-xs font-medium text-green-600"><CheckCircle2 className="w-3.5 h-3.5" /> Connected <span className="text-muted-foreground font-normal">· {formatLastSync(i.lastSync)}</span></div> : <div className="flex items-center gap-1.5 text-xs font-medium text-amber-600"><AlertTriangle className="w-3.5 h-3.5" /> Warning <span className="text-muted-foreground font-normal">· {formatLastSync(i.lastSync)}</span></div>}</div><Link href="/settings?tab=api" className="inline-flex items-center px-3 h-8 text-xs rounded-lg border border-border/40 glass-hover">Manage</Link></div></div></CardContent></Card>)}</div>}

      {activeTab === 'cron' && <div className="space-y-3">{cronJobs.map(j => { const status = activeStatus(j.name, j.status, params.toggle); return <Card key={j.name} className="glass glass-hover border-border/40 overflow-hidden"><CardContent className="p-4"><div className="flex items-center justify-between gap-3"><div className="flex items-center gap-4 min-w-0"><div className={`w-2.5 h-2.5 rounded-full shrink-0 ${status === 'active' ? 'bg-green-500 animate-pulse shadow-lg shadow-green-500/40' : 'bg-slate-400'}`} /><div className="min-w-0"><p className="font-medium text-sm">{j.name}</p><p className="text-xs text-muted-foreground font-mono">{j.schedule}</p></div></div><div className="flex items-center gap-3 shrink-0">{j.lastRun ? <span className="text-xs text-muted-foreground hidden sm:block">{formatLastSync(j.lastRun)}</span> : <span className="text-xs text-muted-foreground hidden sm:block">Nunca executado</span>}<Link href={`/settings?tab=cron&toggle=${encodeURIComponent(j.name)}`} className={`inline-flex items-center px-3 h-8 text-xs rounded-lg border glass-hover ${status === 'active' ? 'border-border/40' : 'badge-glow text-white border-0'}`}>{status === 'active' ? <><RefreshCw className="w-3 h-3 mr-1" /> Pause</> : 'Resume'}</Link></div></div></CardContent></Card> })}</div>}

      {activeTab === 'api' && <div className="space-y-3"><Card className="glass border-border/40 overflow-hidden"><CardHeader className="pb-3"><div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center"><Shield className="w-4 h-4 text-indigo-600" /></div><div><CardTitle className="text-base">API Keys</CardTitle><p className="text-xs text-muted-foreground">As tuas chaves estão seguras — nunca são expostas na UI</p></div></div></CardHeader><CardContent className="space-y-3">{[{ name: 'Linear API Key', key: 'lin_api_••••••••', hint: 'linear.app/settings/api' }, { name: 'GitHub Token', key: 'ghp_••••••••••••', hint: 'github.com/settings/tokens' }, { name: 'Anthropic API Key', key: 'sk-ant-••••••••••••', hint: 'anthropic.com/api' }].map(k => <div key={k.name} className="flex items-center justify-between p-3 rounded-xl bg-secondary/50 border border-border/30"><div><p className="font-medium text-sm">{k.name}</p><p className="text-xs text-muted-foreground font-mono">{k.key}</p></div><div className="flex gap-2"><a href={`https://${k.hint}`} target="_blank" rel="noopener" className="inline-flex items-center px-3 h-7 text-xs rounded-lg border border-border/40 glass-hover">Update</a><a href={`https://${k.hint}`} target="_blank" rel="noopener" className="inline-flex items-center justify-center h-7 w-7 rounded-lg hover:bg-secondary"><ExternalLink className="w-3.5 h-3.5 text-muted-foreground" /></a></div></div>)}</CardContent></Card><p className="text-xs text-muted-foreground text-center">Todas as chaves são guardadas em <code className="bg-secondary px-1.5 py-0.5 rounded text-foreground font-mono text-[11px]">~/.hermes/.env</code> e <code className="bg-secondary px-1.5 py-0.5 rounded text-foreground font-mono text-[11px]">config/config.yaml</code> — nunca em código.</p></div>}
    </div>
  )
}
