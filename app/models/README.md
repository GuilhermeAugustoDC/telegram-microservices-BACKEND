# Pasta app/models

Define os modelos ORM do banco de dados (SQLAlchemy). Cada classe representa uma tabela.

- **database.py**: Contém todos os modelos, relacionamentos e funções de inicialização do banco.

## Exemplos de uso
- Para criar uma nova tabela/modelo, adicione uma nova classe em `database.py`.
- Para migrar para múltiplos arquivos, crie arquivos separados para cada modelo e importe no `__init__.py`.

## Novas funcionalidades
- Novos modelos devem ser definidos aqui para refletir tabelas no banco.
