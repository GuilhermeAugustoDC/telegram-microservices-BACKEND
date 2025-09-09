from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

from app.models.database import SessionLocal
import logging
from app.config.config import settings
import asyncio
from app.models.database import CollectedMedia
from datetime import datetime
from app.schemas import automation
from app.services.telegram_services import TelegramService
from app.utils.mensage_helpers import build_caption

telegram_service = TelegramService()
active_clients = telegram_service.active_clients
automation_stop_flags = {}
forwarding_tasks = {}


async def start_automation_client(automation):
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    automation_id = automation.id

    # Inicializa flag de stop
    automation_stop_flags[automation_id] = False

    # Cria/obtém cliente
    client = await telegram_service.get_or_create_client(session_name)
    client_data = telegram_service.active_clients[session_name]

    if automation_id in client_data["handlers"]:
        logging.info(f"[START] Automação {automation_id} já possui handler ativo")
        return

    # Preparar canais
    source_chat_ids = [int(ch.chat_id) for ch in automation.source_channels]
    destination_chat_ids = [int(ch.chat_id) for ch in automation.destination_channels]

    logging.info(f"[START] Verificando canais para automação {automation_id}")
    all_chat_ids = list(set(source_chat_ids + destination_chat_ids))
    await telegram_service.verify_and_join_channels(client, all_chat_ids)
    logging.info(f"[START] Verificação de canais concluída")

    # Handler de mensagens
    async def message_handler(client, message):
        if automation_stop_flags.get(automation_id, False):
            logging.info(
                f"[HANDLER] Ignorando mensagem {message.id} porque flag de stop ativa"
            )
            return
        logging.info(
            f"[HANDLER] Mensagem {message.id} recebida em automação {automation_id}"
        )
        await process_and_forward_message(client, message, destination_chat_ids)

    handler = MessageHandler(message_handler, filters.chat(source_chat_ids))
    group = client.add_handler(handler)
    client_data["handlers"][automation_id] = {"handler": handler, "group": group}

    # Task para forward de histórico
    task = asyncio.create_task(forward_history(client, automation))
    forwarding_tasks[automation_id] = task

    logging.info(
        f"[START] Handler e forward_history iniciados para automação {automation_id}"
    )

    """Garante cliente ativo e adiciona handler para automação."""
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    automation_id = automation.id

    # Inicializa flag de stop
    automation_stop_flags[automation_id] = False

    # Garante cliente usando TelegramService
    client = await telegram_service.get_or_create_client(session_name)
    client_data = telegram_service.active_clients[session_name]

    # Evita criar handler duplicado
    if automation_id in client_data["handlers"]:
        logging.info(f"Automação {automation_id} já possui um handler ativo.")
        return

    # Prepara canais
    source_chat_ids = [int(ch.chat_id) for ch in automation.source_channels]
    destination_chat_ids = [int(ch.chat_id) for ch in automation.destination_channels]

    # Verifica/entra nos canais
    logging.info("--- INICIANDO VERIFICAÇÃO DE CANAIS ---")
    all_chat_ids = list(set(source_chat_ids + destination_chat_ids))
    await telegram_service.verify_and_join_channels(client, all_chat_ids)
    logging.info("--- FIM DA VERIFICAÇÃO DE CANAIS ---")

    # Define handler
    async def message_handler(client, message):
        if automation_stop_flags.get(automation_id, False):
            return  # Ignora mensagens se flag de stop estiver ativa
        logging.info(
            f"[Sessão: {session_name}] Mensagem {message.id} recebida de {message.chat.id}"
        )
        await process_and_forward_message(client, message, destination_chat_ids)

    handler = MessageHandler(message_handler, filters.chat(source_chat_ids))
    group = client.add_handler(handler)
    client_data["handlers"][automation_id] = {"handler": handler, "group": group}

    # Cria task para encaminhar histórico
    task = asyncio.create_task(forward_history(client, automation))
    forwarding_tasks[automation_id] = task

    logging.info(
        f"Handler para automação {automation_id} adicionado à sessão {session_name}."
    )

    """Garante cliente ativo e adiciona handler para automação."""
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    automation_id = automation.id

    # garante cliente usando TelegramService
    client = await telegram_service.get_or_create_client(session_name)
    client_data = telegram_service.active_clients[session_name]

    # Evita criar handler duplicado
    if automation_id in client_data["handlers"]:
        logging.info(f"Automação {automation_id} já possui um handler ativo.")
        return

    # Prepara canais
    source_chat_ids = [int(ch.chat_id) for ch in automation.source_channels]
    destination_chat_ids = [int(ch.chat_id) for ch in automation.destination_channels]

    # Verifica/entra nos canais
    logging.info("--- INICIANDO VERIFICAÇÃO DE CANAIS ---")
    all_chat_ids = list(set(source_chat_ids + destination_chat_ids))
    await telegram_service.verify_and_join_channels(client, all_chat_ids)
    logging.info("--- FIM DA VERIFICAÇÃO DE CANAIS ---")

    # Define handler
    async def message_handler(client, message):
        logging.info(
            f"[Sessão: {session_name}] Mensagem {message.id} recebida de {message.chat.id}"
        )
        await process_and_forward_message(client, message, destination_chat_ids)

    handler = MessageHandler(message_handler, filters.chat(source_chat_ids))
    group = client.add_handler(handler)
    client_data["handlers"][automation_id] = {"handler": handler, "group": group}

    # Cria task para encaminhar histórico
    task = asyncio.create_task(forward_history(client, automation))
    forwarding_tasks[automation_id] = task

    logging.info(
        f"Handler para automação {automation_id} adicionado à sessão {session_name}. Fontes: {source_chat_ids}"
    )

    automation_id = automation.id
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )

    if session_name not in active_clients:
        logging.info(f"Nenhum cliente ativo para a sessão {session_name}.")
        return

    client_data = active_clients[session_name]
    client = client_data["client"]

    # Ativa flag de stop
    automation_stop_flags[automation_id] = True

    # Cancela task de forwarding/history
    task = forwarding_tasks.pop(automation_id, None)
    if task:
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=3)
        except Exception:
            logging.warning(
                f"Task da automação {automation_id} não respondeu ao cancelamento."
            )

    # Remove handler
    handler_info = client_data["handlers"].pop(automation_id, None)
    if handler_info:
        try:
            await client.remove_handler(handler_info["handler"], handler_info["group"])
        except Exception as e:
            logging.warning(f"Erro ao remover handler: {e}")

    # Para cliente se não houver mais handlers
    if not client_data["handlers"]:
        if client.is_connected:
            await client.stop()
        active_clients.pop(session_name, None)

    logging.info(f"Automação {automation_id} parada com sucesso.")


