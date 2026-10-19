"""
SQLAlchemy models for ChatBiz.
Provides relational ORM representation for Users, Clients, Invoices, Payments, and Reminders.
"""
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """Business owner registered in ChatBiz."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    phone_whatsapp = Column(String(20), unique=True, nullable=False, index=True)
    business_name = Column(String(150))
    gst_number = Column(String(20))
    subscription_plan = Column(String(30), default="free")
    created_at = Column(DateTime, default=datetime.now)


class Client(Base):
    """Customer or client of the MSME business."""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20))
    email = Column(String(120))
    address = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")


class Invoice(Base):
    """Bill / Invoice issued to a client."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    description = Column(String(255), nullable=False, default="")
    amount = Column(Numeric(10, 2), nullable=False, default=0)
    due_date = Column(String(50))
    upi_id = Column(String(100))
    status = Column(String(20), default="Pending")
    pdf_path = Column(String(255))
    recurring = Column(Integer, default=0)
    recurrence = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    client = relationship("Client", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="invoice", cascade="all, delete-orphan")


class Payment(Base):
    """Payment transaction received against an invoice."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False, default=0)
    transaction_id = Column(String(100))
    payment_date = Column(String(50))
    source = Column(String(50), default="manual")
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    invoice = relationship("Invoice", back_populates="payments")


class Reminder(Base):
    """Scheduled WhatsApp notification for an invoice."""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    reminder_type = Column(String(50))
    scheduled_for = Column(String(50))
    status = Column(String(20), default="PENDING")
    sent_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    invoice = relationship("Invoice", back_populates="reminders")
