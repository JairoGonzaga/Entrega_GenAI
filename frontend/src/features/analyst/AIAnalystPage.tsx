import { useMemo, useRef, useEffect } from 'react'
import { useAnalystChat } from './useAnalystChat'

export function AIAnalystPage() {
  const chat = useAnalystChat()
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  return (
    <main className="analyst-page">
      <header className="analyst-hero">
        <p className="eyebrow">🤖 AI Analyst</p>
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
                  <span className="message-avatar">{message.role === 'user' ? '👤' : '🤖'}</span>
                  <span className="message-name">{message.role === 'user' ? 'Você' : 'Analista'}</span>
                </div>
                <div className="message-content">
                  <p className="message-text">{message.text}</p>

                  {message.sql && (
                    <details className="message-details">
                      <summary className="details-summary">
                        <span className="sql-icon">📊</span> SQL Gerada
                      </summary>
                      <pre className="message-sql">{message.sql}</pre>
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
                  <span className="message-avatar">🤖</span>
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
              id="analyst-question"
              className="analyst-textarea"
              aria-label="Pergunta"
              value={chat.draft}
              rows={1}
              placeholder="Faça uma pergunta... Ex: Qual produto teve mais vendas?"
              onChange={(event) => chat.setDraft(event.target.value)}
              disabled={chat.isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
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
              title="Enviar (Ctrl+Enter)"
            >
              <span>{chat.isLoading ? '⏳' : '📤'}</span>
            </button>
          </div>
          <p className="input-hint">Dica: Use Ctrl+Enter para enviar</p>
        </div>
      </section>
    </main>
  )
}

export default AIAnalystPage
