'use client'

// CEO Steering — index page: list of available weekly reports
import { useEffect, useState } from 'react'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_AXENG_API_BASE || 'http://localhost:3457'

interface SteeringIndex {
  id: string
  week_end: string
  week_start: string
  title: string
  summary: string
  projects: number
  decisions: number
  generated_at: string
  sources: string[]
}

export default function SteeringIndexPage() {
  const [reports, setReports] = useState<SteeringIndex[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/api/reports/steering`)
      .then(r => r.ok ? r.json() : { reports: [] })
      .then(data => setReports(data.reports ?? []))
      .catch(() => setReports([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ maxWidth: 660, margin: '48px auto', padding: '0 24px' }}>
      <p style={{ margin: '0 0 4px', fontSize: 11, color: '#9ca3af', letterSpacing: '0.08em',
                  textTransform: 'uppercase', fontFamily: 'Arial, sans-serif' }}>
        Axeng · Executive Reports
      </p>
      <h1 style={{ margin: '0 0 6px', fontSize: 28, fontWeight: 400, color: '#111827',
                   letterSpacing: '-0.02em' }}>
        Engineering Updates
      </h1>
      <p style={{ margin: '0 0 32px', fontSize: 13, color: '#6b7280',
                  fontFamily: 'Arial, sans-serif' }}>
        Weekly CEO steering documents
      </p>

      {loading ? (
        <p style={{ fontSize: 13, color: '#9ca3af', fontFamily: 'Arial, sans-serif' }}>
          Loading…
        </p>
      ) : reports.length === 0 ? (
        <div style={{ padding: '24px', border: '1px solid #e5e7eb', borderRadius: 8,
                      background: '#fff', textAlign: 'center' }}>
          <p style={{ margin: 0, fontSize: 14, color: '#6b7280', fontFamily: 'Arial, sans-serif' }}>
            No steering reports generated yet.
          </p>
          <p style={{ margin: '8px 0 0', fontSize: 12, color: '#9ca3af',
                      fontFamily: 'Arial, sans-serif' }}>
            Run <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: 3 }}>
              axeng report --steering
            </code> to generate the first one.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {reports.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      )}

      <p style={{ marginTop: 48, fontSize: 11, color: '#d1d5db', textAlign: 'center',
                  fontFamily: 'Arial, sans-serif' }}>
        Axeng · Engineering Manager Accelerator
      </p>
    </div>
  )
}

function ReportCard({ report: r }: { report: SteeringIndex }) {
  const [hovered, setHovered] = useState(false)
  return (
    <Link href={`/steering/${r.week_end}`} style={{ textDecoration: 'none' }}>
      <div
        style={{
          padding: '16px 20px',
          border: `1px solid ${hovered ? '#1d4ed8' : '#e5e7eb'}`,
          borderRadius: 8,
          background: '#fff',
          cursor: 'pointer',
          transition: 'border-color 0.15s, box-shadow 0.15s',
          boxShadow: hovered ? '0 2px 8px rgba(29,78,216,0.08)' : 'none',
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <p style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 600, color: '#111827',
                        fontFamily: 'Arial, sans-serif' }}>
              {r.title}
            </p>
            <p style={{ margin: '0 0 8px', fontSize: 13, color: '#374151', lineHeight: 1.5 }}>
              {r.summary}
            </p>
          </div>
          <span style={{ fontSize: 11, color: '#9ca3af', whiteSpace: 'nowrap', marginLeft: 16,
                          fontFamily: 'Arial, sans-serif' }}>
            {r.week_end}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 16, fontSize: 11, color: '#6b7280',
                       fontFamily: 'Arial, sans-serif' }}>
          <span>{r.projects} projects</span>
          {r.decisions > 0 && (
            <span style={{ color: '#d97706', fontWeight: 600 }}>
              {r.decisions} decision{r.decisions > 1 ? 's' : ''} needed
            </span>
          )}
          <span>Signals: {r.sources?.join(', ') || '—'}</span>
        </div>
      </div>
    </Link>
  )
}
