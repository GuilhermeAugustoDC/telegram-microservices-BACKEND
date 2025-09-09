from pyrogram import Client
from typing import List, Dict, Any, Optional
from app.models.database import CollectedMedia
from app.config.config import settings
import logging


class TelegramService:
    def __init__(self):
        self.active_clients: Dict[str, Client] = {}

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

    async def get_chat_info(self, session_name: str, chat_id: str) -> Dict[str, Any]:
        """Obtém informações detalhadas de um chat"""
        client = self.active_clients.get(session_name)
        if not client:
            raise ValueError(f"Cliente {session_name} não encontrado")

        chat = await client.get_chat(chat_id)
        return {
            "id": str(chat.id),
            "title": chat.title,
            "type": str(chat.type),
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

    async def forward_message(
        self, session_name: str, from_chat: str, to_chat: str, message_id: int
    ):
        """Encaminha mensagem entre chats"""
        client = self.active_clients.get(session_name)
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
                    "caption": message.caption,
                    "original_chat_id": str(message.chat.id),
                    "original_message_id": message.id,
                    "collected_at": message.date,
                }

        return None

    async def send_media_by_type(
        self, client, dest_id, media_info, caption_override=None
    ):
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

        send_func = send_methods.get(media_info["media_type"])
        if not send_func:
            raise ValueError("Tipo de mídia não suportado")

        kwargs = {"chat_id": dest_id, media_info["media_type"]: media_info["file_id"]}
        if caption_override:
            kwargs["caption"] = caption_override
        elif media_info.get("caption"):
            kwargs["caption"] = media_info["caption"]

        await send_func(**kwargs)

    async def send_media_from_cache(
        self, client, cached_media, destination_ids, caption_override=None
    ):
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

        send_func = send_methods.get(cached_media.media_type)
        if not send_func:
            raise ValueError("Tipo de mídia não suportado para envio via cache")

        for dest_id in destination_ids:
            kwargs = {"chat_id": dest_id, cached_media.media_type: cached_media.file_id}
        if caption_override:
            kwargs["caption"] = caption_override
        await send_func(**kwargs)

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
                if chat.username and not chat.is_member:
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

    async def get_client_by_session(self, session_name: str) -> Optional[Client]:
        """Retorna cliente ativo para uma sessão"""
        return self.active_clients.get(session_name)

    async def stop_client(self, session_name: str):
        """Para e remove cliente da sessão"""
        if session_name in self.active_clients:
            client = self.active_clients[session_name]
            await client.stop()
            del self.active_clients[session_name]
            logging.info(f"Cliente para sessão {session_name} parado e removido.")
