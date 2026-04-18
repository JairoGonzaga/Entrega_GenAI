import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CatalogPage from './CatalogPage'

type ProductListItem = {
  id_produto: string
  nome_produto: string
  categoria_produto: string
  descricao_produto: string | null
  preco_base: number | null
  media_avaliacoes: number | null
  total_vendas: number
  quantidade_registros: number
}

function createProducts() {
  const products: ProductListItem[] = [
    {
      id_produto: 'p1',
      nome_produto: 'Mouse Gamer',
      categoria_produto: 'eletronicos',
      descricao_produto: 'Mouse sem fio',
      preco_base: 150,
      media_avaliacoes: 4.5,
      total_vendas: 12,
      quantidade_registros: 1,
    },
    {
      id_produto: 'p2',
      nome_produto: 'Teclado Mecanico',
      categoria_produto: 'eletronicos',
      descricao_produto: 'Teclado de aluminio',
      preco_base: 300,
      media_avaliacoes: 4.2,
      total_vendas: 8,
      quantidade_registros: 1,
    },
    {
      id_produto: 'p3',
      nome_produto: 'Cadeira Office',
      categoria_produto: 'moveis',
      descricao_produto: 'Ergonomica e ajustavel',
      preco_base: 650,
      media_avaliacoes: 4.8,
      total_vendas: 5,
      quantidade_registros: 1,
    },
  ]

  for (let index = 4; index <= 11; index += 1) {
    products.push({
      id_produto: `p${index}`,
      nome_produto: `Produto ${index}`,
      categoria_produto: index % 2 === 0 ? 'casa' : 'eletronicos',
      descricao_produto: `Descricao ${index}`,
      preco_base: 50 + index,
      media_avaliacoes: 3.5,
      total_vendas: index,
      quantidade_registros: 1,
    })
  }

  return products
}

function createDetail(productId: string) {
  if (productId === 'p3') {
    return {
      id_produto: 'p3',
      nome_produto: 'Cadeira Office',
      categoria_produto: 'moveis',
      descricao_produto: 'Ergonomica e ajustavel',
      preco_base: 650,
      medidas: {
        peso_produto_gramas: 12000,
        comprimento_centimetros: 75,
        altura_centimetros: 120,
        largura_centimetros: 60,
      },
      media_avaliacoes: 4.8,
      total_vendas: 5,
      vendas_historico: [
        {
          id_pedido: 'ped-1',
          data_pedido: '2026-03-01T00:00:00.000Z',
          quantidade_itens: 1,
          valor_total: 650,
          status: 'entregue',
        },
      ],
      avaliacoes: [
        {
          id_avaliacao: 'av-1',
          nota: 5,
          titulo: 'Excelente',
          comentario: 'Muito confortavel',
          data_comentario: '2026-03-02T00:00:00.000Z',
        },
      ],
    }
  }

  return {
    id_produto: productId,
    nome_produto: 'Mouse Gamer',
    categoria_produto: 'eletronicos',
    descricao_produto: 'Mouse sem fio',
    preco_base: 150,
    medidas: {
      peso_produto_gramas: 150,
      comprimento_centimetros: 10,
      altura_centimetros: 4,
      largura_centimetros: 6,
    },
    media_avaliacoes: 4.5,
    total_vendas: 12,
    vendas_historico: [],
    avaliacoes: [],
  }
}

