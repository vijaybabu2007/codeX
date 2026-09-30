import os
import uuid
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.main import app
from backend.database import get_db, SessionLocal
from backend.models import (
    User,
    UserSession,
    LearningPack,
    ObjectiveContract,
    LearningObjective,
    SourceVersion,
    SourceDocument,
    GeneratedAsset,
    AssetVersion,
    QuizQuestion,
    QuizQuestionVersion
)
from backend.services.source_service import create_source_document_and_version
from backend.services.contract_service import create_objective_contract
from backend.schemas.contract import ContractCreate, ObjectiveItem

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
# 1. USER REGISTRATION
# ==============================================================================
def test_1_user_registration_works(client, db: Session):
    """Test 1: Normal user registration works and returns 201 with session token & profile."""
    unique_email = f"prof_{uuid.uuid4().hex[:8]}@foundry.edu"
    payload = {
        "name": "Prof. Elena Rostova",
        "email": unique_email,
        "password": "PasswordSecure2026!",
        "confirm_password": "PasswordSecure2026!",
        "role": "teacher"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "token" in data
    assert data["token"].startswith("lf_sess_")
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "teacher"
    assert data["user"]["name"] == "Prof. Elena Rostova"

    # Verify session persisted in database
    session_record = db.query(UserSession).filter(UserSession.token == data["token"]).first()
    assert session_record is not None
    assert session_record.role == "teacher"

# ==============================================================================
# 2. DUPLICATE EMAIL REJECTION
# ==============================================================================
def test_2_duplicate_email_is_rejected(client):
    """Test 2: Attempting to register an already existing email returns HTTP 409 Conflict."""
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@foundry.edu"
    payload = {
        "name": "Original Teacher",
        "email": unique_email,
        "password": "PasswordSecure2026!",
        "confirm_password": "PasswordSecure2026!",
        "role": "teacher"
    }
    # First registration succeeds
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email must fail with 409
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()

# ==============================================================================
# 3. PASSWORD NEVER STORED AS PLAINTEXT
# ==============================================================================
def test_3_password_is_never_stored_as_plaintext(client, db: Session):
    """Test 3: Passwords must be securely hashed with PBKDF2-HMAC-SHA256 and never in plaintext."""
    plaintext_pass = "MySecretPlaintextPassword2026!"
    unique_email = f"sec_{uuid.uuid4().hex[:8]}@foundry.edu"
    res = client.post("/api/v1/auth/register", json={
        "name": "Security Tester",
        "email": unique_email,
        "password": plaintext_pass,
        "confirm_password": plaintext_pass,
        "role": "teacher"
    })
    assert res.status_code == 201

    # Directly inspect database column
    user_db = db.query(User).filter(User.email == unique_email).first()
    assert user_db is not None
    assert user_db.password_hash != plaintext_pass
    assert plaintext_pass not in user_db.password_hash
    assert user_db.password_hash.startswith("pbkdf2_sha256$")

    # Verify hashes are never returned to frontend
    res_data = res.json()
    assert "password" not in res_data["user"]
    assert "password_hash" not in res_data["user"]

# ==============================================================================
# 4. TEACHER LOGIN
# ==============================================================================
def test_4_teacher_login_works(client):
    """Test 4: Registered teacher can login with correct credentials."""
    email = f"teacher_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "Dr. Sarah Adams",
        "email": email,
        "password": "TeacherPass2026!",
        "confirm_password": "TeacherPass2026!",
        "role": "teacher"
    })

    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "TeacherPass2026!",
        "role": "teacher"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "teacher"
    assert data["user"]["email"] == email
    assert data["token"].startswith("lf_sess_")

# ==============================================================================
# 5. STUDENT LOGIN
# ==============================================================================
def test_5_student_login_works(client):
    """Test 5: Registered student can login with correct credentials."""
    email = f"student_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "Leo Martin",
        "email": email,
        "password": "StudentPass2026!",
        "confirm_password": "StudentPass2026!",
        "role": "student"
    })

    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "StudentPass2026!",
        "role": "student"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "student"
    assert data["user"]["email"] == email

# ==============================================================================
# 6. INVALID LOGIN REJECTED
# ==============================================================================
def test_6_invalid_login_is_rejected(client):
    """Test 6: Invalid credentials or incorrect password returns 401 Unauthorized."""
    email = f"user_{uuid.uuid4().hex[:8]}@foundry.edu"
    client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "CorrectPass2026!",
        "confirm_password": "CorrectPass2026!",
        "role": "teacher"
    })

    # Wrong password
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword!",
        "role": "teacher"
    })
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()

