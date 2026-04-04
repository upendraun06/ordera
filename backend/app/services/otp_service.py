"""
OTP Service — database-backed one-time passwords.

Stores OTP codes in PostgreSQL so they work across multiple backend replicas
(the previous in-memory dict broke when requests hit different pods).
"""
import random
import string
import time
from typing import Optional
from sqlalchemy.orm import Session

from app.models.otp import OTPCode

OTP_TTL_SECONDS = 600  # 10 minutes


def generate_otp(db: Session, identifier: str) -> str:
    """Generate a 6-digit OTP code and store it in the database with a 5-minute TTL."""
    code = "".join(random.choices(string.digits, k=6))
    expires_at = time.time() + OTP_TTL_SECONDS

    # Upsert: delete existing OTP for this identifier, then insert new one
    db.query(OTPCode).filter(OTPCode.identifier == identifier).delete()
    otp_entry = OTPCode(identifier=identifier, code=code, expires_at=expires_at)
    db.add(otp_entry)
    db.commit()

    return code


def verify_otp(db: Session, identifier: str, code: str) -> bool:
    """Verify an OTP code. Deletes the OTP on successful verification."""
    print(f"[OTP] verify called — identifier={identifier!r}, code={code!r}")
    entry = db.query(OTPCode).filter(OTPCode.identifier == identifier).first()
    if not entry:
        print(f"[OTP] FAIL — no entry found for identifier={identifier!r}")
        # Show all current entries for debugging
        all_entries = db.query(OTPCode).all()
        print(f"[OTP] All current entries: {[(e.identifier, e.code) for e in all_entries]}")
        return False

    # Expired
    if time.time() > entry.expires_at:
        remaining = entry.expires_at - time.time()
        print(f"[OTP] FAIL — code expired {abs(remaining):.0f}s ago")
        db.delete(entry)
        db.commit()
        return False

    # Wrong code (strip whitespace to handle copy-paste issues)
    if entry.code != code.strip():
        print(f"[OTP] FAIL — code mismatch: stored={entry.code!r}, received={code.strip()!r}")
        return False

    # Correct — consume it
    print(f"[OTP] OK — code matched, consuming")
    db.delete(entry)
    db.commit()
    return True


def get_otp_for_dev(db: Session, identifier: str) -> Optional[str]:
    """Return the current OTP for an identifier (dev/testing only)."""
    entry = db.query(OTPCode).filter(OTPCode.identifier == identifier).first()
    if not entry:
        return None
    if time.time() > entry.expires_at:
        db.delete(entry)
        db.commit()
        return None
    return entry.code
