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
|- backend/          # API FastAPI, models, ingestao, testes e migracoes
|- frontend/         # App React para o painel de catalogo
|- data_ingestao/    # CSVs usados para carga inicial
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

```powershell
python -m app.main
```

Backend disponivel em:
- http://localhost:8000
- Swagger: http://localhost:8000/docs

Observacao:
- Ao iniciar, a API cria tabelas, popula dados a partir dos CSVs (quando necessario) e cria indices.

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

Para habilitar o hook versionado no repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-git-hooks.ps1
```

Hooks configurados:
- `.githooks/pre-commit`: valida frontend lint + backend pytest
- `.githooks/pre-push`: valida frontend lint/test + backend pytest

Ambos chamam o CLI versionado do repositorio:
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
- GET /produtos/categorias-imagens
- GET /produtos/{id_produto}
- POST /produtos
- PUT /produtos/{id_produto}
- DELETE /produtos/{id_produto}

Healthcheck:
- GET /

## Status atual da entrega

- Backend funcional com ingestao de dados e CRUD de produtos
- Frontend funcional com listagem, filtros, detalhes e formulario de criacao/edicao
- Testes de backend cobrindo cenarios de API e ingestao
