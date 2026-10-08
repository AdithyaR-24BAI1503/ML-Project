-- MySQL Schema for ChatBiz Business Management System
CREATE DATABASE IF NOT EXISTS chatbiz CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chatbiz;

-- Users table (Sprint 1 SQLAlchemy model)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    phone_whatsapp VARCHAR(20) NOT NULL UNIQUE,
    business_name VARCHAR(150),
    gst_number VARCHAR(20),
    subscription_plan VARCHAR(30) DEFAULT 'free',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone_whatsapp (phone_whatsapp)
) ENGINE=InnoDB;

-- Clients table (Unified for Sprints 1-6)
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20),
    email VARCHAR(120),
    address VARCHAR(255),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_clients_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Invoices table (Unified for Sprints 1-6)
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    client_id INT NOT NULL,
    invoice_number VARCHAR(50) NULL UNIQUE,
    description VARCHAR(255) NOT NULL DEFAULT '',
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    tax DECIMAL(10, 2) DEFAULT 0.00,
    total DECIMAL(10, 2) NULL,
    due_date VARCHAR(50),
    upi_id VARCHAR(100),
    status VARCHAR(30) DEFAULT 'Pending',
    pdf_path VARCHAR(255),
    pdf_url VARCHAR(255),
    recurring INT DEFAULT 0,
    recurrence VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_invoices_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Invoice Items table (Sprint 1)
CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity INT DEFAULT 1,
    rate DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_items_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Payments table (Unified for Sprints 1-6)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    transaction_id VARCHAR(100),
    payment_date VARCHAR(50),
    source VARCHAR(50) DEFAULT 'manual',
    method VARCHAR(30) NULL,
    raw_text TEXT,
    screenshot_url VARCHAR(255),
    verified TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Reminders table (Unified for Sprints 1-6)
CREATE TABLE IF NOT EXISTS reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    reminder_type VARCHAR(50),
    scheduled_for VARCHAR(50),
    scheduled_at DATETIME NULL,
    sent_at VARCHAR(50),
    status VARCHAR(30) DEFAULT 'PENDING',
    type VARCHAR(30) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reminders_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Recurring Invoices table (Sprint 1)
CREATE TABLE IF NOT EXISTS recurring_invoices (
    recurring_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    client_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    frequency VARCHAR(20),
    next_generation_date DATE,
    active TINYINT(1) DEFAULT 1,
    CONSTRAINT fk_rec_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_rec_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Messages table (Sprint 1)
CREATE TABLE IF NOT EXISTS messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message_type VARCHAR(20),
    content TEXT,
    direction VARCHAR(10),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_messages_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Voice Commands table (Sprints 5-6)
CREATE TABLE IF NOT EXISTS voice_commands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcript TEXT,
    intent VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
