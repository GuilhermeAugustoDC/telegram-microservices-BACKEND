from sqlalchemy.orm import Session
from app.models.database import CachedChannel

# ---------------------------
# CACHED CHANNEL
# ---------------------------


def create_cached_channel(
    db: Session,
    session_id: int,
    channel_id: str,
    title: str = None,
    username: str = None,
    is_channel: bool = False,
    members_count: int = None,
    photo_url: str = None,
):
    cached = CachedChannel(
        session_id=session_id,
        channel_id=channel_id,
        title=title,
        username=username,
        is_channel=is_channel,
        members_count=members_count,
        photo_url=photo_url,
    )
    db.add(cached)
    db.commit()
    db.refresh(cached)
    return cached


def get_cached_channels(db: Session):
    return db.query(CachedChannel).all()


def get_cached_channel(db: Session, cached_id: int):
    return db.query(CachedChannel).filter(CachedChannel.id == cached_id).first()


def update_cached_channel(db: Session, cached_id: int, **kwargs):
    cached = db.query(CachedChannel).filter(CachedChannel.id == cached_id).first()
    if not cached:
        return None

    for key, value in kwargs.items():
        if hasattr(cached, key) and value is not None:
            setattr(cached, key, value)

    db.commit()
    db.refresh(cached)
    return cached


def delete_cached_channel(db: Session, cached_id: int):
    cached = db.query(CachedChannel).filter(CachedChannel.id == cached_id).first()
    if not cached:
        return False

    db.delete(cached)
    db.commit()
    return True
