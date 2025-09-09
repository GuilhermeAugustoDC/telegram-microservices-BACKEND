from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import UserSession

# ---------------------------
# USER SESSION
# ---------------------------


def create_user_session(
    db: Session,
    session_file: str,
    phone_number: str = None,
    api_id: str = None,
    api_hash: str = None,
):
    session_data = UserSession(
        session_file=session_file,
        phone_number=phone_number,
        api_id=api_id,
        api_hash=api_hash,
        created_at=datetime.utcnow(),
    )
    db.add(session_data)
    db.commit()
    db.refresh(session_data)
    return session_data


def get_user_sessions(db: Session):
    return db.query(UserSession).all()


def get_user_session(db: Session, session_id: int):
    return db.query(UserSession).filter(UserSession.id == session_id).first()


def update_user_session(db: Session, session_id: int, **kwargs):
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        return None

    for key, value in kwargs.items():
        if hasattr(session, key) and value is not None:
            setattr(session, key, value)

    db.commit()
    db.refresh(session)
    return session


def delete_user_session(db: Session, session_id: int):
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        return False

    db.delete(session)
    db.commit()
    return True
