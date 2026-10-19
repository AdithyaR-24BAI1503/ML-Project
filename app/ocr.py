"""
ChatBiz Payment Receipt & Screenshot OCR Processor
Extracts transaction IDs and monetary payment amounts from uploaded screenshot images.
"""
import re
from PIL import Image

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

def extract_payment_data(image_path) -> dict:
    """
    Extracts payment amount, transaction reference, and raw text from an image.
    Handles OCR engine errors gracefully.
    """
    text = ""
    if HAS_PYTESSERACT:
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
        except Exception as e:
            text = f"OCR Error: {e}"

    amount = None
    txid = None

    patterns = [
        r'(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.\d{1,2})?)',
        r'(?:amount|paid|sent|total)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.\d{1,2})?)',
        r'\b(?:paid|transferred)\s+([0-9,]+(?:\.\d{1,2})?)'
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            try:
                amount = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                pass

    m_tx = re.search(r'(?:transaction\s*id|txn\s*id|utr|reference\s*no|ref\s*no)\s*[:#\-]?\s*([A-Z0-9\-]{6,})', text, re.I)
    if m_tx:
        txid = m_tx.group(1)

    return {
        "raw_text": text,
        "amount": amount,
        "transaction_id": txid
    }
