# Projeto Telegram Microservices BACKEND

Este projeto é um backend para automação de interações com o Telegram, construído com FastAPI, SQLAlchemy e Pyrogram.

## Estrutura das Pastas

- `app/api/` — Endpoints da API, dependências e inicialização do FastAPI
- `app/config/` — Configurações globais, variáveis de ambiente
- `app/models/` — Modelos ORM do banco de dados (SQLAlchemy)
- `app/schemas/` — Schemas Pydantic para validação e resposta de dados
- `app/services/` — Lógica de negócio, handlers e serviços
- `app/utils/` — Funções utilitárias genéricas

## Como criar novas funcionalidades
- **Novos endpoints:** Crie um novo arquivo em `app/api/routes/` e registre no `main.py`.
- **Novos modelos:** Adicione classes em `app/models/database.py`.
- **Novos schemas:** Crie arquivos em `app/schemas/`.
- **Novos serviços:** Crie arquivos em `app/services/`.
- **Novos utilitários:** Crie arquivos em `app/utils/`.

## Exemplos de uso
Veja os READMEs de cada subpasta para exemplos práticos e orientações detalhadas.

---

### Requisitos
- Python 3.10+
- FastAPI
- SQLAlchemy
- Pyrogram

### Como rodar
1. Instale as dependências: `pip install -r requirements.txt`
2. Configure as variáveis de ambiente em `.env`
3. Rode o servidor: `uvicorn app.api.main:app --reload`

---

### Observações
- Para testes, recomenda-se criar uma pasta `tests/` na raiz.
- Para novas integrações, siga o padrão de modularização já estabelecido.
