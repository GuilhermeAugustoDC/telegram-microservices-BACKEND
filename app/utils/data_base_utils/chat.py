from sqlalchemy.orm import Session
from app.models.database import Chat

# ---------------------------
# CHAT
# ---------------------------


def create_chat(db: Session, chat_id: str, title: str = None, is_channel: bool = False):
    chat = Chat(chat_id=chat_id, title=title, is_channel=is_channel)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_chats(db: Session):
    return db.query(Chat).all()


def get_chat(db: Session, chat_id: int):
    return db.query(Chat).filter(Chat.id == chat_id).first()


def update_chat(db: Session, chat_id: int, **kwargs):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return None

    for key, value in kwargs.items():
        if hasattr(chat, key) and value is not None:
            setattr(chat, key, value)

    db.commit()
    db.refresh(chat)
    return chat


def delete_chat(db: Session, chat_id: int):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return False

    db.delete(chat)
    db.commit()
    return True


