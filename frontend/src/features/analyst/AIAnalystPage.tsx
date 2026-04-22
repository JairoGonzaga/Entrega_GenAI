import { useMemo, useRef, useEffect } from 'react'
import { IoPaperPlaneOutline } from 'react-icons/io5'
import { useAnalystChat } from './useAnalystChat'

export function AIAnalystPage() {
  const chat = useAnalystChat()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const questionInputRef = useRef<HTMLTextAreaElement>(null)

  const getSqlRows = (sql: string) => {
    const lineCount = sql.split(/\r?\n/).length
    // Cresce com o conteudo, mas limita para manter o layout estavel.
    return Math.min(Math.max(lineCount + 1, 5), 20)
  }

  const previewColumns = useMemo(() => {
    const lastWithRows = [...chat.messages].reverse().find((message) => message.rows && message.rows.length > 0)
    if (!lastWithRows?.rows?.length) {
      return [] as string[]
    }

    return Object.keys(lastWithRows.rows[0])
  }, [chat.messages])

  // Auto-scroll para a ultima mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' })
  }, [chat.messages, chat.isLoading])

  useEffect(() => {
    const textarea = questionInputRef.current
    if (!textarea) {
      return
    }

    textarea.style.height = 'auto'

    const computed = window.getComputedStyle(textarea)
    const lineHeight = Number.parseFloat(computed.lineHeight) || 22
    const paddingTop = Number.parseFloat(computed.paddingTop) || 0
    const paddingBottom = Number.parseFloat(computed.paddingBottom) || 0
    const maxHeight = lineHeight * 5 + paddingTop + paddingBottom

    const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
    textarea.style.height = `${nextHeight}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [chat.draft])

  return (
    <main className="analyst-page">
      <header className="analyst-hero">
        <p className="eyebrow">AI Analyst</p>
        <h1>Análise Text-to-SQL Inteligente</h1>
        <p>
          Faça perguntas em linguagem natural e obtenha insights através de SQL gerado automaticamente.
        </p>
      </header>

      {chat.error && (
        <div className="error-banner">
          <span>⚠️ Erro:</span> {chat.error}
        </div>
      )}

      <section className="analyst-chat-container">
        <div className="chat-messages">
          {chat.messages.map((message) => (
            <div key={message.id} className={`message-group ${message.role}`}>
              <div className="message-bubble">
                <div className="message-header">
                  <span className="message-name">{message.role === 'user' ? 'Você' : 'Analista'}</span>
                </div>
                <div className="message-content">
                  <p className="message-text">{message.text}</p>

                  {message.sql && (
                    <details className="message-details">
                      <summary className="details-summary">
                        <span className="sql-icon">📊</span> SQL Gerada
                      </summary>
                      <textarea
                        className="message-sql"
                        value={message.sql}
                        readOnly
                        rows={getSqlRows(message.sql)}
                        aria-label="SQL gerada"
                      />
                    </details>
                  )}

                  {message.rows && message.rows.length > 0 && previewColumns.length > 0 && (
                    <div className="message-table-preview">
                      <div className="table-header">
                        <span className="table-icon">📋</span> Prévia dos Resultados
                      </div>
                      <div className="table-scroll">
                        <table className="preview-table">
                          <thead>
                            <tr>
                              {previewColumns.map((column) => (
                                <th key={column}>{column}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {message.rows.slice(0, 5).map((row, rowIndex) => (
                              <tr key={`${message.id}-${rowIndex}`}>
                                {previewColumns.map((column) => (
                                  <td key={`${message.id}-${rowIndex}-${column}`}>{String(row[column] ?? '-')}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {message.rows.length > 5 && (
                        <p className="table-more">... e mais {message.rows.length - 5} linha(s)</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {chat.isLoading && (
            <div className="message-group assistant">
              <div className="message-bubble">
                <div className="message-header">
                  <span className="message-name">Analista</span>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p className="message-text">Analisando sua pergunta...</p>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="analyst-input-area">
          <div className="input-wrapper">
            <textarea
              ref={questionInputRef}
              id="analyst-question"
              className="analyst-textarea"
              aria-label="Pergunta"
              value={chat.draft}
              rows={1}
              placeholder="Faça uma pergunta... Ex: Qual produto teve mais vendas?"
              onChange={(event) => chat.setDraft(event.target.value)}
              disabled={chat.isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  void chat.sendMessage()
                }
              }}
            />
            <button
              type="button"
              className="send-button"
              aria-label="Enviar"
              onClick={() => void chat.sendMessage()}
              disabled={chat.isLoading || !chat.draft.trim()}
              title="Enviar"
            >
              <span className="send-icon" aria-hidden="true">
                <IoPaperPlaneOutline />
              </span>
            </button>
          </div>
          <p className="input-hint">Dica: Enter envia e Shift+Enter quebra linha</p>
        </div>
      </section>
    </main>
  )
}

export default AIAnalystPage
