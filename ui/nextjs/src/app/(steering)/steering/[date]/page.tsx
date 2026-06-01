// CEO Steering — report detail page.
// Renders the stored HTML directly (iframe-isolated) or falls back to
// structured rendering from JSON if HTML is not available.
import Link from 'next/link'
import { notFound } from 'next/navigation'

const API_BASE = process.env.AXENG_API_BASE || 'http://localhost:3457'

interface ProjectCard {
  name: string
  owner: string
  status: 'on_track' | 'at_risk' | 'off_track'
  health_score: number
  target_date: string | null
  days_left: number | null
  time_progress_pct: number
  work_progress_pct: number
  eta_risk: string
  blockers: string[]
  meeting_signal: string | null
  week_delta: string | null
  decision_needed: string | null
}

interface SteeringReport {
  report_id: string
  week_start: string
  week_end: string
  generated_at: string
  portfolio_summary: {
    total_projects: number
    on_track: number
    at_risk: number
    off_track: number
    decisions_needed: number
    top_risk: string
  }
  decisions_needed: Array<{ project: string; owner: string; text: string; status: string }>
  projects: ProjectCard[]
  cross_project_risks: string[]
  capacity_signals: { ooo_this_week: string[] }
  sources: string[]
  errors: string[]
  rendered_html: string | null
}