async def stop_automation_client(automation):
    automation_id = automation.id
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )

    logging.info(f"[STOP] Iniciando stop da automação {automation_id}")

    if session_name not in active_clients:
        logging.info(f"[STOP] Nenhum cliente ativo para a sessão {session_name}")
        return

    client_data = active_clients[session_name]
    client = client_data["client"]

    # Ativa flag de stop
    automation_stop_flags[automation_id] = True
    logging.info(f"[STOP] Flag de stop ativada para automação {automation_id}")

    # Cancelar task
    task = forwarding_tasks.pop(automation_id, None)
    if task:
        logging.info(
            f"[STOP] Cancelando task de forwarding da automação {automation_id}"
        )
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5)
        except asyncio.TimeoutError:
            logging.warning(
                f"[STOP] Task da automação {automation_id} não respondeu ao cancelamento"
            )
        except asyncio.CancelledError:
            logging.info(
                f"[STOP] Task da automação {automation_id} cancelada com sucesso"
            )
        except Exception as e:
            logging.error(
                f"[STOP] Erro ao cancelar task da automação {automation_id}: {e}"
            )
    else:
        logging.info(
            f"[STOP] Nenhuma task de forwarding encontrada para automação {automation_id}"
        )

    # Remove handler
    handler_info = client_data["handlers"].pop(automation_id, None)
    if handler_info:
        try:
            await client.remove_handler(handler_info["handler"], handler_info["group"])
            logging.info(f"[STOP] Handler da automação {automation_id} removido")
        except Exception as e:
            logging.warning(f"[STOP] Erro ao remover handler: {e}")
    else:
        logging.info(f"[STOP] Nenhum handler encontrado para automação {automation_id}")

    # Para cliente se não houver mais handlers
    if not client_data["handlers"]:
        logging.info(f"[STOP] Nenhum handler restante. Parando cliente {session_name}")
        if client.is_connected:
            await client.stop()
            logging.info(f"[STOP] Cliente {session_name} parado com sucesso")
        active_clients.pop(session_name, None)
    else:
        logging.info(f"[STOP] Ainda existem handlers ativos, cliente não será parado")

    logging.info(f"[STOP] Stop da automação {automation_id} finalizado")


