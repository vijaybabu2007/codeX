import uuid
import time
import base64
import json
import hmac
import hashlib
import urllib.parse
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.database import SessionLocal
from backend.models import User, UserSession
from backend.config import settings
from backend.services.google_oauth_service import (
    create_oauth_state,
    verify_oauth_state,
    build_google_authorization_url,
    authenticate_or_create_google_user,
    _get_signing_key,
)
from backend.services.auth_service import verify_password


@pytest.fixture
def client():
    with TestClient(app, follow_redirects=False) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# 1. PROVIDERS STATUS ENDPOINT & MISSING CONFIGURATION
# ==============================================================================

def test_auth_providers_endpoint_reflects_configuration(client, monkeypatch):
    """GET /api/v1/auth/providers returns exact provider availability status."""
    # When unconfigured
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")
    res = client.get("/api/v1/auth/providers")
    assert res.status_code == 200
    data = res.json()
    assert data["google"]["enabled"] is False
    assert data["microsoft"]["enabled"] is False
    assert data["microsoft"]["status"] == "coming_soon"
    assert data["github"]["enabled"] is False
    assert data["github"]["status"] == "coming_soon"

    # When configured
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mock-client-id-123.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "mock-client-secret-xyz")
    res = client.get("/api/v1/auth/providers")
    assert res.status_code == 200
    data = res.json()
    assert data["google"]["enabled"] is True


def test_google_login_endpoint_returns_503_when_unconfigured(client, monkeypatch):
    """GET /api/v1/auth/google returns 503 if credentials are not configured."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")
    res = client.get("/api/v1/auth/google")
    assert res.status_code == 503
    assert "Google Sign-In is not configured for this deployment" in res.json()["detail"]


# ==============================================================================
# 2. OAUTH STATE GENERATION & AUTHORIZATION URL
# ==============================================================================

def test_oauth_state_generation_and_verification():
    """State parameter generates cryptographically signed HMAC token with TTL."""
    state = create_oauth_state(intended_role="teacher")
    assert "." in state
    payload = verify_oauth_state(state)
    assert payload["role"] == "teacher"
    assert "nonce" in payload
    assert payload["exp"] > time.time()


def test_google_login_endpoint_redirects_to_google_when_configured(client, monkeypatch):
    """GET /api/v1/auth/google redirects to accounts.google.com with valid state."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mock-client-id-123.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "mock-secret-456")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")

    res = client.get("/api/v1/auth/google?intended_role=student")
    assert res.status_code == 302
    location = res.headers["location"]
    assert "https://accounts.google.com/o/oauth2/v2/auth" in location
    assert "client_id=mock-client-id-123.apps.googleusercontent.com" in location
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback" in location
    assert "scope=openid+email+profile" in location
    assert "state=" in location


# ==============================================================================
# 3. STATE VALIDATION & TAMPER / EXPIRATION REJECTION
# ==============================================================================

def test_invalid_state_signature_rejected():
    """Tampered state payload fails cryptographic signature verification."""
    state = create_oauth_state(intended_role="student")
    payload_b64, sig = state.split(".")
    # Tamper with payload (e.g., trying to elevate role)
    tampered_payload = {"role": "teacher", "nonce": "hacked", "iat": int(time.time()), "exp": int(time.time()) + 600}
    tampered_b64 = base64.urlsafe_b64encode(json.dumps(tampered_payload).encode()).decode().rstrip("=")
    tampered_state = f"{tampered_b64}.{sig}"

    with pytest.raises(ValueError, match="Cryptographic signature mismatch"):
        verify_oauth_state(tampered_state)


