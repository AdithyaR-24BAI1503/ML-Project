"""
ChatBiz Invoice PDF Generator
Generates clean, professional PDF invoices with embedded UPI payment QR codes using ReportLab and QRCode.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import qrcode

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated_invoices"
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_invoice_pdf(invoice: dict) -> Path:
    """
    Generates a PDF invoice file with embedded UPI QR code.
    Returns the Path to the generated PDF.
    """
    invoice_id = invoice["id"]
    pdf_path = OUTPUT_DIR / f"invoice_{invoice_id}.pdf"
    qr_path = OUTPUT_DIR / f"upi_qr_{invoice_id}.png"

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    # Header section
    c.setFont("Helvetica-Bold", 22)
    c.drawString(25 * mm, height - 30 * mm, "ChatBiz")
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, height - 37 * mm, "AI-Powered MSME Business Management")

    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(width - 25 * mm, height - 30 * mm, f"INVOICE #{invoice_id:04d}")

    # Bill To section
    y = height - 58 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "Bill To:")
    c.setFont("Helvetica", 10)
    client_name = invoice.get("client_name") or "Valued Client"
    c.drawString(25 * mm, y - 6 * mm, str(client_name))
    if invoice.get("client_phone"):
        c.drawString(25 * mm, y - 12 * mm, str(invoice["client_phone"]))
    if invoice.get("client_email"):
        c.drawString(25 * mm, y - 18 * mm, str(invoice["client_email"]))

    # Invoice metadata (right column)
    c.drawString(width - 80 * mm, y - 6 * mm, f"Due Date: {invoice.get('due_date', 'N/A')}")
    c.drawString(width - 80 * mm, y - 12 * mm, f"Status: {invoice.get('status', 'Pending')}")
    if invoice.get("recurring"):
        c.drawString(width - 80 * mm, y - 18 * mm, f"Cycle: {invoice.get('recurrence', 'MONTHLY')}")

    # Table Header
    y -= 38 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "Description")
    c.drawRightString(width - 25 * mm, y, "Amount (INR)")
    c.setLineWidth(0.8)
    c.line(25 * mm, y - 3 * mm, width - 25 * mm, y - 3 * mm)

    # Line item row
    y -= 12 * mm
    c.setFont("Helvetica", 10)
    description = invoice.get("description", "Professional Services")
    amount = float(invoice.get("amount", 0.0))
    c.drawString(25 * mm, y, description[:65])
    c.drawRightString(width - 25 * mm, y, f"Rs. {amount:,.2f}")

    # Divider & Total
    y -= 18 * mm
    c.setLineWidth(0.5)
    c.line(25 * mm, y + 6 * mm, width - 25 * mm, y + 6 * mm)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "TOTAL DUE")
    c.drawRightString(width - 25 * mm, y, f"Rs. {amount:,.2f}")

    # UPI QR Code Section
    upi_id = invoice.get("upi_id") or "chatbiz.merchant@upi"
    try:
        upi_uri = f"upi://pay?pa={upi_id}&pn=ChatBiz&am={amount:.2f}&cu=INR"
        qr_img = qrcode.make(upi_uri)
        qr_img.save(str(qr_path))
        c.drawImage(str(qr_path), 25 * mm, 32 * mm, width=32 * mm, height=32 * mm)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(62 * mm, 50 * mm, "Scan & Pay instantly using any UPI App (GPay / PhonePe / Paytm):")
        c.setFont("Helvetica", 9)
        c.drawString(62 * mm, 43 * mm, f"UPI ID: {upi_id}")
        c.drawString(62 * mm, 36 * mm, f"Amount: Rs. {amount:,.2f}")
    except Exception as e:
        c.setFont("Helvetica", 9)
        c.drawString(25 * mm, 40 * mm, f"UPI Payment Handle: {upi_id}")

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(25 * mm, 18 * mm, "Generated electronically by ChatBiz — WhatsApp-First MSME Operating System")
    c.save()

    # Cleanup temporary QR image
    try:
        qr_path.unlink(missing_ok=True)
    except Exception:
        pass

    return pdf_path