async def forward_history(client, automation):
    automation_id = automation.id
    logging.info(f"[FORWARD] Iniciando forward_history para automação {automation_id}")
    await asyncio.sleep(2)

    for source_channel in automation.source_channels:
        logging.info(f"[FORWARD] Buscando histórico do canal {source_channel.chat_id}")

        try:
            async for message in client.get_chat_history(source_channel.chat_id):
                if automation_stop_flags.get(automation_id, False):
                    logging.info(
                        f"[FORWARD] Flag de stop ativa, saindo do loop de histórico"
                    )
                    return

                if message.service:
                    continue

                destination_ids = [ch.chat_id for ch in automation.destination_channels]
                logging.info(f"[FORWARD] Processando mensagem {message.id}")
                try:
                    await process_and_forward_message(client, message, destination_ids)
                except Exception as e:
                    logging.error(f"[FORWARD] Erro ao encaminhar msg {message.id}: {e}")
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(
                f"[FORWARD] Erro ao buscar histórico do canal {source_channel.chat_id}: {e}"
            )

    logging.info(f"[FORWARD] Forward_history da automação {automation_id} concluído")

    """Busca e encaminha histórico de mensagens de canais de origem para canais de destino."""
    automation_id = automation.id
    logging.info(
        f"Iniciando histórico para automação '{automation.name}' (ID: {automation_id})"
    )
    await asyncio.sleep(2)  # Garante que o cliente esteja pronto

    for source_channel in automation.source_channels:
        logging.info(f"Buscando histórico do canal {source_channel.chat_id}")

        try:
            async for message in client.get_chat_history(source_channel.chat_id):
                # Verifica flag de stop
                if automation_stop_flags.get(automation_id, False):
                    logging.info(
                        f"Automação {automation_id} flag de stop ativa. Saindo do loop."
                    )
                    return

                if message.service:  # Pula mensagens de serviço
                    continue

                destination_ids = [ch.chat_id for ch in automation.destination_channels]
                await process_and_forward_message(client, message, destination_ids)
                await asyncio.sleep(1)  # Evita limite de taxa

        except Exception as e:
            logging.error(
                f"Erro ao buscar histórico do canal {source_channel.chat_id}: {e}"
            )

    logging.info(
        f"Encaminhamento do histórico da automação '{automation.name}' concluído."
    )

    """Busca e encaminha o histórico de mensagens de canais de origem para canais de destino."""
    logging.info(
        f"Iniciando encaminhamento do histórico para a automação '{automation.name}' (ID: {automation.id})"
    )
    await asyncio.sleep(2)  # Pequeno atraso para garantir que o cliente esteja pronto

    for source_channel in automation.source_channels:
        logging.info(f"Buscando histórico do canal de origem: {source_channel.chat_id}")
        try:
            async for message in client.get_chat_history(source_channel.chat_id):
                if (
                    message.service
                ):  # Pular mensagens de serviço (ex: usuário entrou no grupo)
                    continue

                destination_ids = [ch.chat_id for ch in automation.destination_channels]
                await process_and_forward_message(client, message, destination_ids)
                # Pausa para evitar limites de taxa do Telegram
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(
                f"Erro ao buscar histórico do canal {source_channel.chat_id}: {e}"
            )

    logging.info(
        f"Encaminhamento do histórico para a automação '{automation.name}' concluído."
    )