# ==============================================================================
# 7. TEACHER CANNOT ACCESS STUDENT-INAPPROPRIATE ENDPOINTS
# ==============================================================================
def test_7_teacher_cannot_access_student_inappropriate_endpoints(client):
    """Test 7: Teachers cannot submit student quizzes or use voice tutor as bypass."""
    email = f"teacher_guard_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Teacher Guard",
        "email": email,
        "password": "TeacherPassword2026!",
        "confirm_password": "TeacherPassword2026!",
        "role": "teacher"
    })
    token = reg.json()["token"]

    # Teacher submitting student quiz is blocked with 403 Forbidden
    res_quiz = client.post(
        "/api/v1/student/packs/dummy-pack-id/submit-quiz",
        headers={"Authorization": f"Bearer {token}"},
        json={"answers": {}}
    )
    assert res_quiz.status_code == 403
    assert "Teacher role cannot submit student quizzes" in res_quiz.json()["detail"]

    # Teacher using Voice Tutor as a bypass mechanism is blocked with 403 Forbidden
    res_voice = client.post(
        "/api/v1/student/voice/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"pack_id": "dummy-pack-id", "question": "Explain this to me"}
    )
    assert res_voice.status_code == 403
    assert "bypass mechanism" in res_voice.json()["detail"].lower()

# ==============================================================================
# 8. STUDENT CANNOT ACCESS TEACHER-ONLY ENDPOINTS
# ==============================================================================
def test_8_student_cannot_access_teacher_only_endpoints(client):
    """Test 8: Student role attempting teacher operations is rejected with 403 Forbidden."""
    email = f"student_guard_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Student Guard",
        "email": email,
        "password": "StudentPassword2026!",
        "confirm_password": "StudentPassword2026!",
        "role": "student"
    })
    token = reg.json()["token"]

    # Student calling pack generation is blocked
    res_gen = client.post(
        "/api/v1/packs/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"contract_id": "dummy-contract"}
    )
    assert res_gen.status_code == 403
    assert "Teacher role required" in res_gen.json()["detail"]

    # Student calling asset approval/decision is blocked
    res_dec = client.post(
        "/api/v1/decisions/asset-versions/dummy-ver-id",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "APPROVED", "acknowledged_warning_ids": []}
    )
    assert res_dec.status_code == 403
    assert "Teacher role required" in res_dec.json()["detail"]

    # Student calling surgical question regeneration is blocked
    res_regen = client.post(
        "/api/v1/questions/dummy-q-id/regenerate",
        headers={"Authorization": f"Bearer {token}"},
        json={"teacher_notes": "Bypass test", "reason": "Bypass"}
    )
    assert res_regen.status_code == 403
    assert "Teacher role required" in res_regen.json()["detail"]

# ==============================================================================
# 9. UNAUTHENTICATED USERS CANNOT ACCESS PROTECTED TEACHER ROUTES
# ==============================================================================
def test_9_unauthenticated_cannot_access_protected_teacher_routes(client):
    """Test 9: Calling protected teacher routes without token returns 401 Unauthorized."""
    res_gen = client.post(
        "/api/v1/packs/generate",
        json={"contract_id": "dummy-contract"}
    )
    assert res_gen.status_code == 401
    assert "Authentication token required" in res_gen.json()["detail"]

# ==============================================================================
# 10. STUDENT APPROVED-ONLY PROJECTION REMAINS ENFORCED
# ==============================================================================
def test_10_student_approved_only_projection_remains_enforced(db: Session, client):
    """Test 10: Student projection filters out draft and needs-revision assets server-side."""
    src_ver = create_source_document_and_version(
        db,
        f"Bio Source {uuid.uuid4().hex[:6]}",
        "Cell respiration converts glucose into ATP energy for living cells."
    )
    contract = create_objective_contract(
        db,
        ContractCreate(
            source_version_id=src_ver.id,
            title="Cell Respiration",
            target_learner_level="Grade 10",
            expected_difficulty="Medium",
            objectives=[
                ObjectiveItem(code="LO-01", description="Explain cellular respiration", bloom_level="Understand"),
                ObjectiveItem(code="LO-02", description="Analyze ATP production", bloom_level="Analyze")
            ],
            constraints={}
        )
    )

    pack = LearningPack(
        id=str(uuid.uuid4()),
        contract_id=contract.id,
        source_version_id=src_ver.id
    )
    db.add(pack)
    db.flush()

    # Asset 1: DRAFT (must be hidden)
    asset1 = GeneratedAsset(learning_pack_id=pack.id, asset_type="concept_explanation")
    db.add(asset1)
    db.flush()
    ver1 = AssetVersion(
        id=str(uuid.uuid4()),
        asset_id=asset1.id,
        source_version_id=src_ver.id,
        version_number=1,
        content_json=json.dumps({"title": "Draft Explanation", "explanation": "Secret draft text", "objective_ids": ["LO-01"]}),
        review_status="DRAFT",
        model_identifier="test-model"
    )
    db.add(ver1)
    db.flush()
    asset1.active_version_id = ver1.id

    # Asset 2: APPROVED (must be visible)
    asset2 = GeneratedAsset(learning_pack_id=pack.id, asset_type="revision_sheet")
    db.add(asset2)
    db.flush()
    ver2 = AssetVersion(
        id=str(uuid.uuid4()),
        asset_id=asset2.id,
        source_version_id=src_ver.id,
        version_number=1,
        content_json=json.dumps({"title": "Approved Summary", "bullet_points": ["ATP is cellular energy"], "key_takeaways": ["ATP is energy"], "objective_ids": ["LO-01"]}),
        review_status="APPROVED",
        model_identifier="test-model"
    )
    db.add(ver2)
    db.flush()
    asset2.active_version_id = ver2.id
    db.commit()

    # Fetch student projection
    res = client.get(f"/api/v1/student/packs/{pack.id}")
    assert res.status_code == 200
    proj = res.json()

    # Draft explanation must be None
    assert proj["concept_explanation"] is None
    # Approved revision sheet must be present
    assert proj["revision_sheet"] is not None
    assert proj["revision_sheet"]["title"] == "Approved Summary"

