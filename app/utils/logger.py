from app.models.database import Log, SessionLocal
from datetime import datetime

def db_log(level: str, message: str, source: str):
    """
    Registra uma mensagem de log no banco de dados.
    Níveis: INFO, WARNING, ERROR, DEBUG
    """
    db = SessionLocal()
    try:
        log_entry = Log(
            timestamp=datetime.utcnow(),
            level=level.upper(),
            message=message,
            source=source
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Falha ao registrar log no banco de dados: {e}")
        db.rollback()
    finally:
        db.close()
