'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'

const teamMembers = [
  { id: '1', name: 'Pedro Ferreira', role: 'Backend Engineer', email: 'pedro.ferreira@maiolabs.ai', status: 'active', github: 'pedroferreira-orbit', linear: 'pedro.ferreira', avatar: 'PF', skills: ['Python', 'FastAPI', 'PostgreSQL'], activeProjects: ['Orbit', 'Compass'], openIssues: 12, prsOpen: 3, lastActivity: '2026-05-10T09:15:00' },
  { id: '2', name: 'Diogo Oliveira', role: 'DevOps / Infra', email: 'diogo.oliveira@maiolabs.ai', status: 'active', github: 'DiogoAntunesOliveira', linear: 'diogo.oliveira', avatar: 'DO', skills: ['Kubernetes', 'Terraform', 'AWS'], activeProjects: ['Heimdall', 'Orbit'], openIssues: 8, prsOpen: 2, lastActivity: '2026-05-10T08:50:00' },
  { id: '3', name: 'Anastasiia Mishchenko', role: 'Frontend Engineer', email: 'anastasiia.mishchenko@orbitplatform.ai', status: 'active', github: 'anastasiia-orbit', linear: 'anastasiia.mishchenko', avatar: 'AM', skills: ['React', 'Next.js', 'TypeScript'], activeProjects: ['Orbit', 'Phoenix'], openIssues: 10, prsOpen: 4, lastActivity: '2026-05-10T09:30:00' },
  { id: '4', name: 'João FCSantos', role: 'Engineering', email: 'joao.fcsantos@orbitplatform.ai', status: 'ooo', github: 'jfcsantos', linear: 'joao.fcsantos', avatar: 'JF', skills: ['Python', 'ML', 'Data'], activeProjects: ['Brain', 'Sagittarius'], openIssues: 15, prsOpen: 1, lastActivity: '2026-05-09T17:00:00', oooUntil: '2026-05-16' },
  { id: '5', name: 'Rikkarth R.', role: 'ML / AI Engineer', email: 'rikkarth@orbitplatform.ai', status: 'active', github: 'rikkarth', linear: 'rikkarth', avatar: 'RR', skills: ['PyTorch', 'MLOps', 'LLMs'], activeProjects: ['Brain', 'Sagittarius', 'WareAI'], openIssues: 9, prsOpen: 2, lastActivity: '2026-05-10T09:00:00' },
  { id: '6', name: 'Daniel Almeida', role: 'CEO', email: 'daniel.almeida@maiolabs.ai', status: 'active', github: '', linear: 'daniel.almeida', avatar: 'DA', skills: ['Leadership', 'Product'], activeProjects: [], openIssues: 3, prsOpen: 0, lastActivity: '2026-05-10T08:00:00' },
  { id: '7', name: 'Luis Santos', role: 'Co-founder', email: 'luis.santos@maiolabs.ai', status: 'active', github: '', linear: 'luis.santos', avatar: 'LS', skills: ['Strategy', 'Growth'], activeProjects: [], openIssues: 2, prsOpen: 0, lastActivity: '2026-05-10T09:45:00' },
]

const statusConfig = {
  active: { label: 'Ativo', dot: 'bg-green-500', badge: 'bg-green-100 text-green-700' },
  ooo: { label: 'Fora de escritório', dot: 'bg-amber-400', badge: 'bg-amber-100 text-amber-700' },
}

