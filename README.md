# ChatBiz — WhatsApp-First Business Management System

A multi-sprint software engineering implementation for **ChatBiz**, an AI-powered business management platform tailored for Indian MSMEs (freelancers, tutors, kirana store owners, and service providers).

---

## 📌 Project Overview

ChatBiz enables small business owners to handle customer onboarding, invoice generation with UPI payment QR codes, payment verification, automated payment reminders, voice commands, and business analytics.

This repository contains the complete 6-sprint iterative implementation of ChatBiz:

| Sprint | Module / Feature Focus | Deliverables & Scope |
| :--- | :--- | :--- |
| **Sprint 1** | User Onboarding & DB Schema | Core database architecture, user registration endpoint, SQLAlchemy models, and NLP command parser. |
| **Sprint 2** | Client Management & NLP | Natural language interface to add, search, update, list, and delete client profiles. Interactive web demo UI. |
| **Sprint 3** | Invoicing & PDF Delivery | Dynamic invoice creation, PDF generation with embedded UPI payment QR code, and simulated WhatsApp PDF delivery. |
| **Sprint 4** | Payment Tracking & OCR | Manual payment recording, payment history logging, payment status updates (Pending -> Paid), and payment screenshot OCR extraction. |
| **Sprint 5** | Reminders & Voice Pipeline | Automated scheduled payment reminders (Before Due, Due Today, Overdue), recurring invoices, and voice command intent classification. |
| **Sprint 6** | Analytics Dashboard & Deployment | Comprehensive business analytics dashboard, client metrics summary, CSV export endpoint, Docker containerization, and full test suite. |

---

## 🛠️ Database Architecture

The system utilizes SQLite for local development with a unified 5-table relational schema:

- **`clients`**: Customer profiles (`id`, `name`, `phone`, `email`, `created_at`).
- **`invoices`**: Billing records (`id`, `client_id`, `description`, `amount`, `due_date`, `upi_id`, `status`, `pdf_path`, `recurring`, `recurrence`, `created_at`).
- **`payments`**: Transaction records (`id`, `invoice_id`, `amount`, `transaction_id`, `payment_date`, `source`, `raw_text`, `created_at`).
- **`reminders`**: Notification schedules (`id`, `invoice_id`, `reminder_type`, `scheduled_for`, `status`, `sent_at`, `created_at`).
- **`voice_commands`**: Voice assistant transcripts & intent logs (`id`, `transcript`, `intent`, `created_at`).

---

## ⚙️ Quick Start

### 1. Installation

Clone the repository and install all required Python packages:

```bash
git clone https://github.com/AdithyaR-24BAI1503/ML-Project.git
cd ML-Project
git checkout Database-connect-govind

pip install -r requirements.txt
```

### 2. Run Sprint 6 Web Dashboard

To launch the full ChatBiz web dashboard locally:

```bash
cd Sprint_6
py -m uvicorn app.main:app --port 8000 --reload
```

Open your browser at **`http://127.0.0.1:8000`** to view the analytics dashboard.

### 3. Run Automated Tests

To run tests across all sprints:

```bash
# Test Sprint 1
cd "Sprint 1" && py -m pytest

# Test Sprint 6
cd Sprint_6 && py -m pytest
```

---

## 🐳 Docker Deployment

To build and run the ChatBiz Sprint 6 application in Docker:

```bash
cd Sprint_6
docker build -t chatbiz-sprint6 .
docker run -p 8000:8000 chatbiz-sprint6
```

---

## 📄 License
Academic & SE Lab Project Implementation.
