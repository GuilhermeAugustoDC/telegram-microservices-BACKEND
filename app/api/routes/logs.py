from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.database import Log
from app.api.dependencies import get_db

router = APIRouter()


class LogEntry(BaseModel):
    id: int
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/logs", response_model=List[LogEntry])
def get_logs(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(
        None, description="Filtrar por nível (INFO, WARNING, ERROR)"
    ),
    source: Optional[str] = Query(None, description="Filtrar pela origem do log"),
):
    """Busca os logs do sistema com filtros opcionais."""
    query = db.query(Log)

    if level:
        query = query.filter(Log.level == level.upper())

    if source:
        query = query.filter(Log.source.ilike(f"%{source}%"))

    logs = query.order_by(Log.timestamp.desc()).limit(limit).all()
    return logs
