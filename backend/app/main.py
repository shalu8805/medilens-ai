from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health
from app.core.config import settings
from app.core.database import Base, engine
from app.models import user  # noqa: F401  (isse User table register hota hai)

# Tables banao (agar pehle se nahi hain)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# CORS: React app (port 5173) ko is API (port 8000) ko call karne ki permission
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")