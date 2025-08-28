# Pasta app/api

Esta pasta contém a definição dos endpoints da API, dependências globais e o ponto de entrada principal do FastAPI.

## Estrutura
- **routes/**: Subpasta onde ficam os arquivos de rotas/endpoints organizados por domínio
- **dependencies.py**: Funções utilitárias para injeção de dependências (ex: banco de dados, autenticação)
- **main.py**: Inicialização do FastAPI, inclusão de rotas e middlewares

## Organização de Rotas
Cada arquivo em `routes/` deve representar um domínio específico:
- `automations.py` - Endpoints para gerenciar automações do Telegram
- `sessions.py` - Endpoints para sessões de usuário do Telegram
- `channels.py` - Endpoints para listar e gerenciar canais
- `logs.py` - Endpoints para consulta de logs

## Exemplos de Novas Funcionalidades

### 1. Sistema de Usuários
```python
# routes/users.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Lógica de criação
    pass
```

### 2. Sistema de Webhooks
```python
# routes/webhooks.py
from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/telegram")
async def telegram_webhook(request: Request):
    # Processar webhook do Telegram
    pass
```

### 3. Sistema de Notificações
```python
# routes/notifications.py
from fastapi import APIRouter
from app.schemas.notification import NotificationCreate

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/send")
async def send_notification(notification: NotificationCreate):
    # Enviar notificação
    pass
```

## Dependências Comuns
Adicione em `dependencies.py`:
- Autenticação JWT
- Validação de permissões
- Conexão com banco de dados
- Rate limiting
- Logging de requisições

## Boas Práticas
1. **Um arquivo por domínio**: Mantenha endpoints relacionados no mesmo arquivo
2. **Prefixos consistentes**: Use prefixos claros como `/api/v1/automations`
3. **Tags para documentação**: Agrupe endpoints com tags no Swagger
4. **Response models**: Sempre defina modelos de resposta para documentação
5. **Tratamento de erros**: Use HTTPException para erros padronizados
