import Link from 'next/link'
import {
  Activity,
  ArrowRight,
  BellRing,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  GitPullRequest,
  LineChart,
  Lock,
  MessageSquareText,
  Radar,
  ShieldCheck,
  Sparkles,
  Terminal,
  Users,
  Zap,
} from 'lucide-react'

const navItems = [
  { label: 'Signal', href: '#signal' },
  { label: 'Capabilities', href: '#capabilities' },
  { label: 'Workflow', href: '#workflow' },
  { label: 'Results', href: '#results' },
]

const proofPoints = [
  'Daily standups from GitHub + Linear',
  '1:1 pre-reads from calendar + notes',
  'Self-hosted, open source, no lock-in',
]

const signals = [
  {
    title: 'Status is scattered',
    body: 'GitHub, Linear, calendar, meeting notes, and chat all hold fragments of the truth. Managers spend the morning stitching it together.',
  },
  {
    title: 'Risks surface too late',
    body: 'Blocked issues, stale PRs, sprint drift, and overloaded engineers become visible only after delivery has already slipped.',
  },
  {
    title: 'Operating rhythm is manual',
    body: 'Standups, team reports, 1:1 prep, OOO tracking, and offboarding are repetitive coordination work masquerading as leadership.',
  },
]

const capabilities = [
  {
    icon: GitPullRequest,
    title: 'GitHub shipped summaries',
    body: 'Merged PRs are treated as the primary delivery signal, with direct commits as fallback context and per-developer achievement summaries.',
  },
  {
    icon: LineChart,
    title: 'Sprint and DORA intelligence',
    body: 'Track sprint health, delivery flow, review bottlenecks, lead time, deployment frequency, and team throughput from operational data.',
  },
  {
    icon: CalendarDays,
    title: 'Meeting and 1:1 preparation',
    body: 'Generate concise pre-reads using calendar context, team memory, recent work, action items, and meeting notes.',
  },
  {
    icon: BellRing,
    title: 'Executive briefings',
    body: 'Daily standups, end-of-day digests, weekly reports, and risk alerts delivered where the team already works.',
  },
  {
    icon: ShieldCheck,
    title: 'Operational governance',
    body: 'Offboarding workflows, vacation tracking, team reports, stale project detection, and evidence-backed management rituals.',
  },
  {
    icon: Lock,
    title: 'Local-first deployment',
    body: 'Runs on your machine or a small server. Bring your own GitHub, Linear, Google Workspace, Telegram, and LLM provider.',
  },
]

const workflow = [
  ['Observe', 'Ingest signals from GitHub, Linear, Google Workspace, chat, Granola, and Obsidian.'],
  ['Reason', 'Map activity to people, projects, risks, blockers, and delivery outcomes.'],
  ['Brief', 'Produce Telegram-ready standups, reports, 1:1 pre-reads, and decision summaries.'],
  ['Act', 'Create issues, manage offboarding, update notes, send reports, and keep the operating system current.'],
]

const commands = [
  ['axeng standup', 'Generate today’s engineering standup brief'],
  ['axeng pr-health', 'Find stale PRs and review bottlenecks'],
  ['axeng prep Rui', 'Prepare a 1:1 pre-read'],
  ['axeng report --weekly --send', 'Build and send the weekly team report'],
]

