import type { ProductListItem } from '../types'

type ProductListPanelProps = {
  items: ProductListItem[]
  total: number
  page: number
  totalPages: number
  isLoading: boolean
  selectedId: string | null
  onSelectItem: (id: string) => void
  onEditItem: (item: ProductListItem) => void
  onDeleteItem: (id: string) => void
  onPreviousPage: () => void
  onNextPage: () => void
  formatCurrency: (value: number | null) => string
}

export function ProductListPanel({
  items,
  total,
  page,
  totalPages,
  isLoading,
  selectedId,
  onSelectItem,
  onEditItem,
  onDeleteItem,
  onPreviousPage,
  onNextPage,
  formatCurrency,
}: ProductListPanelProps) {
  return (
    <article className="catalog-card">
      <div className="section-head">
        <h2>Catalogo</h2>
        <span>{total} registros</span>
      </div>

      {isLoading ? (
        <p>Carregando produtos...</p>
      ) : items.length === 0 ? (
        <p>Nenhum produto encontrado para os filtros selecionados.</p>
      ) : (
        <ul className="product-list">
          {items.map((item) => (
            <li
              key={item.id_produto}
              className={item.id_produto === selectedId ? 'active' : ''}
              onClick={() => onSelectItem(item.id_produto)}
            >
              <div className="product-card">
                <div className="product-main">
                  <div className="product-title-row">
                    <h3>{item.nome_produto}</h3>
                    {item.quantidade_registros > 1 && (
                      <span className="summary-badge">{item.quantidade_registros} registros</span>
                    )}
                  </div>
                  <p>{item.categoria_produto}</p>
                  <div className="metrics">
                    <span>{formatCurrency(item.preco_base)}</span>
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
                    onSelectItem(item.id_produto)
                    onEditItem(item)
                  }}
                >
                  Editar
                </button>
                <button
                  type="button"
                  className="danger"
                  onClick={(event) => {
                    event.stopPropagation()
                    onDeleteItem(item.id_produto)
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
        <button type="button" onClick={onPreviousPage} disabled={page <= 1}>
          Anterior
        </button>
        <span>
          Pagina {page} de {totalPages}
        </span>
        <button type="button" onClick={onNextPage} disabled={page >= totalPages}>
          Proxima
        </button>
      </footer>
    </article>
  )
}