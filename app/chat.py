"""
ChatBiz AI-Automated WhatsApp Business Chat Engine
Provides conversational AI engines for:
1. Client Portal: WhatsApp Business AI answering clients regarding their balance, invoices, payments, business hours, and policies.
2. Manager Portal: Executive AI Assistant executing all NLP commands, including fetching client/user profiles, issuing invoices, recording payments, managing clients, and reporting analytics.
"""
import difflib
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List

from .pdf_generator import generate_invoice_pdf
from .reminders import seed_invoice_reminders, run_due_reminders
from .analytics import summary, client_summary
from .nlp import parse_command


def format_inr(val: float) -> str:
    """Formats a float value into Indian Rupee representation."""
    return f"₹{val:,.2f}"


def save_chat_message(
    conn,
    session_id: str,
    role: str,
    sender: str,
    content: str,
    client_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Persists a chat message into the chat_messages table."""
    meta_json = json.dumps(metadata) if metadata else None
    cur = conn.execute("""
        INSERT INTO chat_messages (session_id, role, sender, client_id, content, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, role, sender, client_id, content, meta_json))
    conn.commit()
    return cur.lastrowid


def get_chat_history(conn, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves conversation history for a given session."""
    rows = conn.execute("""
        SELECT id, session_id, role, sender, client_id, content, metadata_json, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (session_id, limit)).fetchall()
    
    result = []
    for r in rows:
        item = dict(r)
        if item.get("metadata_json"):
            try:
                item["metadata"] = json.loads(item["metadata_json"])
            except Exception:
                item["metadata"] = None
        else:
            item["metadata"] = None
        result.append(item)
    return result


def clear_chat_history(conn, session_id: str) -> int:
    """Clears all messages for a session."""
    cur = conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.commit()
    return cur.rowcount