function jsonResponse(body: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

function installFetchMock() {
  let products = createProducts()

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const rawUrl = typeof input === 'string' ? input : input.toString()
    const url = new URL(rawUrl, 'http://localhost')
    const method = (init?.method ?? 'GET').toUpperCase()

    if (url.pathname.endsWith('/api/produtos/categorias')) {
      return jsonResponse(['eletronicos', 'moveis', 'casa'])
    }

    if (url.pathname.includes('/api/produtos/') && method === 'GET') {
      const productId = url.pathname.split('/').pop() ?? ''
      return jsonResponse(createDetail(productId))
    }

    if (url.pathname.endsWith('/api/produtos') && method === 'GET') {
      const skip = Number(url.searchParams.get('skip') ?? '0')
      const limit = Number(url.searchParams.get('limit') ?? '10')
      const search = (url.searchParams.get('busca') ?? '').toLowerCase()
      const categories = url.searchParams.getAll('categoria')
      const minRating = Number(url.searchParams.get('nota_min') ?? '0')

      const filtered = products.filter((product) => {
        const haystack = [product.nome_produto, product.categoria_produto, product.descricao_produto]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        const matchesSearch = !search || haystack.includes(search)
        const matchesCategory = categories.length === 0 || categories.includes(product.categoria_produto)
        const matchesRating = !minRating || (product.media_avaliacoes ?? 0) >= minRating
        return matchesSearch && matchesCategory && matchesRating
      })

      return jsonResponse({
        total: filtered.length,
        itens: filtered.slice(skip, skip + limit),
      })
    }

    if (url.pathname.endsWith('/api/produtos') && method === 'POST') {
      const body = JSON.parse(String(init?.body ?? '{}')) as Partial<ProductListItem>
      const createdProduct: ProductListItem = {
        id_produto: 'p-new',
        nome_produto: body.nome_produto ?? 'Novo produto',
        categoria_produto: body.categoria_produto ?? 'eletronicos',
        descricao_produto: body.descricao_produto ?? null,
        preco_base: body.preco_base ?? null,
        media_avaliacoes: null,
        total_vendas: 0,
        quantidade_registros: 1,
      }

      products = [createdProduct, ...products]
      return new Response(null, { status: 201 })
    }

    if (url.pathname.includes('/api/produtos/') && method === 'DELETE') {
      const productId = url.pathname.split('/').pop() ?? ''
      products = products.filter((product) => product.id_produto !== productId)
      return new Response(null, { status: 204 })
    }

    return jsonResponse({ detail: `Unhandled ${method} ${url.pathname}` }, { status: 404 })
  })

  vi.stubGlobal('fetch', fetchMock)
  return { fetchMock }
}

describe('CatalogPage', () => {
  beforeEach(() => {
    installFetchMock()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders the initial catalog and reacts to search filters', async () => {
    const user = userEvent.setup()
    render(<CatalogPage />)

    expect(await screen.findByText('Mouse Gamer')).toBeInTheDocument()
    expect(await screen.findByText('Cadeira Office')).toBeInTheDocument()

    const cadeiraCard = screen.getAllByText('Cadeira Office')[0].closest('li')
    expect(cadeiraCard).not.toBeNull()
    await user.click(cadeiraCard as HTMLElement)

    expect(await screen.findByText('Excelente')).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText('Buscar por nome, categoria ou descricao'), 'Cadeira')

    await waitFor(() => {
      expect(screen.queryByText('Mouse Gamer')).not.toBeInTheDocument()
      expect(screen.getAllByText('Cadeira Office')[0]).toBeInTheDocument()
    })
  })

  it('supports pagination and create/delete flows', async () => {
    const user = userEvent.setup()
    render(<CatalogPage />)

    expect(await screen.findByText('Pagina 1 de 2')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Proxima' }))

    await waitFor(() => {
      expect(screen.getByText('Pagina 2 de 2')).toBeInTheDocument()
      expect(screen.getByText('Produto 11')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Anterior' }))

    await waitFor(() => {
      expect(screen.getByText('Pagina 1 de 2')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Novo produto' }))
    await user.type(screen.getByLabelText('Nome'), 'Notebook Pro')
    await user.type(screen.getByLabelText('Categoria'), 'eletronicos')
    await user.type(screen.getByLabelText('Descricao'), 'Equipamento novo')
    await user.type(screen.getByLabelText('Preco base'), '4999')

    await user.click(screen.getByRole('button', { name: 'Salvar' }))

    await waitFor(() => {
      expect(screen.getByText('Notebook Pro')).toBeInTheDocument()
    })

    const createdProduct = screen.getByText('Notebook Pro').closest('li')
    expect(createdProduct).not.toBeNull()

    await user.click(within(createdProduct as HTMLElement).getByRole('button', { name: 'Excluir' }))

    await waitFor(() => {
      expect(screen.queryByText('Notebook Pro')).not.toBeInTheDocument()
    })
  })
})