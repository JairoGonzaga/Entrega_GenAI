import { useMemo, useState } from 'react'
import { askAnalyst } from './api'
import type { AnalystMessage } from './types'

const STORAGE_KEY = 'ai-analyst-session-id'

function buildSessionId() {
  if (typeof window === 'undefined') {
    return 'session-local'
  }

  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored) {
    return stored
  }

  const generated = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `session-${Date.now()}`

  window.localStorage.setItem(STORAGE_KEY, generated)
  return generated
}

function createMessage(role: AnalystMessage['role'], text: string, extra?: Partial<AnalystMessage>): AnalystMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    ...extra,
  }
}

export function useAnalystChat() {
  const sessionId = useMemo(() => buildSessionId(), [])
  const [messages, setMessages] = useState<AnalystMessage[]>([
    createMessage(
      'assistant',
      'Sou seu Analista IA. Pergunte em linguagem natural e eu vou gerar a consulta SQL e interpretar os resultados.',
    ),
  ])
  const [draft, setDraft] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function sendMessage() {
    const question = draft.trim()
    if (!question || isLoading) {
      return
    }

    const userMessage = createMessage('user', question)
    const nextMessages = [...messages, userMessage]

    setMessages(nextMessages)
    setDraft('')
    setError(null)
    setIsLoading(true)

    try {
      const response = await askAnalyst(
        {
          question,
          history: nextMessages.map((message) => ({
            role: message.role,
            text: message.text,
          })),
        },
        sessionId,
      )

      setMessages((current) => [
        ...current,
        createMessage('assistant', response.answer, {
          sql: response.sql,
          rows: response.rows,
        }),
      ])
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : 'Erro inesperado ao consultar o analista.'
      setError(message)
      setMessages((current) => [
        ...current,
        createMessage('assistant', 'Nao consegui consultar o backend do agente neste momento. Tente novamente em instantes.'),
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return {
    messages,
    draft,
    error,
    isLoading,
    setDraft,
    sendMessage,
  }
}
