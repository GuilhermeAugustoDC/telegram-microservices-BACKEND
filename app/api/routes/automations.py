from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
import logging

from app.schemas.automation import (
    Automation as AutomationSchema,
    AutomationCreate,
    AutomationUpdate,
)
from app.models.database import AutomationModel, Chat, UserSession
from app.api.dependencies import get_db
from app.services.automation_handler import (
    start_automation_client,
    stop_automation_client,
)
from app.utils.data_base_utils.automation import (
    set_automation_status,
    create_automation,
    get_automations,
)

router = APIRouter()


"""Cria uma nova automação"""


@router.post("/automations/", response_model=AutomationSchema)
async def create_automation_route(
    automation: AutomationCreate, db: Session = Depends(get_db)
):
    db_session = (
        db.query(UserSession).filter(UserSession.id == automation.session_id).first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Criação completa usando o CRUD
    db_automation = create_automation(
        db=db,
        name=automation.name,
        session_id=automation.session_id,
        caption=automation.caption,
        source_chats=automation.source_chats,
        destination_chats=automation.destination_chats,
    )

    return AutomationSchema.from_orm(db_automation)


"""Lista todas as automações"""


@router.get("/automations/", response_model=List[AutomationSchema])
async def list_automations(db: Session = Depends(get_db)):
    automations = get_automations(db)
    return [AutomationSchema.from_orm(automation) for automation in automations]


"""Inicia uma automação"""


@router.put("/automations/{automation_id}/start")
async def start_automation_route(automation_id: int, db: Session = Depends(get_db)):
    automation = set_automation_status(db, automation_id, True)
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    # Inicia o cliente de automação
    await start_automation_client(automation)

    return {"message": f"Automação {automation_id} iniciada com sucesso"}


"""Para uma automação"""


@router.put("/automations/{automation_id}/stop")
async def stop_automation_route(automation_id: int, db: Session = Depends(get_db)):
    automation = set_automation_status(db, automation_id, False)
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    await stop_automation_client(automation)

    return {"message": f"Automação {automation_id} parada com sucesso"}


"""Remove uma automação"""


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: int, db: Session = Depends(get_db)):
    automation = (
        db.query(AutomationModel)
        .options(
            joinedload(AutomationModel.source_channels),
            joinedload(AutomationModel.destination_channels),
            joinedload(AutomationModel.session),
        )
        .filter(AutomationModel.id == automation_id)
        .first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    db.delete(automation)
    db.commit()

    return {"message": f"Automação {automation_id} removida com sucesso"}


"""Atualiza dados de uma autmação"""


@router.put("/automations/{automation_id}", response_model=AutomationSchema)
async def update_automation(
    automation_id: int, automation_data: AutomationUpdate, db: Session = Depends(get_db)
):
    automation = (
        db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    # Atualiza os campos fornecidos
    if automation_data.name is not None:
        automation.name = automation_data.name
    if automation_data.caption is not None:
        automation.caption = automation_data.caption

    db.commit()
    db.refresh(automation)
    return AutomationSchema.from_orm(automation)
