import type { ProductDetail, ProductListResponse } from './types'

const API_URL_BASE = import.meta.env.VITE_API_BASE_URL
const API_CANDIDATES = Array.from(
  new Set(
    [
      API_URL_BASE,
      '/api',
      'http://127.0.0.1:8000/api',
      'http://localhost:8000/api',
    ].filter((value): value is string => Boolean(value?.trim())),
  ),
)

function normalizeBase(base: string) {
  return base.endsWith('/') ? base.slice(0, -1) : base
}

async function readErrorDetail(response: Response) {
  const contentType = response.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    const jsonBody = await response.json().catch(() => null)
    const detail = jsonBody && typeof jsonBody === 'object'
      ? (jsonBody as { detail?: string }).detail
      : null
    if (detail) {
      return detail
    }
  }

  const textBody = await response.text().catch(() => '')
  return textBody.trim() || null
}

async function readJsonResponse(response: Response) {
  const text = await response.text()
  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

export async function fetchWithFallback(path: string, init?: RequestInit) {
  let lastResponse: Response | null = null
  let lastError: Error | null = null

  for (const base of API_CANDIDATES) {
    try {
      const response = await fetch(`${normalizeBase(base)}${path}`, init)
      if (response.ok) {
        return response
      }

      lastResponse = response
    } catch (error) {
      if (error instanceof Error) {
        lastError = error
      }
    }
  }

  if (lastResponse) {
    return lastResponse
  }

  if (lastError) {
    throw lastError
  }

  throw new Error('Nao foi possivel conectar na API')
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetchWithFallback(path)
  if (!response.ok) {
    const detail = await readErrorDetail(response)
    throw new Error(detail ?? `Erro ${response.status} na requisicao`)
  }

  return response.json() as Promise<T>
}

export async function fetchCategories() {
  const response = await fetchWithFallback('/produtos/categorias')
  const data = response.ok ? await readJsonResponse(response) : null

  if (!response.ok) {
    const detail = await readErrorDetail(response)
    throw new Error(detail ?? `Erro ${response.status} ao carregar categorias`)
  }

  if (!Array.isArray(data)) {
    throw new Error('Resposta invalida de categorias')
  }

  return data as string[]
}

export async function fetchProductDetail(productId: string) {
  return fetchJson<ProductDetail>(`/produtos/${productId}`)
}

export async function fetchProductList(path: string) {
  return fetchJson<ProductListResponse>(path)
}