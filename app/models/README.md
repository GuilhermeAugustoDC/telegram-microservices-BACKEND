# Pasta app/models

Define os modelos ORM do banco de dados usando SQLAlchemy. Cada classe representa uma tabela e suas relações.

## Estrutura Atual
- **database.py**: Contém todos os modelos, relacionamentos e configuração do banco

## Modelos Existentes
```python
class Automation(Base):
    __tablename__ = "automations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    session_name = Column(String, nullable=False)
    source_chat_id = Column(String, nullable=False)
    target_chat_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Exemplos de Novos Modelos

### 1. Sistema de Usuários
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com automações
    automations = relationship("Automation", back_populates="owner")
```

### 2. Sistema de Logs
```python
class AutomationLog(Base):
    __tablename__ = "automation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey("automations.id"))
    message = Column(Text, nullable=False)
    level = Column(String, default="INFO")  # INFO, WARNING, ERROR
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    automation = relationship("Automation", back_populates="logs")
```

### 3. Sistema de Configurações
```python
class AutomationConfig(Base):
    __tablename__ = "automation_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey("automations.id"), unique=True)
    
    # Configurações específicas
    forward_media = Column(Boolean, default=True)
    forward_text = Column(Boolean, default=True)
    add_signature = Column(Boolean, default=False)
    signature_text = Column(String, nullable=True)
    delay_seconds = Column(Integer, default=0)
    
    # Filtros
    keyword_filters = Column(JSON, nullable=True)  # Lista de palavras-chave
    user_filters = Column(JSON, nullable=True)     # Lista de usuários
    
    automation = relationship("Automation", back_populates="config")
```

### 4. Sistema de Webhooks
```python
class Webhook(Base):
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    secret_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    events = Column(JSON, nullable=False)  # Lista de eventos
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 5. Sistema de Estatísticas
```python
class MessageStats(Base):
    __tablename__ = "message_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey("automations.id"))
    date = Column(Date, nullable=False)
    
    messages_forwarded = Column(Integer, default=0)
    messages_filtered = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    automation = relationship("Automation")
    
    # Índice único por automação e data
    __table_args__ = (UniqueConstraint('automation_id', 'date'),)
```

## Relacionamentos Complexos
```python
# Exemplo: Relacionamento many-to-many
class AutomationTag(Base):
    __tablename__ = "automation_tags"
    
    automation_id = Column(Integer, ForeignKey("automations.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    color = Column(String, default="#3B82F6")
    
    # Relacionamento many-to-many
    automations = relationship(
        "Automation",
        secondary="automation_tags",
        back_populates="tags"
    )
```

## Organização para Projetos Grandes
Quando o projeto crescer, organize em arquivos separados:

```
models/
├── __init__.py
├── base.py          # Base class e configuração
├── user.py          # Modelos de usuário
├── automation.py    # Modelos de automação
├── logging.py       # Modelos de log
└── webhook.py       # Modelos de webhook
```

## Boas Práticas
1. **Nomes descritivos**: Use nomes claros para tabelas e colunas
2. **Índices apropriados**: Adicione índices em colunas frequentemente consultadas
3. **Relacionamentos bem definidos**: Use ForeignKey e relationship corretamente
4. **Validações no modelo**: Use validators do SQLAlchemy quando necessário
5. **Timestamps**: Inclua created_at/updated_at em modelos importantes
6. **Soft deletes**: Considere usar is_deleted ao invés de deletar registros
7. **Constraints**: Use UniqueConstraint, CheckConstraint quando apropriado