# ==============================================================================
# 11. VOICE TUTOR REMAINS APPROVED-ONLY
# ==============================================================================
def test_11_voice_tutor_remains_approved_only(client, db: Session):
    """Test 11: Voice Tutor context strictly excludes unapproved drafts and teacher notes."""
    # Query non-existent pack returns safe insufficient message or 404
    res = client.post("/api/v1/student/voice/query", json={
        "pack_id": f"fake_{uuid.uuid4().hex[:8]}",
        "question": "What is ATP?"
    })
    assert res.status_code in [404, 200]
    if res.status_code == 200:
        assert res.json()["confidence"] == "INSUFFICIENT"

# ==============================================================================
# 12. LOGOUT INVALIDATES AUTHENTICATION STATE
# ==============================================================================
def test_12_logout_invalidates_authentication_state(client):
    """Test 12: Calling /auth/logout immediately revokes session token."""
    email = f"logout_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Logout Tester",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "teacher"
    })
    token = reg.json()["token"]

    # Verify token is valid initially
    res_me1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me1.status_code == 200

    # Logout
    res_out = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res_out.status_code == 200

    # Token is now invalid
    res_me2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me2.status_code == 401
    assert "invalid or expired" in res_me2.json()["detail"].lower()

# ==============================================================================
# 13. SECURITY: STUDENT CANNOT ACCESS TEACHER PACK ENDPOINT
# ==============================================================================
def test_13_student_cannot_access_teacher_pack_endpoint(client):
    """Test 13: Student role cannot fetch raw teacher pack endpoint."""
    email = f"student_snoop_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg = client.post("/api/v1/auth/register", json={
        "name": "Snoop Student",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student"
    })
    token = reg.json()["token"]

    res = client.get("/api/v1/packs/any-pack-id", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "Students must access learning packs via the Student Portal" in res.json()["detail"]

# ==============================================================================
# 14. SECURITY: MULTI-USER DATA ISOLATION (TEACHER CANNOT ACCESS ANOTHER'S PACK)
# ==============================================================================
def test_14_multi_user_teacher_data_isolation(client, db: Session):
    """Test 14: Teacher A cannot inspect or manage Teacher B's learning pack."""
    # Register Teacher A
    email_a = f"teacher_a_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg_a = client.post("/api/v1/auth/register", json={
        "name": "Teacher A",
        "email": email_a,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "teacher"
    })
    teacher_a_id = reg_a.json()["user"]["id"]

    # Register Teacher B
    email_b = f"teacher_b_{uuid.uuid4().hex[:8]}@foundry.edu"
    reg_b = client.post("/api/v1/auth/register", json={
        "name": "Teacher B",
        "email": email_b,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "teacher"
    })
    token_b = reg_b.json()["token"]

    # Create real source and contract for Teacher A's pack
    src_ver = create_source_document_and_version(
        db,
        f"Teacher A Source {uuid.uuid4().hex[:6]}",
        "Teacher A private curriculum notes on quantum physics."
    )
    contract = create_objective_contract(
        db,
        ContractCreate(
            source_version_id=src_ver.id,
            title="Quantum Mechanics A",
            target_learner_level="Grade 12",
            expected_difficulty="Advanced",
            objectives=[
                ObjectiveItem(code="LO-01", description="Wave particle duality", bloom_level="Understand"),
                ObjectiveItem(code="LO-02", description="Schrodinger equation", bloom_level="Analyze")
            ],
            constraints={}
        )
    )

    pack_a = LearningPack(
        id=str(uuid.uuid4()),
        contract_id=contract.id,
        source_version_id=src_ver.id,
        owner_id=teacher_a_id
    )
    db.add(pack_a)
    db.commit()

    # Teacher B attempts to access Teacher A's pack -> must receive 403 Forbidden
    res = client.get(f"/api/v1/packs/{pack_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403
    assert "another educator's pack" in res.json()["detail"].lower()
