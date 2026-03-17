# Load environment variables FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import user,conversation,message,auth,generate,vision_generate,google_auth

#declarations
App=FastAPI(
    title="DEKAI API",
    description="DEKAI AI Assistant Backend API",
    version="1.0.0"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")

App.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
models.Base.metadata.create_all(engine)

# Environment variables (no debug prints in production)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

#routes
App.include_router(auth.router)
App.include_router(conversation.router)
App.include_router(user.router)
App.include_router(message.router)
App.include_router(generate.router)
App.include_router(vision_generate.router)
App.include_router(google_auth.router)

# Health check endpoint
@App.get("/health")
def health_check():
    return {"status": "healthy"}
