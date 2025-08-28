# Pasta app/config

Centraliza todas as configurações do projeto, variáveis de ambiente e constantes globais.

## Estrutura
- **config.py**: Configurações principais usando Pydantic Settings

## Configurações Atuais
```python
class Settings(BaseSettings):
    # Banco de dados
    DATABASE_URL: str = "sqlite:///./app/databases/telegram_automation.db"
    
    # Diretórios
    SESSIONS_DIR: str = "./app/sessions"
    DATABASES_DIR: str = "./app/databases"
    
    # API do Telegram
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
```

## Exemplos de Novas Configurações

### 1. Sistema de Cache (Redis)
```python
# Adicionar em config.py
REDIS_URL: str = "redis://localhost:6379"
CACHE_TTL: int = 3600  # 1 hora
CACHE_ENABLED: bool = True
```

### 2. Sistema de Email
```python
# Configurações de email
SMTP_SERVER: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USERNAME: Optional[str] = None
SMTP_PASSWORD: Optional[str] = None
EMAIL_FROM: str = "noreply@telegram-automation.com"
```

### 3. Sistema de Logs
```python
# Configurações de logging
LOG_LEVEL: str = "INFO"
LOG_FILE: str = "./logs/app.log"
LOG_ROTATION: str = "1 day"
LOG_RETENTION: str = "30 days"
```

### 4. Autenticação JWT
```python
# JWT Settings
JWT_SECRET_KEY: str = "your-secret-key"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_HOURS: int = 24
REFRESH_TOKEN_EXPIRATION_DAYS: int = 7
```

### 5. Rate Limiting
```python
# Rate limiting
RATE_LIMIT_REQUESTS: int = 100
RATE_LIMIT_WINDOW: int = 60  # segundos
RATE_LIMIT_ENABLED: bool = True
```

## Ambientes Múltiplos
Para diferentes ambientes, crie arquivos `.env`:

```bash
# .env.development
DEBUG=true
DATABASE_URL=sqlite:///./dev.db
LOG_LEVEL=DEBUG

# .env.production
DEBUG=false
DATABASE_URL=postgresql://user:pass@localhost/prod_db
LOG_LEVEL=WARNING
```

## Uso nas Aplicações
```python
# Em qualquer módulo
from app.config.config import settings

# Acessar configurações
db_url = settings.DATABASE_URL
api_id = settings.TELEGRAM_API_ID
```

## Boas Práticas
1. **Nunca hardcode valores**: Use sempre variáveis de ambiente
2. **Valores padrão sensatos**: Defina defaults para desenvolvimento
3. **Validação**: Use Pydantic para validar tipos e valores
4. **Documentação**: Comente o propósito de cada configuração
5. **Segurança**: Nunca commite arquivos `.env` com dados sensíveis
