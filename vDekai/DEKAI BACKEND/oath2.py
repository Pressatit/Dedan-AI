from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import models
from security import SECRET_KEY, ALGORITHM
from database import sessionmk

def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    session = db.query(models.UserSession).filter(models.UserSession.token == token).first()
    if not session:
        raise HTTPException(status_code=401)

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    return user

