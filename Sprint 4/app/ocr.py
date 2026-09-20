import re
from PIL import Image
import pytesseract

def extract_payment_data(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    amount = None
    txid = None

    patterns = [
        r'(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.\d{1,2})?)',
        r'(?:amount|paid|sent)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.\d{1,2})?)'
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            amount = float(m.group(1).replace(",", ""))
            break

    m = re.search(r'(?:transaction\s*id|txn\s*id|utr)\s*[:#\-]?\s*([A-Z0-9\-]{6,})', text, re.I)
    if m:
        txid = m.group(1)

    return {"raw_text": text, "amount": amount, "transaction_id": txid}
