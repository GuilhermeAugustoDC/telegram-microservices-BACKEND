from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
import os
import json
from datetime import datetime
from app.schemas.session import Session as SessionSchema
from app.models.database import UserSession
from app.api.dependencies import get_db
from app.config.config import settings
from app.utils.data_base_utils.user_session import *
from app.utils.file_helpers import remove_file

router = APIRouter()

"""Lista todas as sessões de usuário salvas."""


@router.get("/sessions/", response_model=List[SessionSchema])
async def list_sessions(db: Session = Depends(get_db)):
    return get_user_sessions(db)


"""Faz o download de um arquivo de sessão."""


@router.get("/sessions/download/{phone_number}")
async def download_session(phone_number: str):
    file_path = (
        settings.SESSIONS_DIR / f"{phone_number}{settings.SESSION_EXTENSION_FILE}"
    )

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo de sessão não encontrado")
    return FileResponse(
        path=file_path,
        filename=f"{phone_number}.session",
        media_type="application/octet-stream",
    )


"""Faz a remoção de um arquivo de sessão do DB e do Diretorio."""


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)):

    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    session_file = settings.SESSIONS_DIR / session.session_file

    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontada")

    if not os.path.exists(session_file):
        raise HTTPException(status_code=404, detail="Sessão não encontada no Diretorio")

    remove_file(str(session_file))
    delete_user_session(db, session_id)
    return {"detail": "Sessão removida com sucesso"}


@router.websocket("/ws/generate_session")
async def generate_session_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db),
):
    await websocket.accept()
    client = None
    try:
        data = await websocket.receive_json()
        if data.get("type") == "start":
            api_id = data["api_id"]
            api_hash = data["api_hash"]
            phone_number = data["phone_number"]

            # caminho absoluto para a sessão
            session_path = settings.SESSIONS_DIR / str(phone_number)
            session_name = str(session_path)

            client = Client(session_name, api_id, api_hash, in_memory=False)

            await client.connect()
            await websocket.send_json(
                {
                    "status": "info",
                    "message": "Conectado ao Telegram. Enviando código...",
                }
            )

            try:
                sent_code = await client.send_code(phone_number)
                await websocket.send_json(
                    {
                        "status": "prompt",
                        "message": "Digite o código recebido no Telegram:",
                    }
                )
                code_data = await websocket.receive_json()
                phone_code = code_data["value"]

                await client.sign_in(
                    phone_number, sent_code.phone_code_hash, phone_code
                )

                # arquivo da sessão
                session_filename = f"{phone_number}.session"

                session_data = create_user_session(
                    session_file=session_filename,
                    phone_number=phone_number,
                    api_id=api_id,
                    api_hash=api_hash,
                    db=db,
                )

                await websocket.send_text(
                    json.dumps(
                        {
                            "status": "success",
                            "message": f"Sessão criada com sucesso! Arquivo: {session_filename}",
                            "session_id": session_data.id,
                            "session_data": {
                                "id": session_data.id,
                                "session_file": session_data.session_file,
                                "phone_number": session_data.phone_number,
                                "created_at": session_data.created_at.isoformat(),
                            },
                        }
                    )
                )

            except SessionPasswordNeeded:
                await websocket.send_json(
                    {
                        "status": "prompt",
                        "message": "Digite sua senha de verificação de duas etapas:",
                    }
                )
                password_data = await websocket.receive_json()
                password = password_data["value"]
                await client.check_password(password)

                session_filename = f"{phone_number}.session"
                session_data = create_user_session(
                    db=db,
                    session_file=session_filename,
                    phone_number=phone_number,
                    api_id=api_id,
                    api_hash=api_hash,
                )

                await websocket.send_text(
                    json.dumps(
                        {
                            "status": "success",
                            "message": f"Sessão criada com sucesso! Arquivo: {session_filename}",
                            "session_id": session_data.id,
                            "session_data": {
                                "id": session_data.id,
                                "session_file": session_data.session_file,
                                "phone_number": session_data.phone_number,
                                "created_at": session_data.created_at.isoformat(),
                            },
                        }
                    )
                )

            except (PhoneCodeInvalid, PhoneNumberInvalid) as e:
                await websocket.send_json(
                    {"status": "error", "message": str(e), "error": str(e)}
                )
            finally:
                if client.is_connected:
                    await client.disconnect()

    except Exception as e:
        error_message = f"Ocorreu um erro: {e}"
        await websocket.send_json(
            {"status": "error", "message": error_message, "error": str(e)}
        )
        print(error_message)
    finally:
        if client and client.is_connected:
            await client.disconnect()
        await websocket.close()
