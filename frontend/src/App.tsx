/* Painel principal do catalogo: filtros, detalhes, CRUD e chamadas da API. */
import './App.css'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

type ProdutoItemLista = {
  id_produto: string
  nome_produto: string
  categoria_produto: string
  descricao_produto: string | null
  preco_base: number | null
  media_avaliacoes: number | null
  total_vendas: number
  quantidade_registros: number
}

type ProdutoRespostaLista = {
  total: number
  itens: ProdutoItemLista[]
}

type MapaImagensCategoria = Record<string, string>

type ItemHistoricoVenda = {
  id_pedido: string
  data_pedido: string | null
  quantidade_itens: number
  valor_total: number
  status: string
}

type ItemAvaliacao = {
  id_avaliacao: string
  nota: number
  titulo: string | null
  comentario: string | null
  data_comentario: string | null
}

type ProdutoDetalhe = {
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
  vendas_historico: ItemHistoricoVenda[]
  avaliacoes: ItemAvaliacao[]
}

type DadosProduto = {
  nome_produto: string
  categoria_produto: string
  descricao_produto: string | null
  preco_base: number | null
  peso_produto_gramas: number | null
  comprimento_centimetros: number | null
  altura_centimetros: number | null
  largura_centimetros: number | null
}

const API_URL_BASE = import.meta.env.VITE_API_BASE_URL
const API_CANDIDATAS = Array.from(
  new Set(
    [
      API_URL_BASE,
      '/api',
      'http://127.0.0.1:8000/api',
      'http://localhost:8000/api',
    ].filter((value): value is string => Boolean(value?.trim())),
  ),
)
const TAMANHO_PAGINA = 10

const formularioVazio: DadosProduto = {
  nome_produto: '',
  categoria_produto: '',
  descricao_produto: null,
  preco_base: null,
  peso_produto_gramas: null,
  comprimento_centimetros: null,
  altura_centimetros: null,
  largura_centimetros: null,
}

async function buscarJson<T>(path: string): Promise<T> {
  /*
   * Faz requisicao e retorna JSON tipado.
   * Dispara erro quando a API responde com falha.
   */
  const resposta = await buscarComFallback(path)
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new Error(corpo?.detail ?? 'Falha na requisicao')
  }

  return resposta.json() as Promise<T>
}

async function lerRespostaJson(resposta: Response) {
  /*
   * Le o corpo da resposta com seguranca.
   * Retorna null quando nao ha conteudo ou JSON invalido.
   */
  const texto = await resposta.text()
  if (!texto) {
    return null
  }

  try {
    return JSON.parse(texto)
  } catch {
    return null
  }
}

async function buscarCategorias() {
  /*
   * Busca lista de categorias na API.
   * Valida o formato para evitar estado inconsistente.
   */
  const resposta = await buscarComFallback('/produtos/categorias')
  const dados = await lerRespostaJson(resposta)

  if (!resposta.ok) {
    const detalhe = typeof dados === 'object' && dados ? (dados as { detail?: string }).detail : undefined
    throw new Error(detalhe ?? `Erro ${resposta.status} ao carregar categorias`)
  }

  if (!Array.isArray(dados)) {
    throw new Error('Resposta invalida de categorias')
  }

  return dados as string[]
}

async function buscarImagensCategorias() {
  /*
   * Busca mapeamento categoria -> imagem.
   * Garante que o retorno seja um objeto simples.
   */
  const resposta = await buscarComFallback('/produtos/categorias-imagens')
  const dados = await lerRespostaJson(resposta)

  if (!resposta.ok) {
    const detalhe = typeof dados === 'object' && dados ? (dados as { detail?: string }).detail : undefined
    throw new Error(detalhe ?? `Erro ${resposta.status} ao carregar imagens`) 
  }

  if (!dados || typeof dados !== 'object' || Array.isArray(dados)) {
    throw new Error('Resposta invalida de imagens')
  }

  return dados as MapaImagensCategoria
}

