"""
Security Utilities

JWT token creation, password hashing, and verification.
Implements industry-standard security practices for BFSI.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from uuid import UUID

from jose import JWTError, jwt
import bcrypt

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.
    
    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        # Encode password and truncate to 72 bytes (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash.
    
    Returns:
        str: Bcrypt hashed password.
    """
    # Encode password and truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(
    subject: str | UUID,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User ID (sub claim).
        email: User email.
        role: User role.
        expires_delta: Optional custom expiration time.
    
    Returns:
        str: Encoded JWT token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: str | UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: User ID (sub claim).
        expires_delta: Optional custom expiration time.
    
    Returns:
        str: Encoded JWT refresh token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify.
        token_type: Expected token type ("access" or "refresh").
    
    Returns:
        dict: Decoded token payload if valid, None if invalid.
    
    Raises:
        JWTError: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        return payload
    
    except JWTError:
        return None


def hash_aadhar(aadhar_number: str) -> str:
    """
    Hash Aadhar number for secure storage.
    Uses SHA-256 for irreversible hashing.
    
    Args:
        aadhar_number: 12-digit Aadhar number.
    
    Returns:
        str: SHA-256 hash of the Aadhar number.
    """
    import hashlib
    
    # Remove any spaces or dashes
    cleaned = aadhar_number.replace(" ", "").replace("-", "")
    
    # Hash with SHA-256
    return hashlib.sha256(cleaned.encode()).hexdigest()
