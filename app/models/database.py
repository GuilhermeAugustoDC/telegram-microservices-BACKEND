from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Table,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from app.config.config import settings

load_dotenv()  # .env file is now at the backend root

Base = declarative_base()

# Tabela de associação para relacionamento muitos-para-muitos (destinos)
automation_destinations = Table(
    "automation_destinations",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("automation_id", Integer, ForeignKey("automations.id", ondelete="CASCADE")),
    Column("chat_id", String(255), ForeignKey("chats.chat_id", ondelete="CASCADE")),
    UniqueConstraint("automation_id", "chat_id", name="uix_automation_chat"),
)

# Tabela de associação para relacionamento muitos-para-muitos (origens)
automation_sources = Table(
    "automation_sources",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("automation_id", Integer, ForeignKey("automations.id", ondelete="CASCADE")),
    Column("chat_id", String(255), ForeignKey("chats.chat_id", ondelete="CASCADE")),
    UniqueConstraint("automation_id", "chat_id", name="uix_automation_source_chat"),
)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_file = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True)
    api_id = Column(String(50), nullable=True)
    api_hash = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    channels_last_updated = Column(DateTime, nullable=True)

    automations = relationship("AutomationModel", back_populates="session")
    cached_channels = relationship(
        "CachedChannel", back_populates="session", cascade="all, delete-orphan"
    )


class AutomationModel(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session_id = Column(Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"))
    session = relationship("UserSession", back_populates="automations")

    # Relacionamento muitos-para-muitos com canais de origem
    source_channels = relationship(
        "Chat",
        secondary=automation_sources,
        back_populates="source_automations",
    )

    # Relacionamento muitos-para-muitos com canais de destino
    destination_channels = relationship(
        "Chat",
        secondary=automation_destinations,
        back_populates="destination_automations",
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255))
    is_channel = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos para automações onde este chat é uma origem ou destino
    source_automations = relationship(
        "AutomationModel",
        secondary=automation_sources,
        back_populates="source_channels",
    )
    destination_automations = relationship(
        "AutomationModel",
        secondary=automation_destinations,
        back_populates="destination_channels",
    )


class CachedChannel(Base):
    __tablename__ = "cached_channels"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False
    )

    channel_id = Column(String(255), nullable=False)
    title = Column(String(255))
    username = Column(String(255), nullable=True)
    is_channel = Column(Boolean, default=False)
    members_count = Column(Integer, nullable=True)
    photo_url = Column(String(255), nullable=True)

    session = relationship("UserSession", back_populates="cached_channels")

    __table_args__ = (
        UniqueConstraint("session_id", "channel_id", name="_session_channel_uc"),
    )


# Configuração do banco de dados

BASE_DIR = Path(__file__).resolve().parent  # backend/

print(settings.DATABASE_URL)
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(50), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(String(1024), nullable=False)
    source = Column(String(100))  # Ex: 'session_creation', 'automation_worker'


class CollectedMedia(Base):
    __tablename__ = "collected_media"

    id = Column(Integer, primary_key=True, index=True)

    # Identificador único e permanente do Telegram para o arquivo
    file_unique_id = Column(String(255), unique=True, nullable=False, index=True)

    # Identificador do arquivo para reenvio
    file_id = Column(String(255), nullable=False)

    media_type = Column(String(50), nullable=False)  # ex: photo, video, document
    mime_type = Column(String(100))  # ex: image/jpeg, video/mp4
    file_size = Column(Integer)

    # Opcional: ID do chat e da mensagem onde a mídia foi coletada pela primeira vez
    original_chat_id = Column(
        String(255), ForeignKey("chats.chat_id", ondelete="SET NULL")
    )
    original_message_id = Column(Integer)

    caption = Column(String(4096))  # Legenda da mídia

    collected_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
