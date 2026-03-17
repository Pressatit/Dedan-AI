from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

#engine
# If DATABASE_URL is not set, construct path to project root database
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # Default: look for DEKAI.db in project root (two directories up from backend)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../.."))
    db_path = os.path.join(project_root, "DEKAI.db")
    DATABASE_URL = f"sqlite:///{db_path}"

# SQLite-specific connection args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)
#base
Base=declarative_base()

#session
sessionmk=sessionmaker(bind=engine,autoflush=False,autocommit=False)

def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()