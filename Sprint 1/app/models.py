"""
SQLAlchemy models for ChatBiz.

These map 1:1 onto the eight entities from the Lab 4 ER Diagram:
USER, CLIENT, INVOICE, INVOICE_ITEM, PAYMENT, REMINDER,
RECURRING_INVOICE, MESSAGE. All relationships are one-to-many (1:M),
enforced via foreign keys, matching the ERD's cardinalities exactly.
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

from app.database import Base


class User(Base):
    """Business owner — freelancer, tutor, kirana shop owner, etc."""

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    phone_whatsapp = Column(String(20), unique=True, nullable=False, index=True)
    business_name = Column(String(150))
    gst_number = Column(String(20))
    subscription_plan = Column(String(30), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)

    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    recurring_invoices = relationship(
        "RecurringInvoice", back_populates="user", cascade="all, delete-orphan"
    )


class Client(Base):
    """A customer of the business owner."""

    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(120), nullable=False)
    phone = Column(String(20))
    email = Column(String(120))
    address = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
    recurring_invoices = relationship(
        "RecurringInvoice", back_populates="client", cascade="all, delete-orphan"
    )


class Invoice(Base):
    """A bill issued by a user to a client."""

    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="Pending")  # Pending | Paid | Overdue
    due_date = Column(Date)
    description = Column(String(255))
    pdf_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """A line item within an invoice."""

    __tablename__ = "invoice_items"

    item_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    rate = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class Payment(Base):
    """A payment received against an invoice."""

    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, default=datetime.utcnow)
    method = Column(String(30))  # UPI | cash | bank transfer
    transaction_id = Column(String(100))
    screenshot_url = Column(String(255))
    verified = Column(Boolean, default=False)

    invoice = relationship("Invoice", back_populates="payments")


class Reminder(Base):
    """A scheduled WhatsApp payment reminder."""

    __tablename__ = "reminders"

    reminder_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime)
    status = Column(String(20), default="pending")  # pending | sent | failed
    type = Column(String(20))  # before_due | on_due | after_due

    invoice = relationship("Invoice", back_populates="reminders")


class RecurringInvoice(Base):
    """A template for recurring billing (e.g. monthly tuition fee)."""

    __tablename__ = "recurring_invoices"

    recurring_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    frequency = Column(String(20))  # weekly | monthly
    next_generation_date = Column(Date)
    active = Column(Boolean, default=True)

    user = relationship("User", back_populates="recurring_invoices")
    client = relationship("Client", back_populates="recurring_invoices")


class Message(Base):
    """A logged WhatsApp message exchanged between the user and the bot."""

    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    message_type = Column(String(20))  # text | voice | image
    content = Column(Text)
    direction = Column(String(10))  # incoming | outgoing
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")
