from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.automation import Automation, AutomationCreate
from app.models.database import Automation as AutomationModel, Chat, UserSession
from app.api.dependencies import get_db

router = APIRouter()


"""Cria uma nova automação"""


@router.post("/automations/", response_model=Automation)
async def create_automation(
    automation: AutomationCreate, db: Session = Depends(get_db)
):
    db_session = (
        db.query(UserSession).filter(UserSession.id == automation.session_id).first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    db_automation = AutomationModel(
        name=automation.name,
        is_active=False,
        session_id=automation.session_id,
    )

    # Adiciona canais de origem
    for chat_id in automation.source_chats:
        chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
        if not chat:
            chat = Chat(chat_id=chat_id)
            db.add(chat)
        db_automation.source_chats.append(chat)

    # Adiciona canais de destino
    for chat_id in automation.destination_chats:
        chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
        if not chat:
            chat = Chat(chat_id=chat_id)
            db.add(chat)
        db_automation.destination_chats.append(chat)

    db.add(db_automation)
    db.commit()
    db.refresh(db_automation)

    return Automation.from_orm(db_automation)


"""Lista todas as automações"""


@router.get("/automations/", response_model=List[Automation])
async def list_automations(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):

    automations = db.query(AutomationModel).offset(skip).limit(limit).all()
    return [Automation.from_orm(automation) for automation in automations]


"""Inicia uma automação"""


@router.put("/automations/{automation_id}/start")
async def start_automation(automation_id: int, db: Session = Depends(get_db)):

    automation = (
        db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    automation.is_active = True
    db.commit()

    return {"message": f"Automação {automation_id} iniciada com sucesso"}


"""Para uma automação"""


@router.put("/automations/{automation_id}/stop")
async def stop_automation(automation_id: int, db: Session = Depends(get_db)):

    automation = (
        db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    automation.is_active = False
    db.commit()

    return {"message": f"Automação {automation_id} parada com sucesso"}


"""Remove uma automação"""


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: int, db: Session = Depends(get_db)):

    automation = (
        db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    db.delete(automation)
    db.commit()

    return {"message": f"Automação {automation_id} removida com sucesso"}
