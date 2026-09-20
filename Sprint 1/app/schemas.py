"""
Pydantic schemas — request/response shapes for the API.
Kept separate from the SQLAlchemy models (app/models.py) so the DB
layer and the API contract can evolve independently.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    """Payload for the WhatsApp onboarding / registration flow."""

    name: str = Field(..., min_length=1, max_length=120)
    phone_whatsapp: str = Field(..., min_length=8, max_length=20)
    business_name: Optional[str] = None
    gst_number: Optional[str] = None


class UserResponse(BaseModel):
    user_id: int
    name: str
    phone_whatsapp: str
    business_name: Optional[str] = None
    gst_number: Optional[str] = None
    subscription_plan: str
    created_at: datetime

    class Config:
        from_attributes = True
