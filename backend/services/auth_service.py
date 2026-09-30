import re
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from backend.models.user import User, UserSession

# Email validation regex
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def hash_password(password: str) -> str:
    """NIST-compliant PBKDF2-HMAC-SHA256 password hashing with cryptographically secure random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        200000
    )
    return f"pbkdf2_sha256${salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password in constant time against stored PBKDF2 hash."""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3 or parts[0] != "pbkdf2_sha256":
            return False
        salt, key_hex = parts[1], parts[2]
        key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            200000
        )
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

def create_session(db: Session, user: User, days_valid: int = 30) -> str:
    """Generate cryptographically secure session token and persist to database."""
    token = "lf_sess_" + secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
    
    session_obj = UserSession(
        token=token,
        user_id=user.id,
        role=user.role,
        expires_at=expires_at
    )
    db.add(session_obj)
    db.commit()
    return token

def register_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    confirm_password: str,
    role: str,
    student_id: Optional[str] = None
) -> Tuple[User, str]:
    """Register a new user with secure password hashing and return (user, session_token)."""
    clean_name = (name or "").strip()
    clean_email = (email or "").strip().lower()
    clean_role = (role or "").strip().lower()

    if len(clean_name) < 2:
        raise ValueError("Full name must be at least 2 characters.")

    if not clean_email or not EMAIL_REGEX.match(clean_email):
        raise ValueError("Please provide a valid institutional or personal email address.")

    if clean_role not in ["teacher", "student"]:
        raise ValueError("Role must be specified as either 'teacher' or 'student'.")

    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise KeyError("An account with this email address already exists. Please sign in instead.")

    # Assign and validate student_id for student accounts
    clean_sid = None
    if clean_role == "student":
        if student_id and student_id.strip():
            clean_sid = student_id.strip().upper()
            existing_sid = db.query(User).filter(func.upper(User.student_id) == clean_sid).first()
            if existing_sid:
                raise KeyError(f"Student ID '{clean_sid}' is already assigned to another account.")
        else:
            prefix = clean_email.split('@')[0].upper()
            existing_sid = db.query(User).filter(func.upper(User.student_id) == prefix).first()
            clean_sid = prefix if not existing_sid else f"STU-{uuid.uuid4().hex[:6].upper()}"

    pwd_hash = hash_password(password)

    user = User(
        id=str(uuid.uuid4()),
        name=clean_name,
        email=clean_email,
        student_id=clean_sid,
        password_hash=pwd_hash,
        role=clean_role,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session(db, user)
    return user, token

def authenticate_user(
    db: Session,
    email: str,
    password: str,
    expected_role: Optional[str] = None
) -> Tuple[User, str]:
    """
    Authenticate credentials against stored hash.
    Accepts email, Student ID (e.g. STU001), Teacher ID, or user UUID in the 'email'/'identifier' parameter.
    Validates expected_role if provided to prevent portal confusion.
    """
    clean_ident = (email or "").strip()
    clean_ident_lower = clean_ident.lower()
    
    if not clean_ident or not password:
        raise ValueError("Invalid email/identifier or password.")

    # Look up by email, student_id, UUID, or email prefix
    user = db.query(User).filter(
        or_(
            func.lower(User.email) == clean_ident_lower,
            func.lower(User.student_id) == clean_ident_lower,
            User.id == clean_ident,
            func.lower(User.email).like(f"{clean_ident_lower}@%")
        )
    ).first()

    if not user:
        raise ValueError("Invalid email or password.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")

    # Role enforcement if specific portal intent is declared
    if expected_role:
        clean_expected = expected_role.strip().lower()
        if user.role.lower() != clean_expected:
            raise ValueError(
                f"Role mismatch: This account is registered as a {user.role.upper()}. "
                f"Please sign in through the {user.role.capitalize()} portal."
            )

    token = create_session(db, user)
    return user, token

def get_user_from_token(db: Session, token: str) -> Optional[User]:
    """Retrieve active user matching non-expired session token."""
    if not token:
        return None
    
    clean_token = token.replace("Bearer ", "").strip()
    session_obj = db.query(UserSession).filter(
        UserSession.token == clean_token,
        UserSession.expires_at > datetime.now(timezone.utc)
    ).first()

    if not session_obj:
        return None

    return db.query(User).filter(User.id == session_obj.user_id).first()

def revoke_session(db: Session, token: str) -> None:
    """Invalidate active session token on logout."""
    if not token:
        return
    clean_token = token.replace("Bearer ", "").strip()
    db.query(UserSession).filter(UserSession.token == clean_token).delete()
    db.commit()
