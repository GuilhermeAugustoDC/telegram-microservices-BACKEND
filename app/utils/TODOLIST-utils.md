# TODOLIST - Utils (app/utils)

## 🚀 Melhorias Prioritárias

### 1. Sistema de Logging Avançado
- [ ] Expandir logger.py com formatters customizados
- [ ] Implementar log rotation automático
- [ ] Adicionar structured logging (JSON)
- [ ] Criar log aggregation para múltiplos services
- [ ] Implementar log filtering por contexto

### 2. Validações e Sanitização
- [ ] Criar validators.py com validações do Telegram
- [ ] Implementar sanitização de dados sensíveis
- [ ] Adicionar validações de formato de arquivo
- [ ] Criar validators para URLs e emails
- [ ] Implementar validação de tamanho de payload

### 3. Utilitários de Segurança
- [ ] Criar security.py com funções de criptografia
- [ ] Implementar geração segura de tokens
- [ ] Adicionar hash functions otimizadas
- [ ] Criar JWT utilities
- [ ] Implementar rate limiting utilities

## 🔧 Melhorias Técnicas

### 4. Manipulação de Datas
- [ ] Criar datetime_helpers.py
- [ ] Implementar timezone handling
- [ ] Adicionar formatters de data localizados
- [ ] Criar calculadores de duração
- [ ] Implementar parsers de data flexíveis

### 5. Utilitários de Arquivo
- [ ] Criar file_helpers.py
- [ ] Implementar compressão/descompressão
- [ ] Adicionar validação de tipos de arquivo
- [ ] Criar utilities de upload seguro
- [ ] Implementar limpeza automática de arquivos temporários

### 6. Utilitários de Performance
- [ ] Criar performance_utils.py
- [ ] Implementar profiling decorators
- [ ] Adicionar memory usage tracking
- [ ] Criar cache utilities
- [ ] Implementar connection pooling helpers

## 📋 Novos Utilitários

### 7. Utilitários de API
- [ ] Criar api_helpers.py
- [ ] Implementar response formatters padronizados
- [ ] Adicionar pagination utilities
- [ ] Criar error handling helpers
- [ ] Implementar request validation utilities

### 8. Utilitários de Telegram
- [ ] Criar telegram_utils.py
- [ ] Implementar chat ID validators
- [ ] Adicionar message formatters
- [ ] Criar session management helpers
- [ ] Implementar flood control utilities

### 9. Utilitários de Banco de Dados
- [ ] Criar database_utils.py
- [ ] Implementar query builders
- [ ] Adicionar transaction helpers
- [ ] Criar migration utilities
- [ ] Implementar backup/restore helpers

## 🛠️ Refatoração e Manutenção

### 10. Decorators Reutilizáveis
- [ ] Criar decorators.py
- [ ] Implementar retry decorator
- [ ] Adicionar timing decorator
- [ ] Criar cache decorator
- [ ] Implementar validation decorator

### 11. Conversores e Formatters
- [ ] Criar converters.py
- [ ] Implementar data type converters
- [ ] Adicionar formatters de texto
- [ ] Criar unit converters
- [ ] Implementar currency formatters

### 12. Utilitários de Teste
- [ ] Criar test_utils.py
- [ ] Implementar mock generators
- [ ] Adicionar test data factories
- [ ] Criar assertion helpers
- [ ] Implementar test fixtures

## ⚡ Quick Wins (Implementação Rápida)

### 13. Utilitários Básicos
- [ ] Criar string_utils.py
- [ ] Implementar text cleaning functions
- [ ] Adicionar slug generators
- [ ] Criar random generators
- [ ] Implementar hash utilities

### 14. Utilitários de Configuração
- [ ] Criar config_utils.py
- [ ] Implementar environment helpers
- [ ] Adicionar settings validators
- [ ] Criar configuration loaders
- [ ] Implementar feature flag utilities

## 📊 Utilitários Específicos do Projeto

### 15. Automação Utilities
- [ ] Criar automation_utils.py
- [ ] Implementar rule validators
- [ ] Adicionar condition evaluators
- [ ] Criar action executors
- [ ] Implementar workflow helpers

### 16. Monitoramento e Métricas
- [ ] Criar monitoring_utils.py
- [ ] Implementar metrics collectors
- [ ] Adicionar health check utilities
- [ ] Criar alert helpers
- [ ] Implementar dashboard utilities

## 🔄 Exemplo de Implementação

```python
# utils/telegram_utils.py
import re
from typing import Optional, List

def validate_chat_id(chat_id: str) -> bool:
    """Valida formato de ID de chat do Telegram"""
    pattern = r'^-100\d{10,}$'
    return bool(re.match(pattern, chat_id))

def extract_username(text: str) -> Optional[str]:
    """Extrai username do Telegram de um texto"""
    pattern = r'@([a-zA-Z0-9_]{5,32})'
    match = re.search(pattern, text)
    return match.group(1) if match else None

def format_chat_title(title: str, max_length: int = 50) -> str:
    """Formata título do chat para exibição"""
    if len(title) <= max_length:
        return title
    return title[:max_length-3] + "..."

def is_private_chat(chat_id: str) -> bool:
    """Verifica se é chat privado"""
    return not chat_id.startswith('-')

def sanitize_message_text(text: str) -> str:
    """Remove caracteres perigosos de mensagens"""
    # Remove caracteres de controle
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Remove múltiplas quebras de linha
    sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
    return sanitized.strip()

# utils/performance_utils.py
import time
import functools
from typing import Callable, Any

def timing_decorator(func: Callable) -> Callable:
    """Decorator para medir tempo de execução"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"{func.__name__} executado em {execution_time:.4f}s")
        
        return result
    return wrapper

def retry_decorator(max_attempts: int = 3, delay: float = 1.0):
    """Decorator para retry automático"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    
            raise last_exception
        return wrapper
    return decorator
```

## 📊 Priorização Sugerida

**Alta Prioridade (Semana 1):**
- Sistema de logging avançado
- Validações e sanitização
- Utilitários de segurança
- Decorators básicos

**Média Prioridade (Semana 2-3):**
- Utilitários de Telegram
- Manipulação de arquivos
- Utilitários de API
- Performance utilities

**Baixa Prioridade (Mês 2+):**
- Utilitários de teste avançados
- Monitoramento complexo
- Conversores especializados
- Dashboard utilities
