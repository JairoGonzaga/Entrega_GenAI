Documento de Requisitos: Módulo de Gerenciamento de E-Commerce (Gerente)
1. Visão Geral
Desenvolver um módulo Full Stack (Frontend e Backend) para um Sistema de Gerenciamento de E-Commerce, focado no perfil Gerente. O sistema deve permitir a gestão completa do catálogo de produtos, visualização de métricas de vendas e feedback de consumidores.

2. Stack Tecnológica Obrigatória
Frontend: Vite + React + TypeScript.

Backend: FastAPI (Python).

Banco de Dados: SQLite (via SQLAlchemy ORM).

Migrações: Alembic.

3. Requisitos Funcionais (RF)
ID	Requisito	Descrição
RF01	Catálogo de Produtos	O sistema deve exibir uma lista/grade de todos os produtos cadastrados.
RF02	Busca de Produtos	Permitir a busca por termos específicos para filtrar um ou mais produtos.
RF03	CRUD de Produtos	Capacidade de Criar, Ler, Atualizar e Deletar (remover) produtos individualmente.
RF04	Detalhes do Produto	Exibir informações detalhadas: especificações técnicas (medidas), histórico de vendas e avaliações.
RF05	Cálculo de Média	O sistema deve calcular e exibir automaticamente a média das avaliações de cada produto.
RF06	Persistência de Dados	Operações devem refletir no SQLite utilizando os arquivos .csv fornecidos para a carga inicial.
4. Requisitos Não Funcionais (RNF)
RNF01 (Usabilidade): Interface responsiva voltada para o uso administrativo (Gerente).

RNF02 (Documentação): O repositório deve conter um README.md detalhando o processo de instalação e execução (setup do ambiente, migrações e comandos).

RNF03 (Arquitetura): Código organizado seguindo boas práticas de desenvolvimento (Clean Code, Tipagem forte no TS, Separação de rotas no FastAPI).

5. Estrutura de Dados (Entidades)
A aplicação deve lidar, no mínimo, com as seguintes associações:

Produto: Nome, descrição, preço, medidas.

Vendas: Relacionadas ao produto (quantidade, data).

Avaliações: Nota (rating) e comentário do consumidor.

6. Funcionalidades de Diferencial (Extras Sugeridos)
Paginação de produtos no backend.

Tratamento de erros global (Exception Handlers).

Filtros avançados (categoria, faixa de preço, nota mínima).

Caching de consultas pesadas.

Autenticação simples para o Gerente.

Cronograma de Entrega
Data Limite: 14/04/2026 às 18:00.

Critérios de Avaliação: Qualidade do código, funcionalidade, aderência aos requisitos, usabilidade e organização do Git.