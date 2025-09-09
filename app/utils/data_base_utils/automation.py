from sqlalchemy.orm import Session, joinedload
from app.models.database import AutomationModel, Chat

# ---------------------------
# AUTOMATION
# ---------------------------


def create_automation(
    db: Session,
    name: str,
    session_id: int,
    caption: str = None,
    source_chats: list[str] | None = None,
    destination_chats: list[str] | None = None,
):
    """
    Cria uma automação e adiciona canais de origem e destino.
    """
    automation = AutomationModel(
        name=name,
        session_id=session_id,
        caption=caption,
        is_active=False,
    )

    # Adiciona canais de origem
    if source_chats:
        for chat_id in source_chats:
            chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
            if not chat:
                chat = Chat(chat_id=chat_id)
                db.add(chat)
            automation.source_channels.append(chat)

    # Adiciona canais de destino
    if destination_chats:
        for chat_id in destination_chats:
            chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
            if not chat:
                chat = Chat(chat_id=chat_id)
                db.add(chat)
            automation.destination_channels.append(chat)

    db.add(automation)
    db.commit()
    db.refresh(automation)
    return automation


def get_automations(db: Session):
    """
    Retorna todas as automações com relacionamentos pré-carregados.
    """
    return (
        db.query(AutomationModel)
        .options(
            joinedload(AutomationModel.source_channels),
            joinedload(AutomationModel.destination_channels),
            joinedload(AutomationModel.session),
        )
        .all()
    )


def set_automation_status(db: Session, automation_id: int, is_active: bool):
    """
    Ativa ou desativa a automação e pré-carrega relacionamentos.
    """
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
        return None

    automation.is_active = is_active
    db.commit()
    db.refresh(automation)
    return automation


def get_automation(db: Session, automation_id: int):
    return db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()


def update_automation(db: Session, automation_id: int, **kwargs):
    automation = (
        db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()
    )
    if not automation:
        return None

    for key, value in kwargs.items():
        if hasattr(automation, key) and value is not None:
            setattr(automation, key, value)

    db.commit()
    db.refresh(automation)
    return automation


def delete_automation(db: Session, automation_id: int):
    automation = (
        db.query(AutomationModel).filter(AutomationModel.id == automation_id).first()
    )
    if not automation:
        return False

    db.delete(automation)
    db.commit()
    return True
