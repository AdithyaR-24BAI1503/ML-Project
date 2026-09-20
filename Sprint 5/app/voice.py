import re

def transcribe_demo(text):
    # Demo fallback: accepts an already-transcribed voice command.
    return text.strip()

def classify_voice_command(transcript):
    t = transcript.lower()
    if "invoice" in t and any(x in t for x in ["create", "make", "generate", "anupu", "send"]):
        return "CREATE_INVOICE"
    if "payment" in t or "paid" in t:
        return "CHECK_PAYMENT"
    if "client" in t:
        return "CLIENT_OPERATION"
    return "UNKNOWN"
