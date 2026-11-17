from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# SQLite ke liye ye extra setting chahiye, PostgreSQL ke liye nahi
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

# Engine: database se asli connection
engine = create_engine(settings.database_url, connect_args=connect_args)

# SessionLocal: har request ke liye ek database session banata hai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base: hamare saare tables (models) isi se banenge
class Base(DeclarativeBase):
    pass


# FastAPI dependency: har request ko session dena, aur khatam hone par band karna
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()