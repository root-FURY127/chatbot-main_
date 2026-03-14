import re

# Comprehensive PII regex patterns for India
PII_PATTERNS = {
    "aadhaar": re.compile(r'^\d{4}\s?\d{4}\s?\d{4}$|^\d{12}$'),  # 12 digits, optional spaces
    "pan": re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'),  # e.g., ABCDE1234F
    "phone": re.compile(r'^(\+91|0)?[6-9]\d{9}$'),  # Indian mobile
    "email": re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$'),
    "passport": re.compile(r'^[A-Z][0-9]{7}$'),  # e.g., A1234567
    "driving_license": re.compile(r'^[A-Z]{2}[0-9]{2}[0-9]{11}$'),  # Simplified
    "account_number": re.compile(r'^\d{9,18}$'),  # Bank account number
    "credit_card": re.compile(r'^\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}$'),
    "voter_id": re.compile(r'^[A-Z]{3}[0-9]{7}$'),  # e.g., ABC1234567
}