async function fetchReport(date: string): Promise<SteeringReport | null> {
  // Validate date format before hitting the API
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null
  try {
    const res = await fetch(`${API_BASE}/api/reports/steering/steering-${date}`, {
      cache: 'no-store',
    })
    if (res.status === 404) return null
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

const STATUS_COLOR: Record<string, string> = {
  on_track: '#16a34a',
  at_risk: '#d97706',
  off_track: '#dc2626',
}
const STATUS_LABEL: Record<string, string> = {
  on_track: 'On Track',
  at_risk: 'At Risk',
  off_track: 'Off Track',
}

export default async function SteeringReportPage({
  params,
}: {
  params: Promise<{ date: string }>
}) {
  const { date } = await params
  const report = await fetchReport(date)
  if (!report) notFound()

  // If rendered HTML is available, serve it in a full-page iframe for exact email fidelity
  if (report.rendered_html) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Minimal chrome — back link + download */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '10px 20px',
                      background: '#fff', borderBottom: '1px solid #e5e7eb', flexShrink: 0,
                      fontFamily: 'Arial, sans-serif', fontSize: 12 }}>
          <Link href="/steering" style={{ color: '#6b7280', textDecoration: 'none' }}>
            ← All reports
          </Link>
          <span style={{ color: '#d1d5db' }}>|</span>
          <span style={{ color: '#374151', fontWeight: 600 }}>
            {report.report_id}
          </span>
          <span style={{ color: '#d1d5db' }}>|</span>
          <span style={{ color: '#9ca3af' }}>
            {report.portfolio_summary.total_projects} projects ·{' '}
            {report.portfolio_summary.decisions_needed} decisions
          </span>
          {report.errors?.length > 0 && (
            <>
              <span style={{ color: '#d1d5db' }}>|</span>
              <span style={{ color: '#d97706' }} title={report.errors.join('; ')}>
                ⚠ partial data
              </span>
            </>
          )}
        </div>

        {/* Full-page iframe — renders the email-safe HTML exactly as it appears in Gmail */}
        <iframe
          srcDoc={report.rendered_html}
          style={{ flex: 1, border: 'none', width: '100%' }}
          title={`CEO Steering Report — ${report.week_end}`}
        />
      </div>
    )
  }

  // Fallback: structured JSON render when HTML is not available
  const s = report.portfolio_summary
  return (
    <div style={{ maxWidth: 660, margin: '0 auto', padding: '32px 24px 64px',
                  fontFamily: 'Georgia, serif', color: '#111827' }}>

      {/* Back nav */}
      <Link href="/steering" style={{ fontSize: 12, color: '#6b7280', textDecoration: 'none',
                                       fontFamily: 'Arial, sans-serif' }}>
        ← All reports
      </Link>

      {/* Header */}
      <p style={{ margin: '16px 0 4px', fontSize: 11, color: '#9ca3af',
                  letterSpacing: '0.08em', textTransform: 'uppercase',
                  fontFamily: 'Arial, sans-serif' }}>
        Confidential · Week of {report.week_end}
      </p>
      <h1 style={{ margin: '0 0 6px', fontSize: 28, fontWeight: 400, letterSpacing: '-0.02em' }}>
        Engineering Update
      </h1>
      <p style={{ margin: '0 0 24px', fontSize: 13, color: '#6b7280', fontFamily: 'Arial, sans-serif' }}>
        Generated {report.generated_at.slice(0, 16).replace('T', ' ')}
      </p>

      {/* Bottom line */}
      <div style={{ padding: 16, background: '#fffbeb', borderLeft: '4px solid #d97706',
                    borderRadius: 4, marginBottom: 24 }}>
        <p style={{ margin: '0 0 6px', fontSize: 11, fontWeight: 700, color: '#92400e',
                    textTransform: 'uppercase', letterSpacing: '0.08em',
                    fontFamily: 'Arial, sans-serif' }}>
          Bottom Line
        </p>
        <p style={{ margin: 0, fontSize: 16, lineHeight: 1.6 }}>{s.top_risk}</p>
      </div>

      {/* Decisions */}
      {report.decisions_needed.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ margin: '0 0 12px', fontSize: 13, fontWeight: 700, textTransform: 'uppercase',
                       letterSpacing: '0.08em', fontFamily: 'Arial, sans-serif' }}>
            Decisions Needed ({report.decisions_needed.length})
          </h2>
          <div style={{ border: '1px solid #e5e7eb', borderRadius: 6, overflow: 'hidden', background: '#fff' }}>
            {report.decisions_needed.map((d, i) => (
              <div key={i} style={{ padding: '12px 16px',
                                     borderBottom: i < report.decisions_needed.length - 1 ? '1px solid #e5e7eb' : 'none' }}>
                <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                                background: STATUS_COLOR[d.status] ?? '#6b7280',
                                marginRight: 10, verticalAlign: 'middle' }} />
                <strong style={{ fontFamily: 'Arial, sans-serif', fontSize: 14 }}>{d.project}</strong>
                <span style={{ fontSize: 12, color: '#6b7280', marginLeft: 8,
                                fontFamily: 'Arial, sans-serif' }}>{d.owner}</span>
                <p style={{ margin: '4px 0 0 18px', fontSize: 13, lineHeight: 1.5, color: '#374151' }}>
                  {d.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Portfolio summary chips */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap',
                    fontFamily: 'Arial, sans-serif', fontSize: 12 }}>
        {[
          { label: `${s.on_track} On Track`, color: '#16a34a' },
          { label: `${s.at_risk} At Risk`,   color: '#d97706' },
          { label: `${s.off_track} Off Track`, color: '#dc2626' },
        ].map(({ label, color }) => (
          <span key={label} style={{ padding: '4px 10px', borderRadius: 20, fontWeight: 600,
                                      background: color + '18', color }}>
            {label}
          </span>
        ))}
      </div>

      {/* Project cards */}
      {report.projects.map((p) => {
        const color = STATUS_COLOR[p.status] ?? '#6b7280'
        const work = Math.round(p.work_progress_pct)
        const time = Math.round(p.time_progress_pct)
        return (
          <div key={p.name} style={{ marginBottom: 12, border: `1px solid ${color}`,
                                      borderRadius: 6, overflow: 'hidden', background: '#fff' }}>
            {/* Card header */}
            <div style={{ padding: '10px 16px', background: color, display: 'flex',
                           justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, color: '#fff', fontSize: 15,
                              fontFamily: 'Arial, sans-serif' }}>
                {p.name}
                <span style={{ fontWeight: 400, fontSize: 12, color: 'rgba(255,255,255,0.8)', marginLeft: 10 }}>
                  {p.owner}
                </span>
              </span>
              <span style={{ fontSize: 11, color: '#fff', fontWeight: 700, letterSpacing: '0.06em',
                              fontFamily: 'Arial, sans-serif' }}>
                {STATUS_LABEL[p.status]} · {Math.round(p.health_score)}/100
              </span>
            </div>

            {/* Timeline */}
            <div style={{ padding: '8px 16px', background: '#f9fafb', borderBottom: '1px solid #e5e7eb',
                           fontSize: 12, color: '#6b7280', fontFamily: 'Arial, sans-serif',
                           display: 'flex', justifyContent: 'space-between' }}>
              <span>
                <strong style={{ color: '#111827' }}>{work}% done</strong> / {time}% elapsed ·
                ETA risk: <strong style={{ color: color }}>{p.eta_risk.toUpperCase()}</strong>
              </span>
              {p.target_date && (
                <span>Target: <strong style={{ color: '#111827' }}>{p.target_date}</strong>
                  {p.days_left != null && ` (${p.days_left}d)`}
                </span>
              )}
            </div>

            {/* Progress bar */}
            <div style={{ height: 4, background: '#e5e7eb', position: 'relative' }}>
              <div style={{ position: 'absolute', left: 0, top: 0, height: '100%',
                             width: `${work}%`, background: color }} />
              {/* Time cursor */}
              <div style={{ position: 'absolute', left: `${time}%`, top: 0,
                             width: 2, height: '100%', background: '#9ca3af' }} />
            </div>

            {/* Blockers */}
            {p.blockers.length > 0 && (
              <div style={{ padding: '8px 16px', borderBottom: '1px solid #e5e7eb' }}>
                <p style={{ margin: '0 0 4px', fontSize: 11, fontWeight: 700, color: '#6b7280',
                             textTransform: 'uppercase', letterSpacing: '0.06em',
                             fontFamily: 'Arial, sans-serif' }}>Blockers</p>
                {p.blockers.slice(0, 3).map((b, i) => (
                  <p key={i} style={{ margin: '0 0 2px', fontSize: 13, color: '#374151', lineHeight: 1.4 }}>
                    &bull; {b}
                  </p>
                ))}
              </div>
            )}

            {/* Meeting signal */}
            {p.meeting_signal && (
              <div style={{ padding: '8px 16px', background: '#f0f9ff',
                             borderBottom: '1px solid #e5e7eb' }}>
                <p style={{ margin: '0 0 4px', fontSize: 11, fontWeight: 700, color: '#0369a1',
                             textTransform: 'uppercase', letterSpacing: '0.06em',
                             fontFamily: 'Arial, sans-serif' }}>From Meetings</p>
                <p style={{ margin: 0, fontSize: 13, color: '#374151', fontStyle: 'italic',
                             lineHeight: 1.4 }}>{p.meeting_signal}</p>
              </div>
            )}

            {/* Decision needed */}
            {p.decision_needed && (
              <div style={{ padding: '8px 16px', background: '#fefce8' }}>
                <p style={{ margin: '0 0 4px', fontSize: 11, fontWeight: 700, color: '#854d0e',
                             textTransform: 'uppercase', letterSpacing: '0.06em',
                             fontFamily: 'Arial, sans-serif' }}>Action Needed</p>
                <p style={{ margin: 0, fontSize: 13, color: '#1c1917', fontWeight: 600,
                             lineHeight: 1.4 }}>{p.decision_needed}</p>
              </div>
            )}
          </div>
        )
      })}

      {/* Footer */}
      <p style={{ marginTop: 40, fontSize: 11, color: '#d1d5db', textAlign: 'center',
                  fontFamily: 'Arial, sans-serif' }}>
        Generated by Axeng · signals: {report.sources.join(', ') || '—'}
        {report.errors.length > 0 && ` · partial data: ${report.errors.join('; ')}`}
      </p>
    </div>
  )
}