export default function AxengWebsitePage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#05070d] text-slate-100">
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(17,94,89,0.32),transparent_34%),radial-gradient(circle_at_78%_18%,rgba(245,158,11,0.16),transparent_28%),linear-gradient(180deg,#05070d_0%,#071018_45%,#030507_100%)]" />
        <div className="absolute inset-0 opacity-[0.18] [background-image:linear-gradient(rgba(148,163,184,0.16)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.16)_1px,transparent_1px)] [background-size:56px_56px]" />
        <div className="absolute left-1/2 top-16 h-[420px] w-[720px] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-3xl" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#05070d]/72 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
          <Link href="/website" className="flex items-center gap-3">
            <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl border border-cyan-300/30 bg-cyan-300/10 shadow-[0_0_28px_rgba(34,211,238,0.22)]">
              <span className="absolute inset-0 bg-[linear-gradient(135deg,rgba(34,211,238,0.24),rgba(245,158,11,0.12))]" />
              <span className="relative font-bold tracking-tight text-cyan-100">A</span>
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">Axeng</div>
              <div className="text-[11px] uppercase tracking-[0.22em] text-cyan-200/70">Engineering OS</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            {navItems.map((item) => (
              <a key={item.href} href={item.href} className="transition hover:text-cyan-200">
                {item.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <Link href="/" className="hidden text-sm text-slate-400 transition hover:text-white sm:block">
              Open app
            </Link>
            <a
              href="https://github.com/ruimachado-orbit/axeng"
              className="rounded-full border border-cyan-300/30 bg-cyan-300/10 px-4 py-2 text-sm font-medium text-cyan-100 shadow-[0_0_24px_rgba(34,211,238,0.14)] transition hover:bg-cyan-300/16"
            >
              View GitHub
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl flex-col items-center justify-center px-5 py-20 text-center sm:px-8">
        <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-white/[0.04] px-3 py-1.5 text-xs font-medium uppercase tracking-[0.22em] text-cyan-100">
          <span className="h-2 w-2 rounded-full bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,0.9)]" />
          Engineering Intelligence Online
        </div>

        <h1 className="max-w-5xl text-balance text-5xl font-semibold tracking-[-0.06em] text-white sm:text-7xl lg:text-8xl">
          Stop managing status. <span className="bg-gradient-to-r from-cyan-200 via-teal-200 to-amber-200 bg-clip-text text-transparent">Start shipping.</span>
        </h1>

        <p className="mt-7 max-w-3xl text-pretty text-lg leading-8 text-slate-300 sm:text-xl">
          Axeng is an autonomous AI chief of staff for engineering leaders. It watches the operational signals across GitHub, Linear, calendar, meeting notes, and team memory — then turns them into briefings, risks, reports, and actions.
        </p>

        <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <a
            href="#workflow"
            className="group inline-flex items-center gap-2 rounded-full bg-cyan-200 px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_0_42px_rgba(34,211,238,0.24)] transition hover:bg-cyan-100"
          >
            Explore the system <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </a>
          <a
            href="#capabilities"
            className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.03] px-6 py-3 text-sm font-medium text-slate-200 transition hover:border-white/24 hover:bg-white/[0.06]"
          >
            See capabilities
          </a>
        </div>

        <div className="mt-9 flex flex-col gap-3 text-sm text-slate-300 sm:flex-row sm:items-center sm:gap-6">
          {proofPoints.map((point) => (
            <div key={point} className="flex items-center justify-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-300" />
              {point}
            </div>
          ))}
        </div>

        <div className="mt-16 w-full max-w-5xl rounded-[2rem] border border-white/10 bg-slate-950/70 p-3 text-left shadow-2xl shadow-cyan-950/30 backdrop-blur-xl">
          <div className="rounded-[1.4rem] border border-white/8 bg-[#070b12] p-4 sm:p-6">
            <div className="mb-4 flex items-center justify-between border-b border-white/8 pb-4">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Terminal className="h-4 w-4 text-cyan-300" />
                axeng terminal
              </div>
              <div className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2.5 py-1 text-xs text-emerald-200">live signals</div>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {commands.map(([command, output]) => (
                <div key={command} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <code className="text-sm text-cyan-200">$ {command}</code>
                  <p className="mt-2 text-sm text-slate-400">{output}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="signal" className="mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-amber-200">The real problem</p>
            <h2 className="mt-4 max-w-2xl text-4xl font-semibold tracking-[-0.04em] text-white sm:text-6xl">
              Engineering leadership has too much signal and not enough operating system.
            </h2>
          </div>
          <p className="text-lg leading-8 text-slate-300">
            Axeng does not replace judgment. It removes the repetitive collection, synthesis, and follow-up work that keeps engineering leaders away from decisions only they can make.
          </p>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {signals.map((item, index) => (
            <div key={item.title} className="rounded-[1.6rem] border border-white/10 bg-white/[0.035] p-6 backdrop-blur transition hover:border-cyan-300/25 hover:bg-white/[0.055]">
              <div className="mb-8 text-sm text-cyan-200/80">0{index + 1}</div>
              <h3 className="text-xl font-semibold text-white">{item.title}</h3>
              <p className="mt-3 leading-7 text-slate-400">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="capabilities" className="mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-200">Capabilities</p>
          <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-white sm:text-6xl">
            Built for the rituals that make teams move.
          </h2>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((item) => {
            const Icon = item.icon
            return (
              <div key={item.title} className="group rounded-[1.6rem] border border-white/10 bg-slate-950/58 p-6 transition hover:-translate-y-1 hover:border-cyan-300/30 hover:bg-slate-900/70">
                <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-200 shadow-[0_0_24px_rgba(34,211,238,0.1)]">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                <p className="mt-3 leading-7 text-slate-400">{item.body}</p>
              </div>
            )
          })}
        </div>
      </section>

      <section id="workflow" className="mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <div className="rounded-[2.2rem] border border-white/10 bg-white/[0.035] p-6 backdrop-blur-xl sm:p-8 lg:p-10">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-amber-200">Workflow</p>
              <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl">
                From scattered activity to executive-ready action.
              </h2>
              <p className="mt-5 leading-8 text-slate-300">
                The product pattern mirrors how strong engineering managers already operate: observe the system, reason from evidence, brief the team, and act decisively.
              </p>
            </div>
            <div className="relative">
              <div className="absolute left-6 top-6 hidden h-[calc(100%-3rem)] w-px bg-gradient-to-b from-cyan-300 via-teal-300 to-amber-200 md:block" />
              <div className="space-y-4">
                {workflow.map(([step, body], index) => (
                  <div key={step} className="relative rounded-3xl border border-white/10 bg-[#05070d]/70 p-5 md:ml-12">
                    <div className="mb-4 inline-flex items-center gap-3">
                      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-200 text-sm font-bold text-slate-950 shadow-[0_0_28px_rgba(34,211,238,0.24)]">{index + 1}</span>
                      <h3 className="text-xl font-semibold text-white">{step}</h3>
                    </div>
                    <p className="leading-7 text-slate-400">{body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="results" className="mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <div className="grid gap-4 md:grid-cols-4">
          {[
            ['30–45 min/day', 'saved on recurring engineering management rituals'],
            ['24/7', 'monitoring from a local machine or server'],
            ['GPL-3.0', 'open source, auditable, and self-hosted'],
            ['$200 Mac Mini', 'enough to run a real engineering command center'],
          ].map(([value, label]) => (
            <div key={value} className="rounded-[1.6rem] border border-white/10 bg-white/[0.035] p-6">
              <div className="text-3xl font-semibold tracking-[-0.04em] text-white">{value}</div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-5 py-24 text-center sm:px-8">
        <div className="rounded-[2rem] border border-cyan-300/20 bg-cyan-300/[0.06] px-6 py-12 shadow-[0_0_80px_rgba(34,211,238,0.12)]">
          <Sparkles className="mx-auto h-8 w-8 text-cyan-200" />
          <h2 className="mt-5 text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl">Build an engineering operating layer that does not forget.</h2>
          <p className="mx-auto mt-5 max-w-2xl leading-8 text-slate-300">
            Install locally, connect the sources your team already uses, and let Axeng turn operational noise into a daily execution rhythm.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <a href="https://github.com/ruimachado-orbit/axeng" className="inline-flex items-center justify-center gap-2 rounded-full bg-cyan-200 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100">
              Get Axeng <ChevronRight className="h-4 w-4" />
            </a>
            <Link href="/" className="inline-flex items-center justify-center gap-2 rounded-full border border-white/12 px-6 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/[0.06]">
              Open dashboard
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 px-5 py-10 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3 text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-300/10 text-cyan-100">A</div>
              <span className="font-semibold">Axeng</span>
            </div>
            <p className="mt-3 max-w-md text-sm leading-6 text-slate-500">
              Autonomous engineering intelligence for leaders who need evidence, rhythm, and execution — not another dashboard to babysit.
            </p>
          </div>
          <div className="flex flex-wrap gap-4 text-sm text-slate-400">
            <a href="#signal" className="hover:text-cyan-200">Signal</a>
            <a href="#capabilities" className="hover:text-cyan-200">Capabilities</a>
            <a href="#workflow" className="hover:text-cyan-200">Workflow</a>
            <a href="https://github.com/ruimachado-orbit/axeng" className="hover:text-cyan-200">GitHub</a>
          </div>
        </div>
      </footer>
    </main>
  )
}
