# Pasta app/schemas

Define os schemas Pydantic para validação, serialização e documentação automática da API.

## Estrutura Atual
- **automation.py**: Schemas para automações (create, update, response)
- **session.py**: Schemas para sessões do Telegram

## Tipos de Schemas

### 1. Request Schemas (Input)
```python
# Para dados recebidos via POST/PUT
class AutomationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    session_name: str
    source_chat_id: str
    target_chat_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Encaminhar Notícias",
                "session_name": "minha_sessao",
                "source_chat_id": "-1001234567890",
                "target_chat_id": "-1009876543210"
            }
        }
```

### 2. Response Schemas (Output)
```python
# Para dados retornados pela API
class AutomationResponse(BaseModel):
    id: int
    name: str
    session_name: str
    source_chat_id: str
    target_chat_id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Para converter de ORM
```

### 3. Update Schemas
```python
# Para atualizações parciais
class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Novo nome da automação",
                "is_active": True
            }
        }
```

## Exemplos de Novos Schemas

### 1. Sistema de Usuários
```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str
```

### 2. Sistema de Configurações
```python
# schemas/automation_config.py
from pydantic import BaseModel, Field
from typing import List, Optional

class AutomationConfigCreate(BaseModel):
    automation_id: int
    forward_media: bool = True
    forward_text: bool = True
    add_signature: bool = False
    signature_text: Optional[str] = None
    delay_seconds: int = Field(0, ge=0, le=3600)
    keyword_filters: Optional[List[str]] = None
    user_filters: Optional[List[str]] = None

class AutomationConfigResponse(AutomationConfigCreate):
    id: int
    
    class Config:
        from_attributes = True
```

### 3. Sistema de Logs
```python
# schemas/log.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class LogCreate(BaseModel):
    automation_id: Optional[int] = None
    message: str
    level: LogLevel = LogLevel.INFO

class LogResponse(BaseModel):
    id: int
    automation_id: Optional[int]
    message: str
    level: LogLevel
    timestamp: datetime
    
    class Config:
        from_attributes = True

class LogFilter(BaseModel):
    automation_id: Optional[int] = None
    level: Optional[LogLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
```

### 4. Sistema de Webhooks
```python
# schemas/webhook.py
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    secret_token: Optional[str] = None
    events: List[str] = Field(..., min_items=1)

class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    events: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    events: Optional[List[str]] = None
```

### 5. Schemas de Estatísticas
```python
# schemas/stats.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

class DailyStats(BaseModel):
    date: date
    messages_forwarded: int
    messages_filtered: int
    errors_count: int

class AutomationStats(BaseModel):
    automation_id: int
    automation_name: str
    total_forwarded: int
    total_filtered: int
    total_errors: int
    daily_stats: List[DailyStats]

class StatsFilter(BaseModel):
    automation_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
```

## Validações Avançadas
```python
from pydantic import BaseModel, validator, root_validator

class AutomationAdvanced(BaseModel):
    name: str
    source_chat_id: str
    target_chat_id: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Nome não pode estar vazio')
        return v.strip()
    
    @validator('source_chat_id', 'target_chat_id')
    def chat_id_format(cls, v):
        if not v.startswith('-100'):
            raise ValueError('ID do chat deve começar com -100')
        return v
    
    @root_validator
    def different_chats(cls, values):
        source = values.get('source_chat_id')
        target = values.get('target_chat_id')
        if source == target:
            raise ValueError('Chat de origem e destino devem ser diferentes')
        return values
```

## Organização de Arquivos
```
schemas/
├── __init__.py
├── base.py              # Schemas base reutilizáveis
├── automation.py        # Schemas de automação
├── user.py              # Schemas de usuário
├── webhook.py           # Schemas de webhook
├── log.py               # Schemas de log
└── stats.py             # Schemas de estatísticas
```

## Boas Práticas
1. **Separe por responsabilidade**: Create, Update, Response para cada entidade
2. **Use Field para validações**: min_length, max_length, ge, le, etc.
3. **Exemplos na documentação**: Use schema_extra para exemplos no Swagger
4. **Validators customizados**: Para lógicas de validação complexas
5. **Enums para constantes**: Use Enum para valores fixos
6. **Tipos apropriados**: EmailStr, HttpUrl, datetime, etc.
7. **Config from_attributes**: Para converter de modelos ORM
8. **Documentação**: Adicione docstrings nas classes
