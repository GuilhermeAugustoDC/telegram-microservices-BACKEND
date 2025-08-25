from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pyrogram import Client
from pyrogram.errors import FloodWait
import os
from datetime import datetime, timedelta
import asyncio

from app.models.database import UserSession, CachedChannel
from app.api.dependencies import get_db
from app.utils.logger import db_log
from pydantic import BaseModel

router = APIRouter()

class ChannelInfo(BaseModel):
    id: str
    title: str
    username: str | None = None
    is_channel: bool
    members_count: int | None = None
    photo_url: str | None = None

"""Lista todos os canais/grupos que o usuário participa"""

@router.get("/sessions/{session_id}/channels", response_model=List[ChannelInfo])
async def get_user_channels(session_id: int, incremental: bool = False, db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Verifica se o cache é recente (ex: 1 hora)
    CACHE_DURATION_HOURS = 1
    if session.channels_last_updated and (datetime.utcnow() - session.channels_last_updated) < timedelta(hours=CACHE_DURATION_HOURS) and not incremental:
        cached_channels = db.query(CachedChannel).filter(CachedChannel.session_id == session_id).order_by(CachedChannel.title.asc()).all()
        if cached_channels:
            message = f"Retornando {len(cached_channels)} canais do cache para a sessão {session_id}."
            db_log("INFO", message, f"channels:cache_hit:session_{session_id}")
            return [ChannelInfo(
                id=str(c.channel_id),
                title=c.title,
                username=c.username,
                is_channel=c.is_channel,
                members_count=c.members_count,
                photo_url=c.photo_url
            ) for c in cached_channels]

    # Se o cache não for válido, busca no Telegram
    message = f"Buscando {'novos ' if incremental else ''}canais no Telegram para a sessão {session_id}"
    db_log("INFO", message, f"channels:{'incremental_' if incremental else ''}fetch:session_{session_id}")
    return await fetch_and_cache_channels(session, db, incremental)


async def fetch_and_cache_channels(session: UserSession, db: Session, incremental: bool = False) -> List[ChannelInfo]:
    session_file_path = f"sessions/{session.session_file}"
    if not os.path.exists(session_file_path):
        raise HTTPException(status_code=404, detail="Arquivo de sessão não encontrado")

    try:
        api_id = int(str(session.api_id).strip())
        api_hash = str(session.api_hash).strip()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="API_ID ou API_HASH inválidos na sessão.")

    if not api_id or not api_hash:
        raise HTTPException(status_code=400, detail="Credenciais da API ausentes. Recrie a sessão.")

    session_name = session.session_file.replace('.session', '')
    channels_list = []
    existing_channels = set()
    
    if incremental:
        # Pega lista de canais já cacheados
        cached = db.query(CachedChannel).filter(CachedChannel.session_id == session.id).all()
        existing_channels = {c.channel_id for c in cached}
    
    try:
        async with Client(name=session_name, api_id=api_id, api_hash=api_hash, workdir="sessions") as app:
            if not incremental:
                # Limpa o cache antigo apenas se não for busca incremental
                db.query(CachedChannel).filter(CachedChannel.session_id == session.id).delete()
            
            async for dialog in app.get_dialogs():
                chat = dialog.chat
                if hasattr(chat, 'type') and chat.type.value in ["group", "supergroup", "channel"]:
                    if str(chat.id) in existing_channels:
                        continue
                        
                    try:
                        photo_url = None
                        if chat.photo:
                            photo_dir = "app/static/pfp"
                            os.makedirs(photo_dir, exist_ok=True)
                            photo_path = os.path.join(photo_dir, f"{chat.id}.jpg")
                            
                            if not os.path.exists(photo_path):
                                try:
                                    await app.download_media(chat.photo.small_file_id, file_name=photo_path)
                                    photo_url = f"/static/pfp/{chat.id}.jpg"
                                except Exception as download_error:
                                    print(f"Erro ao baixar foto para {chat.id}: {download_error}")
                            else:
                                photo_url = f"/static/pfp/{chat.id}.jpg"

                        channel_data = {
                            "channel_id": str(chat.id),
                            "title": chat.title or "Sem título",
                            "username": getattr(chat, 'username', None),
                            "is_channel": chat.type.value == "channel",
                            "members_count": getattr(chat, 'members_count', None),
                            "photo_url": photo_url
                        }
                        
                        # Adiciona ao cache
                        cached_channel = CachedChannel(session_id=session.id, **channel_data)
                        db.add(cached_channel)
                        channels_list.append(ChannelInfo(id=str(chat.id), **channel_data))

                    except Exception as chat_error:
                        print(f"Erro ao processar chat {chat.id}: {chat_error}")
            
            # Atualiza o timestamp e commita as mudanças
            session.channels_last_updated = datetime.utcnow()
            db.add(session)
            db.commit()

    except FloodWait as e:
        print(f"FloodWait: esperando por {e.value} segundos.")
        await asyncio.sleep(e.value)
        raise HTTPException(status_code=429, detail=f"Muitas requisições. Tente novamente em {e.value} segundos.")
    except Exception as e:
        print(f"[ERRO] Falha ao buscar canais para a sessão {session.id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao Telegram: {e}")

    channels_list.sort(key=lambda x: x.title.lower())
    message = f"Sucesso! {len(channels_list)} novos canais foram adicionados ao cache para a sessão {session.id}."
    db_log("INFO", message, f"channels:fetch_incremental:session_{session.id}")
    return channels_list
