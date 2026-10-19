"""
ChatBiz Voice Assistant Pipeline
Transcribes input commands and classifies MSME voice intents.
"""
def transcribe_demo(text: str) -> str:
    """Accepts spoken or typed voice transcript."""
    return text.strip()

def classify_voice_command(transcript: str) -> str:
    """Classifies spoken transcript into actionable MSME operational intents."""
    t = transcript.lower()
    if "invoice" in t and any(x in t for x in ["create", "make", "generate", "bill", "issue", "send", "anupu"]):
        return "CREATE_INVOICE"
    if "payment" in t or any(x in t for x in ["paid", "settle", "received"]):
        return "RECORD_PAYMENT"
    if "reminder" in t or "remind" in t:
        return "SEND_REMINDER"
    if "client" in t or "customer" in t:
        return "CLIENT_OPERATION"
    if "overdue" in t or "pending" in t or "balance" in t:
        return "VIEW_PENDING"
    if "revenue" in t or "sales" in t or "analytics" in t:
        return "VIEW_ANALYTICS"
    return "GENERAL_QUERY"
