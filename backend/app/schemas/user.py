from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Register karte waqt user ye bhejega."""

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class UserRead(BaseModel):
    """API user ko ye wapas bhejegi (password kabhi nahi)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    """Login ke baad ye token milega."""

    access_token: str
    token_type: str = "bearer"