# =========================================================================
# 1. CLIENT-SIDE WHATSAPP BUSINESS AI
# =========================================================================
def handle_client_message(client_id: int, message: str, conn) -> Dict[str, Any]:
    """
    Automated WhatsApp Business AI chatbot answering client inquiries in natural language.
    Understands balance checks, invoice queries, payment instructions, payment confirmations,
    business hours, and general business information.
    """
    clean_msg = message.strip()
    t = clean_msg.lower()
    
    # 1. Fetch client profile
    client = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    if not client:
        return {
            "reply": "⚠️ Error: Selected client account could not be found. Please select a valid client from the dropdown.",
            "metadata": {"type": "error"}
        }
    
    client_dict = dict(client)
    client_name = client_dict["name"]
    first_name = client_name.split()[0] if client_name else "Valued Client"
    
    # 2. Fetch client's invoices
    invoices = conn.execute("""
        SELECT * FROM invoices WHERE client_id=? ORDER BY id DESC
    """, (client_id,)).fetchall()
    invoices_list = [dict(i) for i in invoices]
    
    total_invoiced = sum(i["amount"] for i in invoices_list)
    paid_invoices = [i for i in invoices_list if i["status"] == "Paid"]
    total_paid = sum(i["amount"] for i in paid_invoices)
    pending_invoices = [i for i in invoices_list if i["status"] != "Paid"]
    pending_balance = sum(i["amount"] for i in pending_invoices)
    overdue_invoices = [i for i in pending_invoices if i["status"] == "Overdue"]
    latest_invoice = invoices_list[0] if invoices_list else None
    
    # 3. Fetch past payments
    payments = conn.execute("""
        SELECT p.*, i.description AS invoice_desc
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        WHERE i.client_id=?
        ORDER BY p.id DESC
        LIMIT 5
    """, (client_id,)).fetchall()
    payments_list = [dict(p) for p in payments]
    
    # Session identifier for this client's WhatsApp chat thread
    session_id = f"client_{client_id}"
    
    # Save user's incoming message
    save_chat_message(
        conn=conn,
        session_id=session_id,
        role="user",
        sender=client_name,
        content=clean_msg,
        client_id=client_id
    )
    
    reply = ""
    metadata: Dict[str, Any] = {}
    
    # ---------------------------------------------------------------------
    # Intent A: Outstanding Balance / Dues Inquiry
    # ---------------------------------------------------------------------
    if any(k in t for k in [
        "balance", "due", "pending", "owe", "how much", "kitna", "baki",
        "clear", "status of payment", "my dues", "account status", "unpaid"
    ]):
        if pending_balance <= 0:
            reply = (
                f"Hello {first_name}! 🌟\n\n"
                f"Your account is completely up to date with **{format_inr(0.0)} outstanding balance**.\n"
                f"All {len(invoices_list)} past invoice(s) are fully settled. Thank you for your continued partnership!"
            )
            metadata = {
                "type": "balance_clear",
                "pending_balance": 0.0,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid
            }
        else:
            inv_lines = []
            for inv in pending_invoices[:4]:
                inv_lines.append(f"• **Invoice #{inv['id']:04d}**: {format_inr(inv['amount'])} ({inv['description']}) — Due: {inv['due_date']}")
            
            overdue_note = f"\n⚠️ **Note:** {len(overdue_invoices)} invoice(s) are currently overdue." if overdue_invoices else ""
            
            reply = (
                f"Hello {first_name}! 📋\n\n"
                f"Your total outstanding balance is **{format_inr(pending_balance)}** across {len(pending_invoices)} unpaid invoice(s):{overdue_note}\n\n"
                + "\n".join(inv_lines) +
                f"\n\n💳 You can pay instantly using UPI ID: `chatbiz.merchant@upi`."
            )
            metadata = {
                "type": "balance_due",
                "pending_balance": pending_balance,
                "pending_count": len(pending_invoices),
                "invoices": pending_invoices[:4],
                "upi_id": "chatbiz.merchant@upi"
            }

    # ---------------------------------------------------------------------
    # Intent B: Invoice Request / Specific Invoice / PDF Download
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["invoice", "bill", "receipt", "pdf", "download", "copy", "inv-", "send invoice", "latest bill"]):
        # Check if client asked for a specific invoice ID
        inv_match = re.search(r'(?:inv-?|#|\binvoice\s*#?)\s*(\d+)', t)
        target_inv = None
        if inv_match:
            req_id = int(inv_match.group(1))
            target_inv = next((i for i in invoices_list if i["id"] == req_id), None)
        
        if not target_inv:
            target_inv = latest_invoice
            
        if not target_inv:
            reply = f"Hello {first_name}, there are currently no invoices issued for your account."
            metadata = {"type": "no_invoices"}
        else:
            reply = (
                f"📄 **Invoice #{target_inv['id']:04d}**\n\n"
                f"• **Description:** {target_inv['description']}\n"
                f"• **Amount:** {format_inr(target_inv['amount'])}\n"
                f"• **Due Date:** {target_inv['due_date']}\n"
                f"• **Status:** {target_inv['status']}\n"
                f"• **UPI ID:** `{target_inv.get('upi_id') or 'chatbiz.merchant@upi'}`\n\n"
                f"Click below to download your official PDF invoice with the embedded UPI payment QR code."
            )
            metadata = {
                "type": "invoice_download",
                "invoice_id": target_inv["id"],
                "download_url": f"/api/invoices/{target_inv['id']}/pdf",
                "amount": target_inv["amount"],
                "status": target_inv["status"]
            }

    # ---------------------------------------------------------------------
    # Intent C: Payment Methods / UPI / QR Code / How to Pay
    # ---------------------------------------------------------------------
    elif any(k in t for k in [
        "pay", "upi", "qr", "gpay", "phonepe", "paytm", "bank", "account",
        "transfer", "how to pay", "payment method", "where to pay", "scanner"
    ]):
        reply = (
            f"💳 **Official Payment Instructions — ChatBiz Enterprise**\n\n"
            f"You can settle any outstanding dues securely via Instant UPI:\n"
            f"• **Merchant UPI ID:** `chatbiz.merchant@upi`\n"
            f"• **Payee Name:** ChatBiz Solutions Pvt Ltd\n"
            f"• **Accepted Apps:** Google Pay, PhonePe, Paytm, BHIM UPI, and Banking apps.\n\n"
            f"📱 **QR Code:** Available on each invoice PDF.\n"
            f"🧾 **Instant Reconciliation:** Once you transfer, simply upload or share your payment screenshot. Our automated OCR will verify the reference and settle your account immediately!"
        )
        metadata = {
            "type": "payment_info",
            "upi_id": "chatbiz.merchant@upi",
            "suggested_action": "Download Invoice PDF to scan QR code"
        }

    # ---------------------------------------------------------------------
    # Intent D: Payment Confirmation / History
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["paid", "already paid", "payment status", "received", "payment history", "did you get", "transferred", "settled"]):
        if payments_list:
            pmt_lines = []
            for p in payments_list:
                pmt_lines.append(f"• **{p['payment_date']}**: {format_inr(p['amount'])} (Txn: `{p['transaction_id'] or 'Verified'}`) — {p['invoice_desc']}")
            
            reply = (
                f"✅ **Verified Payment History for {first_name}**\n\n"
                f"We have recorded the following payments from your account:\n\n"
                + "\n".join(pmt_lines) +
                f"\n\n**Current Outstanding Balance:** {format_inr(pending_balance)}."
            )
            metadata = {
                "type": "payment_history",
                "payments": payments_list,
                "pending_balance": pending_balance
            }
        else:
            reply = (
                f"Hello {first_name}, we do not have any recorded payment transactions on file for your account yet.\n\n"
                f"If you made a payment recently, please share the transaction reference number or a screenshot of the receipt so our team can immediately reconcile it!"
            )
            metadata = {"type": "no_payments_found"}

    # ---------------------------------------------------------------------
    # Intent E: Business Information / Timings / Location / GST / Contact
    # ---------------------------------------------------------------------
    elif any(k in t for k in [
        "hours", "timings", "timing", "open", "address", "location", "office",
        "services", "gst", "contact", "phone", "support", "who are you", "about",
        "company", "email", "website"
    ]):
        reply = (
            f"🏢 **ChatBiz Enterprise Solutions — Official Information**\n\n"
            f"• **Company:** ChatBiz Solutions Pvt. Ltd.\n"
            f"• **GSTIN:** 33AAAAA0000A1Z5\n"
            f"• **Working Hours:** Monday to Saturday, 9:00 AM – 7:00 PM IST\n"
            f"• **Registered Office:** 402 Tech Boulevard, Indiranagar, Bengaluru, KA - 560038\n"
            f"• **Support WhatsApp / Phone:** +91 98765 00000\n"
            f"• **Support Email:** support@chatbiz.in\n"
            f"• **Services:** B2B Invoicing, UPI Payment Integration, Automated Reminders & MSME Ledger Management."
        )
        metadata = {
            "type": "business_info",
            "gstin": "33AAAAA0000A1Z5",
            "hours": "Mon-Sat 9AM - 7PM IST"
        }

    # ---------------------------------------------------------------------
    # Intent F: Greetings & Pleasantries
    # ---------------------------------------------------------------------
    elif any(t.startswith(w) for w in ["hi", "hello", "hey", "namaste", "good morning", "good afternoon", "good evening", "thanks", "thank you", "help"]):
        greeting_word = "Hello"
        if "morning" in t: greeting_word = "Good morning"
        elif "afternoon" in t: greeting_word = "Good afternoon"
        elif "evening" in t: greeting_word = "Good evening"
        
        balance_summary = f"Your current balance is **{format_inr(pending_balance)}**." if pending_balance > 0 else "Your account balance is fully settled."
        
        reply = (
            f"{greeting_word}, {first_name}! 👋 Welcome to the ChatBiz Automated WhatsApp Business Assistant.\n\n"
            f"{balance_summary}\n\n"
            f"How can I help you today? You can ask me:\n"
            f"• *'What is my outstanding balance?'*\n"
            f"• *'Send my latest invoice PDF'*\n"
            f"• *'How do I pay via UPI?'*\n"
            f"• *'Check my payment history'*\n"
            f"• *'What are your business hours?'*"
        )
        metadata = {
            "type": "greeting",
            "pending_balance": pending_balance
        }

    # ---------------------------------------------------------------------
    # Fallback / General Query
    # ---------------------------------------------------------------------
    else:
        reply = (
            f"Thank you for your message, {first_name}! I am the automated WhatsApp assistant for ChatBiz.\n\n"
            f"Regarding your account: Your pending balance is **{format_inr(pending_balance)}**.\n\n"
            f"Feel free to ask for your **invoice PDF**, **UPI payment details**, **payment history**, or **business operating hours**. If you require human assistance, our executive team is reachable at +91 98765 00000."
        )
        metadata = {
            "type": "general_fallback",
            "pending_balance": pending_balance
        }

    # Save assistant's reply into database
    save_chat_message(
        conn=conn,
        session_id=session_id,
        role="assistant",
        sender="ChatBiz AI (WhatsApp Business)",
        content=reply,
        client_id=client_id,
        metadata=metadata
    )
    
    return {
        "reply": reply,
        "metadata": metadata,
        "client": {
            "id": client_dict["id"],
            "name": client_dict["name"],
            "pending_balance": pending_balance,
            "invoices_count": len(invoices_list)
        }
    }