function paraNumeroOuNulo(value: string) {
  /*
   * Converte input de texto em numero ou null.
   * Evita NaN propagando valores vazios.
   */
  const normalizado = value.trim()
  if (!normalizado) {
    return null
  }

  const convertido = Number(normalizado)
  return Number.isNaN(convertido) ? null : convertido
}

function normalizarBase(base: string) {
  /*
   * Remove barra final de URLs base.
   * Mantem consistencia ao montar endpoints.
   */
  return base.endsWith('/') ? base.slice(0, -1) : base
}

async function buscarComFallback(path: string, init?: RequestInit) {
  /*
   * Tenta varios endpoints ate encontrar um valido.
   * Retorna a ultima resposta/erro se nenhum funcionar.
   */
  let ultimaResposta: Response | null = null
  let ultimoErro: Error | null = null

  for (const base of API_CANDIDATAS) {
    try {
      const resposta = await fetch(`${normalizarBase(base)}${path}`, init)
      if (resposta.ok) {
        return resposta
      }

      ultimaResposta = resposta
    } catch (erro) {
      if (erro instanceof Error) {
        ultimoErro = erro
      }
    }
  }

  if (ultimaResposta) {
    return ultimaResposta
  }

  if (ultimoErro) {
    throw ultimoErro
  }

  throw new Error('Nao foi possivel conectar na API')
}

