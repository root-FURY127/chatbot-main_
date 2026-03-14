import re
from utils.constants import PII_PATTERNS

class PIIDetectionService:
    def __init__(self):
        self.patterns = PII_PATTERNS

    def detect_type(self, value: str) -> str:
        """Detect PII type based on regex patterns"""
        value = value.strip()
        for pii_type, pattern in self.patterns.items():
            if pattern.fullmatch(value):
                return pii_type
        return "unknown"

    def extract_all(self, text: str) -> list:
        """Extract all PII values from text (for file scanning)"""
        found = []
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                found.append({"value": match, "type": pii_type})
        return found