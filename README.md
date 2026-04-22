# E-Commerce AI Analyst

Agente analítico em linguagem natural para consultar o banco do e-commerce via Text-to-SQL, com guardrails, validação de SQL, execução segura e interpretação em português.

## O que o agente faz

- recebe perguntas em linguagem natural
- identifica a intenção da pergunta
- lê o schema do SQLite e usa chaves, tipos e amostras de valores reais
- monta um plano interno de consulta
- gera SQL apenas de leitura
- valida o SQL antes de executar
- executa a consulta no banco local
- interpreta o resultado em português
- mantém contexto por sessão
- sugere perguntas de continuidade

## Como configurar

1. Copie o arquivo de exemplo de ambiente:

```powershell
copy backend\.env.example backend\.env
```

2. Se quiser respostas reais do Gemini, preencha uma das chaves no `backend\.env`:
- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`

3. O banco SQLite já vem apontado no exemplo de ambiente. Se necessário, ajuste `DATABASE_URL` para o arquivo do seu ambiente.

## Como executar

Abra dois terminais na raiz do projeto.

No primeiro terminal, inicie a aplicação principal:

```powershell
cd backend
python -m app.main
```

No segundo terminal, inicie a interface local do agente:

```powershell
cd frontend
corepack pnpm install
corepack pnpm dev
```

Acesse a interface em:
- http://localhost:5173

A API do agente fica disponível em:
- http://localhost:8000

## Como usar

1. Abra a interface local.
2. Digite uma pergunta em português.
3. Pressione `Enter` para enviar.
4. Use `Shift+Enter` para quebrar linha.
5. Veja o SQL gerado, os dados retornados e a interpretação em português.

Exemplos de perguntas:
- Top 10 produtos mais vendidos
- Percentual de pedidos entregues no prazo por estado
- Média de avaliação por vendedor
- Estados com maior ticket médio
- Categorias com maior taxa de avaliação negativa

## Observação sobre Gemini

Se nenhuma chave de API estiver configurada, o projeto continua subindo, mas as rotas do agente que dependem do Gemini retornam uma mensagem amigável indicando que a API não está configurada.

## Arquivos importantes

- `backend/app/routers/agent/agent.py`: endpoints do agente
- `backend/app/routers/agent/pipeline.py`: orquestração do fluxo do agente
- `backend/app/routers/agent/llm.py`: integração com Gemini e tratamento de erros
- `backend/app/routers/agent/prompts.py`: schema, regras e contexto do banco
- `backend/app/routers/agent/guardrails.py`: validações de segurança
- `backend/app/routers/agent/memory.py`: memória por sessão
- `backend/app/routers/agent/interpreter.py`: interpretação e follow-ups

## Testes

Rodar a suíte do backend:

```powershell
cd backend
python -m pytest -q
```

Rodar a suíte da interface:

```powershell
cd frontend
corepack pnpm test --run
```
