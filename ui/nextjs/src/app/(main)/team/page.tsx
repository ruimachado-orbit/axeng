import Link from 'next/link'
import { Card, CardContent } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { Generate1on1Button } from '@/components/generate-1on1-button'
import {
  Grid2X2, List, GitBranch, Clock
} from 'lucide-react'

const teamMembers = [
  { id: '1', name: 'Alice Silva', role: 'Backend Engineer', email: 'alice@example.com', status: 'active', github: 'alice-dev', linear: 'alice.silva', avatar: 'AS', skills: ['Python', 'FastAPI', 'PostgreSQL'], activeProjects: ['Project A', 'Project B'], openIssues: 12, prsOpen: 3, lastActivity: new Date().toISOString() },
  { id: '2', name: 'Bob Santos', role: 'DevOps / Infra', email: 'bob@example.com', status: 'active', github: 'bob-devops', linear: 'bob.santos', avatar: 'BS', skills: ['Kubernetes', 'Terraform', 'AWS'], activeProjects: ['Project C', 'Project A'], openIssues: 8, prsOpen: 2, lastActivity: new Date().toISOString() },
  { id: '3', name: 'Carol Chen', role: 'Frontend Engineer', email: 'carol@example.com', status: 'active', github: 'carol-fe', linear: 'carol.chen', avatar: 'CC', skills: ['React', 'Next.js', 'TypeScript'], activeProjects: ['Project B', 'Project D'], openIssues: 10, prsOpen: 4, lastActivity: new Date().toISOString() },
  { id: '4', name: 'Daniel Kumar', role: 'ML / AI Engineer', email: 'daniel@example.com', status: 'active', github: 'daniel-ml', linear: 'daniel.kumar', avatar: 'DK', skills: ['PyTorch', 'MLOps', 'LLMs'], activeProjects: ['Project E', 'Project F'], openIssues: 9, prsOpen: 2, lastActivity: new Date().toISOString() },
  { id: '5', name: 'Eve Johnson', role: 'Engineering Manager', email: 'eve@example.com', status: 'active', github: 'eve-em', linear: 'eve.johnson', avatar: 'EJ', skills: ['Leadership', 'System Design', 'Agile'], activeProjects: [], openIssues: 3, prsOpen: 0, lastActivity: new Date().toISOString() },
]

