from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
import os
import shutil
import json
from datetime import datetime

from app.schemas.session import Session as SessionSchema
from app.models.database import UserSession
from app.api.dependencies import get_db

router = APIRouter()

"""Endpoint para fazer upload de um arquivo .session"""


@router.post("/sessions/", response_model=SessionSchema)
async def upload_session(
    phone_number: str = Form(...),
    session_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not session_file.filename.endswith(".session"):
        raise HTTPException(
            status_code=400, detail="O arquivo deve ter a extensão .session"
        )

    session_filename = f"{phone_number}.session"
    file_location = f"sessions/{session_filename}"

    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(session_file.file, file_object)

    db_session = UserSession(session_file=session_filename, phone_number=phone_number)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session


"""Lista todas as sessões de usuário salvas."""


@router.get("/sessions/", response_model=List[SessionSchema])
async def list_sessions(db: Session = Depends(get_db)):

    sessions = db.query(UserSession).all()
    return sessions


"""Faz o download de um arquivo de sessão."""


@router.get("/sessions/download/{phone_number}")
async def download_session(phone_number: str):

    file_path = f"sessions/{phone_number}.session"
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
    # Remover do Banco De Dados
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontada")
    session_file = f"sessions/{session.session_file}"
    if not os.path.exists(session_file):
        raise HTTPException(status_code=404, detail="Sessão não encontada no Diretorio")
    os.remove(session_file)
    db.delete(session)
    db.commit()
    return {"detail": "Sessão removida com sucesso"}


@router.websocket("/ws/generate_session")
async def generate_session_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    client = None
    try:
        data = await websocket.receive_json()
        if data.get("type") == "start":
            api_id = data["api_id"]
            api_hash = data["api_hash"]
            phone_number = data["phone_number"]
            session_name = f"sessions/{phone_number}"

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
                session_filename = f"{phone_number}.session"
                session_data = UserSession(
                    session_file=session_filename,
                    phone_number=phone_number,
                    api_id=api_id,
                    api_hash=api_hash,
                    created_at=datetime.utcnow(),
                )

                db.add(session_data)
                db.commit()
                db.refresh(session_data)

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

                # Salva no banco após autenticação com senha
                session_filename = f"{phone_number}.session"
                session_data = UserSession(
                    session_file=session_filename,
                    phone_number=phone_number,
                    api_id=api_id,
                    api_hash=api_hash,
                    created_at=datetime.utcnow(),
                )
                db.add(session_data)
                db.commit()
                db.refresh(session_data)

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

    except WebSocketDisconnect:
        print("Cliente desconectado")
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
