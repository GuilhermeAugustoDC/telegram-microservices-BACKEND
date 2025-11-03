from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from typing import Optional


class AutomationBase(BaseModel):
    name: str
    source_chats: List[str]  # Múltiplos canais de origem
    destination_chats: List[str]  # Múltiplos canais de Destino
    session_id: int
    caption: str | None = None


class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    caption: Optional[str] = None


class Automation(BaseModel):
    id: int
    name: str
    source_chats: List[str] = Field(default_factory=list)
    destination_chats: List[str] = Field(default_factory=list)
    session_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    caption: str | None = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        # Converte objetos Chat para strings (chat_id)
        source_chats = [chat.chat_id for chat in getattr(obj, "source_channels", [])]
        destination_chats = [
            chat.chat_id for chat in getattr(obj, "destination_channels", [])
        ]
        return cls(
            id=obj.id,
            name=obj.name,
            source_chats=source_chats,
            destination_chats=destination_chats,
            session_id=obj.session_id,
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            caption=obj.caption,
        )
