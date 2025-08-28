# Pasta app/services

Contém a lógica de negócio (business logic) que não pertence diretamente aos endpoints. Separa a lógica complexa das rotas da API.

## Estrutura Atual
- **automation_handler.py**: Gerenciamento de automações, clientes Pyrogram, processamento de mensagens

## Responsabilidades dos Services
1. **Lógica de negócio complexa**: Algoritmos, validações, processamento
2. **Integração com APIs externas**: Telegram, webhooks, notificações
3. **Operações no banco de dados**: Queries complexas, transações
4. **Processamento assíncrono**: Tasks em background, filas

## Exemplos de Novos Services

### 1. User Service
```python
# services/user_service.py
from sqlalchemy.orm import Session
from app.models.database import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"])
    
    async def create_user(self, user_data: UserCreate) -> User:
        # Hash da senha
        hashed_password = self.pwd_context.hash(user_data.password)
        
        # Criar usuário
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = self.db.query(User).filter(User.username == username).first()
        if user and self.pwd_context.verify(password, user.hashed_password):
            return user
        return None
```

### 2. Notification Service
```python
# services/notification_service.py
import aiohttp
from typing import List, Dict, Any
from app.config.config import settings

class NotificationService:
    def __init__(self):
        self.webhook_urls = []
    
    async def send_webhook(self, event: str, data: Dict[str, Any]):
        """Envia webhook para URLs configuradas"""
        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            for url in self.webhook_urls:
                try:
                    await session.post(url, json=payload, timeout=10)
                except Exception as e:
                    print(f"Erro ao enviar webhook: {e}")
    
    async def send_email(self, to: str, subject: str, body: str):
        """Envia email usando SMTP"""
        # Implementação de envio de email
        pass
    
    async def send_telegram_notification(self, chat_id: str, message: str):
        """Envia notificação via Telegram Bot"""
        # Implementação usando bot do Telegram
        pass
```

### 3. Analytics Service
```python
# services/analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta
from app.models.database import Automation, MessageStats

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_automation_stats(self, automation_id: int, days: int = 30):
        """Estatísticas de uma automação nos últimos N dias"""
        start_date = date.today() - timedelta(days=days)
        
        stats = self.db.query(
            func.sum(MessageStats.messages_forwarded).label('total_forwarded'),
            func.sum(MessageStats.messages_filtered).label('total_filtered'),
            func.sum(MessageStats.errors_count).label('total_errors')
        ).filter(
            and_(
                MessageStats.automation_id == automation_id,
                MessageStats.date >= start_date
            )
        ).first()
        
        return {
            "automation_id": automation_id,
            "period_days": days,
            "total_forwarded": stats.total_forwarded or 0,
            "total_filtered": stats.total_filtered or 0,
            "total_errors": stats.total_errors or 0
        }
    
    async def get_daily_stats(self, automation_id: int, start_date: date, end_date: date):
        """Estatísticas diárias de uma automação"""
        return self.db.query(MessageStats).filter(
            and_(
                MessageStats.automation_id == automation_id,
                MessageStats.date >= start_date,
                MessageStats.date <= end_date
            )
        ).order_by(MessageStats.date).all()
```

### 4. Cache Service
```python
# services/cache_service.py
import redis
import json
from typing import Any, Optional
from app.config.config import settings

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL) if settings.CACHE_ENABLED else None
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Armazena valor no cache"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or settings.CACHE_TTL
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False
```

### 5. Telegram Service
```python
# services/telegram_service.py
from pyrogram import Client
from typing import List, Dict, Any
from app.models.database import Automation

class TelegramService:
    def __init__(self):
        self.active_clients: Dict[str, Client] = {}
    
    async def create_client(self, session_name: str, api_id: int, api_hash: str) -> Client:
        """Cria e conecta cliente Pyrogram"""
        client = Client(
            session_name,
            api_id=api_id,
            api_hash=api_hash,
            workdir="./app/sessions"
        )
        
        await client.start()
        self.active_clients[session_name] = client
        return client
    
    async def get_chat_info(self, session_name: str, chat_id: str) -> Dict[str, Any]:
        """Obtém informações de um chat"""
        client = self.active_clients.get(session_name)
        if not client:
            raise ValueError(f"Cliente {session_name} não encontrado")
        
        chat = await client.get_chat(chat_id)
        return {
            "id": str(chat.id),
            "title": chat.title,
            "type": str(chat.type),
            "members_count": getattr(chat, 'members_count', None)
        }
    
    async def forward_message(self, session_name: str, from_chat: str, to_chat: str, message_id: int):
        """Encaminha mensagem entre chats"""
        client = self.active_clients.get(session_name)
        if not client:
            raise ValueError(f"Cliente {session_name} não encontrado")
        
        await client.forward_messages(
            chat_id=to_chat,
            from_chat_id=from_chat,
            message_ids=message_id
        )
```

## Padrões de Injeção de Dependência
```python
# services/__init__.py
from .user_service import UserService
from .notification_service import NotificationService
from .analytics_service import AnalyticsService

# Em dependencies.py
from app.services import UserService, NotificationService

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

def get_notification_service() -> NotificationService:
    return NotificationService()

# Uso nas rotas
@router.post("/users/")
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(user_data)
```

## Organização de Arquivos
```
services/
├── __init__.py
├── base_service.py          # Classe base para services
├── automation_handler.py    # Service de automações (atual)
├── user_service.py          # Gerenciamento de usuários
├── telegram_service.py      # Integração com Telegram
├── notification_service.py  # Notificações e webhooks
├── analytics_service.py     # Estatísticas e relatórios
├── cache_service.py         # Sistema de cache
└── file_service.py          # Upload/download de arquivos
```

## Boas Práticas
1. **Single Responsibility**: Cada service tem uma responsabilidade específica
2. **Injeção de Dependência**: Use Depends() para injetar services nas rotas
3. **Tratamento de Erros**: Capture e trate exceções apropriadamente
4. **Logging**: Adicione logs para operações importantes
5. **Testes**: Services devem ser facilmente testáveis
6. **Async/Await**: Use programação assíncrona quando apropriado
7. **Type Hints**: Sempre use type hints para melhor documentação
8. **Configurações**: Use settings do config para valores configuráveis
