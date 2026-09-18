from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Check for DATABASE_PATH environment variable (for Dokku mounted storage)
DATABASE_PATH = os.getenv("DATABASE_PATH")

if DATABASE_PATH:
    # Ensure the parent directory exists (e.g. /app/storage/)
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
else:
    # Fallback to local path for development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "chat_history_database.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
