'use client'

import { useState } from 'react'
import { MessageSquare, Loader2, X, Copy, Check, TrendingUp, CheckCircle2, AlertCircle, Lightbulb, Calendar } from 'lucide-react'

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

  for (const line of lines) {
    const trimmed = line.trim()

    if (trimmed.includes('1:1 Pre-read')) {
      const match = trimmed.match(/1:1 Pre-read\s*[—–-]\s*(.+)/)
      if (match) parsed.title = match[1].replace(/\*/g, '').trim()
    }

    if (trimmed === 'Bottom line:') currentSection = 'bottomLine'
    else if (trimmed === 'Evidence:') currentSection = 'evidence'
    else if (trimmed.match(/^Risks?\s*\/\s*gaps?:/i)) currentSection = 'risks'
    else if (trimmed.match(/^Recommended actions?:/i)) currentSection = 'recommendations'
    else if (trimmed.match(/^\*?Talking points?\*?:?/i)) currentSection = 'talkingPoints'
    else if (trimmed.startsWith('_') && trimmed.endsWith('_')) parsed.footer = trimmed.replace(/_/g, '')

    if (currentSection === 'bottomLine' && trimmed && !trimmed.includes('Bottom line:')) {
      parsed.bottomLine += (parsed.bottomLine ? ' ' : '') + trimmed
    } else if (currentSection === 'evidence' && trimmed.startsWith('•')) {
      const content = trimmed.substring(1).trim()
      const match = content.match(/^(.+?):\s*(.+)$/)
      if (match) {
        parsed.evidence.push({
          label: match[1].trim(),
          value: match[2].trim(),
          highlight: match[2].includes('/Users/') || match[2].includes('MAI')
        })
      } else {
        parsed.evidence.push({ label: '', value: content })
      }
    } else if ((currentSection === 'risks' || currentSection === 'recommendations' || currentSection === 'talkingPoints') && (trimmed.startsWith('•') || trimmed.startsWith('-'))) {
      const text = trimmed.substring(1).trim()
      if (currentSection === 'risks') parsed.risks.push(text)
      else if (currentSection === 'recommendations') parsed.recommendations.push(text)
      else if (currentSection === 'talkingPoints') parsed.talkingPoints.push(text)
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
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[88vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gradient-to-r from-indigo-500/10 to-purple-500/10 shrink-0">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                  <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">1:1 Pre-read</span>
                </div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{parsed.title || person}</h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition text-gray-700 dark:text-gray-300"
                >
                  {copied ? <><Check className="w-3 h-3" /> Copiado</> : <><Copy className="w-3 h-3" /> Copiar</>}
                </button>
                <button onClick={() => setShowModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition text-gray-700 dark:text-gray-300">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gray-50 dark:bg-gray-950">
              {parsed.bottomLine && (
                <div className="border border-emerald-500/30 rounded-lg p-4 bg-emerald-50 dark:bg-emerald-950/20">
                  <div className="flex gap-3">
                    <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-semibold text-sm mb-1 text-emerald-700 dark:text-emerald-300">Bottom Line</h3>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{parsed.bottomLine}</p>
                    </div>
                  </div>
                </div>
              )}

              {parsed.evidence.length > 0 && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-900">
                  <div className="flex gap-3 mb-3">
                    <CheckCircle2 className="w-5 h-5 text-indigo-600 dark:text-indigo-400 shrink-0" />
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Evidence</h3>
                  </div>
                  <div className="space-y-1.5 pl-8">
                    {parsed.evidence.map((item, i) => (
                      <div key={i} className="text-xs">
                        {item.label ? (
                          <><span className="font-medium text-gray-900 dark:text-gray-100">{item.label}:</span> <span className="text-gray-600 dark:text-gray-400">{item.value}</span></>
                        ) : (
                          <span className="text-gray-600 dark:text-gray-400">{item.value}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {parsed.risks.length > 0 && (
                <div className="border border-amber-500/30 rounded-lg p-4 bg-amber-50 dark:bg-amber-950/20">
                  <div className="flex gap-3 mb-3">
                    <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Risks / Gaps</h3>
                  </div>
                  <div className="space-y-2 pl-8">
                    {parsed.risks.map((risk, i) => <p key={i} className="text-xs text-gray-800 dark:text-gray-200">{risk}</p>)}
                  </div>
                </div>
              )}

              {parsed.recommendations.length > 0 && (
                <div className="border border-blue-500/30 rounded-lg p-4 bg-blue-50 dark:bg-blue-950/20">
                  <div className="flex gap-3 mb-3">
                    <Lightbulb className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0" />
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Recommended Actions</h3>
                  </div>
                  <div className="space-y-2 pl-8">
                    {parsed.recommendations.map((rec, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-blue-600 dark:text-blue-400 font-bold text-xs">{i + 1}.</span>
                        <p className="text-xs text-gray-800 dark:text-gray-200 flex-1">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {parsed.talkingPoints.length > 0 && (
                <div className="border border-purple-500/30 rounded-lg p-4 bg-purple-50 dark:bg-purple-950/20">
                  <div className="flex gap-3 mb-3">
                    <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400 shrink-0" />
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Talking Points</h3>
                  </div>
                  <div className="space-y-2 pl-8">
                    {parsed.talkingPoints.map((point, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-purple-600 dark:text-purple-400 font-bold text-xs">{i + 1}.</span>
                        <p className="text-xs text-gray-800 dark:text-gray-200 flex-1">{point}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {parsed.footer && (
                <p className="text-xs text-center text-gray-500 dark:text-gray-500 pt-2">{parsed.footer}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
