from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import requests, os
import models
from database import sessionmk
from security import create_access_token
from datetime import timedelta,datetime,timezone
from starlette.responses import RedirectResponse
import urllib.parse
from models import UserSession

router = APIRouter(prefix="/auth/google", tags=["authentication"])

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI
)

ACCESS_TOKEN_EXPIRE_MINUTES = 120

def get_db():
    db = sessionmk()
    try:
        yield db
    finally:
        db.close()

@router.get("/login")
def google_login():
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
    )
    return RedirectResponse(url)

@router.get("/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    # Exchange code for token
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        },
    )
    token_data = token_resp.json()

    access_token_google = token_data.get("access_token")
    if not access_token_google:
        raise HTTPException(status_code=400, detail="Google auth failed")

    # Get user info
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token_google}"},
    ).json()

    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    # Find or create user
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email, name=name, password="GOOGLE_OAUTH")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue DEKAI token
    dekai_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=24)
    )
    

# after creating access_token and getting user.id
    expires_at = datetime.now(timezone.utc)  + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    db_session = UserSession(
    user_id=user.id,
    token=dekai_token,
    expires_at=expires_at
    )

    db.add(db_session)
    db.commit()

    # Use environment variable for frontend URL
    streamlit_url = os.getenv("FRONTEND_URL", "http://localhost:8501")

    query = urllib.parse.urlencode({
    "token": dekai_token,
    "email": email,
    "name": name
    })

    return RedirectResponse(f"{streamlit_url}/?{query}")
