import { fetchWithFallback } from '../catalog/api'
import type { AnalystMessage, AnalystResponse } from './types'

type AnalystRequest = {
  question: string
  history: Array<Pick<AnalystMessage, 'role' | 'text'>>
}

const ENDPOINT_CANDIDATES = ['/agent/query', '/agent/chat', '/agent']

function toText(value: unknown): string {
  if (typeof value === 'string') {
    return value
  }

  if (value === null || value === undefined) {
    return ''
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }

  try {
    return JSON.stringify(value)
  } catch {
    return ''
  }
}

function toRows(value: unknown): Array<Record<string, unknown>> | undefined {
  if (!Array.isArray(value)) {
    return undefined
  }

  const validRows = value.filter((row) => row && typeof row === 'object') as Array<Record<string, unknown>>
  return validRows.length ? validRows : undefined
}

function normalizeResponse(payload: unknown): AnalystResponse {
  if (typeof payload === 'string') {
    return { answer: payload }
  }

  if (!payload || typeof payload !== 'object') {
    return { answer: 'Nao foi possivel interpretar a resposta do agente.' }
  }

  const data = payload as Record<string, unknown>
  const answer =
    toText(data.interpretacao) ||
    toText(data.answer) ||
    toText(data.response) ||
    toText(data.message) ||
    'Resposta recebida, mas sem interpretacao textual.'

  const sql = toText(data.sql || data.query || data.generated_sql) || undefined
  const rows = toRows(data.dados) || toRows(data.data) || toRows(data.rows) || toRows(data.result)

  return { answer, sql, rows }
}

async function readErrorDetail(response: Response) {
  const contentType = response.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    const body = await response.json().catch(() => null)
    if (body && typeof body === 'object') {
      const detail = (body as { detail?: string }).detail
      if (detail) {
        return detail
      }
    }
  }

  const text = await response.text().catch(() => '')
  return text || `Erro ${response.status}`
}

export async function askAnalyst(
  request: AnalystRequest,
  sessionId: string,
): Promise<AnalystResponse> {
  let lastError = 'Nao foi possivel conectar com o agente de analise.'

  for (const path of ENDPOINT_CANDIDATES) {
    const response = await fetchWithFallback(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId,
      },
      body: JSON.stringify(request),
    })

    if (response.ok) {
      const payload = await response.json().catch(() => null)
      return normalizeResponse(payload)
    }

    if (response.status === 404) {
      lastError = 'Endpoint de agente ainda nao disponivel no backend.'
      continue
    }

    lastError = await readErrorDetail(response)
    break
  }

  throw new Error(lastError)
}