function PainelCatalogo() {
  /*
   * Componente principal do painel do catalogo.
   * Orquestra filtros, detalhes, CRUD e chamadas da API.
   */
  const [itens, setItens] = useState<ProdutoItemLista[]>([])
  const [total, setTotal] = useState(0)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const [busca, setBusca] = useState('')
  const [categoriasSelecionadas, setCategoriasSelecionadas] = useState<string[]>([])
  const [notaMinima, setNotaMinima] = useState('')
  const [precoMinimo, setPrecoMinimo] = useState('')
  const [precoMaximo, setPrecoMaximo] = useState('')
  const [buscaDebounce, setBuscaDebounce] = useState('')
  const [categoriasDebounce, setCategoriasDebounce] = useState<string[]>([])
  const [notaMinimaDebounce, setNotaMinimaDebounce] = useState('')
  const [precoMinimoDebounce, setPrecoMinimoDebounce] = useState('')
  const [precoMaximoDebounce, setPrecoMaximoDebounce] = useState('')
  const [pagina, setPagina] = useState(1)
  const [todasCategorias, setTodasCategorias] = useState<string[]>([])
  const [erroCategorias, setErroCategorias] = useState<string | null>(null)
  const [imagensCategorias, setImagensCategorias] = useState<MapaImagensCategoria>({})
  const [categoriasAberto, setCategoriasAberto] = useState(false)

  const [idSelecionado, setIdSelecionado] = useState<string | null>(null)
  const [detalhe, setDetalhe] = useState<ProdutoDetalhe | null>(null)
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false)

  const [formularioAberto, setFormularioAberto] = useState(false)
  const [idEdicao, setIdEdicao] = useState<string | null>(null)
  const [formulario, setFormulario] = useState<DadosProduto>(formularioVazio)
  const [enviando, setEnviando] = useState(false)
  const [mostrarSugestoesCategoria, setMostrarSugestoesCategoria] = useState(false)

  const totalPaginas = Math.max(1, Math.ceil(total / TAMANHO_PAGINA))

  async function carregarProdutos(paginaAtual = pagina) {
    /*
     * Carrega a listagem com filtros e paginacao.
     * Atualiza estado de itens, total e categorias.
     */
    setCarregando(true)
    setErro(null)

    const parametros = new URLSearchParams({
      skip: String((paginaAtual - 1) * TAMANHO_PAGINA),
      limit: String(TAMANHO_PAGINA),
    })

    if (buscaDebounce.trim()) {
      parametros.set('busca', buscaDebounce.trim())
    }
    if (categoriasDebounce.length > 0) {
      categoriasDebounce.forEach((categoria) => {
        if (categoria.trim()) {
          parametros.append('categoria', categoria.trim())
        }
      })
    }
    if (notaMinimaDebounce.trim()) {
      parametros.set('nota_min', notaMinimaDebounce.trim())
    }
    if (precoMinimoDebounce.trim()) {
      parametros.set('preco_min', precoMinimoDebounce.trim())
    }
    if (precoMaximoDebounce.trim()) {
      parametros.set('preco_max', precoMaximoDebounce.trim())
    }

    try {
      const dados = await buscarJson<ProdutoRespostaLista>(`/produtos?${parametros.toString()}`)
      setItens(dados.itens)
      setTotal(dados.total)

      if (todasCategorias.length === 0) {
        try {
          const categorias = await buscarCategorias()
          console.info('categorias:total', categorias.length)
          setTodasCategorias(categorias)
          setErroCategorias(null)
        } catch (err) {
          setErroCategorias(err instanceof Error ? err.message : 'Erro ao carregar categorias')
          const alternativa = Array.from(
            new Set(dados.itens.map((item) => item.categoria_produto).filter(Boolean)),
          ).sort()
          if (alternativa.length > 0) {
            setTodasCategorias(alternativa)
          }
        }
      }

      if (dados.itens.length === 0) {
        setIdSelecionado(null)
        setDetalhe(null)
        return
      }

      const temSelecionado = idSelecionado
        ? dados.itens.some((item) => item.id_produto === idSelecionado)
        : false

      if (!temSelecionado) {
        setIdSelecionado(dados.itens[0].id_produto)
      }
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro inesperado')
    } finally {
      setCarregando(false)
    }
  }

  async function carregarDetalhe(produtoId: string) {
    /*
     * Carrega detalhes do produto selecionado.
     * Inclui historico de vendas e avaliacoes.
     */
    setCarregandoDetalhe(true)
    setErro(null)
    try {
      const dados = await buscarJson<ProdutoDetalhe>(`/produtos/${produtoId}`)
      setDetalhe(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar detalhes')
      setDetalhe(null)
    } finally {
      setCarregandoDetalhe(false)
    }
  }

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setBuscaDebounce(busca)
      setCategoriasDebounce(categoriasSelecionadas)
      setNotaMinimaDebounce(notaMinima)
      setPrecoMinimoDebounce(precoMinimo)
      setPrecoMaximoDebounce(precoMaximo)
    }, 300)

    return () => {
      window.clearTimeout(timeout)
    }
  }, [busca, categoriasSelecionadas, notaMinima, precoMinimo, precoMaximo])

  useEffect(() => {
    void carregarProdutos(1)
    setPagina(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buscaDebounce, categoriasDebounce, notaMinimaDebounce, precoMinimoDebounce, precoMaximoDebounce])


  useEffect(() => {
    async function carregarCategorias() {
      try {
        const dados = await buscarCategorias()
        console.info('categorias:total', dados.length)
        setTodasCategorias(dados)
        setErroCategorias(null)
      } catch (err) {
        setErroCategorias(err instanceof Error ? err.message : 'Erro ao carregar categorias')
      }
    }

    void carregarCategorias()
  }, [])

  useEffect(() => {
    async function carregarImagensCategorias() {
      try {
        const dados = await buscarImagensCategorias()
        setImagensCategorias(dados)
      } catch (err) {
        console.info('categorias:imagens', err)
      }
    }

    void carregarImagensCategorias()
  }, [])

  useEffect(() => {
    if (!idSelecionado) {
      return
    }
    void carregarDetalhe(idSelecionado)
  }, [idSelecionado])

  function abrirFormularioCriacao() {
    /*
     * Abre o formulario de criacao com valores vazios.
     * Reseta estado de edicao e sugestoes.
     */
    setIdEdicao(null)
    setFormulario(formularioVazio)
    setMostrarSugestoesCategoria(false)
    setFormularioAberto(true)
  }

  function abrirFormularioEdicao(item: ProdutoItemLista) {
    /*
     * Abre o formulario de edicao com dados do item.
     * Usa medidas do detalhe quando disponiveis.
     */
    setIdEdicao(item.id_produto)
    setFormulario({
      nome_produto: item.nome_produto,
      categoria_produto: item.categoria_produto,
      descricao_produto: item.descricao_produto,
      preco_base: item.preco_base,
      peso_produto_gramas: detalhe?.medidas.peso_produto_gramas ?? null,
      comprimento_centimetros: detalhe?.medidas.comprimento_centimetros ?? null,
      altura_centimetros: detalhe?.medidas.altura_centimetros ?? null,
      largura_centimetros: detalhe?.medidas.largura_centimetros ?? null,
    })
    setMostrarSugestoesCategoria(false)
    setFormularioAberto(true)
  }

  function selecionarSugestaoCategoria(value: string) {
    /*
     * Aplica a sugestao de categoria ao formulario.
     * Fecha o painel de sugestoes.
     */
    setFormulario((prev) => ({ ...prev, categoria_produto: value }))
    setMostrarSugestoesCategoria(false)
  }

  function alternarCategoria(value: string) {
    /*
     * Alterna categoria selecionada nos filtros.
     * Remove se ja estiver marcada, adiciona caso contrario.
     */
    setCategoriasSelecionadas((prev) =>
      prev.includes(value)
        ? prev.filter((current) => current !== value)
        : [...prev, value],
    )
  }

  async function aoEnviarFormulario(event: FormEvent<HTMLFormElement>) {
    /*
     * Envia criacao/edicao para a API.
     * Recarrega a lista ao concluir com sucesso.
     */
    event.preventDefault()
    setEnviando(true)
    setErro(null)

    const dados: DadosProduto = {
      nome_produto: formulario.nome_produto.trim(),
      categoria_produto: formulario.categoria_produto.trim(),
      descricao_produto: formulario.descricao_produto?.trim() || null,
      preco_base: formulario.preco_base,
      peso_produto_gramas: formulario.peso_produto_gramas,
      comprimento_centimetros: formulario.comprimento_centimetros,
      altura_centimetros: formulario.altura_centimetros,
      largura_centimetros: formulario.largura_centimetros,
    }

    try {
      const ehEdicao = Boolean(idEdicao)

      const resposta = await buscarComFallback(ehEdicao ? `/produtos/${idEdicao}` : '/produtos', {
        method: ehEdicao ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados),
      })

      if (!resposta.ok) {
        const corpo = await resposta.json().catch(() => null)
        const mensagemDetalhe = corpo?.detail ?? 'Nao foi possivel salvar o produto'
        throw new Error(mensagemDetalhe)
      }

      setFormularioAberto(false)
      await carregarProdutos(pagina)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao salvar produto')
    } finally {
      setEnviando(false)
    }
  }

  async function aoExcluirProduto(id: string) {
    /*
     * Remove produto via API apos confirmacao.
     * Recarrega a listagem para refletir a exclusao.
     */
    const confirmado = window.confirm('Deseja remover este produto?')
    if (!confirmado) {
      return
    }

    setErro(null)
    try {
      const resposta = await buscarComFallback(`/produtos/${id}`, {
        method: 'DELETE',
      })

      if (!resposta.ok) {
        const corpo = await resposta.json().catch(() => null)
        throw new Error(corpo?.detail ?? 'Nao foi possivel remover o produto')
      }

      if (idSelecionado === id) {
        setIdSelecionado(null)
      }

      await carregarProdutos(pagina)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao remover produto')
    }
  }

  function formatarMoeda(valor: number | null) {
    /*
     * Formata valores monetarios no padrao pt-BR.
     * Retorna "-" quando o valor e ausente.
     */
    if (valor == null) {
      return '-'
    }

    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    })
  }

  function formatarData(valor: string | null) {
    /*
     * Converte datas ISO para exibicao pt-BR.
     * Retorna "-" quando o valor e vazio.
     */
    if (!valor) {
      return '-'
    }

    return new Date(valor).toLocaleDateString('pt-BR')
  }

  function iniciaisCategoria(valor: string) {
    /*
     * Gera iniciais de categoria para o placeholder.
     * Usa ate duas partes separadas por underscore.
     */
    return valor
      .split('_')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('')
  }

  return (
    <main className="dashboard">
      <header className="hero-panel">
        <div>
          <p className="eyebrow">Painel do gerente</p>
          <h1>Gestao de catalogo e desempenho</h1>
          <p className="subhead">
            Controle produtos, avaliacoes e historico de vendas em um unico lugar.
          </p>
        </div>
        <button className="primary" onClick={abrirFormularioCriacao}>
          Novo produto
        </button>
      </header>

      <section className="filters">
        <input
          type="text"
          placeholder="Buscar por nome, categoria ou descricao"
          value={busca}
          onChange={(event) => setBusca(event.target.value)}
        />

        <div className="multi-select">
          <button
            type="button"
            className={`toggle ${categoriasAberto ? 'active' : ''}`}
            onClick={() => setCategoriasAberto((prev) => !prev)}
            aria-expanded={categoriasAberto}
            aria-controls="category-panel"
          >
            Categorias
            <span className="toggle-count">
              {categoriasSelecionadas.length > 0 ? categoriasSelecionadas.length : 'Todas'}
            </span>
          </button>
          {categoriasAberto && (
            <div className="multi-select-panel" id="category-panel">
              <div className="category-options" role="listbox" aria-multiselectable="true">
                {todasCategorias.map((categoriaAtual) => {
                  const ativo = categoriasSelecionadas.includes(categoriaAtual)
                  return (
                    <button
                      key={categoriaAtual}
                      type="button"
                      role="option"
                      aria-selected={ativo}
                      className={`category-option ${ativo ? 'active' : ''}`}
                      onClick={() => alternarCategoria(categoriaAtual)}
                    >
                      {categoriaAtual}
                    </button>
                  )
                })}
              </div>
              <button
                type="button"
                className="clear"
                onClick={() => setCategoriasSelecionadas([])}
                disabled={categoriasSelecionadas.length === 0}
              >
                Limpar
              </button>
            </div>
          )}
        </div>

        <input
          type="number"
          min="0"
          max="5"
          step="0.1"
          placeholder="Nota minima"
          value={notaMinima}
          onChange={(event) => setNotaMinima(event.target.value)}
        />

        <div className="price-range">
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Preco minimo"
            value={precoMinimo}
            onChange={(event) => setPrecoMinimo(event.target.value)}
          />
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Preco maximo"
            value={precoMaximo}
            onChange={(event) => setPrecoMaximo(event.target.value)}
          />
        </div>
      </section>

      <section className="category-chips" aria-label="Categorias selecionadas">
        {categoriasSelecionadas.length > 0 ? (
          categoriasSelecionadas.map((categoria) => (
            <button
              key={categoria}
              type="button"
              className="chip active"
              onClick={() =>
                setCategoriasSelecionadas((prev) => prev.filter((current) => current !== categoria))
              }
            >
              {categoria}
            </button>
          ))
        ) : (
          <p className="chip-empty">Nenhuma categoria selecionada.</p>
        )}
      </section>

      {erro && <p className="error">{erro}</p>}
      {erroCategorias && <p className="error">{erroCategorias}</p>}

      <section className="content-grid">
        <article className="catalog-card">
          <div className="section-head">
            <h2>Catalogo</h2>
            <span>{total} registros</span>
          </div>

          {carregando ? (
            <p>Carregando produtos...</p>
          ) : itens.length === 0 ? (
            <p>Nenhum produto encontrado para os filtros selecionados.</p>
          ) : (
            <ul className="product-list">
              {itens.map((item) => (
                <li
                  key={item.id_produto}
                  className={item.id_produto === idSelecionado ? 'active' : ''}
                  onClick={() => setIdSelecionado(item.id_produto)}
                >
                  <div className="product-card">
                    <div className="product-thumb">
                      {imagensCategorias[item.categoria_produto] ? (
                        <img
                          src={imagensCategorias[item.categoria_produto]}
                          alt={item.categoria_produto}
                          loading="lazy"
                        />
                      ) : (
                        <span>{iniciaisCategoria(item.categoria_produto)}</span>
                      )}
                    </div>
                    <div className="product-main">
                      <div className="product-title-row">
                        <h3>{item.nome_produto}</h3>
                        {item.quantidade_registros > 1 && (
                          <span className="summary-badge">{item.quantidade_registros} registros</span>
                        )}
                      </div>
                      <p>{item.categoria_produto}</p>
                      <div className="metrics">
                        <span>{formatarMoeda(item.preco_base)}</span>
                        <span>
                          {item.media_avaliacoes != null ? `${item.media_avaliacoes.toFixed(1)} / 5` : 'Sem nota'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="actions">
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation()
                        setIdSelecionado(item.id_produto)
                        abrirFormularioEdicao(item)
                      }}
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      className="danger"
                      onClick={(event) => {
                        event.stopPropagation()
                        void aoExcluirProduto(item.id_produto)
                      }}
                    >
                      Excluir
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <footer className="pagination">
            <button
              type="button"
              onClick={() => {
                const proximaPagina = Math.max(1, pagina - 1)
                setPagina(proximaPagina)
                void carregarProdutos(proximaPagina)
              }}
              disabled={pagina <= 1}
            >
              Anterior
            </button>
            <span>
              Pagina {pagina} de {totalPaginas}
            </span>
            <button
              type="button"
              onClick={() => {
                const proximaPagina = Math.min(totalPaginas, pagina + 1)
                setPagina(proximaPagina)
                void carregarProdutos(proximaPagina)
              }}
              disabled={pagina >= totalPaginas}
            >
              Proxima
            </button>
          </footer>
        </article>

        <article className="details-card">
          <div className="section-head">
            <h2>Detalhes</h2>
          </div>

          {carregandoDetalhe ? (
            <p>Carregando detalhes...</p>
          ) : !detalhe ? (
            <p>Selecione um produto para ver as informacoes completas.</p>
          ) : (
            <>
              <div className="summary-row">
                <div className="detail-hero">
                  <div className="detail-thumb">
                    {imagensCategorias[detalhe.categoria_produto] ? (
                      <img
                        src={imagensCategorias[detalhe.categoria_produto]}
                        alt={detalhe.categoria_produto}
                        loading="lazy"
                      />
                    ) : (
                      <span>{iniciaisCategoria(detalhe.categoria_produto)}</span>
                    )}
                  </div>
                  <div>
                    <h3>{detalhe.nome_produto}</h3>
                    <p>{detalhe.categoria_produto}</p>
                    <p>{detalhe.descricao_produto || 'Sem descricao cadastrada'}</p>
                  </div>
                </div>
              </div>

              <div className="stat-grid">
                <div>
                  <span>Preco base</span>
                  <strong>{formatarMoeda(detalhe.preco_base)}</strong>
                </div>
                <div>
                  <span>Media de avaliacoes</span>
                  <strong>
                    {detalhe.media_avaliacoes != null ? `${detalhe.media_avaliacoes.toFixed(2)} / 5` : 'Sem nota'}
                  </strong>
                </div>
                <div>
                  <span>Total de vendas</span>
                  <strong>{detalhe.total_vendas}</strong>
                </div>
              </div>

              <div className="measures">
                <h4>Medidas tecnicas</h4>
                <p>Peso: {detalhe.medidas.peso_produto_gramas ?? '-'} g</p>
                <p>Comprimento: {detalhe.medidas.comprimento_centimetros ?? '-'} cm</p>
                <p>Altura: {detalhe.medidas.altura_centimetros ?? '-'} cm</p>
                <p>Largura: {detalhe.medidas.largura_centimetros ?? '-'} cm</p>
              </div>

              <div className="tables">
                <section>
                  <h4>Historico de vendas</h4>
                  {detalhe.vendas_historico.length === 0 ? (
                    <p>Sem vendas registradas.</p>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Pedido</th>
                          <th>Data</th>
                          <th>Itens</th>
                          <th>Total</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detalhe.vendas_historico.map((venda) => (
                          <tr key={venda.id_pedido}>
                            <td>{venda.id_pedido}</td>
                            <td>{formatarData(venda.data_pedido)}</td>
                            <td>{venda.quantidade_itens}</td>
                            <td>{formatarMoeda(venda.valor_total)}</td>
                            <td>{venda.status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </section>

                <section>
                  <h4>Avaliacoes</h4>
                  {detalhe.avaliacoes.length === 0 ? (
                    <p>Sem avaliacoes registradas.</p>
                  ) : (
                    <ul className="reviews">
                      {detalhe.avaliacoes.map((avaliacao) => (
                        <li key={avaliacao.id_avaliacao}>
                          <strong>{avaliacao.nota} / 5</strong>
                          <p>{avaliacao.titulo || 'Sem titulo'}</p>
                          <small>{avaliacao.comentario || 'Sem comentario'}</small>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>
            </>
          )}
        </article>
      </section>

      {formularioAberto && (
        <section className="modal-backdrop" onClick={() => setFormularioAberto(false)}>
          <form className="product-form" onSubmit={aoEnviarFormulario} onClick={(event) => event.stopPropagation()}>
            <h3>{idEdicao ? 'Editar produto' : 'Novo produto'}</h3>

            <label>
              Nome
              <input
                type="text"
                required
                value={formulario.nome_produto}
                onChange={(event) => setFormulario((prev) => ({ ...prev, nome_produto: event.target.value }))}
              />
            </label>

            <label>
              Categoria
              <input
                type="text"
                required
                value={formulario.categoria_produto}
                onChange={(event) => {
                  const value = event.target.value
                  setFormulario((prev) => ({ ...prev, categoria_produto: value }))
                  setMostrarSugestoesCategoria(Boolean(value.trim()))
                }}
                onFocus={() => setMostrarSugestoesCategoria(Boolean(formulario.categoria_produto.trim()))}
                onBlur={() => window.setTimeout(() => setMostrarSugestoesCategoria(false), 120)}
              />
              {mostrarSugestoesCategoria && (
                <div className="category-suggestions" role="listbox">
                  {todasCategorias
                    .filter((categoriaAtual) =>
                      categoriaAtual.toLowerCase().includes(formulario.categoria_produto.toLowerCase()),
                    )
                    .slice(0, 8)
                    .map((categoriaAtual) => (
                      <button
                        type="button"
                        key={categoriaAtual}
                        className="category-suggestion"
                        onMouseDown={() => selecionarSugestaoCategoria(categoriaAtual)}
                      >
                        {categoriaAtual}
                      </button>
                    ))}
                </div>
              )}
            </label>

            <label>
              Descricao
              <textarea
                rows={3}
                value={formulario.descricao_produto ?? ''}
                onChange={(event) => setFormulario((prev) => ({ ...prev, descricao_produto: event.target.value }))}
              />
            </label>

            <div className="row-grid">
              <label>
                Preco base
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.preco_base ?? ''}
                  onChange={(event) => setFormulario((prev) => ({ ...prev, preco_base: paraNumeroOuNulo(event.target.value) }))}
                />
              </label>
              <label>
                Peso (g)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.peso_produto_gramas ?? ''}
                  onChange={(event) => setFormulario((prev) => ({ ...prev, peso_produto_gramas: paraNumeroOuNulo(event.target.value) }))}
                />
              </label>
              <label>
                Comprimento (cm)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.comprimento_centimetros ?? ''}
                  onChange={(event) => setFormulario((prev) => ({ ...prev, comprimento_centimetros: paraNumeroOuNulo(event.target.value) }))}
                />
              </label>
              <label>
                Altura (cm)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.altura_centimetros ?? ''}
                  onChange={(event) => setFormulario((prev) => ({ ...prev, altura_centimetros: paraNumeroOuNulo(event.target.value) }))}
                />
              </label>
              <label>
                Largura (cm)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.largura_centimetros ?? ''}
                  onChange={(event) => setFormulario((prev) => ({ ...prev, largura_centimetros: paraNumeroOuNulo(event.target.value) }))}
                />
              </label>
            </div>

            <div className="form-actions">
              <button type="button" onClick={() => setFormularioAberto(false)}>
                Cancelar
              </button>
              <button className="primary" type="submit" disabled={enviando}>
                {enviando ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        </section>
      )}
    </main>
  )
}

export default PainelCatalogo
