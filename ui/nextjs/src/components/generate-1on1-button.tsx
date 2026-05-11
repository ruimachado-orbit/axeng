'use client'

import { useState } from 'react'
import { MessageSquare, Loader2, X, Copy, Check } from 'lucide-react'

interface Generate1on1ButtonProps {
  person: string
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

      {showModal && result?.output && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-card border border-border/40 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/40">
              <div>
                <h3 className="text-lg font-bold">1:1 Pre-read — {person}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Gerado agora</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-secondary hover:bg-secondary/80 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      Copiado!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Copiar
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 rounded-lg hover:bg-secondary transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-sm bg-secondary/50 rounded-lg p-4 border border-border/40">
                  {result.output}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
