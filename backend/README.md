# Backend - Sistema de Compras Online

API REST em FastAPI para gerenciamento de catalogo de produtos com metricas de vendas e avaliacoes.

## Tecnologias

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- SQLite
- Pytest

## Estrutura principal

```
backend/
|- app/
|  |- main.py                  # Inicializacao da API, CORS e startup
|  |- config.py                # Configuracoes e variaveis de ambiente
|  |- database.py              # Engine, SessionLocal e Base
|  |- data_ingestion.py        # Legado: carga via CSV, nao usada no fluxo atual
|  |- models/                  # Models SQLAlchemy
|  |- schemas/                 # Schemas Pydantic
|  |- routers/
|     |- produtos.py           # Endpoints de produtos
|- alembic/
|  |- versions/                # Migracoes
|- tests/
|  |- test_api.py
|  |- test_data_ingestion.py
|- scripts/
|  |- contar_categorias.py
|- requirements.txt
|- pytest.ini
|- alembic.ini
```

## Setup rapido

1. Criar ambiente virtual e ativar:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Rodar API:

```powershell
python -m app.main
```

Acessos:
- API: http://localhost:8000
- Docs Swagger: http://localhost:8000/docs

## Banco e migracoes

Aplicar todas as migracoes:

```powershell
alembic upgrade head
```

Ver migration atual:

```powershell
alembic current
```

Criar nova migration:

```powershell
alembic revision -m "descricao da mudanca"
```

## Banco de dados

A API roda diretamente sobre o banco existente em `backend/Banco/banco.db`.
O arquivo `data_ingestion.py` permanece apenas como compatibilidade legada.

Comportamento atual:
- ao iniciar a API, tabelas sao criadas se nao existirem
- indices sao aplicados para otimizar consultas

## Endpoints implementados

Prefixo base: /api

- GET /produtos
  - filtros: busca, categoria, preco_min, preco_max, nota_min
  - paginacao: skip e limit
- GET /produtos/categorias
- GET /produtos/{id_produto}
- POST /produtos (criar novo)
- PUT /produtos/{id_produto} (atualizar)
- DELETE /produtos/{id_produto} (deletar)

## Testes

Cobertura de testes com pytest:

```powershell
pytest -v
```

Com cobertura de codigo:

```powershell
pytest --cov=app --cov-report=term-missing --cov-report=html
```

Testes implementados:
- Endpoints de listagem, criacao, atualizacao e remocao
- Smoke test do banco SQLite versionado
- Validacoes de entrada

## Notas de Producao

- SQLite atual é adequado para desenvolvimento.
- Para producao com multiplos usuarios, considere PostgreSQL.
- CORS habilitado para http://localhost:5173 (desenvolvi
to).
  - Ajuste em `app/config.py` para dominios de producao.
- Indices criados automaticamente nas tabelas principais.

Healthcheck:
- GET /

## Testes

Rodar toda a suite:

```powershell
pytest -v
```

Cobertura:

```powershell
pytest --cov=app --cov-report=term-missing
```

Escopo de testes atual:
- healthcheck
- listagem e filtros de produtos
- detalhe com historico e avaliacoes
- CRUD de produtos
- caminhos de validacao e not found
- ingestao de dados e funcoes auxiliares
