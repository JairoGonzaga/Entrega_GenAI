  # Entrega DEV - Sistema de Gerenciamento de E-Commerce

  Projeto full stack desenvolvido para o desafio de entrega do modulo DEV.

  Stack usada:
  - Frontend: React + TypeScript + Vite
  - Backend: FastAPI (Python)
  - Banco: SQLite com SQLAlchemy
  - Migracoes: Alembic

  ## Objetivo da entrega

  Disponibilizar um painel para o perfil Gerente com:
  - catalogo de produtos
  - busca e filtros
  - detalhe de produto (medidas, historico de vendas e avaliacoes)
  - CRUD de produtos
  - media de avaliacoes por produto

  ## Estrutura

  ```
  Entrega_DEV_Visagio/
  |- backend/          # API FastAPI, models, testes e migracoes
  |- frontend/         # App React para o painel de catalogo
  |- atividade.md      # Enunciado da atividade
  |- requisitos.md     # Documento de requisitos
  ```

  ## Como executar

  ## 1. Backend

  Pre-requisitos:
  - Python 3.11+

  Passos:

  1. Abrir terminal na pasta backend
  2. Criar e ativar ambiente virtual

  Windows (PowerShell):

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

  3. Instalar dependencias

  ```powershell
  pip install -r requirements.txt
  ```

  4. (Opcional) aplicar migracoes

  ```powershell
  alembic upgrade head
  ```

  5. Rodar API

  Esse comando e suficiente desde que voce esteja dentro da pasta `backend` com o ambiente virtual ativado.

  ```powershell
  python -m app.main
  ```

  Backend disponivel em:
  - http://localhost:8000
  - Swagger: http://localhost:8000/docs

  Observacao:
  - A API usa o banco existente em `backend/Banco/banco.db`.
  - `data_ingestion.py` e legado e nao faz parte do fluxo atual.

  ## 2. Frontend

  Pre-requisitos:
  - Node.js 20+
  - pnpm

  Passos:

  1. Abrir terminal na pasta frontend
  2. Instalar dependencias

  ```powershell
  pnpm install
  ```

  3. Rodar em modo desenvolvimento

  ```powershell
  pnpm dev
  ```

  Frontend disponivel em:
  - http://localhost:5173

  Configuracao de API:
  - O frontend tenta, nessa ordem: VITE_API_BASE_URL, /api, http://127.0.0.1:8000/api e http://localhost:8000/api.
  - O proxy de desenvolvimento do Vite aponta para o backend em http://127.0.0.1:8000.
  - Se quiser fixar a URL, crie frontend/.env com:

  ```env
  VITE_API_BASE_URL=http://localhost:8000/api
  ```

  ## Testes

  Testes automatizados implementados no backend com pytest.

  Na pasta backend:

  ```powershell
  pytest -v
  ```

  Com cobertura:

  ```powershell
  pytest --cov=app --cov-report=term-missing
  ```

  Testes do frontend (Vitest):

  Na pasta frontend:

  ```powershell
  corepack pnpm test
  ```

  Modo watch:

  ```powershell
  corepack pnpm test:watch
  ```

  ## Git Hook (pre-push)

  Para habilitar os hooks locais do projeto:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup-git-hooks.ps1
  ```

  Hooks configurados:
  - `.githooks/pre-commit`: valida frontend lint + backend pytest
  - `.githooks/pre-push`: valida frontend lint/test + backend pytest

  Ambos chamam o CLI local do projeto:
  - `scripts/qa-cli.sh` (shell)
  - `scripts/qa-cli.ps1` (PowerShell)

  Uso manual no PowerShell:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\qa-cli.ps1 pre-commit
  powershell -ExecutionPolicy Bypass -File .\scripts\qa-cli.ps1 pre-push
  powershell -ExecutionPolicy Bypass -File .\scripts\qa-cli.ps1 full
  ```

  ## GitLab CI

  Arquivo pronto: `.gitlab-ci.yml`

  Pipeline configurado com dois jobs:
  - `frontend_tests`: instala dependencias e roda lint, testes e build do frontend
  - `backend_tests`: instala dependencias Python e roda pytest do backend

  ## Endpoints principais

  Prefixo da API: /api

  - GET /produtos
  - GET /produtos/categorias
  - GET /produtos/{id_produto}
  - POST /produtos
  - PUT /produtos/{id_produto}
  - DELETE /produtos/{id_produto}

  Healthcheck:
  - GET /

  ## CI/CD

  Pipeline automatizado configurado para validar frontend e backend:

  - **Frontend**: lint (ESLint), testes (Vitest) e build
  - **Backend**: testes (pytest)

  ## Estrutura do codigo

  ### Backend

  Organizacao por responsabilidade:
  - `models/`: definicoes de banco SQLAlchemy
  - `schemas/`: validacao Pydantic para request/response
  - `routers/`: endpoints da API
  - `database.py`: conexao e sessao
  - `data_ingestion.py`: compatibilidade legada, sem uso no fluxo atual
  - `main.py`: configuracao FastAPI

  ### Frontend

  Arquitetura modularizada:
  - `src/features/catalog/`: dominio de catálogo isolado
    - `types.ts`: tipos TypeScript
    - `api.ts`: chamadas HTTP
    - `utils.ts`: utilitarios (busca, paginacao)
    - `useCatalogPanel.ts`: gerenciamento de estado
    - `components/`: componentes UI
    - `CatalogPage.tsx`: pagina principal
  - `src/App.tsx`: entrada da aplicacao
  - `src/App.css`: estilos globais

  ## Status atual da entrega

  ✅ Backend funcional
  - CRUD de produtos com validacoes
  - Testes cobrindo cenarios principais

  ✅ Frontend funcional
  - Listagem e filtros
  - Detalhes com historico de vendas e avaliacoes
  - Criacao, edicao e remocao de produtos
  - Tratamento de erros com mensagens claras
  - Pronto para produção (Vercel ou similar)

  ## DevOps
  - CI/CD automatizado
  - CI GitLab Pipeline (`.gitlab-ci.yml`)
  - Git hooks pre-push/pre-commit
  - QA CLI local versionado