const statusConfig = {
  active: { label: 'Ativo', dot: 'bg-emerald-500', badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' },
  ooo:   { label: 'OOO',   dot: 'bg-amber-400',   badge: 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400' },
}

const avatarGradients = ['from-indigo-500 to-purple-600', 'from-blue-500 to-cyan-600', 'from-pink-500 to-rose-600', 'from-amber-500 to-orange-600', 'from-emerald-500 to-teal-600', 'from-violet-500 to-fuchsia-600', 'from-cyan-500 to-blue-600']

function formatLastSeen(ts: string) {
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `Há ${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `Há ${hours}h`
  return `Há ${Math.floor(hours / 24)}d`
}

function firstName(name: string) {
  return name.split(' ')[0].toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

export default async function TeamPage({ searchParams }: { searchParams: Promise<{ view?: string; member?: string }> }) {
  const params = await searchParams
  const view = params.view === 'table' ? 'table' : 'cards'
  const selected = params.member || ''
  const activeCount = teamMembers.filter(m => m.status === 'active').length
  const oooCount = teamMembers.filter(m => m.status === 'ooo').length
  const selectedMember = teamMembers.find(m => m.id === selected)

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-2xl font-bold tracking-tight"><span className="gradient-text">Team</span></h1>
        <p className="text-muted-foreground text-sm mt-1">Estado da equipa · assignments · atividade</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total', value: teamMembers.length, color: 'text-foreground' },
          { label: 'Ativos', value: activeCount, color: 'text-emerald-600' },
          { label: 'OOO', value: oooCount, color: 'text-amber-600' },
        ].map(s => (
          <Card key={s.label} className="glass border-border/40 overflow-hidden"><CardContent className="p-4"><div className={`text-2xl font-bold ${s.color}`}>{s.value}</div><div className="text-xs text-muted-foreground mt-1">{s.label}</div></CardContent></Card>
        ))}
      </div>

      <div className="flex gap-2">
        <Link href="/team?view=cards" className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all glass-hover border ${view === 'cards' ? 'nav-active text-white border-indigo-400/30' : 'glass border-border/40 text-muted-foreground'}`}>
          <Grid2X2 className="w-3.5 h-3.5" /> Cards
        </Link>
        <Link href="/team?view=table" className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all glass-hover border ${view === 'table' ? 'nav-active text-white border-indigo-400/30' : 'glass border-border/40 text-muted-foreground'}`}>
          <List className="w-3.5 h-3.5" /> Tabela
        </Link>
      </div>

      {view === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {teamMembers.map((member, i) => {
            const cfg = statusConfig[member.status as keyof typeof statusConfig]
            const grad = avatarGradients[i % avatarGradients.length]
            return (
              <Link key={member.id} href={`/team?view=cards&member=${member.id}`} className={`glass glass-hover border-border/40 cursor-pointer overflow-hidden transition-all rounded-xl block ${selected === member.id ? 'ring-2 ring-indigo-500 border-indigo-400/40' : ''}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <Avatar className="w-11 h-11 ring-2 ring-border/40"><AvatarFallback className={`bg-gradient-to-br ${grad} text-white text-sm font-bold shadow-lg`}>{member.avatar}</AvatarFallback></Avatar>
                      <div className="min-w-0"><p className="font-semibold text-sm truncate">{member.name}</p><p className="text-xs text-muted-foreground truncate">{member.role}</p></div>
                    </div>
                    <div className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${cfg.badge}`}><span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />{cfg.label}</div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    {[{ v: member.openIssues, label: 'Issues', color: 'text-foreground' }, { v: member.prsOpen, label: 'PRs', color: 'text-indigo-600' }, { v: formatLastSeen(member.lastActivity), label: 'Ativo', color: 'text-muted-foreground', small: true }].map(item => (
                      <div key={item.label} className="text-center bg-secondary/50 rounded-lg py-2 px-1"><div className={`font-bold ${item.small ? 'text-[11px]' : 'text-lg'} ${item.color}`}>{item.v}</div><div className="text-[10px] text-muted-foreground">{item.label}</div></div>
                    ))}
                  </div>
                  {member.activeProjects.length > 0 && <div className="flex gap-1.5 flex-wrap">{member.activeProjects.map(p => <span key={p} className="text-[11px] bg-indigo-50 text-indigo-600 dark:bg-indigo-950/30 dark:text-indigo-400 px-2 py-0.5 rounded-full font-medium">{p}</span>)}</div>}
                  {member.status === 'ooo' && 'oooUntil' in member && member.oooUntil && <p className="text-xs text-amber-600 mt-2 flex items-center gap-1"><Clock className="w-3 h-3" /> Volta: {new Date(member.oooUntil).toLocaleDateString('pt-PT')}</p>}
                </CardContent>
              </Link>
            )
          })}
        </div>
      )}

      {view === 'table' && (
        <Card className="glass border-border/40 overflow-hidden"><div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b border-border/40">{['Membro', 'Estado', 'Issues', 'PRs', 'Projetos', 'Última atividade'].map(h => <th key={h} className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase tracking-wider">{h}</th>)}</tr></thead><tbody>{teamMembers.map((m, i) => { const cfg = statusConfig[m.status as keyof typeof statusConfig]; const grad = avatarGradients[i % avatarGradients.length]; return <tr key={m.id} className="border-b border-border/20 hover:bg-secondary/30 transition-colors"><td className="py-3 px-4"><Link href={`/team?view=table&member=${m.id}`} className="flex items-center gap-3"><Avatar className="w-7 h-7"><AvatarFallback className={`bg-gradient-to-br ${grad} text-white text-[10px] font-bold`}>{m.avatar}</AvatarFallback></Avatar><div><p className="font-medium text-sm">{m.name}</p><p className="text-xs text-muted-foreground">{m.role}</p></div></Link></td><td className="py-3 px-4"><div className={`inline-flex items-center gap-1.5 text-xs font-medium ${cfg.badge} px-2 py-1 rounded-full`}><span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />{cfg.label}</div></td><td className="py-3 px-4 font-semibold text-foreground">{m.openIssues}</td><td className="py-3 px-4 font-semibold text-indigo-600">{m.prsOpen}</td><td className="py-3 px-4"><div className="flex gap-1 flex-wrap">{m.activeProjects.map(p => <span key={p} className="text-xs bg-secondary text-muted-foreground px-1.5 py-0.5 rounded">{p}</span>)}</div></td><td className="py-3 px-4 text-xs text-muted-foreground">{formatLastSeen(m.lastActivity)}</td></tr> })}</tbody></table></div></Card>
      )}

      {selectedMember && (
        <Card className="glass border-indigo-400/30 overflow-hidden" id="member-detail"><CardContent className="p-5">
          <div className="flex items-start justify-between mb-4"><div className="flex items-center gap-4"><Avatar className="w-12 h-12 ring-2 ring-indigo-500/30"><AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-lg font-bold">{selectedMember.avatar}</AvatarFallback></Avatar><div><h3 className="font-bold text-lg">{selectedMember.name}</h3><p className="text-sm text-muted-foreground">{selectedMember.role}</p></div></div><div className={`inline-flex items-center gap-1.5 text-sm font-medium ${statusConfig[selectedMember.status as keyof typeof statusConfig].badge} px-3 py-1.5 rounded-full`}><span className={`w-2 h-2 rounded-full ${statusConfig[selectedMember.status as keyof typeof statusConfig].dot}`} />{statusConfig[selectedMember.status as keyof typeof statusConfig].label}</div></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">{[{ v: selectedMember.openIssues, label: 'Issues abertas' }, { v: selectedMember.prsOpen, label: 'PRs abertos' }, { v: selectedMember.activeProjects.length, label: 'Projetos' }, { v: formatLastSeen(selectedMember.lastActivity), label: 'Última atividade', small: true }].map(item => <div key={item.label} className="text-center rounded-xl p-3 bg-secondary/50"><div className={`font-bold ${item.small ? 'text-xs' : 'text-xl'} text-foreground`}>{item.v}</div><div className="text-[11px] text-muted-foreground mt-0.5">{item.label}</div></div>)}</div>
          <Separator className="my-4" />
          <div className="grid md:grid-cols-3 gap-4"><div><p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Skills</p><div className="flex gap-2 flex-wrap">{selectedMember.skills.map(s => <span key={s} className="text-xs bg-secondary text-foreground px-2.5 py-1 rounded-full border border-border/40">{s}</span>)}</div></div><div><p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Projetos</p><div className="flex gap-2 flex-wrap">{selectedMember.activeProjects.map(p => <span key={p} className="text-xs bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-400 px-2.5 py-1 rounded-full font-medium">{p}</span>)}</div></div><div><p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Links</p><div className="space-y-1">{selectedMember.github && <a href={`https://github.com/${selectedMember.github}`} target="_blank" rel="noopener" className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1"><GitBranch className="w-3 h-3" /> @{selectedMember.github}</a>}<a href={`https://linear.app/workspace/search?q=${encodeURIComponent(selectedMember.linear)}`} target="_blank" rel="noopener" className="text-xs text-purple-500 hover:text-purple-600 flex items-center gap-1"><List className="w-3 h-3" /> {selectedMember.linear}</a></div></div></div>
          <div className="flex gap-3 mt-5"><Generate1on1Button person={selectedMember.name} /><a href={`https://linear.app/workspace/search?q=${encodeURIComponent(selectedMember.linear)}`} target="_blank" rel="noopener" className="inline-flex items-center rounded-lg px-3 py-2 text-xs glass-hover border border-border/40">Ver Linear</a></div>
        </CardContent></Card>
      )}
    </div>
  )
}
