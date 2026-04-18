export type ProductListItem = {
  id_produto: string
  nome_produto: string
  categoria_produto: string
  descricao_produto: string | null
  preco_base: number | null
  media_avaliacoes: number | null
  total_vendas: number
  quantidade_registros: number
}

export type ProductListResponse = {
  total: number
  itens: ProductListItem[]
}

export type OrderHistoryItem = {
  id_pedido: string
  data_pedido: string | null
  quantidade_itens: number
  valor_total: number
  status: string
}

export type ReviewItem = {
  id_avaliacao: string
  nota: number
  titulo: string | null
  comentario: string | null
  data_comentario: string | null
}

export type ProductDetail = {
  id_produto: string
  nome_produto: string
  categoria_produto: string
  descricao_produto: string | null
  preco_base: number | null
  medidas: {
    peso_produto_gramas: number | null
    comprimento_centimetros: number | null
    altura_centimetros: number | null
    largura_centimetros: number | null
  }
  media_avaliacoes: number | null
  total_vendas: number
  vendas_historico: OrderHistoryItem[]
  avaliacoes: ReviewItem[]
}

export type ProductFormData = {
  nome_produto: string
  categoria_produto: string
  descricao_produto: string | null
  preco_base: number | null
  peso_produto_gramas: number | null
  comprimento_centimetros: number | null
  altura_centimetros: number | null
  largura_centimetros: number | null
}

export const PAGE_SIZE = 10

export const emptyForm: ProductFormData = {
  nome_produto: '',
  categoria_produto: '',
  descricao_produto: null,
  preco_base: null,
  peso_produto_gramas: null,
  comprimento_centimetros: null,
  altura_centimetros: null,
  largura_centimetros: null,
}