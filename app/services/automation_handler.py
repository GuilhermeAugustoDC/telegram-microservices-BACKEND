from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

from app.models.database import SessionLocal
import logging
from app.config.config import settings
import asyncio
from app.models.database import CollectedMedia
from datetime import datetime
from app.services.telegram_services import TelegramService

active_clients = {}
forwarding_tasks = {}
telegram_service = TelegramService()


async def start_automation_client(automation):
    """Garante que um cliente para a sessão está ativo e adiciona um handler para a automação."""
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    automation_id = automation.id

    # Verifica se já existe um cliente para esta sessão
    if session_name not in active_clients:
        logging.info(f"Iniciando cliente para a sessão {session_name}...")
        client = Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir=settings.SESSIONS_DIR,
        )
        await client.start()
        active_clients[session_name] = {"client": client, "handlers": {}}

    client_data = active_clients[session_name]
    client = client_data["client"]

    if automation_id in client_data["handlers"]:
        logging.info(f"Automação {automation_id} já possui um handler ativo.")
        return

    # Prepara os IDs dos canais de origem e destino
    source_chat_ids = [int(channel.chat_id) for channel in automation.source_channels]
    destination_chat_ids = [
        int(channel.chat_id) for channel in automation.destination_channels
    ]

    # Verificação de acesso aos canais usando TelegramService
    logging.info("--- INICIANDO VERIFICAÇÃO DE CANAIS ---")
    all_chat_ids = list(set(source_chat_ids + destination_chat_ids))
    await telegram_service.verify_and_join_channels(client, all_chat_ids)
    logging.info("--- FIM DA VERIFICAÇÃO DE CANAIS ---")

    async def message_handler(client, message):
        logging.info(
            f"[Sessão: {session_name}] Mensagem {message.id} recebida de {message.chat.id}"
        )
        await process_and_forward_message(client, message, destination_chat_ids)

    handler = MessageHandler(message_handler, filters.chat(source_chat_ids))
    group = client.add_handler(handler)  # add_handler returns the group number
    client_data["handlers"][automation_id] = {"handler": handler, "group": group}

    # Inicia o encaminhamento do histórico em uma tarefa de fundo e armazena para possível cancelamento
    task = asyncio.create_task(forward_history(client, automation))
    forwarding_tasks[automation_id] = task

    logging.info(
        f"Handler para automação {automation_id} adicionado à sessão {session_name}. Fontes: {source_chat_ids}"
    )


async def stop_automation_client(automation):
    """Remove o handler de uma automação e para o cliente se não houver mais handlers."""
    session_name = automation.session.session_file.replace(
        settings.SESSION_EXTENSION_FILE, ""
    )
    automation_id = automation.id

    if (
        session_name not in active_clients
        or automation_id not in active_clients[session_name]["handlers"]
    ):
        logging.info(
            f"Nenhum handler ativo para a automação {automation_id} na sessão {session_name}."
        )
        return  # Apenas return vazio para garantir coroutine

    client_data = active_clients[session_name]
    client = client_data["client"]
    handler_info = client_data["handlers"][automation_id]
    try:
        handler_to_remove = handler_info["handler"]
        group_to_remove = handler_info["group"]
        try:
            await client.remove_handler(handler_to_remove, group_to_remove)
            logging.info(f"Handler para automação {automation_id} removido.")
        except ValueError as e:
            logging.warning(
                f"Handler para automação {automation_id} já havia sido removido ou grupo não existe: {e}"
            )
    except Exception as e:
        logging.error(f"Erro inesperado ao tentar remover handler: {e}")
    finally:
        if automation_id in client_data["handlers"]:
            del client_data["handlers"][automation_id]

    # Se não houver mais handlers, para o cliente
    if not client_data["handlers"]:
        logging.info(
            f"Nenhum handler ativo restante para a sessão {session_name}. Parando o cliente."
        )
        # Cancela task de forwarding/history se existir
        task = forwarding_tasks.pop(automation_id, None)
        if task:
            try:
                task.cancel()
                await asyncio.sleep(0)  # Permite propagação do cancelamento
                logging.info(
                    f"Task de forwarding/history para automação {automation_id} cancelada."
                )
            except Exception as e:
                logging.warning(f"Falha ao cancelar task de forwarding: {e}")
        await client.stop()
        del active_clients[session_name]
        logging.info(f"Cliente para a sessão {session_name} parado com sucesso.")
    logging.info("Finalizando stop_automation_client")
    return  # Nunca retorne None explicitamente


async def forward_history(client, automation):
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


async def process_and_forward_message(client, message, destination_ids):
    """Processa uma mensagem, utiliza o cache de mídia se aplicável, e a encaminha."""
    media_info = await telegram_service.get_media_info(message)

    if not media_info:
        # Mensagem sem mídia, apenas encaminha
        for dest_id in destination_ids:
            try:
                if media_info is None:
                    await client.send_message(dest_id, message.text or "")
                else:
                    # Replica mídia sem marca de encaminhado
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
                    if send_func:
                        kwargs = {
                            "chat_id": dest_id,
                            media_info["media_type"]: media_info["file_id"],
                        }
                        if media_info.get("caption"):
                            kwargs["caption"] = media_info["caption"]
                        await send_func(**kwargs)
                    else:
                        await client.send_message(
                            dest_id, message.text or "[Mídia não suportada para copiar]"
                        )
                logging.info(
                    f"Mensagem {message.id} copiada para {dest_id} sem tag de encaminhado"
                )
            except Exception as e:
                logging.error(
                    f"Erro ao copiar mensagem {message.id} para {dest_id}: {e}"
                )
        return

    # Mensagem com mídia, processa o cache
    # get_db_session é síncrono, não use await no contexto
    with SessionLocal() as db:
        logging.info(
            f"[CACHE] Buscando file_unique_id={media_info['file_unique_id']} no banco..."
        )
        cached_media = (
            db.query(CollectedMedia)
            .filter_by(file_unique_id=media_info["file_unique_id"])
            .first()
        )

        if cached_media:
            logging.info(
                f"[CACHE] Mídia {cached_media.file_unique_id} encontrada no cache. Reenviando via file_id."
            )
            await telegram_service.send_media_from_cache(
                client, cached_media, destination_ids
            )
        else:
            logging.info(
                f"[CACHE] Mídia {media_info['file_unique_id']} NÃO encontrada no cache. Salvando no banco..."
            )
            new_media = CollectedMedia(
                file_unique_id=media_info["file_unique_id"],
                file_id=media_info["file_id"],
                media_type=media_info["media_type"],
                mime_type=media_info["mime_type"],
                file_size=media_info["file_size"],
                original_chat_id=str(message.chat.id),
                original_message_id=message.id,
                caption=media_info["caption"],
                collected_at=datetime.utcnow(),
            )
            db.add(new_media)
            db.commit()
            logging.info(
                f"[CACHE] Mídia {media_info['file_unique_id']} salva no banco com id={new_media.id}."
            )

            for dest_id in destination_ids:
                try:
                    try:
                        await telegram_service.send_media_by_type(
                            client, str(dest_id), media_info
                        )
                        logging.info(
                            f"Mídia {media_info['file_unique_id']} reenviada para {dest_id} como nova mensagem."
                        )
                    except ValueError:
                        await message.forward(dest_id)
                        logging.info(
                            f"Mídia {media_info['file_unique_id']} encaminhada para {dest_id} via forward (tipo não suportado para envio manual)."
                        )
                except Exception as e:
                    logging.error(f"Erro ao reenviar mídia para {dest_id}: {e}")
