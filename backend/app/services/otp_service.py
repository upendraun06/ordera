import random
import string
import time
from typing import Dict, Tuple, Optional

# In-memory OTP storage: {identifier: (code, expiry_timestamp)}
_otp_store: Dict[str, Tuple[str, float]] = {}

OTP_TTL_SECONDS = 300  # 5 minutes


def generate_otp(identifier: str) -> str:
    """Generate a 6-digit OTP code and store it with a 5-minute TTL."""
    code = "".join(random.choices(string.digits, k=6))
    _otp_store[identifier] = (code, time.time() + OTP_TTL_SECONDS)
    return code


def verify_otp(identifier: str, code: str) -> bool:
    """Verify an OTP code. Deletes the OTP on successful verification."""
    entry = _otp_store.get(identifier)
    if not entry:
        return False
    stored_code, expiry = entry
    # Expired
    if time.time() > expiry:
        del _otp_store[identifier]
        return False
    # Wrong code
    if stored_code != code:
        return False
    # Correct — consume it
    del _otp_store[identifier]
    return True


def get_otp_for_dev(identifier: str) -> Optional[str]:
    """Return the current OTP for an identifier (dev/testing only)."""
    entry = _otp_store.get(identifier)
    if not entry:
        return None
    stored_code, expiry = entry
    if time.time() > expiry:
        del _otp_store[identifier]
        return None
    return stored_code
