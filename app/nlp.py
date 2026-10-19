"""
ChatBiz Natural Language Command Parser
Translates freeform WhatsApp / chat messages into structured business intents.
"""
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Intent:
    name: str
    name_arg: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    field: Optional[str] = None
    value: Optional[str] = None

def parse_command(text: str) -> Intent:
    """
    Parses conversational commands like:
    - 'add client Rahul, 9876543210, rahul@gmail.com'
    - 'list clients'
    - 'update client Rahul phone 9999999999'
    - 'delete client Rahul'
    """
    original = text.strip()
    t = original.lower()

    m = re.match(
        r"add\s+client\s+([^,]+)(?:,\s*([+\d][\d\s-]{7,}))?(?:,\s*([^,\s]+@[^,\s]+))?$",
        original, re.I
    )
    if m:
        return Intent("ADD_CLIENT", m.group(1).strip(),
                      (m.group(2) or "").strip() or None,
                      (m.group(3) or "").strip() or None)

    if re.search(r"\b(list|show)\b.*\bclients?\b", t) or t in {"clients", "client list"}:
        return Intent("LIST_CLIENTS")

    m = re.match(r"(?:find|show|get)\s+client\s+(.+)$", original, re.I)
    if m:
        return Intent("FIND_CLIENT", m.group(1).strip())

    m = re.match(r"update\s+client\s+(.+?)\s+(phone|email)\s+(.+)$", original, re.I)
    if m:
        return Intent("UPDATE_CLIENT", m.group(1).strip(),
                      field=m.group(2).lower(), value=m.group(3).strip())

    m = re.match(r"(?:delete|remove)\s+client\s+(.+)$", original, re.I)
    if m:
        return Intent("DELETE_CLIENT", m.group(1).strip())

    return Intent("UNKNOWN")
