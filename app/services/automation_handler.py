import asyncio
import logging
from pyrogram.handlers import MessageHandler
from pyrogram import filters
from app.utils.telegram.verify_and_validate_mensage import (
    VerifyAndValidateMessage,
    process_and_forward_message,
)
from app.services.telegram_services import TelegramService
from app.config.config import settings

telegram_service = TelegramService()
active_clients = telegram_service.active_clients
automation_stop_flags = {}
forwarding_tasks = {}


async def start_automation_client(automation):
    """Inicia o processo de automação: garante cliente ativo, adiciona handler e inicia."""
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    automation_id = automation.id
    automation_stop_flags[automation_id] = False

    client = await telegram_service.get_or_create_client(session_name)
    client_data = telegram_service.active_clients[session_name]

    if automation_id in client_data["handlers"]:
        logging.info(f"[START] Automação {automation_id} já possui handler ativo")
        return

    source_chat_ids = [int(ch.chat_id) for ch in automation.source_channels]
    destination_chat_ids = [int(ch.chat_id) for ch in automation.destination_channels]
    all_chat_ids = list(set(source_chat_ids + destination_chat_ids))
    await telegram_service.verify_and_join_channels(client, all_chat_ids)

    async def message_handler(client, message):
        if automation_stop_flags.get(automation_id, False):
            return
        await process_and_forward_message(client, message, destination_chat_ids)

    handler = MessageHandler(message_handler, filters.chat(source_chat_ids))
    group = client.add_handler(handler)
    client_data["handlers"][automation_id] = {"handler": handler, "group": group}

    forwarding_tasks[automation_id] = asyncio.create_task(
        forward_history(client, automation)
    )
    logging.info(f"[START] Automação {automation_id} iniciada na sessão {session_name}")


async def stop_automation_client(automation):
    """Encerra a automação: cancela tasks, remove handlers e para o cliente se necessário."""
    automation_id = automation.id
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    client_data = active_clients.get(session_name)
    if not client_data:
        return

    client = client_data["client"]
    automation_stop_flags[automation_id] = True

    task = forwarding_tasks.pop(automation_id, None)
    if task:
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5)
        except Exception:
            pass

    handler_info = client_data["handlers"].pop(automation_id, None)
    if handler_info:
        remove_handler = getattr(client, "remove_handler", None)
        if callable(remove_handler):
            await remove_handler(handler_info["handler"], handler_info["group"])

    if not client_data["handlers"] and getattr(client, "is_connected", False):
        await client.stop()
        active_clients.pop(session_name, None)


async def forward_history(client, automation):
    verifier = VerifyAndValidateMessage(client, telegram_service)
    await asyncio.sleep(2)

    for source_channel in automation.source_channels:
        try:
            async for message in client.get_chat_history(source_channel.chat_id):
                if await verifier.should_skip_message(message, automation):
                    continue
                destination_ids = [ch.chat_id for ch in automation.destination_channels]
                await verifier.process_forward_message_safe(
                    message, destination_ids, automation
                )
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(
                f"[FORWARD] Erro ao buscar histórico do canal {source_channel.chat_id}: {e}"
            )
