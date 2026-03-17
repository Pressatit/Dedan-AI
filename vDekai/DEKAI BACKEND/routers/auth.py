from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime,timezone
import models, schemas
from database import sessionmk
from Hashing import Hash
from security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    tags=["authentication"],
    prefix="/auth"
)


def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()



@router.post("/login", response_model=schemas.Token)
def login(request: OAuth2PasswordRequestForm=Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.username).first()

    if not user or not Hash.verify(user.password, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    session = models.UserSession(
        user_id=user.id,
        token=access_token,
        expires_at=datetime.now(timezone.utc) + access_token_expires
    )
    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/signup", response_model=schemas.ShowUser)
def signup(request: schemas.User, db: Session = Depends(get_db)):
    # check if user exists
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    # create new user
    new_user = models.User(
        email=request.email,
        name=request.name,
        password=Hash.bcrypt(request.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

