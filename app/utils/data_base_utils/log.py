from sqlalchemy.orm import Session
from app.models.database import Log


# ---------------------------
# LOG
# ---------------------------


def create_log(db: Session, level: str, message: str, source: str = None):
    log = Log(
        level=level,
        message=message,
        source=source,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs(db: Session):
    return db.query(Log).order_by(Log.timestamp.desc()).all()


def get_log(db: Session, log_id: int):
    return db.query(Log).filter(Log.id == log_id).first()


def update_log(db: Session, log_id: int, **kwargs):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        return None

    for key, value in kwargs.items():
        if hasattr(log, key) and value is not None:
            setattr(log, key, value)

    db.commit()
    db.refresh(log)
    return log


def delete_log(db: Session, log_id: int):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True
