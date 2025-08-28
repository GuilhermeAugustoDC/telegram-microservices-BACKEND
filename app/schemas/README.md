# Pasta app/schemas

Define os schemas Pydantic usados para validação e serialização de dados nas rotas.

- **automation.py, session.py**: Schemas para automações, sessões, etc.

## Exemplos de uso
- Para criar um novo schema, adicione um novo arquivo (ex: `user.py`) e defina classes Pydantic.
- Utilize estes schemas como `response_model` ou `body` nos endpoints.

## Novas funcionalidades
- Adicione schemas para cada novo domínio de dados que precise ser validado/serializado na API.
