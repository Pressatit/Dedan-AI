from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

# Load .env file if it exists (in case this module is imported before main.py loads it)
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable must be set. "
        "Please check your .env file in the DEKAI BACKEND directory. "
        "You can generate one with: openssl rand -hex 32"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)