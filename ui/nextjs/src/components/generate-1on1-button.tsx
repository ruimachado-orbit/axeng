'use client'

import { useState } from 'react'
import { MessageSquare, Loader2 } from 'lucide-react'

interface Generate1on1ButtonProps {
  person: string
}

export function Generate1on1Button({ person }: Generate1on1ButtonProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; message?: string; error?: string } | null>(null)

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

      if (data.ok) {
        // Show success message
        setTimeout(() => setResult(null), 5000)
      }
    } catch (error) {
      setResult({ ok: false, error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
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

      {result && (
        <div className={`mt-3 text-xs p-2 rounded-lg ${result.ok ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400'}`}>
          {result.ok ? (
            <p>✅ {result.message}</p>
          ) : (
            <p>❌ {result.error || 'Erro ao gerar pre-read'}</p>
          )}
        </div>
      )}
    </div>
  )
}
