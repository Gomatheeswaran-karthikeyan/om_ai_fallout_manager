from __future__ import annotations
import re
from typing import Optional, Any, Dict, List

# Fields that should have PII masking applied
MASKED_KEYS = {"notes", "work_notes", "description", "short_description"}

# ── Masking rules: (pattern, replacement) ─────────────────────────────────────

_RULES: list[tuple[re.Pattern, str]] = [
    # Email addresses
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE), "[EMAIL]"),

    # US phone numbers (various formats)
    (re.compile(r"\b(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"), "[PHONE]"),

    # Social Security Numbers
    (re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"), "[SSN]"),

    # Credit / debit card numbers (13-19 digits, optionally grouped)
    (re.compile(r"\b(?:\d[ \-]?){13,19}\b"), "[CARD]"),

    # IPv6 addresses (full and compressed forms)
    (re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
                r"|(?:[0-9a-fA-F]{1,4}:){1,7}:"
                r"|:(?::[0-9a-fA-F]{1,4}){1,7}"
                r"|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}"
                r"|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}"
                r"|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}"
                r"|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}"
                r"|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}"
                r"|[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}"
                r"|::(?:ffff(?::0{1,4})?:)?(?:\d{1,3}\.){3}\d{1,3}"
                r"|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:\d{1,3}\.){3}\d{1,3}",
                re.IGNORECASE), "[IPV6]"),

    # IPv4 addresses (after IPv6 so mixed IPv6/IPv4 is caught first)
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),

    # MAC addresses (xx:xx:xx:xx:xx:xx or xx-xx-xx-xx-xx-xx or xxxxxxxxxxxx)
    (re.compile(r"\b(?:[0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}\b"
                r"|\b[0-9a-fA-F]{12}\b", re.IGNORECASE), "[MAC]"),

    # Account numbers: digits-only blocks of 8-16 chars
    (re.compile(r"\b\d{8,16}\b"), "[ACCOUNT]"),

    # Full names: two or more capitalized words in a row
    (re.compile(r"\b([A-Z][a-z]+ ){1,2}[A-Z][a-z]+\b"), "[NAME]"),
]


def mask(text: Optional[str]) -> Optional[str]:
    """Apply all PII masking rules to a string. Returns None if input is None."""
    if not text:
        return text
    result = text
    for pattern, replacement in _RULES:
        result = pattern.sub(replacement, result)
    return result


def mask_if_sensitive(key: str, value: Optional[str]) -> Optional[str]:
    """Mask only if the field key is in MASKED_KEYS, otherwise return as-is."""
    if key in MASKED_KEYS:
        return mask(value)
    return value


SENSITIVE_KEYS = {
    "customername",
    "customeremail",
    "phonenumber",
    "account",
    "accountnum",
    "accountnumber",
    "street",
    "address",
}


def mask_value(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) <= 4:
            return "****"
        return value[:2] + "****" + value[-2:]
    return "****"


def mask_payload(data: Any) -> Any:
    """
    Recursively mask sensitive fields in dict/list payloads.
    """
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()

            if key_lower in SENSITIVE_KEYS:
                masked[key] = mask_value(value)
            else:
                masked[key] = mask_payload(value)

        return masked

    elif isinstance(data, list):
        return [mask_payload(item) for item in data]

    return data