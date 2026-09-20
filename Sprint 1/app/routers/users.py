"""
User registration endpoint.

Implements the functional requirement from Lab 1:
"The system shall allow users to register through a WhatsApp
onboarding conversation using their phone number."

For now this exposes a plain REST endpoint that the future
WhatsApp webhook handler (Gateway Layer, per Lab 3 architecture)
will call once it has parsed an onboarding conversation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register_user(payload: schemas.UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new business owner, keyed by their WhatsApp phone number."""
    existing = (
        db.query(models.User)
        .filter(models.User.phone_whatsapp == payload.phone_whatsapp)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A user with this WhatsApp number is already registered.",
        )

    user = models.User(
        name=payload.name,
        phone_whatsapp=payload.phone_whatsapp,
        business_name=payload.business_name,
        gst_number=payload.gst_number,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{phone_whatsapp}", response_model=schemas.UserResponse)
def get_user_by_phone(phone_whatsapp: str, db: Session = Depends(get_db)):
    """Look up a registered user by WhatsApp phone number."""
    user = (
        db.query(models.User)
        .filter(models.User.phone_whatsapp == phone_whatsapp)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
