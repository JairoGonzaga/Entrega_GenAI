import { useEffect, useRef, useState } from 'react'
import type { ProductDetail } from '../types'

type ProductDetailsPanelProps = {
  detail: ProductDetail | null
  isDetailLoading: boolean
  formatCurrency: (value: number | null) => string
  formatDate: (value: string | null) => string
}

type ReviewCommentProps = {
  comment: string
  isExpanded: boolean
  onToggle: () => void
}

type ReviewsSectionProps = {
  reviews: ProductDetail['avaliacoes']
}

function ReviewComment({ comment, isExpanded, onToggle }: ReviewCommentProps) {
  const commentRef = useRef<HTMLElement | null>(null)
  const [isOverflowing, setIsOverflowing] = useState(false)

  useEffect(() => {
    const element = commentRef.current
    if (!element) {
      return
    }

    const measureOverflow = () => {
      const wasExpanded = element.classList.contains('expanded')
      if (wasExpanded) {
        element.classList.remove('expanded')
      }

      const overflowing = element.scrollHeight > element.clientHeight + 1

      if (wasExpanded) {
        element.classList.add('expanded')
      }

      setIsOverflowing(overflowing)
    }

    measureOverflow()

    const resizeObserver = typeof ResizeObserver !== 'undefined'
      ? new ResizeObserver(() => measureOverflow())
      : null

    resizeObserver?.observe(element)
    window.addEventListener('resize', measureOverflow)

    return () => {
      resizeObserver?.disconnect()
      window.removeEventListener('resize', measureOverflow)
    }
  }, [comment])

  return (
    <>
      <small ref={commentRef} className={`review-comment ${isExpanded ? 'expanded' : ''}`}>
        {comment}
      </small>
      {(isOverflowing || isExpanded) && (
        <button type="button" className="link-button" onClick={onToggle}>
          {isExpanded ? 'Ver menos' : 'Ver mais'}
        </button>
      )}
    </>
  )
}

function ReviewsSection({ reviews }: ReviewsSectionProps) {
  const [expandedReviewIds, setExpandedReviewIds] = useState<Set<string>>(new Set())

  function toggleReview(reviewId: string) {
    setExpandedReviewIds((prev) => {
      const next = new Set(prev)
      if (next.has(reviewId)) {
        next.delete(reviewId)
      } else {
        next.add(reviewId)
      }
      return next
    })
  }

  if (reviews.length === 0) {
    return <p>Sem avaliacoes registradas.</p>
  }

  return (
    <div className="reviews-scroll" role="region" aria-label="Lista de avaliacoes">
      <ul className="reviews">
        {reviews.map((avaliacao) => {
          const isExpanded = expandedReviewIds.has(avaliacao.id_avaliacao)
          const comment = avaliacao.comentario?.trim() || 'Sem comentario'

          return (
            <li key={avaliacao.id_avaliacao}>
              <strong>{avaliacao.nota} / 5</strong>
              <p>{avaliacao.titulo || 'Sem titulo'}</p>
              <ReviewComment
                comment={comment}
                isExpanded={isExpanded}
                onToggle={() => toggleReview(avaliacao.id_avaliacao)}
              />
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export function ProductDetailsPanel({
  detail,
  isDetailLoading,
  formatCurrency,
  formatDate,
}: ProductDetailsPanelProps) {
  return (
    <article className="details-card">
      <div className="section-head">
        <h2>Detalhes</h2>
      </div>

      <div className="details-body">
        {isDetailLoading ? (
          <p>Carregando detalhes...</p>
        ) : !detail ? (
          <p>Selecione um produto para ver as informacoes completas.</p>
        ) : (
          <>
          <div className="summary-row">
            <div className="detail-hero">
              <div>
                <h3>{detail.nome_produto}</h3>
                <p>{detail.categoria_produto}</p>
                <p>{detail.descricao_produto || 'Sem descricao cadastrada'}</p>
              </div>
            </div>
          </div>

          <div className="stat-grid">
            <div>
              <span>Preco base</span>
              <strong>{formatCurrency(detail.preco_base)}</strong>
            </div>
            <div>
              <span>Media de avaliacoes</span>
              <strong>
                {detail.media_avaliacoes != null ? `${detail.media_avaliacoes.toFixed(2)} / 5` : 'Sem nota'}
              </strong>
            </div>
            <div>
              <span>Total de vendas</span>
              <strong>{detail.total_vendas}</strong>
            </div>
          </div>

          <div className="measures">
            <h4>Medidas tecnicas</h4>
            <p>Peso: {detail.medidas.peso_produto_gramas ?? '-'} g</p>
            <p>Comprimento: {detail.medidas.comprimento_centimetros ?? '-'} cm</p>
            <p>Altura: {detail.medidas.altura_centimetros ?? '-'} cm</p>
            <p>Largura: {detail.medidas.largura_centimetros ?? '-'} cm</p>
          </div>

          <div className="tables">
            <section>
              <h4>Historico de vendas</h4>
              {detail.vendas_historico.length === 0 ? (
                <p>Sem vendas registradas.</p>
              ) : (
                <div className="table-scroll" role="region" aria-label="Tabela de historico de vendas">
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
                      {detail.vendas_historico.map((venda) => (
                        <tr key={venda.id_pedido}>
                          <td>{venda.id_pedido}</td>
                          <td>{formatDate(venda.data_pedido)}</td>
                          <td>{venda.quantidade_itens}</td>
                          <td>{formatCurrency(venda.valor_total)}</td>
                          <td>{venda.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section>
              <h4>Avaliacoes</h4>
              <ReviewsSection key={detail.id_produto} reviews={detail.avaliacoes} />
            </section>
          </div>
          </>
        )}
      </div>
    </article>
  )
}