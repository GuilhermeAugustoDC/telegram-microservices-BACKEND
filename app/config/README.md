# Pasta app/config

Centraliza as configurações do projeto (variáveis de ambiente, caminhos, etc).

- **config.py**: Define e carrega variáveis de ambiente, caminhos de diretórios, chaves de API, etc.

## Exemplos de uso
- Para adicionar uma nova configuração, inclua no arquivo `config.py`.
- Para acessar configurações em outros módulos: `from app.config.config import settings`

## Novas funcionalidades
- Se precisar de múltiplos ambientes (dev/prod), adicione lógica condicional em `config.py`.