function formatLastSeen(ts: string) {
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `Há ${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `Há ${hours}h`
  return `Há ${Math.floor(hours / 24)}d`
}

export default function TeamPage() {
  const [view, setView] = useState<'cards' | 'table'>('cards')
  const [selected, setSelected] = useState<string | null>(null)

  const activeCount = teamMembers.filter(m => m.status === 'active').length
  const oooCount = teamMembers.filter(m => m.status === 'ooo').length

  const selectedMember = teamMembers.find(m => m.id === selected)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Team</h1>
        <p className="text-slate-500 text-sm mt-1">Estado da equipa · assignments · atividade</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-white">
          <CardContent className="pt-4 pb-3">
            <div className="text-2xl font-bold text-slate-900">{teamMembers.length}</div>
            <div className="text-slate-500 text-sm mt-1">Total membros</div>
          </CardContent>
        </Card>
        <Card className="bg-white">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <div className="text-2xl font-bold text-green-700">{activeCount}</div>
            </div>
            <div className="text-slate-500 text-sm mt-1">Ativos</div>
          </CardContent>
        </Card>
        <Card className="bg-white">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <div className="text-2xl font-bold text-amber-700">{oooCount}</div>
            </div>
            <div className="text-slate-500 text-sm mt-1">OOO</div>
          </CardContent>
        </Card>
      </div>

      {/* View toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setView('cards')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === 'cards' ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          Cards
        </button>
        <button
          onClick={() => setView('table')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === 'table' ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          Tabela
        </button>
      </div>

      {/* Team grid */}
      {view === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {teamMembers.map(member => {
            const cfg = statusConfig[member.status as keyof typeof statusConfig]
            return (
              <Card
                key={member.id}
                className={`bg-white cursor-pointer transition-all hover:ring-2 hover:ring-blue-400 ${
                  selected === member.id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelected(selected === member.id ? null : member.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-10 h-10">
                        <AvatarFallback className="bg-blue-600 text-white text-sm">{member.avatar}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-semibold text-slate-900 text-sm">{member.name}</p>
                        <p className="text-xs text-slate-500">{member.role}</p>
                      </div>
                    </div>
                    <div className={`flex items-center gap-1.5 text-xs font-medium ${cfg.badge} px-2 py-1 rounded-full`}>
                      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                      {cfg.label}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="text-center bg-slate-50 rounded-lg py-2">
                      <div className="text-lg font-bold text-slate-900">{member.openIssues}</div>
                      <div className="text-xs text-slate-500">Issues</div>
                    </div>
                    <div className="text-center bg-slate-50 rounded-lg py-2">
                      <div className="text-lg font-bold text-blue-600">{member.prsOpen}</div>
                      <div className="text-xs text-slate-500">PRs</div>
                    </div>
                    <div className="text-center bg-slate-50 rounded-lg py-2">
                      <div className="text-xs font-medium text-slate-700 mt-0.5">{formatLastSeen(member.lastActivity)}</div>
                      <div className="text-xs text-slate-500">Ativo</div>
                    </div>
                  </div>
                  {member.activeProjects.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap">
                      {member.activeProjects.map(p => (
                        <span key={p} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{p}</span>
                      ))}
                    </div>
                  )}
                  {member.status === 'ooo' && member.oooUntil && (
                    <p className="text-xs text-amber-600 mt-2">↩️ Volta: {new Date(member.oooUntil).toLocaleDateString('pt-PT')}</p>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <Card className="bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-3 px-4 font-medium text-slate-500">Membro</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-500">Estado</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-500">Issues</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-500">PRs</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-500">Projetos</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-500">Última atividade</th>
                </tr>
              </thead>
              <tbody>
                {teamMembers.map(m => {
                  const cfg = statusConfig[m.status as keyof typeof statusConfig]
                  return (
                    <tr key={m.id} className="border-b border-slate-50 hover:bg-slate-50 cursor-pointer" onClick={() => setSelected(selected === m.id ? null : m.id)}>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <Avatar className="w-7 h-7">
                            <AvatarFallback className="bg-blue-600 text-white text-xs">{m.avatar}</AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium text-slate-900">{m.name}</p>
                            <p className="text-xs text-slate-400">{m.role}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className={`inline-flex items-center gap-1.5 text-xs font-medium ${cfg.badge} px-2 py-1 rounded-full`}>
                          <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                          {cfg.label}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-700">{m.openIssues}</td>
                      <td className="py-3 px-4 font-semibold text-blue-600">{m.prsOpen}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-1">
                          {m.activeProjects.map(p => (
                            <span key={p} className="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">{p}</span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-400">{formatLastSeen(m.lastActivity)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Member detail panel */}
      {selectedMember && (
        <Card className="bg-white border-blue-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Avatar className="w-12 h-12">
                  <AvatarFallback className="bg-blue-600 text-white text-lg">{selectedMember.avatar}</AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle>{selectedMember.name}</CardTitle>
                  <p className="text-sm text-slate-500">{selectedMember.role}</p>
                </div>
              </div>
              <div className={`inline-flex items-center gap-1.5 text-sm font-medium ${statusConfig[selectedMember.status as keyof typeof statusConfig].badge} px-3 py-1.5 rounded-full`}>
                <span className={`w-2.5 h-2.5 rounded-full ${statusConfig[selectedMember.status as keyof typeof statusConfig].dot}`} />
                {statusConfig[selectedMember.status as keyof typeof statusConfig].label}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-slate-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-slate-900">{selectedMember.openIssues}</div>
                <div className="text-xs text-slate-500 mt-1">Issues abertas</div>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-blue-600">{selectedMember.prsOpen}</div>
                <div className="text-xs text-blue-500 mt-1">PRs abertos</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-slate-900">{selectedMember.activeProjects.length}</div>
                <div className="text-xs text-slate-500 mt-1">Projetos</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 text-center">
                <div className="text-sm font-semibold text-slate-700">{formatLastSeen(selectedMember.lastActivity)}</div>
                <div className="text-xs text-slate-500 mt-1">Última atividade</div>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="space-y-3">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Skills</p>
                <div className="flex gap-2 flex-wrap">
                  {selectedMember.skills.map(s => (
                    <span key={s} className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-full">{s}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Projetos</p>
                <div className="flex gap-2 flex-wrap">
                  {selectedMember.activeProjects.map(p => (
                    <span key={p} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full font-medium">{p}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Links</p>
                <div className="flex gap-3 text-xs">
                  {selectedMember.github && (
                    <span className="text-slate-500">GH: <span className="text-blue-600">@{selectedMember.github}</span></span>
                  )}
                  <span className="text-slate-500">Linear: <span className="text-purple-600">{selectedMember.linear}</span></span>
                  <span className="text-slate-500">Email: <span className="text-slate-700">{selectedMember.email}</span></span>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-5">
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white text-xs">Gerar 1:1 Pre-read</Button>
              <Button size="sm" variant="outline" className="text-xs">Ver Linear</Button>
              <Button size="sm" variant="outline" className="text-xs">Ver GitHub</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}