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
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-3">
              <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl border border-cyan-300/30 bg-cyan-300/10 shadow-[0_0_28px_rgba(34,211,238,0.22)]">
                <span className="absolute inset-0 bg-[linear-gradient(135deg,rgba(34,211,238,0.24),rgba(245,158,11,0.12))]" />
                <span className="relative font-bold tracking-tight text-cyan-100">A</span>
              </div>
              <div className="text-sm font-semibold tracking-wide text-white">Axeng</div>
            </Link>
            <a href="https://maiolabs.ai" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-500 transition hover:text-slate-400">
              by Maio Labs
            </a>
          </div>

          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            {navItems.map((item) => (
              <a key={item.href} href={item.href} className="transition hover:text-cyan-200">
                {item.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <a href="http://localhost:3000" className="hidden text-sm text-slate-400 transition hover:text-white sm:block">
              Open app
            </a>
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

      <section className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <div className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Ships with integrations for</p>
          <div className="mt-10 grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-6">
            <div className="group flex flex-col items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.02] p-5 transition hover:border-cyan-300/20 hover:bg-white/[0.04]">
              <svg className="h-10 w-10 text-slate-400 transition group-hover:scale-110 group-hover:text-slate-200" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <span className="text-xs font-medium text-slate-400 transition group-hover:text-slate-200">GitHub</span>
            </div>
            <div className="group flex flex-col items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.02] p-5 transition hover:border-purple-300/20 hover:bg-white/[0.04]">
              <svg className="h-10 w-10 text-slate-400 transition group-hover:scale-110 group-hover:text-purple-300" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/>
              </svg>
              <span className="text-sm font-medium text-slate-300">Linear</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span className="text-sm font-medium text-slate-300">Google Workspace</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="currentColor">
                <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
              </svg>
              <span className="text-sm font-medium text-slate-300">Slack</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21.198 10.425c-.237-.972-.906-1.636-1.88-1.873.02-.083.039-.167.055-.251.325-1.725-.28-3.445-1.57-4.47l-.323-.255-.256.322c-.604.76-.982 1.68-1.075 2.638a3.888 3.888 0 0 0 .315 2.011c-.485.282-1.019.486-1.586.602-1.14.233-2.321.164-3.41-.2a5.615 5.615 0 0 1-2.415-1.522c-1.263-1.396-1.669-3.23-1.084-4.907l.147-.421-.407-.186C5.83 1.35 4.105 1.515 2.82 2.653 1.535 3.79.948 5.51 1.2 7.207c.254 1.697 1.383 3.101 2.987 3.723a3.757 3.757 0 0 0 1.445.294c.23 0 .459-.022.685-.066.02-.004.04-.007.059-.01.018.118.042.235.074.35.237.972.906 1.636 1.88 1.873-.02.084-.039.168-.055.252-.325 1.725.28 3.444 1.57 4.469l.323.255.256-.322c.604-.76.982-1.68 1.075-2.638a3.888 3.888 0 0 0-.315-2.011c.485-.282 1.019-.486 1.586-.602 1.14-.233 2.321-.164 3.41.2a5.615 5.615 0 0 1 2.415 1.522c1.263 1.396 1.669 3.23 1.084 4.907l-.147.421.407.186c1.879.857 3.604.692 4.889-.446 1.285-1.137 1.872-2.857 1.62-4.554z"/>
              </svg>
              <span className="text-sm font-medium text-slate-300">Telegram</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 22C6.486 22 2 17.514 2 12S6.486 2 12 2s10 4.486 10 10-4.486 10-10 10zm1-17h-2v2H9v2h2v2h2v-2h2V7h-2V5z"/>
              </svg>
              <span className="text-sm font-medium text-slate-300">Obsidian</span>
            </div>
          </div>
          <p className="mt-6 text-sm text-slate-500">
            Need more integrations?{' '}
            <a href="https://maiolabs.ai" target="_blank" rel="noopener noreferrer" className="text-cyan-300 transition hover:text-cyan-200">
              Maio Labs
            </a>{' '}
            can build custom connectors for your stack.
          </p>
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
            <a href="http://localhost:3000" className="inline-flex items-center justify-center gap-2 rounded-full border border-white/12 px-6 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/[0.06]">
              Open dashboard
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 px-5 py-10 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-300/10 text-cyan-100">A</div>
              <span className="font-semibold text-white">Axeng</span>
              <a href="https://maiolabs.ai" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-500 transition hover:text-slate-400">
                by Maio Labs
              </a>
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
