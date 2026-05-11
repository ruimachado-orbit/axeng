'use client'

import { useState } from 'react'
import { MessageSquare, Loader2, X, Copy, Check, GitBranch, AlertCircle, Lightbulb, Calendar, TrendingUp, CheckCircle2 } from 'lucide-react'

interface Generate1on1ButtonProps {
  person: string
}

interface ParsedPreread {
  title: string
  bottomLine: string
  evidence: { label: string; value: string; highlight?: boolean }[]
  risks: string[]
  recommendations: string[]
  talkingPoints: string[]
  footer: string
}

function parsePrereadOutput(output: string): ParsedPreread {
  const lines = output.split('\n')
  const parsed: ParsedPreread = {
    title: '',
    bottomLine: '',
    evidence: [],
    risks: [],
    recommendations: [],
    talkingPoints: [],
    footer: ''
  }

  let currentSection = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()

    // Title
    if (trimmed.includes('1:1 Pre-read')) {
      const match = trimmed.match(/1:1 Pre-read\s*[—–-]\s*(.+)/)
      if (match) parsed.title = match[1].replace(/\*/g, '').trim()
    }

    // Sections
    if (trimmed === 'Bottom line:') {
      currentSection = 'bottomLine'
    } else if (trimmed === 'Evidence:') {
      currentSection = 'evidence'
    } else if (trimmed.match(/^Risks?\s*\/\s*gaps?:/i)) {
      currentSection = 'risks'
    } else if (trimmed.match(/^Recommended actions?:/i)) {
      currentSection = 'recommendations'
    } else if (trimmed.match(/^\*?Talking points?\*?:?/i)) {
      currentSection = 'talkingPoints'
    } else if (trimmed.startsWith('_') && trimmed.endsWith('_')) {
      parsed.footer = trimmed.replace(/_/g, '')
    }

    // Parse content based on section
    if (currentSection === 'bottomLine' && trimmed && !trimmed.includes('Bottom line:')) {
      parsed.bottomLine += (parsed.bottomLine ? ' ' : '') + trimmed
    } else if (currentSection === 'evidence' && trimmed.startsWith('•')) {
      const content = trimmed.substring(1).trim()

      // Parse structured evidence lines like "Linear open issues: 0"
      const match = content.match(/^(.+?):\s*(.+)$/)
      if (match) {
        const label = match[1].trim()
        const value = match[2].trim()
        const isHighlight = value.includes('/Users/') || value.includes('MAI')

        parsed.evidence.push({
          label,
          value,
          highlight: isHighlight
        })
      } else {
        parsed.evidence.push({ label: '', value: content })
      }
    } else if (currentSection === 'risks' && trimmed.startsWith('•')) {
      parsed.risks.push(trimmed.substring(1).trim())
    } else if (currentSection === 'risks' && trimmed.startsWith('-')) {
      parsed.risks.push(trimmed.substring(1).trim())
    } else if (currentSection === 'recommendations' && trimmed.startsWith('•')) {
      parsed.recommendations.push(trimmed.substring(1).trim())
    } else if (currentSection === 'talkingPoints' && trimmed.startsWith('•')) {
      parsed.talkingPoints.push(trimmed.substring(1).trim())
    }
  }

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

            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              {/* Bottom line - Hero section */}
              {parsed.bottomLine && (
                <div className="glass border border-emerald-500/30 rounded-2xl p-6 bg-gradient-to-br from-emerald-500/5 to-teal-600/5">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                      <TrendingUp className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold text-base mb-2 text-emerald-700 dark:text-emerald-400">Bottom Line</h3>
                      <p className="text-sm text-foreground leading-relaxed">{parsed.bottomLine}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Evidence */}
              {parsed.evidence.length > 0 && (
                <div className="glass border border-indigo-500/30 rounded-2xl p-6 bg-indigo-500/5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                      <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                    </div>
                    <h3 className="font-bold text-lg">Evidence</h3>
                  </div>
                  <div className="space-y-2">
                    {parsed.evidence.map((item, i) => (
                      <div key={i} className={`flex items-start gap-3 text-sm ${item.highlight ? 'bg-indigo-500/10 -mx-2 px-2 py-1.5 rounded-lg' : ''}`}>
                        <span className="text-indigo-600 font-medium">•</span>
                        {item.label ? (
                          <div className="flex-1">
                            <span className="font-medium text-foreground">{item.label}:</span>{' '}
                            <span className={item.highlight ? 'text-indigo-600 dark:text-indigo-400 font-medium' : 'text-muted-foreground'}>
                              {item.value}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground flex-1">{item.value}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risks / Gaps */}
              {parsed.risks.length > 0 && (
                <div className="glass border border-amber-500/30 rounded-2xl p-6 bg-amber-500/5">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                    </div>
                    <h3 className="font-bold text-lg">Risks / Gaps</h3>
                  </div>
                  <div className="space-y-3">
                    {parsed.risks.map((risk, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <span className="text-amber-600 font-medium text-sm">⚠</span>
                        <p className="text-sm text-foreground leading-relaxed flex-1">{risk}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Actions */}
              {parsed.recommendations.length > 0 && (
                <div className="glass border border-blue-500/30 rounded-2xl p-6 bg-blue-500/5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                      <Lightbulb className="w-5 h-5 text-blue-600" />
                    </div>
                    <h3 className="font-bold text-lg">Recommended Actions</h3>
                  </div>
                  <div className="space-y-3">
                    {parsed.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-3 group">
                        <div className="w-6 h-6 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-xs font-bold text-blue-600">{i + 1}</span>
                        </div>
                        <p className="text-sm text-foreground leading-relaxed group-hover:text-blue-600 transition-colors flex-1">
                          {rec}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Talking points */}
              {parsed.talkingPoints.length > 0 && (
                <div className="glass border border-purple-500/30 rounded-2xl p-6 bg-gradient-to-br from-purple-500/5 to-pink-600/5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-purple-600" />
                    </div>
                    <h3 className="font-bold text-lg">Talking Points</h3>
                  </div>
                  <div className="space-y-3">
                    {parsed.talkingPoints.map((point, i) => (
                      <div key={i} className="flex items-start gap-3 group">
                        <div className="w-6 h-6 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-xs font-bold text-purple-600">{i + 1}</span>
                        </div>
                        <p className="text-sm text-foreground leading-relaxed group-hover:text-purple-600 transition-colors flex-1">
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
