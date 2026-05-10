'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const llmProviders = [
  { id: 'anthropic', name: 'Anthropic', models: ['claude-sonnet-4', 'claude-opus-4', 'claude-haiku-4'], active: 'claude-sonnet-4', status: 'connected' },
  { id: 'openrouter', name: 'OpenRouter', models: ['anthropic/claude-sonnet-4', 'openai/gpt-4o'], active: 'anthropic/claude-sonnet-4', status: 'connected' },
  { id: 'openai', name: 'OpenAI', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'], active: '', status: 'not_configured' },
  { id: 'google', name: 'Google AI', models: ['gemini-2.0-flash', 'gemini-1.5-pro'], active: '', status: 'not_configured' },
]

const integrations = [
  { name: 'Linear', desc: 'Issue tracking & project management', status: 'connected', icon: '🔵', lastSync: '2026-05-10T09:38:00' },
  { name: 'GitHub', desc: 'PRs, repos, contributors', status: 'connected', icon: '🐙', lastSync: '2026-05-10T09:30:00' },
  { name: 'Telegram', desc: 'Briefings & notifications', status: 'connected', icon: '✈️', lastSync: '2026-05-10T09:42:00' },
  { name: 'Google Calendar', desc: 'Events & OOO detection', status: 'connected', icon: '📅', lastSync: '2026-05-10T09:00:00' },
  { name: 'Obsidian', desc: 'Session logs & team notes', status: 'connected', icon: '💎', lastSync: '2026-05-10T09:45:00' },
  { name: 'Google Chat', desc: 'Team notifications', status: 'warning', icon: '💬', lastSync: '2026-05-09T17:00:00' },
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

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('llm')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Configuração do Axeng · integrações · cron jobs</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white">
          <TabsTrigger value="llm">🤖 LLM</TabsTrigger>
          <TabsTrigger value="integrations">🔗 Integrações</TabsTrigger>
          <TabsTrigger value="cron">⏰ Cron Jobs</TabsTrigger>
          <TabsTrigger value="api">🔑 API Keys</TabsTrigger>
        </TabsList>

        {/* LLM */}
        <TabsContent value="llm" className="mt-4 space-y-4">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-base">LLM Providers</CardTitle>
              <CardDescription>Modelos ativos e configuração</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {llmProviders.map(p => (
                  <div key={p.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-slate-900 text-sm">{p.name}</p>
                        <Badge variant={p.status === 'connected' ? 'default' : 'outline'} className="text-xs">
                          {p.status === 'connected' ? 'Connected' : 'Not configured'}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        {p.active ? `Active: ${p.active}` : 'No model selected'}
                      </p>
                    </div>
                    <Button size="sm" variant="outline" className="text-xs">Configure</Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Integrations */}
        <TabsContent value="integrations" className="mt-4 space-y-4">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-base">Connected Integrations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {integrations.map(i => (
                  <div key={i.name} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{i.icon}</span>
                      <div>
                        <p className="font-medium text-slate-900 text-sm">{i.name}</p>
                        <p className="text-xs text-slate-500">{i.desc}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className={`text-xs font-medium ${
                          i.status === 'connected' ? 'text-green-600' : 'text-amber-600'
                        }`}>
                          {i.status === 'connected' ? '✓ Connected' : '⚠ Warning'}
                        </div>
                        <div className="text-xs text-slate-400">Last sync: {formatLastSync(i.lastSync)}</div>
                      </div>
                      <Button size="sm" variant="outline" className="text-xs">Manage</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cron Jobs */}
        <TabsContent value="cron" className="mt-4 space-y-4">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-base">Scheduled Jobs</CardTitle>
              <CardDescription>Automation timeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {cronJobs.map(j => (
                  <div key={j.name} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50">
                    <div className="flex items-center gap-4">
                      <div className={`w-2.5 h-2.5 rounded-full ${
                        j.status === 'active' ? 'bg-green-500' : 'bg-slate-300'
                      }`} />
                      <div>
                        <p className="font-medium text-slate-900 text-sm">{j.name}</p>
                        <p className="text-xs text-slate-500 font-mono">{j.schedule}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {j.lastRun ? (
                        <span className="text-xs text-slate-400">{formatLastSync(j.lastRun)}</span>
                      ) : (
                        <span className="text-xs text-slate-400">Nunca executado</span>
                      )}
                      <Button size="sm" variant="outline" className="text-xs">
                        {j.status === 'active' ? 'Pause' : 'Resume'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys */}
        <TabsContent value="api" className="mt-4 space-y-4">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-base">API Keys</CardTitle>
              <CardDescription>As tuas chaves estão seguras — nunca são expostas na UI</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: 'Linear API Key', key: 'lin_api_***', hint: 'linear.app/settings/api' },
                  { name: 'GitHub Token', key: 'ghp_***', hint: 'github.com/settings/tokens' },
                  { name: 'Anthropic API Key', key: 'sk-ant-***', hint: 'anthropic.com/api' },
                ].map(k => (
                  <div key={k.name} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900 text-sm">{k.name}</p>
                      <p className="text-xs text-slate-400 font-mono">{k.key}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="text-xs">Update</Button>
                    </div>
                  </div>
                ))}
              </div>
              <Separator className="my-4" />
              <p className="text-xs text-slate-400">Todas as chaves são guardadas em <code className="bg-slate-100 px-1 rounded">~/.hermes/.env</code> e <code className="bg-slate-100 px-1 rounded">config/config.yaml</code> — nunca em código.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}