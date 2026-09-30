import time
import json
import base64
import hmac
import hashlib
import secrets
import urllib.parse
from typing import Tuple, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from backend.config import (
    settings,
    get_effective_google_client_id,
    get_effective_google_client_secret,
    get_effective_google_redirect_uri,
    is_google_oauth_configured
)
from backend.models.user import User
from backend.services.auth_service import hash_password, create_session

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

STATE_TTL_SECONDS = 600  # 10 minutes


def _get_signing_key() -> bytes:
    key_str = getattr(settings, "AUTH_SECRET_KEY", "lessonfoundry-oauth-secret-key-yuva-2026")
    return key_str.encode("utf-8")


def create_oauth_state(intended_role: str = "student") -> str:
    """
    Creates a cryptographically signed, tamper-proof state parameter with TTL.
    Protects against CSRF and prevents untrusted client parameters from modifying intended role.
    """
    valid_role = "teacher" if str(intended_role).lower() == "teacher" else "student"
    payload = {
        "role": valid_role,
        "nonce": secrets.token_hex(16),
        "iat": int(time.time()),
        "exp": int(time.time()) + STATE_TTL_SECONDS
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    
    sig = hmac.new(_get_signing_key(), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    
    return f"{payload_b64}.{sig_b64}"


def verify_oauth_state(state_token: str) -> Dict[str, Any]:
    """
    Validates HMAC signature and expiration of state parameter in constant time.
    Returns the decoded payload if valid, otherwise raises ValueError.
    """
    if not state_token or "." not in state_token:
        raise ValueError("Invalid OAuth state: Missing or malformed state token.")

    parts = state_token.split(".")
    if len(parts) != 2:
        raise ValueError("Invalid OAuth state: Incorrect token structure.")

    payload_b64, sig_b64 = parts

    # Re-compute expected signature
    expected_sig = hmac.new(_get_signing_key(), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")

    if not secrets.compare_digest(sig_b64, expected_sig_b64):
        raise ValueError("Invalid OAuth state: Cryptographic signature mismatch. Possible tampering or CSRF.")

    # Decode payload with padding
    pad = len(payload_b64) % 4
    if pad:
        payload_b64 += "=" * (4 - pad)

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid OAuth state: Could not parse state payload: {e}")

    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise ValueError("OAuth state has expired. Please initiate sign-in again.")

    return payload


def build_google_authorization_url(state: str) -> str:
    """
    Constructs the official Google OAuth 2.0 authorization URL.
    """
    client_id = get_effective_google_client_id()
    redirect_uri = get_effective_google_redirect_uri()

    if not client_id or not redirect_uri:
        raise ValueError("Google OAuth is not configured. Missing Client ID or Redirect URI.")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account"
    }

    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchanges authorization code for tokens with Google's OAuth token endpoint.
    Client secret is transmitted strictly from the backend server.
    """
    client_id = get_effective_google_client_id()
    client_secret = get_effective_google_client_secret()
    redirect_uri = get_effective_google_redirect_uri()

    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials are not configured on the server.")

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    with httpx.Client(timeout=15.0) as client:
        response = client.post(GOOGLE_TOKEN_URL, data=data)

    if response.status_code != 200:
        error_detail = "Failed to exchange authorization code with Google."
        try:
            err_json = response.json()
            if "error_description" in err_json:
                error_detail = err_json["error_description"]
        except Exception:
            pass
        raise ValueError(f"Google OAuth token exchange failed: {error_detail}")

    tokens = response.json()
    if not tokens.get("access_token"):
        raise ValueError("Google token response did not contain a valid access_token.")

    return tokens


def fetch_google_user_profile(access_token: str) -> Dict[str, Any]:
    """
    Retrieves verified user identity from Google OpenID userinfo endpoint.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client(timeout=15.0) as client:
        response = client.get(GOOGLE_USERINFO_URL, headers=headers)

    if response.status_code != 200:
        raise ValueError("Failed to retrieve user profile from Google OpenID service.")

    profile = response.json()
    return profile


def authenticate_or_create_google_user(
    db: Session,
    google_profile: Dict[str, Any],
    intended_role: str = "student"
) -> Tuple[User, str]:
    """
    Validates Google identity and maps to a LessonFoundry user:
    - Rejects unverified emails (email_verified must be True).
    - If user exists: Authoritative DB role is retained (never overridden).
    - If user is new: Creates user with validated intended_role ('teacher' or 'student')
      and generates an unguessable password hash.
    - Creates and returns (user, session_token).
    """
    email = google_profile.get("email", "").strip().lower()
    if not email:
        raise ValueError("Google profile did not provide an email address.")

    email_verified = google_profile.get("email_verified")
    if email_verified is not True:
        raise ValueError("Google email is not verified. Unverified accounts cannot authenticate.")

    display_name = google_profile.get("name", "").strip() or email.split("@")[0].capitalize()
    google_sub = google_profile.get("sub", "")

    # Look up existing user by email
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        # AUTHORITATIVE ROLE RETENTION: An existing user's role can never be overridden by OAuth params
        user = existing_user
        if not user.name and display_name:
            user.name = display_name
            db.commit()
    else:
        # New user registration
        clean_role = "teacher" if str(intended_role).lower() == "teacher" else "student"
        clean_sid = None
        if clean_role == "student":
            prefix = email.split("@")[0].upper()
            existing_sid = db.query(User).filter(User.student_id == prefix).first()
            clean_sid = prefix if not existing_sid else f"STU-{secrets.token_hex(4).upper()}"

        # Cryptographically secure random password hash (cannot be guessed or brute-forced)
        random_pwd = secrets.token_urlsafe(48)
        pwd_hash = hash_password(random_pwd)

        user = User(
            id=str(secrets.token_hex(16)),
            name=display_name,
            email=email,
            student_id=clean_sid,
            password_hash=pwd_hash,
            role=clean_role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_session(db, user)
    return user, token
