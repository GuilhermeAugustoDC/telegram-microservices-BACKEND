import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from pyrogram import Client
from app.models.database import CollectedMedia, SessionLocal
from app.config.config import settings


class TelegramService:
    def __init__(self):
        self.active_clients: Dict[str, Dict[str, Any]] = {}

    # =========================
    # LEGENDAS
    # =========================
    @staticmethod
    def build_caption(
        original: Optional[str], override: Optional[str]
    ) -> Optional[str]:
        """
        Cria legenda final unindo legenda original e override da automação.
        """
        if override:
            return f"{original}\n\n{override}" if original else override
        return original

    # =========================
    # CLIENTE
    # =========================
    async def create_client(
        self, session_name: str, api_id: int, api_hash: str
    ) -> Client:
        """Cria e conecta cliente Pyrogram"""
        client = Client(
            session_name,
            api_id=api_id,
            api_hash=api_hash,
            workdir=settings.SESSIONS_DIR,
        )
        await client.start()
        self.active_clients[session_name] = {"client": client, "handlers": {}}
        return client

    async def get_or_create_client(self, session_name: str) -> Client:
        """Retorna cliente existente ou cria um novo"""
        if session_name not in self.active_clients:
            logging.info(f"Iniciando cliente para a sessão {session_name}...")
            client = await self.create_client(
                session_name=session_name,
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
            )
        else:
            client = self.active_clients[session_name]["client"]
        return client

    async def get_client_by_session(self, session_name: str) -> Optional[Client]:
        """Retorna cliente ativo para uma sessão"""
        client_data = self.active_clients.get(session_name)
        return client_data["client"] if client_data else None

    async def stop_client(self, session_name: str):
        """Para e remove cliente da sessão"""
        client_data = self.active_clients.get(session_name)
        if client_data:
            await client_data["client"].stop()
            del self.active_clients[session_name]
            logging.info(f"Cliente para sessão {session_name} parado e removido.")

    # =========================
    # CHAT
    # =========================
    async def get_chat_info(self, session_name: str, chat_id: str) -> Dict[str, Any]:
        """Obtém informações detalhadas de um chat"""
        client = await self.get_client_by_session(session_name)
        if not client:
            raise ValueError(f"Cliente {session_name} não encontrado")
        chat = await client.get_chat(chat_id)
        return {
            "id": str(chat.id),
            "title": getattr(chat, "title", None),
            "type": str(getattr(chat, "type", None)),
            "username": getattr(chat, "username", None),
            "members_count": getattr(chat, "members_count", None),
            "is_verified": getattr(chat, "is_verified", None),
            "is_restricted": getattr(chat, "is_restricted", None),
            "description": getattr(chat, "description", None),
            "photo_url": (
                getattr(chat.photo, "big_file_id", None)
                if getattr(chat, "photo", None)
                else None
            ),
        }

    async def verify_and_join_channels(
        self, client: Client, chat_ids: List[int]
    ) -> Dict[int, bool]:
        """Verifica acesso aos canais e tenta entrar se necessário"""
        results = {}
        for chat_id in chat_ids:
            try:
                chat = await client.get_chat(chat_id)
                logging.info(
                    f"[DEBUG] Acesso ao canal '{chat.title}' ({chat.id}) bem-sucedido."
                )
                # Tenta entrar no canal se for público e não for membro
                if getattr(chat, "username", None) and not getattr(
                    chat, "is_member", False
                ):
                    logging.info(f"[DEBUG] Tentando entrar no canal {chat.username}...")
                    await client.join_chat(chat.username)
                    logging.info(
                        f"[DEBUG] Entrada no canal {chat.username} bem-sucedida."
                    )
                results[chat_id] = True
            except Exception as e:
                logging.error(
                    f"[ERRO] Falha ao acessar ou entrar no canal {chat_id}: {e}"
                )
                results[chat_id] = False
        return results

    # =========================
    # MENSAGEM E MÍDIA
    # =========================
    async def forward_message(
        self, session_name: str, from_chat: str, to_chat: str, message_id: int
    ):
        """Encaminha mensagem entre chats"""
        client = await self.get_client_by_session(session_name)
        if not client:
            raise ValueError(f"Cliente {session_name} não encontrado")
        await client.forward_messages(
            chat_id=to_chat, from_chat_id=from_chat, message_ids=message_id
        )

    async def get_media_info(self, message) -> Optional[Dict[str, Any]]:
        """Extrai informações de mídia de uma mensagem"""
        media_types = [
            "photo",
            "video",
            "audio",
            "document",
            "voice",
            "video_note",
            "sticker",
            "animation",
        ]
        for media_type in media_types:
            if hasattr(message, media_type) and getattr(message, media_type):
                media = getattr(message, media_type)
                return {
                    "media_type": media_type,
                    "file_id": media.file_id,
                    "file_unique_id": media.file_unique_id,
                    "file_size": getattr(media, "file_size", None),
                    "mime_type": getattr(media, "mime_type", None),
                    "caption": getattr(message, "caption", None),
                    "original_chat_id": str(message.chat.id),
                    "original_message_id": message.id,
                    "collected_at": getattr(message, "date", datetime.utcnow()),
                }
        return None

    # =========================
    # CACHE DE MÍDIA
    # =========================
    async def get_cached_media(self, file_unique_id: str) -> Optional[CollectedMedia]:
        loop = asyncio.get_event_loop()

        def sync_db():
            with SessionLocal() as db:
                return (
                    db.query(CollectedMedia)
                    .filter_by(file_unique_id=file_unique_id)
                    .first()
                )

        return await loop.run_in_executor(None, sync_db)

    async def save_media_to_cache(self, media_info: Dict[str, Any]) -> CollectedMedia:
        if not media_info or not media_info.get("file_unique_id"):
            return None
        loop = asyncio.get_event_loop()

        def sync_db_add():
            with SessionLocal() as db:
                # Verifica se a mídia já existe no banco
                existing_media = (
                    db.query(CollectedMedia)
                    .filter_by(file_unique_id=media_info["file_unique_id"])
                    .first()
                )
                if existing_media:
                    return existing_media  # Retorna a existente sem inserir duplicata
                new_media = CollectedMedia(
                    file_unique_id=media_info["file_unique_id"],
                    file_id=media_info["file_id"],
                    media_type=media_info["media_type"],
                    mime_type=media_info.get("mime_type"),
                    file_size=media_info.get("file_size"),
                    original_chat_id=str(media_info["original_chat_id"]),
                    original_message_id=media_info["original_message_id"],
                    caption=media_info.get("caption"),
                    collected_at=media_info.get("collected_at", datetime.utcnow()),
                )
                db.add(new_media)
                db.commit()
                db.refresh(new_media)
                return new_media

        return await loop.run_in_executor(None, sync_db_add)

    # =========================
    # ENVIO DE MÍDIA
    # =========================
    async def _send_media(self, client, dest_id, file_id, media_type, caption=None):
        """Função interna para enviar mídia por tipo"""
        send_methods = {
            "photo": client.send_photo,
            "video": client.send_video,
            "audio": client.send_audio,
            "document": client.send_document,
            "voice": client.send_voice,
            "video_note": client.send_video_note,
            "sticker": client.send_sticker,
            "animation": client.send_animation,
        }
        send_func = send_methods.get(media_type)
        if not send_func:
            raise ValueError(f"Tipo de mídia '{media_type}' não suportado")
        kwargs = {"chat_id": dest_id, media_type: file_id}
        if caption:
            kwargs["caption"] = caption
        await send_func(**kwargs)

    async def send_media_by_type(
        self, client, dest_id, media_info, caption_override=None
    ):
        final_caption = caption_override or media_info.get("caption")
        await self._send_media(
            client,
            dest_id,
            media_info["file_id"],
            media_info["media_type"],
            final_caption,
        )

    async def send_media_from_cache(
        self, client, cached_media, destination_ids, caption_override=None
    ):
        final_caption = caption_override or cached_media.caption
        for dest_id in destination_ids:
            await self._send_media(
                client,
                dest_id,
                cached_media.file_id,
                cached_media.media_type,
                final_caption,
            )

    # =========================
    # ATUALIZAÇÃO DE MÍDIA
    # =========================
    async def update_media_info(self, client, cached_media):
        """
        Atualiza file_id de mídia expirado no cache.
        Busca a mensagem original para obter um file_id válido.
        """
        chat_id = cached_media.original_chat_id
        msg_id = cached_media.original_message_id

        try:
            orig_msg = await client.get_messages(chat_id, msg_id)
        except Exception as e:
            logging.error(
                f"[UPDATE] Não foi possível obter mensagem original {msg_id}: {e}"
            )
            return None

        new_info = await self.get_media_info(orig_msg)
        if not new_info:
            logging.warning(f"[UPDATE] Mensagem {msg_id} não contém mídia válida")
            return None

        loop = asyncio.get_event_loop()

        def sync_db_update(info):
            with SessionLocal() as db:
                media = (
                    db.query(CollectedMedia)
                    .filter_by(file_unique_id=info["file_unique_id"])
                    .first()
                )
                if media:
                    media.file_id = info["file_id"]
                    media.mime_type = info.get("mime_type")
                    media.file_size = info.get("file_size")
                    media.caption = info.get("caption")
                    media.original_message_id = msg_id
                    media.original_chat_id = chat_id
                    media.collected_at = info.get("collected_at", datetime.utcnow())
                    db.commit()
                    db.refresh(media)
                    logging.info(
                        f"[UPDATE] file_id atualizado para {media.file_unique_id}"
                    )
                return media

        return await loop.run_in_executor(None, sync_db_update, new_info)