# =========================================================================
# 2. MANAGER-SIDE WHATSAPP OPERATIONS ASSISTANT
# =========================================================================
def handle_manager_message(message: str, conn) -> Dict[str, Any]:
    """
    Manager WhatsApp AI Assistant capable of executing ALL NLP command functionalities:
    1. Fetching and providing a particular user's or client's complete info and ledger.
    2. Creating invoices with PDF generation and reminder queueing.
    3. Recording payments & settling invoices.
    4. Adding, updating, deleting, and listing clients.
    5. Executive business analytics, revenue, and collection rates.
    6. Listing overdue and pending invoices.
    7. Triggering and dispatching reminders.
    """
    clean_msg = message.strip()
    t = clean_msg.lower()
    session_id = "manager"
    
    # Save manager's incoming command
    save_chat_message(
        conn=conn,
        session_id=session_id,
        role="user",
        sender="Manager",
        content=clean_msg,
        client_id=None
    )
    
    reply = ""
    action_taken = None
    data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    # ---------------------------------------------------------------------
    # 1. FETCH & PROVIDE A PARTICULAR USER'S OR CLIENT'S INFO
    # E.g.: "show details for client Rajesh Patel", "who is client Rohit",
    # "fetch info for client 3", "client info Anita", "find client Ramesh",
    # "user info +91 98765 43210", "fetch user details"
    # ---------------------------------------------------------------------
    user_lookup_match = re.search(
        r'(?:fetch|show|get|find|view|lookup|details|profile|info|who\s+is)\s+(?:for\s+|of\s+|about\s+)?(?:user|owner)\s+(.+)$',
        clean_msg, re.I
    )
    is_lookup_query = (
        any(w in t for w in ["who is", "profile", "details", "dossier", "info", "find client", "get client", "fetch client", "show client", "client info", "user info"]) or
        re.search(r'\b(?:show|get|fetch|view|lookup|details|profile|info|who\s+is)\b.*\b(?:client|customer|user)\b', t) is not None
    )

    # Specific check for registered business users
    if user_lookup_match and "client" not in t:
        target = user_lookup_match.group(1).strip()
        user_row = conn.execute("""
            SELECT * FROM users WHERE phone_whatsapp LIKE ? OR name LIKE ? OR user_id=?
        """, (f"%{target}%", f"%{target}%", int(target) if target.isdigit() else -1)).fetchone()
        
        if user_row:
            u = dict(user_row)
            reply = (
                f"👤 **Registered Business User Dossier**\n\n"
                f"• **User ID:** #{u['user_id']}\n"
                f"• **Owner Name:** {u['name']}\n"
                f"• **WhatsApp:** {u['phone_whatsapp']}\n"
                f"• **Business Name:** {u.get('business_name') or 'N/A'}\n"
                f"• **GST Number:** {u.get('gst_number') or 'Unregistered'}\n"
                f"• **Plan:** {u.get('subscription_plan', 'free').capitalize()}\n"
                f"• **Registered On:** {u['created_at']}"
            )
            action_taken = f"Retrieved user profile for {u['name']}"
            metadata = {"type": "user_profile", "user": u}
        else:
            reply = f"🔍 No registered user found matching *'{target}'*."
            metadata = {"type": "not_found"}

    # Client Profile Lookup
    elif is_lookup_query and not any(w in t for w in ["create", "add", "bill", "invoice", "payment", "record", "delete", "update", "revenue", "analytics"]):
        all_clients = conn.execute("SELECT * FROM clients").fetchall()
        client_row = None

        # Direct containment check against registered client names
        for cl in all_clients:
            cl_clean = re.sub(r'\(.*?\)', '', cl["name"]).strip().lower()
            if cl_clean and (cl_clean in t or cl["name"].lower() in t):
                client_row = cl
                break

        # Check by numeric ID
        if not client_row:
            id_match = re.search(r'\b(?:id|client|#)\s*(\d+)\b', t)
            if id_match:
                client_row = conn.execute("SELECT * FROM clients WHERE id=?", (int(id_match.group(1)),)).fetchone()

        # Clean candidate text check
        cand = clean_msg
        cand = re.sub(r'^(?:fetch|show|get|find|view|lookup|who\s+is|display)?\s*', '', cand, flags=re.I)
        cand = re.sub(r'^(?:details|profile|info|dossier)?\s*', '', cand, flags=re.I)
        cand = re.sub(r'^(?:for|of|about)?\s*', '', cand, flags=re.I)
        cand = re.sub(r'^(?:client|customer|user)?\s*', '', cand, flags=re.I)
        cand = cand.strip(' ?.,')
        target = cand if cand else clean_msg

        if not client_row and cand:
            tokens = [tk.lower() for tk in re.split(r'\s+', cand) if len(tk) >= 3]
            for cl in all_clients:
                cl_clean = re.sub(r'\(.*?\)', '', cl["name"]).strip().lower()
                cl_words = [w.lower() for w in re.split(r'\s+', cl_clean) if len(w) >= 3]
                if any(tk in cl_words for tk in tokens):
                    client_row = cl
                    break

        if not client_row and cand:
            best_score = 0.0
            best_match = None
            for cl in all_clients:
                ratio = difflib.SequenceMatcher(None, cand.lower(), cl["name"].lower()).ratio()
                if ratio > best_score:
                    best_score = ratio
                    best_match = cl
            if best_score >= 0.40:
                client_row = best_match

        if client_row:
            c = dict(client_row)
            # Fetch invoices for this client
            client_invs = conn.execute("""
                SELECT * FROM invoices WHERE client_id=? ORDER BY id DESC
            """, (c["id"],)).fetchall()
            inv_list = [dict(i) for i in client_invs]
            
            tot_invoiced = sum(i["amount"] for i in inv_list)
            tot_paid = sum(i["amount"] for i in inv_list if i["status"] == "Paid")
            tot_pending = sum(i["amount"] for i in inv_list if i["status"] != "Paid")
            overdue_cnt = sum(1 for i in inv_list if i["status"] == "Overdue")
            
            inv_bullets = []
            for i in inv_list[:5]:
                status_emoji = "🟢" if i["status"] == "Paid" else ("🔴" if i["status"] == "Overdue" else "🟡")
                inv_bullets.append(f"  {status_emoji} **#INV-{i['id']:04d}**: {format_inr(i['amount'])} ({i['description']}) — {i['status']} (Due: {i['due_date']})")
            
            inv_summary_text = "\n".join(inv_bullets) if inv_bullets else "  *No invoices issued yet.*"
            
            reply = (
                f"👤 **Executive Client Dossier: {c['name']}**\n\n"
                f"• **Client ID:** #{c['id']}\n"
                f"• **Phone:** {c.get('phone') or 'Not provided'}\n"
                f"• **Email:** {c.get('email') or 'Not provided'}\n"
                f"• **Address:** {c.get('address') or 'On File'}\n"
                f"• **Notes:** {c.get('notes') or 'Active Account'}\n"
                f"• **Member Since:** {c['created_at']}\n\n"
                f"📊 **Financial Ledger Summary:**\n"
                f"• Total Invoiced: **{format_inr(tot_invoiced)}** ({len(inv_list)} invoices)\n"
                f"• Total Collected: **{format_inr(tot_paid)}**\n"
                f"• Outstanding Balance: **{format_inr(tot_pending)}**\n"
                f"• Overdue Invoices: **{overdue_cnt}**\n\n"
                f"📄 **Recent Invoices:**\n"
                f"{inv_summary_text}"
            )
            action_taken = f"Fetched client details for {c['name']} (ID #{c['id']})"
            metadata = {
                "type": "client_dossier",
                "client": c,
                "total_invoiced": tot_invoiced,
                "pending_balance": tot_pending,
                "invoices": inv_list[:5]
            }
        else:
            reply = (
                f"🔍 Could not find any client matching *'{target}'*.\n\n"
                f"💡 Try typing `list clients` to view all registered clients, or `add client {target}, +91 98000 00000, email@example.com` to register them."
            )
            metadata = {"type": "client_not_found"}

    # ---------------------------------------------------------------------
    # 2. CREATE INVOICE
    # E.g.: "create invoice for Rajesh 5000 due 2026-11-01 for Web Design"
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["create invoice", "make invoice", "generate invoice", "new invoice", "bill client"]) or (
        "invoice" in t and any(w in t for w in ["create", "generate", "bill", "issue"])
    ):
        # Extract amount
        amount_match = re.search(r'(?:rs\.?|inr|₹|\bamount\b)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k|thousand|lakh)?', clean_msg, re.I)
        amount = 5000.0
        cleaned_str = re.sub(r'(\d+),(\d+)', r'\1\2', clean_msg)
        
        m_k = re.search(r'(\d+(?:\.\d+)?)\s*(?:k|thousand)\b', cleaned_str, re.I)
        if m_k:
            amount = float(m_k.group(1)) * 1000
        else:
            nums = re.findall(r'\b\d+(?:\.\d{1,2})?\b', cleaned_str)
            for n in nums:
                val = float(n)
                if val >= 50:
                    amount = val
                    break

        # Extract due date
        date_match = re.search(r'\b(20\d{2}-\d{2}-\d{2})\b', clean_msg)
        due_date = date_match.group(1) if date_match else str(date.today())

        # Match client
        all_clients = conn.execute("SELECT id, name FROM clients").fetchall()
        matched_client = None
        for cl in all_clients:
            if cl["name"].lower() in t:
                matched_client = dict(cl)
                break
        
        if not matched_client:
            # Fuzzy match
            cand = re.search(r'(?:for|to|bill)\s+([A-Za-z\s\.\']+?)(?:\s+(?:of|for|amount|\d+|rupees|rs|due)\b|$)', clean_msg, re.I)
            if cand:
                cand_name = cand.group(1).strip()
                for cl in all_clients:
                    ratio = difflib.SequenceMatcher(None, cand_name.lower(), cl["name"].lower()).ratio()
                    if ratio >= 0.65:
                        matched_client = dict(cl)
                        break

        if not matched_client and all_clients:
            matched_client = dict(all_clients[0])

        if matched_client:
            # Extract description
            desc = "Professional Business Services"
            desc_match = re.search(r'(?:for|towards|desc(?:ription)?)\s+([A-Za-z\s]+?)(?:\s+(?:due|amount|\d+)|$)', clean_msg, re.I)
            if desc_match and len(desc_match.group(1).strip()) > 3:
                cand_desc = desc_match.group(1).strip()
                if cand_desc.lower() != matched_client["name"].lower():
                    desc = cand_desc.capitalize()

            # Insert invoice
            cur = conn.execute("""
                INSERT INTO invoices (client_id, description, amount, due_date, upi_id, status)
                VALUES (?, ?, ?, ?, 'chatbiz.merchant@upi', 'Pending')
            """, (matched_client["id"], desc, amount, due_date))
            new_inv_id = cur.lastrowid
            conn.commit()

            # Generate PDF
            inv_dict = {
                "id": new_inv_id,
                "client_id": matched_client["id"],
                "client_name": matched_client["name"],
                "description": desc,
                "amount": amount,
                "due_date": due_date,
                "upi_id": "chatbiz.merchant@upi",
                "status": "Pending"
            }
            try:
                pdf_path = generate_invoice_pdf(inv_dict)
                conn.execute("UPDATE invoices SET pdf_path=? WHERE id=?", (str(pdf_path), new_inv_id))
                conn.commit()
            except Exception:
                pass

            # Seed reminders
            seed_invoice_reminders(new_inv_id, due_date)

            reply = (
                f"✅ **Invoice Created Successfully**\n\n"
                f"• **Invoice Number:** #INV-{new_inv_id:04d}\n"
                f"• **Client:** {matched_client['name']}\n"
                f"• **Description:** {desc}\n"
                f"• **Amount:** {format_inr(amount)}\n"
                f"• **Due Date:** {due_date}\n"
                f"• **Status:** Pending\n"
                f"• **UPI QR Code:** Generated & embedded in PDF\n"
                f"• **Automated Reminders:** Scheduled in queue\n\n"
                f"📄 Official invoice PDF is ready for immediate distribution."
            )
            action_taken = f"Created Invoice #INV-{new_inv_id:04d} for {matched_client['name']} ({format_inr(amount)})"
            metadata = {
                "type": "invoice_created",
                "invoice_id": new_inv_id,
                "download_url": f"/api/invoices/{new_inv_id}/pdf",
                "amount": amount
            }
        else:
            reply = "⚠️ Please specify a valid client name to create an invoice for."
            metadata = {"type": "error"}

    # ---------------------------------------------------------------------
    # 3. RECORD PAYMENT / SETTLE INVOICE
    # E.g.: "record payment 5000 from Rajesh via UPI", "mark invoice 3 as paid"
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["record payment", "mark paid", "mark as paid", "payment received", "settle invoice"]):
        # Find invoice ID if mentioned
        inv_match = re.search(r'(?:invoice|inv-?|#)\s*(\d+)', t)
        target_inv = None
        if inv_match:
            inv_id = int(inv_match.group(1))
            target_inv = conn.execute("SELECT i.*, c.name AS client_name FROM invoices i JOIN clients c ON i.client_id=c.id WHERE i.id=?", (inv_id,)).fetchone()
        
        if not target_inv:
            # Match by client
            all_clients = conn.execute("SELECT id, name FROM clients").fetchall()
            matched_cl = None
            for cl in all_clients:
                if cl["name"].lower() in t:
                    matched_cl = cl
                    break
            if matched_cl:
                target_inv = conn.execute("""
                    SELECT i.*, c.name AS client_name FROM invoices i JOIN clients c ON i.client_id=c.id
                    WHERE i.client_id=? AND i.status!='Paid' ORDER BY i.id DESC LIMIT 1
                """, (matched_cl["id"],)).fetchone()

        if target_inv:
            inv_row = dict(target_inv)
            conn.execute("UPDATE invoices SET status='Paid' WHERE id=?", (inv_row["id"],))
            tx_id = f"MGR/{datetime.now().strftime('%Y%m%d%H%M%S')}/{inv_row['id']}"
            conn.execute("""
                INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
                VALUES (?, ?, ?, ?, 'manager_chat', ?)
            """, (inv_row["id"], inv_row["amount"], tx_id, str(date.today()), f"Manager WhatsApp Chat: {clean_msg}"))
            conn.commit()

            reply = (
                f"✅ **Payment Settlement Recorded**\n\n"
                f"• **Invoice:** #INV-{inv_row['id']:04d}\n"
                f"• **Client:** {inv_row['client_name']}\n"
                f"• **Amount Settled:** {format_inr(inv_row['amount'])}\n"
                f"• **Transaction Reference:** `{tx_id}`\n"
                f"• **Status:** Updated to **Paid**\n\n"
                f"All overdue reminders for this invoice have been automatically cleared."
            )
            action_taken = f"Recorded payment settlement of {format_inr(inv_row['amount'])} for Invoice #INV-{inv_row['id']:04d}"
            metadata = {
                "type": "payment_recorded",
                "invoice_id": inv_row["id"],
                "amount": inv_row["amount"]
            }
        else:
            reply = "⚠️ Could not identify the target unpaid invoice. Please mention the invoice number (e.g. `mark invoice 4 as paid`)."
            metadata = {"type": "error"}

    # ---------------------------------------------------------------------
    # 4. ADD / UPDATE / DELETE / LIST CLIENTS (NLP Command Parser)
    # ---------------------------------------------------------------------
    elif any(t.startswith(w) or f" {w} " in f" {t} " for w in ["add client", "update client", "delete client", "list clients", "show clients"]):
        parsed = parse_command(clean_msg)
        
        if parsed.name == "ADD_CLIENT":
            c_name = parsed.name_arg
            c_phone = parsed.phone or "+91 98000 00000"
            c_email = parsed.email or f"{re.sub(r'[^a-z0-9]', '', c_name.lower())}@example.com"
            try:
                cur = conn.execute(
                    "INSERT INTO clients (name, phone, email, notes) VALUES (?, ?, ?, 'Registered via WhatsApp Manager')",
                    (c_name, c_phone, c_email)
                )
                conn.commit()
                reply = (
                    f"✅ **Client Added Successfully**\n\n"
                    f"• **Client ID:** #{cur.lastrowid}\n"
                    f"• **Name:** {c_name}\n"
                    f"• **Phone:** {c_phone}\n"
                    f"• **Email:** {c_email}"
                )
                action_taken = f"Added new client: {c_name}"
                metadata = {"type": "client_added", "client_id": cur.lastrowid}
            except Exception as e:
                reply = f"⚠️ Could not add client: {e}"
                metadata = {"type": "error"}

        elif parsed.name == "LIST_CLIENTS":
            clients_all = conn.execute("""
                SELECT c.id, c.name, c.phone, COALESCE(SUM(i.amount), 0) AS total_invoiced,
                       COALESCE(SUM(CASE WHEN i.status!='Paid' THEN i.amount ELSE 0 END), 0) AS pending_amount
                FROM clients c
                LEFT JOIN invoices i ON c.id = i.client_id
                GROUP BY c.id
                ORDER BY c.name ASC
            """).fetchall()
            
            cl_bullets = []
            for cl in clients_all:
                cl_bullets.append(f"• **#{cl['id']} {cl['name']}** ({cl['phone'] or 'No phone'}) — Pending: {format_inr(cl['pending_amount'])}")
            
            reply = (
                f"👥 **Registered Clients Directory ({len(clients_all)} Total)**\n\n"
                + "\n".join(cl_bullets)
            )
            action_taken = f"Listed {len(clients_all)} registered clients"
            metadata = {"type": "clients_list", "count": len(clients_all)}

        elif parsed.name == "UPDATE_CLIENT":
            cl = conn.execute("SELECT * FROM clients WHERE LOWER(name)=LOWER(?)", (parsed.name_arg,)).fetchone()
            if cl:
                col = "phone" if parsed.field == "phone" else "email"
                conn.execute(f"UPDATE clients SET {col}=? WHERE id=?", (parsed.value, cl["id"]))
                conn.commit()
                reply = f"✅ Updated {parsed.field} for client **{cl['name']}** to `{parsed.value}`."
                action_taken = f"Updated client {cl['name']}"
                metadata = {"type": "client_updated"}
            else:
                reply = f"🔍 Client '{parsed.name_arg}' not found."
                metadata = {"type": "not_found"}

        elif parsed.name == "DELETE_CLIENT":
            cl = conn.execute("SELECT * FROM clients WHERE LOWER(name)=LOWER(?)", (parsed.name_arg,)).fetchone()
            if cl:
                conn.execute("DELETE FROM clients WHERE id=?", (cl["id"],))
                conn.commit()
                reply = f"🗑️ Client **{cl['name']}** and associated records have been removed."
                action_taken = f"Deleted client {cl['name']}"
                metadata = {"type": "client_deleted"}
            else:
                reply = f"🔍 Client '{parsed.name_arg}' not found."
                metadata = {"type": "not_found"}

    # ---------------------------------------------------------------------
    # 5. BUSINESS ANALYTICS & FINANCIAL KPIS
    # E.g.: "what is our total revenue", "show analytics", "collection rate"
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["revenue", "sales", "analytics", "kpi", "collection rate", "financial status", "summary", "how much revenue", "total collected"]):
        s = summary()
        rate = s.get("collection_rate_pct", 0.0)
        
        reply = (
            f"📊 **Executive Financial & Operational Summary**\n\n"
            f"• **Total Invoiced:** {format_inr(s['total_invoiced'])} ({s.get('invoice_count', 0)} invoices)\n"
            f"• **Total Collected:** {format_inr(s['paid_amount'])} ({s.get('paid_count', 0)} paid)\n"
            f"• **Pending Receivables:** {format_inr(s['pending_amount'])} ({s.get('pending_count', 0)} awaiting)\n"
            f"• **Overdue Amount:** {format_inr(s['overdue_amount'])} ({s.get('overdue_count', 0)} overdue)\n"
            f"• **Collection Efficiency Rate:** {rate:.1f}%\n\n"
            f"💡 Type `list overdue` to see which clients have overdue invoices."
        )
        action_taken = "Generated live executive business analytics"
        metadata = {"type": "analytics_summary", "summary": s}

    # ---------------------------------------------------------------------
    # 6. LIST OVERDUE / PENDING INVOICES
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["overdue", "pending invoices", "unpaid invoices", "who owes", "defaulters"]):
        overdues = conn.execute("""
            SELECT i.id, i.description, i.amount, i.due_date, c.name AS client_name, c.phone AS client_phone
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.status = 'Overdue'
            ORDER BY i.amount DESC
        """).fetchall()
        
        if overdues:
            lines = []
            for o in overdues:
                lines.append(f"• **#INV-{o['id']:04d}** ({o['client_name']}): {format_inr(o['amount'])} — Due: {o['due_date']} (📞 {o['client_phone'] or 'No phone'})")
            
            tot_overdue = sum(o["amount"] for o in overdues)
            reply = (
                f"⚠️ **Overdue Invoices Ledger ({len(overdues)} Total — {format_inr(tot_overdue)})**\n\n"
                + "\n".join(lines) +
                f"\n\n💡 You can say `send reminder for invoice <id>` to trigger an automated WhatsApp notification."
            )
            action_taken = f"Listed {len(overdues)} overdue invoices"
            metadata = {"type": "overdue_list", "count": len(overdues)}
        else:
            reply = "🌟 Great news! There are currently **no overdue invoices** across any client accounts."
            metadata = {"type": "no_overdue"}

    # ---------------------------------------------------------------------
    # 7. SEND REMINDERS / DISPATCH
    # ---------------------------------------------------------------------
    elif any(k in t for k in ["send reminder", "run reminders", "trigger reminder", "dispatch reminder"]):
        # Single invoice reminder
        inv_match = re.search(r'(?:invoice|inv-?|#)\s*(\d+)', t)
        if inv_match:
            inv_id = int(inv_match.group(1))
            rem = conn.execute("SELECT r.*, c.name AS client_name, c.phone AS client_phone FROM reminders r JOIN invoices i ON r.invoice_id=i.id JOIN clients c ON i.client_id=c.id WHERE r.invoice_id=? ORDER BY r.id DESC LIMIT 1", (inv_id,)).fetchone()
            if rem:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("UPDATE reminders SET status='SENT', sent_at=? WHERE id=?", (now_str, rem["id"]))
                conn.commit()
                reply = f"📨 WhatsApp payment reminder for **Invoice #{inv_id}** delivered to **{rem['client_name']}** ({rem['client_phone']})."
                action_taken = f"Dispatched reminder for Invoice #{inv_id}"
                metadata = {"type": "reminder_sent", "invoice_id": inv_id}
            else:
                reply = f"⚠️ No reminder record found for Invoice #{inv_id}."
                metadata = {"type": "error"}
        else:
            dispatched = run_due_reminders()
            reply = f"📨 Triggered batch reminder run. Dispatched **{len(dispatched)}** due WhatsApp reminder(s)."
            action_taken = f"Executed batch reminders: {len(dispatched)} sent"
            metadata = {"type": "batch_reminders", "sent_count": len(dispatched)}

    # ---------------------------------------------------------------------
    # 8. HELP & AVAILABLE OPERATIONS
    # ---------------------------------------------------------------------
    elif any(w in t for w in ["help", "commands", "what can you do", "options"]):
        reply = (
            f"🛠️ **ChatBiz Manager WhatsApp AI — Available Operations**\n\n"
            f"1. **Client Dossier / Profile:**\n"
            f"   • *'Show details for client Rajesh Patel'*\n"
            f"   • *'Who is client Rohit?'*\n"
            f"   • *'Get info for client 3'*\n\n"
            f"2. **Invoice Operations:**\n"
            f"   • *'Create invoice for Rajesh 4500 due 2026-11-20 for Web Dev'*\n"
            f"   • *'List overdue invoices'*\n\n"
            f"3. **Payment Settlements:**\n"
            f"   • *'Record payment 4500 from Rajesh via UPI'*\n"
            f"   • *'Mark invoice 4 as paid'*\n\n"
            f"4. **Client Management:**\n"
            f"   • *'Add client Anita Rao, 9876543210, anita@tech.com'*\n"
            f"   • *'List all clients'*\n"
            f"   • *'Update client Anita phone 9999988888'*\n\n"
            f"5. **Business Analytics:**\n"
            f"   • *'What is our total revenue?'*\n"
            f"   • *'Show collection rate and summary'*\n\n"
            f"6. **Reminders:**\n"
            f"   • *'Send reminder for invoice 2'*\n"
            f"   • *'Run all due reminders'*"
        )
        metadata = {"type": "help"}

    # ---------------------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------------------
    else:
        reply = (
            f"Understood, Manager. Command received: *'{clean_msg}'*.\n\n"
            f"You can ask me to **fetch a client's profile** (e.g. *'Show details for client Rohit'*), **issue an invoice**, **record a payment**, **view business revenue**, or **list overdue bills**.\n\n"
            f"Type `help` anytime to view all automated operations."
        )
        metadata = {"type": "manager_fallback"}

    # Save assistant's reply
    save_chat_message(
        conn=conn,
        session_id=session_id,
        role="assistant",
        sender="ChatBiz Operations AI",
        content=reply,
        client_id=None,
        metadata=metadata
    )
    
    return {
        "reply": reply,
        "action_taken": action_taken,
        "metadata": metadata
    }
