import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, UserSession

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# ==============================================================================
# 1. TEACHER REGISTRATION & ROLE MODEL
# ==============================================================================
def test_teacher_registration_returns_complete_role_model(client):
    """Teacher registration returns user_id, name, role='TEACHER', authenticated=True, token."""
    email = f"teacher_{uuid.uuid4().hex[:8]}@foundry.edu"
    payload = {
        "name": "Prof. Ajay Verma",
        "email": email,
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
        "role": "teacher"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["authenticated"] is True
    assert data["role"] == "TEACHER"
    assert data["name"] == "Prof. Ajay Verma"
    assert "user_id" in data
    assert data["token"].startswith("lf_sess_")
    assert data["user"]["role"] == "teacher"

# ==============================================================================
# 2. STUDENT REGISTRATION WITH STUDENT ID
# ==============================================================================
def test_student_registration_with_custom_student_id(client):
    """Student registration supports custom student_id and returns role='STUDENT'."""
    sid = f"STU{uuid.uuid4().hex[:6].upper()}"
    email = f"student_{uuid.uuid4().hex[:8]}@foundry.edu"
    payload = {
        "name": "Vishwajith Kumar",
        "email": email,
        "password": "StudentPassword2026!",
        "confirm_password": "StudentPassword2026!",
        "role": "student",
        "student_id": sid
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["authenticated"] is True
    assert data["role"] == "STUDENT"
    assert data["name"] == "Vishwajith Kumar"
    assert data["user"]["student_id"] == sid

# ==============================================================================
# 3. STUDENT REGISTRATION AUTO-ASSIGN STUDENT ID FROM USERNAME
# ==============================================================================
def test_student_registration_auto_assigns_student_id_from_email(client):
    """When student_id is not explicitly provided, it defaults to the uppercase username part of email."""
    unique_prefix = f"stud{uuid.uuid4().hex[:6]}"
    email = f"{unique_prefix}@foundry.edu"
    payload = {
        "name": "Ananya Sharma",
        "email": email,
        "password": "StudentPassword2026!",
        "confirm_password": "StudentPassword2026!",
        "role": "student"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["student_id"] == unique_prefix.upper()

# ==============================================================================
# 4. DUPLICATE STUDENT ID IS REJECTED
# ==============================================================================
def test_duplicate_student_id_is_rejected(client):
    """Duplicate custom student ID is rejected with 409 Conflict."""
    fixed_sid = f"STUFIX{uuid.uuid4().hex[:4].upper()}"
    client.post("/api/v1/auth/register", json={
        "name": "Student One",
        "email": f"s1_{uuid.uuid4().hex[:6]}@foundry.edu",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student",
        "student_id": fixed_sid
    })
    res2 = client.post("/api/v1/auth/register", json={
        "name": "Student Two",
        "email": f"s2_{uuid.uuid4().hex[:6]}@foundry.edu",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student",
        "student_id": fixed_sid
    })
    assert res2.status_code == 409
    assert "already assigned" in res2.json()["detail"].lower()

# ==============================================================================
# 5. TEACHER LOGIN WITH EMAIL
# ==============================================================================
def test_teacher_login_returns_teacher_role(client):
    """Teacher login returns role='TEACHER' and authenticated=True."""
    email = f"teach_log_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "Prof. Rao",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "teacher"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
        "role": "teacher"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "TEACHER"
    assert data["authenticated"] is True
    assert data["name"] == "Prof. Rao"

# ==============================================================================
# 6. STUDENT LOGIN WITH EMAIL
# ==============================================================================
def test_student_login_with_email(client):
    """Student can log in using their registered email address."""
    email = f"stu_email_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "Kavita Nair",
        "email": email,
        "password": "StudentPassword123!",
        "confirm_password": "StudentPassword123!",
        "role": "student"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "StudentPassword123!",
        "role": "student"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "STUDENT"
    assert data["authenticated"] is True

# ==============================================================================
# 7. STUDENT LOGIN WITH STUDENT ID (e.g. STU001)
# ==============================================================================
def test_student_login_with_student_id(client):
    """Student can log in using their Student ID (e.g. STU001) without email."""
    sid = f"STU{uuid.uuid4().hex[:4].upper()}"
    client.post("/api/v1/auth/register", json={
        "name": "Rohan Deshmukh",
        "email": f"rohan_{uuid.uuid4().hex[:6]}@foundry.edu",
        "password": "StudentPassword123!",
        "confirm_password": "StudentPassword123!",
        "role": "student",
        "student_id": sid
    })
    # Login using identifier field or email field with Student ID
    res = client.post("/api/v1/auth/login", json={
        "identifier": sid,
        "password": "StudentPassword123!",
        "role": "student"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "STUDENT"
    assert data["name"] == "Rohan Deshmukh"
    assert data["authenticated"] is True

# ==============================================================================
# 8. INVALID PASSWORD REJECTED
# ==============================================================================
def test_login_invalid_password_returns_401(client):
    """Login with wrong password returns HTTP 401."""
    email = f"usr_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "User Alpha",
        "email": email,
        "password": "CorrectPassword123!",
        "confirm_password": "CorrectPassword123!",
        "role": "teacher"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword999!",
        "role": "teacher"
    })
    assert res.status_code == 401

# ==============================================================================
# 9. UNKNOWN USER REJECTED
# ==============================================================================
def test_login_unknown_user_returns_401(client):
    """Login with non-existent user returns HTTP 401."""
    res = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_99999@foundry.edu",
        "password": "AnyPassword123!",
        "role": "student"
    })
    assert res.status_code == 401

# ==============================================================================
# 10. ROLE MISMATCH ON LOGIN REJECTED
# ==============================================================================
def test_role_mismatch_on_login_is_rejected(client):
    """
    If a student attempts to log in via the Teacher login form,
    the backend rejects with role mismatch.
    """
    student_email = f"student_portal_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "Portal Student",
        "email": student_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student"
    })

    # Student enters credentials in Teacher login form (expected_role='teacher')
    res = client.post("/api/v1/auth/login", json={
        "email": student_email,
        "password": "Password123!",
        "role": "teacher"
    })
    assert res.status_code == 401
    assert "role mismatch" in res.json()["detail"].lower()

