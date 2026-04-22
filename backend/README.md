# Backend do Agente

Este diretório contém a API e a implementação do agente Text-to-SQL do projeto.

## Estrutura

```text
backend/
|- app/
|  |- main.py                  # Sobe a API e registra o agente
|  |- config.py                # Variáveis de ambiente e configurações
|  |- database.py              # Conexão com o SQLite
|  |- models/                  # Models do banco
|  |- routers/
|     |- agent/                # Lógica principal do agente
|     |  |- agent.py           # Endpoints HTTP do agente
|     |  |- pipeline.py        # Orquestração da pergunta até a resposta
|     |  |- prompts.py         # Schema, regras e contexto do banco
|     |  |- guardrails.py      # Validações de segurança
|     |  |- intent.py          # Classificação da intenção da pergunta
|     |  |- memory.py          # Memória por sessão
|     |  |- llm.py             # Integração com Gemini
|     |  |- interpreter.py     # Interpretação dos resultados
|- tests/                      # Testes automatizados do agente e da API
|- Banco/                      # Banco SQLite usado pelo projeto
```

## Como o agente funciona

1. O usuário envia uma pergunta em linguagem natural.
2. O backend valida a entrada com guardrails.
3. O agente identifica a intenção da pergunta.
4. O schema do SQLite é lido dinamicamente para capturar tabelas, chaves, tipos e valores reais de colunas categóricas.
5. O agente monta um plano interno de consulta.
6. O Gemini gera o SQL somente de leitura.
7. O SQL é validado antes da execução.
8. O SQLite executa a consulta.
9. O resultado é interpretado em português.
10. A resposta é devolvida com contexto de sessão e sugestões de follow-up.

## Por que essa arquitetura foi escolhida

- **Segurança primeiro**: o fluxo passa por guardrails antes do banco.
- **Melhor grounding**: o prompt usa schema real, chaves, tipos e amostras do banco.
- **Baixo acoplamento**: cada responsabilidade fica em um módulo separado.
- **Testabilidade**: planejamento, geração, reparo e interpretação têm testes próprios.
- **Escalabilidade do fluxo**: a mesma estrutura suporta resposta JSON e streaming SSE.

## Como usar o backend

1. Copie o exemplo de ambiente para `.env`:

```powershell
copy .env.example .env
```

2. Se quiser usar o Gemini, ajuste a chave em `.env`:

```dotenv
GEMINI_API_KEY=CHAVE_GEMINI_API_KEY
```

3. Inicie a API:

```powershell
python -m app.main
```

## Observações

- O arquivo `.env.example` já vem com um placeholder para a chave do Gemini.
- Se a chave não estiver preenchida, as rotas do agente retornam uma mensagem amigável de configuração ausente.
