import logging
from typing import List
import app.services.telegram_services as TelegramService


class VerifyAndValidateMessage:
    """Classe para verificar, validar e reenviar mensagens do Telegram."""

    def __init__(self, client, telegram_service: TelegramService):
        self.client = client
        self.telegram_service = telegram_service

    async def only_text_message(
        self, media_info, message, caption_override, destination_ids
    ):
        """Verifica e envia mensagens de texto simples."""
        if media_info:
            return  # Se tiver mídia, sai do método

        text_to_send = self.telegram_service.build_caption(
            getattr(message, "text", ""), caption_override
        )

        if not text_to_send or not text_to_send.strip():
            logging.warning(
                f"[TEXTO] Mensagem {message.id} está vazia. Ignorando envio."
            )
            return

        for dest_id in destination_ids:
            try:
                await self.client.send_message(dest_id, text_to_send)
                logging.info(f"[TEXTO] Mensagem {message.id} enviada para {dest_id}")
            except Exception as e:
                logging.error(
                    f"[TEXTO] Erro ao enviar msg {message.id} para {dest_id}: {e}"
                )

    async def resend_cached_media(self, media_info, caption_override, destination_ids):
        """Verifica cache e reenvia mídia, atualizando file_id expirado."""
        cached_media = await self.telegram_service.get_cached_media(
            media_info["file_unique_id"]
        )

        if not cached_media:
            return False

        logging.info(
            f"[CACHE] Mídia {cached_media.file_unique_id} encontrada. Reenviando."
        )

        for dest_id in destination_ids:
            try:
                await self.telegram_service.send_media_from_cache(
                    self.client, cached_media, [dest_id], caption_override
                )
            except Exception as e:
                if any(
                    x in str(e)
                    for x in [
                        "FILE_REFERENCE_EXPIRED",
                        "FILE_ID_INVALID",
                        "file_reference",
                    ]
                ):
                    logging.info(
                        f"[RECUPERAR] File_id expirado para {cached_media.file_unique_id}, atualizando..."
                    )
                    updated_media = await self.telegram_service.update_media_info(
                        self.client, cached_media
                    )
                    if updated_media:
                        try:
                            await self.telegram_service.send_media_from_cache(
                                self.client, updated_media, [dest_id], caption_override
                            )
                            logging.info(
                                f"[SUCESSO] Mídia {updated_media.file_unique_id} reenviada após atualização"
                            )
                        except Exception as e2:
                            logging.error(
                                f"[FALHA] Mesmo após atualização não foi possível enviar: {e2}"
                            )
                    continue
                else:
                    logging.error(
                        f"[CACHE] Erro ao reenviar mídia {cached_media.file_unique_id}: {e}"
                    )
        return True

    async def send_media_with_recovery(
        self, new_media, media_info, caption_override, destination_ids
    ):
        """Envia mídia normalmente e atualiza file_id expirado se necessário."""
        for dest_id in destination_ids:
            try:
                await self.telegram_service.send_media_by_type(
                    self.client, dest_id, media_info, caption_override
                )
                logging.info(
                    f"[MÍDIA] Mídia {media_info['file_unique_id']} enviada para {dest_id}"
                )
            except Exception as e:
                if any(
                    x in str(e)
                    for x in [
                        "FILE_REFERENCE_EXPIRED",
                        "FILE_ID_INVALID",
                        "file_reference",
                    ]
                ):
                    logging.info(
                        f"[RECUPERAR] File_id expirado para {media_info['file_unique_id']}, atualizando..."
                    )
                    updated_media = await self.telegram_service.update_media_info(
                        self.client, new_media
                    )
                    if updated_media:
                        try:
                            await self.telegram_service.send_media_from_cache(
                                self.client, updated_media, [dest_id], caption_override
                            )
                            logging.info(
                                f"[SUCESSO] Mídia {updated_media.file_unique_id} reenviada após atualização"
                            )
                        except Exception as e2:
                            logging.error(
                                f"[FALHA] Mesmo após atualização não foi possível enviar: {e2}"
                            )
                else:
                    logging.error(f"[MÍDIA] Erro ao enviar mídia para {dest_id}: {e}")

    async def should_skip_message(self, message, automation) -> bool:
        """Retorna True se a mensagem deve ser ignorada (serviço ou stop_flag)."""
        if getattr(automation, "stop_flag", False):
            logging.info(
                f"[FORWARD] Automação {automation.id} interrompida por flag de stop."
            )
            return True
        if getattr(message, "service", False):
            return True
        return False

    async def process_forward_message_safe(
        self, message, destination_ids, automation=None
    ):
        """Processa e encaminha uma mensagem com log de erro seguro."""
        try:
            await process_and_forward_message(
                self.client, message, destination_ids, automation
            )
        except Exception as e:
            logging.error(f"[FORWARD] Erro ao encaminhar msg {message.id}: {e}")


async def process_and_forward_message(
    client, message, destination_ids: List[int], automation=None
):
    """Função principal de envio de mensagens/mídias, usando VerifyAndValidateMessage."""
    from app.services.telegram_services import TelegramService

    telegram_service = TelegramService()
    verifier = VerifyAndValidateMessage(client, telegram_service)

    caption_override = automation.caption if automation else None
    media_info = await telegram_service.get_media_info(message)
    new_media = await telegram_service.save_media_to_cache(media_info)

    logging.info(f"[PROCESS] Processando mensagem {message.id} de {message.chat.id}")

    await verifier.only_text_message(
        media_info, message, caption_override, destination_ids
    )

    if await verifier.resend_cached_media(
        media_info, caption_override, destination_ids
    ):
        return

    logging.info(f"[CACHE] Mídia salva com id={new_media.id}")

    await verifier.send_media_with_recovery(
        new_media, media_info, caption_override, destination_ids
    )
