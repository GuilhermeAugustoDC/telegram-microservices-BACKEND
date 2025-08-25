from pyrogram import Client, filters
from pyrogram.types import Message
from app.models.database import (
    get_db,
    CollectedMedia,
    Automation as AutomationModel,
    UserSession,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramCollector:
    def __init__(self, session_file: str):
        self.session_file = session_file
        self.client = None
        self.db = next(get_db())

    async def start_collection(self, automation_id: int):
        """Inicia a coleta de mídias para uma automação específica"""
        try:
            # Busca a automação
            automation = (
                self.db.query(AutomationModel)
                .filter(AutomationModel.id == automation_id)
                .first()
            )
            if not automation:
                logger.error(f"Automação {automation_id} não encontrada")
                return

            # Resolve a sessão e credenciais da API
            session_obj = (
                self.db.query(UserSession)
                .filter(UserSession.id == automation.session_id)
                .first()
            )
            if not session_obj:
                logger.error(
                    f"Sessão vinculada à automação {automation_id} não encontrada"
                )
                return

            if not session_obj.api_id or not session_obj.api_hash:
                logger.error(
                    "Credenciais da API ausentes na sessão. Recrie a sessão com API_ID/API_HASH."
                )
                return

            try:
                api_id_value = int(str(session_obj.api_id).strip())
                api_hash_value = str(session_obj.api_hash).strip()
            except Exception:
                logger.error("Credenciais da API inválidas na sessão.")
                return

            session_path = f"sessions/{session_obj.session_file}"

            # Configura o cliente Pyrogram
            self.client = Client(
                session_path.replace(".session", ""),
                api_id=api_id_value,
                api_hash=api_hash_value,
            )

            # Registra handlers para cada canal de origem
            for source_chat in automation.source_chats:
                chat_id = source_chat.chat_id

                @self.client.on_message(filters.chat(chat_id))
                async def handle_message(client, message: Message):
                    await self.process_message(message, automation_id)

            await self.client.start()
            logger.info(f"Coleta iniciada para automação {automation_id}")

            # Mantém o cliente rodando
            await self.client.idle()

        except Exception as e:
            logger.error(f"Erro na coleta: {e}")
        finally:
            if self.client:
                await self.client.stop()

    async def process_message(self, message: Message, automation_id: int):
        """Processa uma mensagem recebida e salva mídias"""
        try:
            chat_id = str(message.chat.id)

            # Verifica se a mensagem tem mídia
            media_info = self.extract_media_info(message)
            if not media_info:
                return

            # Verifica se já foi coletada (evita duplicatas)
            existing = (
                self.db.query(CollectedMedia)
                .filter(
                    CollectedMedia.chat_id == chat_id,
                    CollectedMedia.message_id == message.id,
                )
                .first()
            )

            if existing:
                return

            # Salva a mídia coletada
            collected_media = CollectedMedia(
                chat_id=chat_id,
                message_id=message.id,
                media_type=media_info["type"],
                file_id=media_info["file_id"],
                file_name=media_info.get("file_name"),
                file_size=media_info.get("file_size"),
                caption=message.caption,
            )

            self.db.add(collected_media)
            self.db.commit()

            logger.info(f"Mídia coletada: {media_info['type']} do chat {chat_id}")

            # Se a automação estiver ativa, encaminha para destinos
            automation = (
                self.db.query(AutomationModel)
                .filter(AutomationModel.id == automation_id)
                .first()
            )
            if automation and automation.is_active:
                await self.forward_message(message, automation)

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")

    def extract_media_info(self, message: Message):
        """Extrai informações de mídia da mensagem"""
        if message.photo:
            return {
                "type": "photo",
                "file_id": message.photo.file_id,
                "file_size": message.photo.file_size,
            }
        elif message.video:
            return {
                "type": "video",
                "file_id": message.video.file_id,
                "file_name": message.video.file_name,
                "file_size": message.video.file_size,
            }
        elif message.document:
            return {
                "type": "document",
                "file_id": message.document.file_id,
                "file_name": message.document.file_name,
                "file_size": message.document.file_size,
            }
        elif message.audio:
            return {
                "type": "audio",
                "file_id": message.audio.file_id,
                "file_name": message.audio.file_name,
                "file_size": message.audio.file_size,
            }
        elif message.voice:
            return {
                "type": "voice",
                "file_id": message.voice.file_id,
                "file_size": message.voice.file_size,
            }
        elif message.sticker:
            return {
                "type": "sticker",
                "file_id": message.sticker.file_id,
                "file_size": message.sticker.file_size,
            }

        return None

    async def forward_message(self, message: Message, automation):
        """Encaminha mensagem para todos os canais de destino"""
        try:
            for dest_chat in automation.destination_chats:
                await message.forward(dest_chat.chat_id)
                logger.info(f"Mensagem encaminhada para {dest_chat.chat_id}")
        except Exception as e:
            logger.error(f"Erro ao encaminhar mensagem: {e}")
