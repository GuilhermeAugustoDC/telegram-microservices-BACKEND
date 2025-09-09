from pydantic import BaseModel
from typing import Optional


class ChannelInfo(BaseModel):
    id: str
    title: str
    username: Optional[str] = None
    is_channel: bool
    members_count: Optional[int] = None
    photo_url: Optional[str] = None