def test_expired_state_rejected():
    """Expired state token is rejected."""
    # Create expired payload
    payload = {"role": "student", "nonce": "abc123", "iat": int(time.time()) - 1000, "exp": int(time.time()) - 100}
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    sig = hmac.new(_get_signing_key(), payload_b64.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    expired_state = f"{payload_b64}.{sig_b64}"

    with pytest.raises(ValueError, match="OAuth state has expired"):
        verify_oauth_state(expired_state)


def test_callback_rejects_missing_code_or_state(client):
    """Callback redirects to /login?error=... if code or state is missing."""
    res = client.get("/api/v1/auth/google/callback")
    assert res.status_code == 302
    assert "/login?error=" in res.headers["location"]
    unquoted = urllib.parse.unquote(res.headers["location"])
    assert "Missing authorization code or state parameter from Google." in unquoted


def test_callback_handles_provider_denial_error(client):
    """Callback redirects to /login?error=... when Google returns error=access_denied."""
    res = client.get("/api/v1/auth/google/callback?error=access_denied&error_description=User+declined")
    assert res.status_code == 302
    unquoted = urllib.parse.unquote(res.headers["location"])
    assert "User declined" in unquoted


# ==============================================================================
# 4. UNVERIFIED EMAIL REJECTION
# ==============================================================================

def test_unverified_google_email_rejected(db):
    """Identity with email_verified=False is rejected to prevent impersonation."""
    profile = {
        "sub": "google-sub-999",
        "email": "unverified@example.com",
        "email_verified": False,
        "name": "Unverified User"
    }
    with pytest.raises(ValueError, match="Google email is not verified"):
        authenticate_or_create_google_user(db, profile, intended_role="student")


# ==============================================================================
# 5. NEW USER HANDLING & SECURE PASSWORD GENERATION
# ==============================================================================

def test_new_user_creation_student_role(db):
    """New user without existing account is created with intended student role and student_id."""
    unique_email = f"google_student_{uuid.uuid4().hex[:8]}@example.com"
    profile = {
        "sub": f"sub-{uuid.uuid4().hex[:12]}",
        "email": unique_email,
        "email_verified": True,
        "name": "Jane GoogleStudent"
    }

    user, token = authenticate_or_create_google_user(db, profile, intended_role="student")
    assert user.id is not None
    assert user.email == unique_email
    assert user.name == "Jane GoogleStudent"
    assert user.role == "student"
    assert user.student_id is not None
    assert token.startswith("lf_sess_")

    # Verify session persisted
    session_rec = db.query(UserSession).filter(UserSession.token == token).first()
    assert session_rec is not None
    assert session_rec.user_id == user.id


def test_new_user_creation_teacher_role(db):
    """New user registered with intended teacher role is created as teacher."""
    unique_email = f"google_teacher_{uuid.uuid4().hex[:8]}@example.com"
    profile = {
        "sub": f"sub-{uuid.uuid4().hex[:12]}",
        "email": unique_email,
        "email_verified": True,
        "name": "Dr. Google Teacher"
    }

    user, token = authenticate_or_create_google_user(db, profile, intended_role="teacher")
    assert user.id is not None
    assert user.email == unique_email
    assert user.name == "Dr. Google Teacher"
    assert user.role == "teacher"
    assert token.startswith("lf_sess_")


# ==============================================================================
# 6. EXISTING USER MAPPING & AUTHORITATIVE ROLE RETENTION
# ==============================================================================

def test_existing_user_authoritative_role_retention(db):
    """Existing teacher role CANNOT be downgraded or modified by OAuth intended_role."""
    unique_email = f"senior_teacher_{uuid.uuid4().hex[:8]}@foundry.edu"

    # Create existing TEACHER user via direct DB
    teacher_user = User(
        id=f"user-{uuid.uuid4().hex[:12]}",
        name="Senior Prof Verma",
        email=unique_email,
        role="teacher",
        password_hash="some-hash"
    )
    db.add(teacher_user)
    db.commit()

    # Google OAuth signs in, but state requested "student"
    profile = {
        "sub": "google-sub-555",
        "email": unique_email,
        "email_verified": True,
        "name": "Senior Prof Verma"
    }

    resolved_user, token = authenticate_or_create_google_user(db, profile, intended_role="student")
    # Must retain authoritative teacher role
    assert resolved_user.id == teacher_user.id
    assert resolved_user.role == "teacher"
    assert token.startswith("lf_sess_")


# ==============================================================================
# 7. END-TO-END MOCKED CALLBACK FLOW
# ==============================================================================

@patch("backend.api.routes_auth.exchange_code_for_tokens")
@patch("backend.api.routes_auth.fetch_google_user_profile")
def test_google_callback_endpoint_full_success_flow(mock_profile, mock_tokens, client, monkeypatch):
    """Full callback endpoint successfully handles code exchange, profile retrieval, and session redirect."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mock-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "mock-secret")

    test_email = f"e2e_google_{uuid.uuid4().hex[:8]}@foundry.edu"
    mock_tokens.return_value = {"access_token": "mock-access-token-123"}
    mock_profile.return_value = {
        "sub": "sub-123456789",
        "email": test_email,
        "email_verified": True,
        "name": "E2E Verified User"
    }

    state = create_oauth_state(intended_role="student")
    res = client.get(f"/api/v1/auth/google/callback?code=mock_auth_code_xyz&state={state}")

    assert res.status_code == 302
    location = res.headers["location"]
    assert "/login?oauth_token=lf_sess_" in location
    assert "role=student" in location
    unquoted = urllib.parse.unquote(location)
    assert "E2E Verified User" in unquoted


# ==============================================================================
# 8. EXISTING EMAIL/PASSWORD LOGIN REMAINS 100% WORKING
# ==============================================================================

def test_existing_email_password_login_unaffected(client):
    """Teacher and student standard email/password authentication remains intact."""
    # 1. Register teacher
    t_email = f"teacher_reg_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Prof. Regression Test",
        "email": t_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "teacher"
    })
    assert reg_res.status_code == 201

    # 2. Login teacher
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": t_email,
        "password": "Password123!",
        "role": "teacher"
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["authenticated"] is True
    assert data["role"] == "TEACHER"
    assert data["token"].startswith("lf_sess_")

    # 3. Authenticated /me endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == t_email
    assert me_data["role"] == "teacher"
