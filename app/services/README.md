# Pasta app/services

Contém a lógica de negócio (services/handlers) que não pertence diretamente aos endpoints.

- **automation_handler.py**: Lógica de automações, controle de clientes Pyrogram, manipulação de mensagens, etc.

## Exemplos de uso
- Adicione novos arquivos para serviços complexos (ex: `user_service.py`).
- Mantenha a lógica de negócio separada das rotas.

## Novas funcionalidades
- Crie um novo arquivo para cada serviço de domínio (ex: `payment_service.py`).
