import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, UserSession, LearningPack, StudentQuizAttempt

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

def create_test_user(db, role="teacher"):
    uid = str(uuid.uuid4())
    email = f"test_{role}_{uid[:8]}@foundry.edu"
    user = User(
        id=uid,
        name=f"Test {role.capitalize()}",
        email=email,
        password_hash="test_hash_123",
        role=role,
        student_id=f"STU-{uid[:6].upper()}" if role == "student" else None
    )
    db.add(user)
    db.commit()

    token = f"lf_sess_{role}_{uid[:8]}"
    session = UserSession(
        token=token,
        user_id=uid,
        role=role,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db.add(session)
    db.commit()
    return user, token

def test_teacher_analytics_unauthenticated_fails(client):
    """Unauthenticated requests must be rejected with 401."""
    res = client.get("/api/v1/teacher/analytics/overview")
    assert res.status_code == 401

def test_teacher_analytics_student_forbidden(client, db):
    """Students must NOT be allowed to access teacher student performance analytics (403 Forbidden)."""
    _, student_token = create_test_user(db, role="student")
    res = client.get(
        "/api/v1/teacher/analytics/overview",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res.status_code == 403
    assert "Teacher role required" in res.json()["detail"]

def test_teacher_analytics_overview_success(client, db):
    """Teacher can successfully query class performance overview and KPI metrics."""
    _, teacher_token = create_test_user(db, role="teacher")
    res = client.get(
        "/api/v1/teacher/analytics/overview",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res.status_code == 200
    data = res.json()

    assert "summary" in data
    assert "total_enrolled_students" in data["summary"]
    assert "active_students_count" in data["summary"]
    assert "class_average_score" in data["summary"]
    assert "pass_rate" in data["summary"]
    assert "mastery_distribution" in data["summary"]

    assert "students" in data
    assert isinstance(data["students"], list)

    assert "objectives_analysis" in data
    assert isinstance(data["objectives_analysis"], list)

    assert "available_packs" in data
    assert isinstance(data["available_packs"], list)

    assert "recent_attempts" in data
    assert isinstance(data["recent_attempts"], list)

def test_teacher_student_detail_report(client, db):
    """Teacher can retrieve an individual student's diagnostic dossier."""
    student_user, _ = create_test_user(db, role="student")
    _, teacher_token = create_test_user(db, role="teacher")

    # Add a mock quiz attempt for this student
    pack = db.query(LearningPack).first()
    if pack:
        attempt = StudentQuizAttempt(
            student_id=student_user.id,
            pack_id=pack.id,
            total_questions=4,
            correct_count=3,
            score_percentage=75.0,
            answers_json='{"q1": "A", "q2": "B"}'
        )
        db.add(attempt)
        db.commit()

    res = client.get(
        f"/api/v1/teacher/analytics/student/{student_user.id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res.status_code == 200
    detail = res.json()
    assert "student" in detail
    assert detail["student"]["student_id"] == student_user.id
    assert detail["student"]["name"] == student_user.name
    assert "attempts" in detail
    assert "objectives" in detail

def test_teacher_analytics_pack_filtering(client, db):
    """Teacher can filter analytics by a specific learning pack."""
    _, teacher_token = create_test_user(db, role="teacher")
    pack = db.query(LearningPack).first()
    if pack:
        res = client.get(
            f"/api/v1/teacher/analytics/overview?pack_id={pack.id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["selected_pack_id"] == pack.id
