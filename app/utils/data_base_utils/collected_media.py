from sqlalchemy.orm import Session
from app.models.database import CollectedMedia


# ---------------------------
# COLLECTED MEDIA
# ---------------------------


def create_collected_media(
    db: Session,
    file_unique_id: str,
    file_id: str,
    media_type: str,
    mime_type: str = None,
    file_size: int = None,
    original_chat_id: str = None,
    original_message_id: int = None,
    caption: str = None,
):
    media = CollectedMedia(
        file_unique_id=file_unique_id,
        file_id=file_id,
        media_type=media_type,
        mime_type=mime_type,
        file_size=file_size,
        original_chat_id=original_chat_id,
        original_message_id=original_message_id,
        caption=caption,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def get_collected_media(db: Session):
    return db.query(CollectedMedia).all()


def get_media(db: Session, media_id: int):
    return db.query(CollectedMedia).filter(CollectedMedia.id == media_id).first()


def update_collected_media(db: Session, media_id: int, **kwargs):
    media = db.query(CollectedMedia).filter(CollectedMedia.id == media_id).first()
    if not media:
        return None

    for key, value in kwargs.items():
        if hasattr(media, key) and value is not None:
            setattr(media, key, value)

    db.commit()
    db.refresh(media)
    return media


def delete_collected_media(db: Session, media_id: int):
    media = db.query(CollectedMedia).filter(CollectedMedia.id == media_id).first()
    if not media:
        return False

    db.delete(media)
    db.commit()
    return True
