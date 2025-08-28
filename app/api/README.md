# Pasta app/api

Esta pasta contém a definição dos endpoints da API, dependências globais e o ponto de entrada principal do FastAPI.

- **routes/**: Subpasta onde ficam os arquivos de rotas/endpoints organizados por domínio (ex: `automations.py`, `sessions.py`).
- **dependencies.py**: Funções utilitárias para injeção de dependências (ex: banco de dados).
- **main.py**: Inicialização do FastAPI, inclusão de rotas e middlewares.

## Exemplos de uso
- Para criar um novo endpoint, adicione um arquivo em `routes/` (ex: `users.py`) e registre suas rotas no `main.py`.
- Dependências globais (ex: autenticação, banco) devem ser declaradas em `dependencies.py`.

## Novas funcionalidades
- Crie um novo arquivo em `routes/` para cada novo domínio de negócio (ex: `webhooks.py`).
- Adicione novas dependências reutilizáveis em `dependencies.py`.
