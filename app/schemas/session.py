from pydantic import BaseModel
from datetime import datetime

class SessionBase(BaseModel):
    phone_number: str

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    session_file: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
