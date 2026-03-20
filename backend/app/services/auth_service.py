from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from sqlalchemy.orm import Session
from app.config import settings
from app.models.owner import Owner


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_owner_by_email(db: Session, email: str) -> Optional[Owner]:
    return db.query(Owner).filter(Owner.email == email).first()


def get_owner_by_id(db: Session, owner_id: str) -> Optional[Owner]:
    return db.query(Owner).filter(Owner.id == owner_id).first()


def authenticate_owner(db: Session, email: str, password: str) -> Optional[Owner]:
    owner = get_owner_by_email(db, email)
    if not owner or not verify_password(password, owner.password_hash):
        return None
    return owner
