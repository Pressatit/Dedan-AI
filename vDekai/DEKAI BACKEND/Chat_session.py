from sqlalchemy.orm import Session
from models import Session
import secrets
from datetime import datetime

def create_session(db: Session, user_id: int, expires_at: datetime):
    session = Session(
        user_id=user_id,          # 🔗 foreign key link
        token=secrets.token_urlsafe(32),
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
