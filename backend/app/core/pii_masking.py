"""
PII Masking Utilities

Sanitizes sensitive data for logging and external exposure.
Critical for BFSI compliance with data protection regulations.
"""

import re
from typing import Any, Dict


class PIIMasker:
    """
    Utility class for masking Personally Identifiable Information (PII).
    
    Supports masking of:
    - PAN Card numbers
    - Aadhar numbers
    - Phone numbers
    - Email addresses
    - Credit card numbers
    - Bank account numbers
    
    Example:
        masker = PIIMasker()
        safe_log = masker.mask_dict({"pan": "ABCDE1234F", "phone": "9876543210"})
        # Result: {"pan": "XXXXXX34F", "phone": "XXXXXX3210"}
    """
    
    # Regex patterns for PII detection
    PATTERNS = {
        "pan": re.compile(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", re.IGNORECASE),
        "aadhar": re.compile(r"\d{4}[\s-]?\d{4}[\s-]?\d{4}"),
        "phone": re.compile(r"[6-9]\d{9}"),
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "credit_card": re.compile(r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"),
        "bank_account": re.compile(r"\d{9,18}"),
    }
    
    # Fields that should always be masked
    SENSITIVE_FIELDS = {
        "pan", "aadhar", "aadhar_number", "aadhaar", "phone", "mobile",
        "email", "password", "credit_card", "bank_account", "account_number",
        "cvv", "otp", "pin", "secret", "token", "api_key", "access_token",
        "refresh_token", "salary", "income"
    }
    
    @staticmethod
    def mask_pan(pan: str) -> str:
        """Mask PAN number, showing only last 4 characters."""
        if len(pan) == 10:
            return f"XXXXXX{pan[-4:]}"
        return "XXXXXXXXXX"
    
    @staticmethod
    def mask_aadhar(aadhar: str) -> str:
        """Mask Aadhar number completely."""
        return "XXXX-XXXX-XXXX"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number, showing only last 4 digits."""
        cleaned = re.sub(r"\D", "", phone)
        if len(cleaned) >= 10:
            return f"XXXXXX{cleaned[-4:]}"
        return "XXXXXXXXXX"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email, showing only domain and partial username."""
        if "@" in email:
            local, domain = email.split("@", 1)
            if len(local) > 2:
                masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
            else:
                masked_local = "*" * len(local)
            return f"{masked_local}@{domain}"
        return "***@***.***"
    
    @staticmethod
    def mask_credit_card(card: str) -> str:
        """Mask credit card, showing only last 4 digits."""
        cleaned = re.sub(r"\D", "", card)
        if len(cleaned) >= 16:
            return f"XXXX-XXXX-XXXX-{cleaned[-4:]}"
        return "XXXX-XXXX-XXXX-XXXX"
    
    @staticmethod
    def mask_generic(value: str, visible_chars: int = 4) -> str:
        """Generic masking function showing last N characters."""
        if len(value) > visible_chars:
            return "X" * (len(value) - visible_chars) + value[-visible_chars:]
        return "X" * len(value)
    
    def mask_string(self, text: str) -> str:
        """
        Scan a string and mask any detected PII patterns.
        
        Args:
            text: Input string to scan and mask.
        
        Returns:
            str: String with all detected PII masked.
        """
        result = text
        
        # Mask each pattern type
        for pattern_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(result)
            for match in matches:
                if pattern_type == "pan":
                    result = result.replace(match, self.mask_pan(match))
                elif pattern_type == "aadhar":
                    result = result.replace(match, self.mask_aadhar(match))
                elif pattern_type == "phone":
                    result = result.replace(match, self.mask_phone(match))
                elif pattern_type == "email":
                    result = result.replace(match, self.mask_email(match))
                elif pattern_type == "credit_card":
                    result = result.replace(match, self.mask_credit_card(match))
        
        return result
    
    def mask_dict(self, data: Dict[str, Any], depth: int = 0, max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively mask PII in a dictionary.
        
        Args:
            data: Dictionary to mask.
            depth: Current recursion depth.
            max_depth: Maximum recursion depth to prevent stack overflow.
        
        Returns:
            Dict: Dictionary with all PII masked.
        """
        if depth > max_depth:
            return {"masked": "max_depth_exceeded"}
        
        masked = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field is in sensitive list
            if key_lower in self.SENSITIVE_FIELDS:
                if isinstance(value, str):
                    # Apply type-specific masking
                    if "pan" in key_lower:
                        masked[key] = self.mask_pan(value)
                    elif "aadhar" in key_lower or "aadhaar" in key_lower:
                        masked[key] = self.mask_aadhar(value)
                    elif "phone" in key_lower or "mobile" in key_lower:
                        masked[key] = self.mask_phone(value)
                    elif "email" in key_lower:
                        masked[key] = self.mask_email(value)
                    else:
                        masked[key] = self.mask_generic(value)
                elif isinstance(value, (int, float)):
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = "***MASKED***"
            
            # Recurse into nested dicts
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value, depth + 1, max_depth)
            
            # Recurse into lists
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_dict(item, depth + 1, max_depth)
                    if isinstance(item, dict)
                    else (self.mask_string(item) if isinstance(item, str) else item)
                    for item in value
                ]
            
            # Mask strings that might contain PII
            elif isinstance(value, str) and len(value) > 5:
                masked[key] = self.mask_string(value)
            
            else:
                masked[key] = value
        
        return masked


# Global instance
pii_masker = PIIMasker()
