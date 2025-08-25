from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class AutomationBase(BaseModel):
    name: str
    source_chats: List[str]  # Múltiplos canais de origem
    destination_chats: List[str]
    session_id: int

class AutomationCreate(AutomationBase):
    pass

class Automation(BaseModel):
    id: int
    name: str
    source_chats: List[str] = Field(default_factory=list)
    destination_chats: List[str] = Field(default_factory=list)
    session_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Converte objetos Chat para strings (chat_id)
        source_chats = [chat.chat_id for chat in obj.source_chats]
        destination_chats = [chat.chat_id for chat in obj.destination_chats]
        return cls(
            id=obj.id,
            name=obj.name,
            source_chats=source_chats,
            destination_chats=destination_chats,
            session_id=obj.session_id,
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )
