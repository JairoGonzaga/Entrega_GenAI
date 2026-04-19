import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import AIAnalystPage from './AIAnalystPage'

function jsonResponse(body: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

describe('AIAnalystPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
    window.localStorage.clear()
  })

  it('sends a question and renders response with sql preview', async () => {
    const user = userEvent.setup()

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const rawUrl = typeof input === 'string' ? input : input.toString()
      const url = new URL(rawUrl, 'http://localhost')
      const method = (init?.method ?? 'GET').toUpperCase()

      if (method === 'POST' && url.pathname.endsWith('/api/agent/query')) {
        return jsonResponse({
          interpretacao: 'Eletronicos lideram receita no periodo analisado.',
          sql: 'SELECT categoria_produto, SUM(valor_total) AS receita FROM vw_receita_categoria LIMIT 100',
          data: [
            { categoria_produto: 'eletronicos', receita: 125000 },
            { categoria_produto: 'moveis', receita: 91000 },
          ],
        })
      }

      return jsonResponse({ detail: 'Not Found' }, { status: 404 })
    })

    vi.stubGlobal('fetch', fetchMock)

    render(<AIAnalystPage />)

    const input = screen.getByLabelText('Pergunta')
    await user.type(input, 'Qual categoria vendeu mais no periodo?')
    await user.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Qual categoria vendeu mais no periodo?')).toBeInTheDocument()
    expect(await screen.findByText('Eletronicos lideram receita no periodo analisado.')).toBeInTheDocument()
    expect(await screen.findByText(/SQL Gerada/i)).toBeInTheDocument()
    expect(await screen.findByText('eletronicos')).toBeInTheDocument()

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled()
    })
  })
})
