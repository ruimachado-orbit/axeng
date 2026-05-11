'use client'

import { useState } from 'react'
import { MessageSquare, Loader2, X, Copy, Check, GitBranch, AlertCircle, Lightbulb, Calendar, TrendingUp, CheckCircle2 } from 'lucide-react'

interface Generate1on1ButtonProps {
  person: string
}

interface ParsedPreread {
  title: string
  metrics: { label: string; value: string; icon: string }[]
  sections: { title: string; content: string[]; icon: string; type: 'success' | 'warning' | 'info' }[]
  talkingPoints: string[]
  footer: string
}

function parsePrereadOutput(output: string): ParsedPreread {
  const lines = output.split('\n')
  const parsed: ParsedPreread = {
    title: '',
    metrics: [],
    sections: [],
    talkingPoints: [],
    footer: ''
  }

  let currentSection: { title: string; content: string[]; icon: string; type: 'success' | 'warning' | 'info' } | null = null

  for (const line of lines) {
    const trimmed = line.trim()

    if (trimmed.startsWith('*1:1 Pre-read')) {
      parsed.title = trimmed.replace(/\*/g, '').replace('1:1 Pre-read —', '').trim()
    } else if (trimmed.startsWith('Open Linear issues:') || trimmed.startsWith('Open PRs:') || trimmed.includes('PRs abertos') || trimmed.includes('Projetos')) {
      const match = trimmed.match(/(.+?):\s*\*?(\d+|\?)\*?/)
      if (match) {
        parsed.metrics.push({
          label: match[1].replace(/\*/g, '').trim(),
          value: match[2],
          icon: match[1].includes('Linear') ? 'list' : match[1].includes('PR') ? 'git' : 'folder'
        })
      }
    } else if (trimmed.startsWith('*Linear*') || trimmed.startsWith('*GitHub*')) {
      if (currentSection) parsed.sections.push(currentSection)

      const platform = trimmed.includes('Linear') ? 'Linear' : 'GitHub'
      const hasNoIssues = trimmed.includes('no open issues') || trimmed.includes('no commits')

      currentSection = {
        title: platform,
        content: [trimmed.replace(/\*/g, '')],
        icon: platform === 'Linear' ? 'list' : 'git',
        type: hasNoIssues ? 'success' : 'info'
      }
    } else if (trimmed.startsWith('*Talking points*')) {
      if (currentSection) parsed.sections.push(currentSection)
      currentSection = null
    } else if (trimmed.startsWith('•')) {
      parsed.talkingPoints.push(trimmed.substring(1).trim())
    } else if (trimmed.startsWith('_') && trimmed.endsWith('_')) {
      parsed.footer = trimmed.replace(/_/g, '')
    } else if (currentSection && trimmed) {
      currentSection.content.push(trimmed)
    }
  }

  if (currentSection) parsed.sections.push(currentSection)

  return parsed
}

export function Generate1on1Button({ person }: Generate1on1ButtonProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; message?: string; error?: string; output?: string } | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleGenerate() {
    setLoading(true)
    setResult(null)

    try {
      const response = await fetch('/api/generate-1on1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person }),
      })

      const data = await response.json()
      setResult(data)

      if (data.ok && data.output) {
        setShowModal(true)
      }
    } catch (error) {
      setResult({ ok: false, error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  function handleCopy() {
    if (result?.output) {
      navigator.clipboard.writeText(result.output)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const parsed = result?.output ? parsePrereadOutput(result.output) : null

  return (
    <>
      <button
        onClick={handleGenerate}
        disabled={loading}
        className="inline-flex items-center rounded-lg px-3 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90 text-white text-xs shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
      >
        {loading ? (
          <>
            <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            A gerar...
          </>
        ) : (
          <>
            <MessageSquare className="w-3.5 h-3.5 mr-1.5" />
            Gerar 1:1 Pre-read
          </>
        )}
      </button>

      {result && !result.ok && (
        <div className="mt-3 text-xs p-2 rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400">
          <p>❌ {result.error || 'Erro ao gerar pre-read'}</p>
        </div>
      )}

      {showModal && parsed && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="glass border border-border/40 rounded-3xl shadow-2xl max-w-5xl w-full max-h-[85vh] overflow-hidden flex flex-col animate-fade-in-up">
            {/* Header with gradient */}
            <div className="relative px-8 py-6 bg-gradient-to-r from-indigo-500/10 to-purple-600/10 border-b border-border/40">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-xs font-medium mb-3">
                    <Calendar className="w-3 h-3" />
                    1:1 Meeting Pre-read
                  </div>
                  <h2 className="text-2xl font-bold gradient-text">{parsed.title || person}</h2>
                  <p className="text-sm text-muted-foreground mt-1.5 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5" />
                    {parsed.footer || 'Gerado agora'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopy}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-xl glass-hover border border-border/40 transition-all"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 text-emerald-600" />
                        <span className="text-emerald-600 font-medium">Copiado!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copiar
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setShowModal(false)}
                    className="p-2.5 rounded-xl hover:bg-secondary/80 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Metrics cards */}
              {parsed.metrics.length > 0 && (
                <div className="grid grid-cols-3 gap-3 mt-6">
                  {parsed.metrics.map((metric, i) => (
                    <div key={i} className="glass-hover border border-border/40 rounded-xl p-4 text-center">
                      <div className="text-3xl font-bold text-foreground mb-1">{metric.value}</div>
                      <div className="text-xs text-muted-foreground">{metric.label}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              {/* Status sections */}
              {parsed.sections.map((section, i) => (
                <div key={i} className={`glass-hover border rounded-2xl p-5 ${
                  section.type === 'success' ? 'border-emerald-500/30 bg-emerald-500/5' :
                  section.type === 'warning' ? 'border-amber-500/30 bg-amber-500/5' :
                  'border-indigo-500/30 bg-indigo-500/5'
                }`}>
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      section.type === 'success' ? 'bg-emerald-500/10' :
                      section.type === 'warning' ? 'bg-amber-500/10' :
                      'bg-indigo-500/10'
                    }`}>
                      {section.icon === 'git' ? (
                        <GitBranch className={`w-5 h-5 ${
                          section.type === 'success' ? 'text-emerald-600' :
                          section.type === 'warning' ? 'text-amber-600' :
                          'text-indigo-600'
                        }`} />
                      ) : section.type === 'success' ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-indigo-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-base mb-2">{section.title}</h3>
                      {section.content.map((line, j) => (
                        <p key={j} className="text-sm text-muted-foreground leading-relaxed">
                          {line}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              ))}

              {/* Talking points */}
              {parsed.talkingPoints.length > 0 && (
                <div className="glass border border-indigo-500/30 rounded-2xl p-6 bg-gradient-to-br from-indigo-500/5 to-purple-600/5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                      <Lightbulb className="w-5 h-5 text-indigo-600" />
                    </div>
                    <h3 className="font-bold text-lg">Talking Points</h3>
                  </div>
                  <div className="space-y-3">
                    {parsed.talkingPoints.map((point, i) => (
                      <div key={i} className="flex items-start gap-3 group">
                        <div className="w-6 h-6 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-xs font-bold text-indigo-600">{i + 1}</span>
                        </div>
                        <p className="text-sm text-foreground leading-relaxed group-hover:text-indigo-600 transition-colors">
                          {point}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
