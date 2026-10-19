"""
Pydantic Schemas for ChatBiz API requests and responses.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# User Schemas
class UserRegisterRequest(BaseModel):
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
    subscription_plan: str = "free"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Client Schemas
class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


# Invoice Schemas
class InvoiceCreate(BaseModel):
    client_id: int
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    due_date: str
    upi_id: Optional[str] = None
    recurring: Optional[int] = 0
    recurrence: Optional[str] = None


class InvoiceStatusUpdate(BaseModel):
    status: str


class RecurringInvoiceCreate(BaseModel):
    client_id: int
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    due_date: str
    recurrence: str = "MONTHLY"


# Payment Schemas
class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float = Field(..., gt=0)
    transaction_id: Optional[str] = None
    payment_date: Optional[str] = None
    source: Optional[str] = "manual"
    raw_text: Optional[str] = None


# Voice Command Schemas
class VoiceCommandCreate(BaseModel):
    transcript: str
    intent: Optional[str] = "GENERAL_QUERY"


class VoiceDemo(BaseModel):
    transcript: str
