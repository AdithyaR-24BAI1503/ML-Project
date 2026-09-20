"""
ChatBiz REST API — entrypoint.

Per Lab 3 architecture, this is the "REST API Server (FastAPI + OTP Auth)"
component in the Gateway/API Layer. It currently exposes the Sprint 1
deliverable: user registration + a health check. Later sprints will add
invoices, payments, reminders, and analytics routers here.
"""
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import users

# Sprint 1: create tables from models on startup (dev convenience).
# In production this will be replaced by Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChatBiz API",
    description="WhatsApp-first business management system for Indian MSMEs",
    version="0.1.0",
)

app.include_router(users.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "ChatBiz API", "version": app.version}


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}
