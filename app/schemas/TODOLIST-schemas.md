# TODOLIST - Schemas (app/schemas)

## 🚀 Melhorias Prioritárias

### 1. Estrutura e Organização
- [ ] Separar schemas em arquivos por domínio
- [ ] Criar schemas base reutilizáveis
- [ ] Implementar herança de schemas comum
- [ ] Padronizar nomenclatura (Create, Update, Response)
- [ ] Adicionar schemas de filtro e paginação

### 2. Validações Avançadas
- [ ] Implementar validators customizados para IDs do Telegram
- [ ] Adicionar validação de formato de telefone
- [ ] Criar validators para URLs e emails
- [ ] Implementar validação de tamanho de arquivos
- [ ] Adicionar validators de data/hora

### 3. Documentação e Exemplos
- [ ] Adicionar schema_extra com exemplos em todos os schemas
- [ ] Documentar todos os campos com descriptions
- [ ] Criar exemplos de request/response
- [ ] Adicionar documentação de casos de erro
- [ ] Implementar OpenAPI tags e descriptions

## 🔧 Melhorias Técnicas

### 4. Sistema de Usuários
- [ ] Criar UserCreate, UserUpdate, UserResponse schemas
- [ ] Implementar UserLogin e UserRegister schemas
- [ ] Adicionar UserProfile schema
- [ ] Criar schemas de permissões e roles
- [ ] Implementar schemas de recuperação de senha

### 5. Configurações Avançadas
- [ ] Criar AutomationConfigCreate/Update schemas
- [ ] Implementar FilterRuleSchema para filtros
- [ ] Adicionar ScheduleSchema para agendamentos
- [ ] Criar WebhookConfigSchema
- [ ] Implementar NotificationConfigSchema

### 6. Sistema de Logs e Analytics
- [ ] Criar LogFilterSchema para filtros de log
- [ ] Implementar StatsRequestSchema
- [ ] Adicionar ReportConfigSchema
- [ ] Criar MetricsFilterSchema
- [ ] Implementar ExportRequestSchema

## 📋 Novos Schemas

### 7. Sistema de Arquivos
- [ ] Criar FileUploadSchema
- [ ] Implementar FileMetadataSchema
- [ ] Adicionar ImageProcessingSchema
- [ ] Criar FileFilterSchema
- [ ] Implementar StorageConfigSchema

### 8. Sistema de Notificações
- [ ] Criar NotificationCreateSchema
- [ ] Implementar NotificationTemplateSchema
- [ ] Adicionar NotificationPreferenceSchema
- [ ] Criar WebhookEventSchema
- [ ] Implementar EmailTemplateSchema

### 9. Sistema de Cache
- [ ] Criar CacheConfigSchema
- [ ] Implementar CacheStatsSchema
- [ ] Adicionar CacheInvalidationSchema
- [ ] Criar CacheEntrySchema
- [ ] Implementar CacheMetricsSchema

## 🛠️ Refatoração e Manutenção

### 10. Tipos e Enums
- [ ] Criar enums para status de automação
- [ ] Implementar enums para tipos de log
- [ ] Adicionar enums para roles de usuário
- [ ] Criar enums para tipos de notificação
- [ ] Implementar enums para status de arquivo

### 11. Schemas de Resposta Padronizados
- [ ] Criar ResponseBase para respostas padrão
- [ ] Implementar ErrorResponseSchema
- [ ] Adicionar PaginatedResponseSchema
- [ ] Criar SuccessResponseSchema
- [ ] Implementar MetadataResponseSchema

### 12. Validações de Negócio
- [ ] Implementar root_validators para regras complexas
- [ ] Adicionar validações de relacionamentos
- [ ] Criar validações de permissões
- [ ] Implementar validações de limites
- [ ] Adicionar validações de formato específico

## ⚡ Quick Wins (Implementação Rápida)

### 13. Melhorias Imediatas
- [ ] Adicionar Field descriptions em todos os campos
- [ ] Implementar aliases para campos
- [ ] Adicionar constraints básicos (min_length, max_length)
- [ ] Criar schemas de health check
- [ ] Implementar schemas de versão da API

### 14. Schemas de Desenvolvimento
- [ ] Criar DebugInfoSchema
- [ ] Implementar TestDataSchema
- [ ] Adicionar MockConfigSchema
- [ ] Criar DevelopmentStatsSchema
- [ ] Implementar ProfileInfoSchema

## 📊 Schemas Específicos do Projeto

### 15. Telegram Integration
- [ ] Criar TelegramAuthSchema
- [ ] Implementar TelegramChatSchema
- [ ] Adicionar TelegramMessageSchema
- [ ] Criar TelegramUserSchema
- [ ] Implementar TelegramSessionSchema

### 16. Automação Avançada
- [ ] Criar AutomationRuleSchema
- [ ] Implementar AutomationConditionSchema
- [ ] Adicionar AutomationActionSchema
- [ ] Criar AutomationTriggerSchema
- [ ] Implementar AutomationWorkflowSchema

## 🔄 Exemplo de Implementação

```python
# schemas/base.py
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

class PaginationSchema(BaseModel):
    page: int = Field(1, ge=1, description="Número da página")
    per_page: int = Field(20, ge=1, le=100, description="Items por página")

# schemas/automation.py
class AutomationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nome da automação")
    session_name: str = Field(..., description="Nome da sessão do Telegram")
    source_chat_id: str = Field(..., regex=r'^-100\d+$', description="ID do chat origem")
    target_chat_id: str = Field(..., regex=r'^-100\d+$', description="ID do chat destino")
    
    @validator('source_chat_id', 'target_chat_id')
    def validate_chat_id(cls, v):
        if not v.startswith('-100'):
            raise ValueError('ID do chat deve começar com -100')
        return v
    
    @root_validator
    def validate_different_chats(cls, values):
        source = values.get('source_chat_id')
        target = values.get('target_chat_id')
        if source == target:
            raise ValueError('Chat origem e destino devem ser diferentes')
        return values
    
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

## 📊 Priorização Sugerida

**Alta Prioridade (Semana 1-2):**
- Separar schemas por domínio
- Adicionar validações básicas
- Criar schemas de usuário
- Documentação com exemplos

**Média Prioridade (Semana 3-4):**
- Schemas de configuração avançada
- Sistema de logs e analytics
- Validações de negócio
- Schemas de resposta padronizados

**Baixa Prioridade (Mês 2+):**
- Sistema de cache
- Workflows complexos
- Schemas de desenvolvimento
- Analytics avançado