# ==============================================================================
# 11. STUDENT BLOCKED FROM TEACHER APIS (HTTP 403)
# ==============================================================================
def test_student_blocked_from_teacher_apis(client):
    """Student token calling Teacher-only endpoints is blocked with 403 Forbidden."""
    email = f"stu_sec_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Sec Student",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Pack generation
    res_gen = client.post("/api/v1/packs/generate", headers=headers, json={"contract_id": "dummy"})
    assert res_gen.status_code == 403
    assert "Teacher role required" in res_gen.json()["detail"]

    # 2. Decision endpoint
    res_dec = client.post("/api/v1/decisions/asset-versions/dummy", headers=headers, json={"action": "APPROVED", "acknowledged_warning_ids": []})
    assert res_dec.status_code == 403

    # 3. Surgical question regeneration
    res_regen = client.post("/api/v1/questions/dummy/regenerate", headers=headers, json={"teacher_notes": "Note", "reason": "Reason"})
    assert res_regen.status_code == 403

# ==============================================================================
# 12. TEACHER BLOCKED FROM STUDENT QUIZ SUBMISSION (HTTP 403)
# ==============================================================================
def test_teacher_blocked_from_student_quiz_submission(client):
    """Teacher token cannot submit student quizzes."""
    email = f"teach_sec_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Sec Teacher",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "teacher"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/student/packs/dummy-pack/submit-quiz", headers=headers, json={"answers": {}})
    assert res.status_code == 403
    assert "Teacher role cannot submit student quizzes" in res.json()["detail"]

# ==============================================================================
# 13. UNAUTHENTICATED CALL TO PROTECTED ROUTE RETURNS 401
# ==============================================================================
def test_unauthenticated_protected_route_returns_401(client):
    """Requests without authorization header return HTTP 401."""
    res_dash = client.get("/api/v1/student/dashboard")
    assert res_dash.status_code == 401
    res_me = client.get("/api/v1/auth/me")
    assert res_me.status_code == 401

# ==============================================================================
# 14. LOGOUT INVALIDATES TOKEN
# ==============================================================================
def test_logout_revokes_session(client):
    """After logout, session token is revoked and cannot be reused."""
    email = f"logout_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Logout User",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_me1 = client.get("/api/v1/auth/me", headers=headers)
    assert res_me1.status_code == 200

    res_out = client.post("/api/v1/auth/logout", headers=headers)
    assert res_out.status_code == 200

    res_me2 = client.get("/api/v1/auth/me", headers=headers)
    assert res_me2.status_code == 401