async def process_and_forward_message(
    client, message, destination_ids, automation=None
):
    """
    Encaminha mensagens com ou sem mídia, aplicando legenda da automação
    e evitando envio duplicado de mídias.
    """

    def build_caption(original: str | None, automation_caption: str | None) -> str:
        if automation_caption:
            return (
                f"{original}\n\n{automation_caption}"
                if original
                else automation_caption
            )
        return original or ""

    caption_override = automation.caption if automation else None
    media_info = await telegram_service.get_media_info(message)

    # --- Mensagem apenas texto
    if not media_info:
        text_to_send = build_caption(message.text, caption_override)
        for dest_id in destination_ids:
            try:
                await client.send_message(dest_id, text_to_send)
                logging.info(f"[TEXTO] Msg {message.id} enviada para {dest_id}")
            except Exception as e:
                logging.error(
                    f"[TEXTO] Erro ao enviar msg {message.id} para {dest_id}: {e}"
                )
        return

    # --- Mensagem com mídia
    loop = asyncio.get_event_loop()

    def sync_db_block():
        with SessionLocal() as db:
            return (
                db.query(CollectedMedia)
                .filter_by(file_unique_id=media_info["file_unique_id"])
                .first()
            )

    cached_media = await loop.run_in_executor(None, sync_db_block)

    if cached_media:
        logging.info(
            f"[CACHE] Mídia {cached_media.file_unique_id} encontrada. Reenviando."
        )
        for dest_id in destination_ids:
            try:
                final_caption = build_caption(cached_media.caption, caption_override)
                await telegram_service.send_media_from_cache(
                    client, cached_media, [dest_id], caption_override=final_caption
                )
            except Exception as e:
                logging.error(f"[CACHE] Erro ao reenviar mídia para {dest_id}: {e}")
        return

    # --- Salva mídia no cache
    def sync_db_add():
        with SessionLocal() as db:
            new_media = CollectedMedia(
                file_unique_id=media_info["file_unique_id"],
                file_id=media_info["file_id"],
                media_type=media_info["media_type"],
                mime_type=media_info["mime_type"],
                file_size=media_info["file_size"],
                original_chat_id=str(message.chat.id),
                original_message_id=message.id,
                caption=media_info.get("caption"),
                collected_at=datetime.utcnow(),
            )
            db.add(new_media)
            db.commit()
            db.refresh(new_media)
            return new_media

    new_media = await loop.run_in_executor(None, sync_db_add)
    logging.info(f"[CACHE] Mídia salva com id={new_media.id}")

    # --- Envia mídia
    for dest_id in destination_ids:
        try:
            final_caption = build_caption(media_info.get("caption"), caption_override)
            await telegram_service.send_media_by_type(
                client, str(dest_id), media_info, caption_override=final_caption
            )
            logging.info(
                f"[MÍDIA] Mídia {media_info['file_unique_id']} enviada para {dest_id}"
            )
        except ValueError:
            await message.forward(dest_id)
            logging.info(
                f"[MÍDIA] Mídia {media_info['file_unique_id']} encaminhada via forward para {dest_id}"
            )
        except Exception as e:
            logging.error(f"[MÍDIA] Erro ao enviar mídia para {dest_id}: {e}")
