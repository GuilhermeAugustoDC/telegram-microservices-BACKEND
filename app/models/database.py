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
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() # .env file is now at the backend root

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

    automations = relationship("Automation", back_populates="session")
    cached_channels = relationship("CachedChannel", back_populates="session", cascade="all, delete-orphan")


class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session_id = Column(Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"))
    session = relationship("UserSession", back_populates="automations")

    # Relacionamento muitos-para-muitos com canais de origem
    source_chats = relationship(
        "Chat",
        secondary=automation_sources,
        back_populates="source_automations",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )

    # Relacionamento muitos-para-muitos com destinos
    destination_chats = relationship(
        "Chat",
        secondary=automation_destinations,
        back_populates="destination_automations",
        lazy="dynamic",
        cascade="all, delete",
        passive_deletes=True,
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255))
    is_channel = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos com automações
    source_automations = relationship(
        "Automation",
        secondary=automation_sources,
        back_populates="source_chats",
        lazy="dynamic",
    )
    
    destination_automations = relationship(
        "Automation",
        secondary=automation_destinations,
        back_populates="destination_chats",
        lazy="dynamic",
    )

    # Relacionamento com mídias coletadas
    collected_media = relationship("CollectedMedia", back_populates="chat", cascade="all, delete-orphan")


class CachedChannel(Base):
    __tablename__ = "cached_channels"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('user_sessions.id', ondelete="CASCADE"), nullable=False)
    
    channel_id = Column(String(255), nullable=False)
    title = Column(String(255))
    username = Column(String(255), nullable=True)
    is_channel = Column(Boolean, default=False)
    members_count = Column(Integer, nullable=True)
    photo_url = Column(String(255), nullable=True)

    session = relationship("UserSession", back_populates="cached_channels")

    __table_args__ = (UniqueConstraint('session_id', 'channel_id', name='_session_channel_uc'),)


# Configuração do banco de dados

# O diretório base do projeto agora é a pasta 'backend'
BASE_DIR = Path(__file__).resolve().parent.parent


# Define o caminho do banco de dados dentro da pasta 'backend'
DB_NAME = "telegram_automation.db"
DB_PATH = str(BASE_DIR / DB_NAME)

# Usa o caminho absoluto para o SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")


engine = create_engine(DATABASE_URL)
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
    chat_id = Column(String(255), ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, nullable=False)
    media_type = Column(String(50), nullable=False)  # photo, video, document, audio, etc.
    file_id = Column(String(255), nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    caption = Column(String(4096))
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com chat
    chat = relationship("Chat", back_populates="collected_media")
    
    # Índice único para evitar duplicatas
    __table_args__ = (UniqueConstraint("chat_id", "message_id", name="uix_chat_message"),)


def create_tables():
    Base.metadata.create_all(bind=engine)
