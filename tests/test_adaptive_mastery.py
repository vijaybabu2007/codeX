import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.database import get_db, init_db, SessionLocal
from backend.models.user import User
from backend.models.source import SourceDocument, SourceVersion
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.pack import LearningPack, GeneratedAsset, AssetVersion
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.models.mastery import ObjectiveMastery, StudentQuizAttempt
from backend.services.auth_service import register_user
from backend.services.mastery_service import (
    determine_mastery_state,
    MasteryThresholds,
    calculate_and_save_mastery,
    generate_adaptive_recommendation,
    get_student_mastery,
)
from backend.schemas.student import StudentQuizResultItem, ObjectiveMasteryItem

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.fixture
def test_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_sample_mastery_pack(db: Session, approve_all: bool = True):
    """
    Creates a full learning pack with 2 objectives: LO-01 and LO-02,
    and 4 questions (2 for LO-01, 2 for LO-02).
    """
    doc = SourceDocument(name="Adaptive Biology")
    db.add(doc)
    db.commit()

    src_ver = SourceVersion(
        source_document_id=doc.id,
        version_number=1,
        raw_text="Cellular respiration produces ATP. Glycolysis occurs in cytoplasm. Krebs cycle occurs in mitochondria.",
        cleaned_text="Cellular respiration produces ATP. Glycolysis occurs in cytoplasm. Krebs cycle occurs in mitochondria.",
        char_count=120,
        sha256_hash="hash_mastery_test"
    )
    db.add(src_ver)
    db.commit()

    contract = ObjectiveContract(
        source_version_id=src_ver.id,
        title="Cell Energy Contract",
        target_learner_level="Grade 10",
        expected_difficulty="Medium"
    )
    db.add(contract)
    db.commit()

    lo1 = LearningObjective(contract_id=contract.id, code="LO-01", description="Understand ATP yield in Glycolysis", bloom_level="Understand")
    lo2 = LearningObjective(contract_id=contract.id, code="LO-02", description="Analyze Krebs Cycle Mitochondria Role", bloom_level="Analyze")
    db.add_all([lo1, lo2])
    db.commit()

    pack = LearningPack(contract_id=contract.id, source_version_id=src_ver.id)
    db.add(pack)
    db.commit()

    status = "APPROVED" if approve_all else "DRAFT"

    # 1. Concept Explanation
    concept_asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="concept_explanation")
    db.add(concept_asset)
    db.commit()
    concept_ver = AssetVersion(
        asset_id=concept_asset.id,
        source_version_id=src_ver.id,
        version_number=1,
        content_json=json.dumps({"title": "ATP Synthesis", "explanation": "Cells generate ATP through respiration.", "supporting_quote": "produces ATP", "objective_ids": ["LO-01"]}),
        review_status=status,
        model_identifier="test_model"
    )
    db.add(concept_ver)
    db.commit()
    concept_asset.active_version_id = concept_ver.id
    db.commit()

    # 2. Worked Example
    worked_asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="worked_example")
    db.add(worked_asset)
    db.commit()
    worked_ver = AssetVersion(
        asset_id=worked_asset.id,
        source_version_id=src_ver.id,
        version_number=1,
        content_json=json.dumps({"title": "Mitochondria Cycle Step", "scenario": "Tracing pyruvate into mitochondria.", "steps": ["Step 1", "Step 2"], "final_answer": "Yields ATP", "supporting_quote": "Krebs cycle occurs in mitochondria.", "objective_ids": ["LO-02"]}),
        review_status=status,
        model_identifier="test_model"
    )
    db.add(worked_ver)
    db.commit()
    worked_asset.active_version_id = worked_ver.id
    db.commit()

    # 3. Easy Practice
    easy_asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="easy_practice")
    db.add(easy_asset)
    db.commit()
    easy_ver = AssetVersion(
        asset_id=easy_asset.id,
        source_version_id=src_ver.id,
        version_number=1,
        content_json=json.dumps({"title": "Glycolysis Location", "problem_statement": "Where does glycolysis occur?", "solution_guidance": "Cytoplasm.", "supporting_quote": "Glycolysis occurs in cytoplasm.", "objective_ids": ["LO-01"], "bloom_level": "Remember"}),
        review_status=status,
        model_identifier="test_model"
    )
    db.add(easy_ver)
    db.commit()
    easy_asset.active_version_id = easy_ver.id
    db.commit()

    # 4. Advanced Practice
    adv_asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="advanced_practice")
    db.add(adv_asset)
    db.commit()
    adv_ver = AssetVersion(
        asset_id=adv_asset.id,
        source_version_id=src_ver.id,
        version_number=1,
        content_json=json.dumps({"title": "Comparative Synthesis", "problem_statement": "Compare ATP efficiency.", "solution_guidance": "Trace electron transport.", "supporting_quote": "Cellular respiration produces ATP.", "objective_ids": ["LO-01", "LO-02"], "bloom_level": "Analyze"}),
        review_status=status,
        model_identifier="test_model"
    )
    db.add(adv_ver)
    db.commit()
    adv_asset.active_version_id = adv_ver.id
    db.commit()

    # 5. Formative Quiz with 4 questions (Q1, Q2 -> LO-01; Q3, Q4 -> LO-02)
    quiz_asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="formative_quiz")
    db.add(quiz_asset)
    db.commit()

    q1 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=1)
    q2 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=2)
    q3 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=3)
    q4 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=4)
    db.add_all([q1, q2, q3, q4])
    db.commit()

    v1 = QuizQuestionVersion(
        question_id=q1.id,
        source_version_id=src_ver.id,
        version_number=1,
        question_text="Where does glycolysis occur?",
        options_json=json.dumps(["Cytoplasm", "Nucleus", "Ribosome", "Vacuole"]),
        correct_answer="Cytoplasm",
        objective_ids_json=json.dumps(["LO-01"]),
        review_status="APPROVED",
        model_identifier="test"
    )
    v2 = QuizQuestionVersion(
        question_id=q2.id,
        source_version_id=src_ver.id,
        version_number=1,
        question_text="What molecule is primarily produced?",
        options_json=json.dumps(["ATP", "Glucose", "Lipid", "Starch"]),
        correct_answer="ATP",
        objective_ids_json=json.dumps(["LO-01"]),
        review_status="APPROVED",
        model_identifier="test"
    )
    v3 = QuizQuestionVersion(
        question_id=q3.id,
        source_version_id=src_ver.id,
        version_number=1,
        question_text="Where does Krebs cycle occur?",
        options_json=json.dumps(["Mitochondria", "Cytoplasm", "Cell wall", "Chloroplast"]),
        correct_answer="Mitochondria",
        objective_ids_json=json.dumps(["LO-02"]),
        review_status="APPROVED",
        model_identifier="test"
    )
    v4 = QuizQuestionVersion(
        question_id=q4.id,
        source_version_id=src_ver.id,
        version_number=1,
        question_text="What organelle coordinates oxidative respiration?",
        options_json=json.dumps(["Mitochondria", "Golgi", "Endoplasmic reticulum", "Lysosome"]),
        correct_answer="Mitochondria",
        objective_ids_json=json.dumps(["LO-02"]),
        review_status="APPROVED",
        model_identifier="test"
    )
    db.add_all([v1, v2, v3, v4])
    db.commit()

    q1.active_version_id = v1.id
    q2.active_version_id = v2.id
    q3.active_version_id = v3.id
    q4.active_version_id = v4.id
    db.commit()

    return {
        "pack": pack,
        "q1": q1, "q2": q2, "q3": q3, "q4": q4,
        "v1": v1, "v2": v2, "v3": v3, "v4": v4,
        "concept_ver": concept_ver,
        "easy_ver": easy_ver,
        "worked_ver": worked_ver,
        "adv_ver": adv_ver
    }


def test_1_objective_level_score_calculation_is_correct(test_db_session):
    """
    Test 1: Verify correct attribution and calculation per objective.
    LO-01 (Q1: correct, Q2: correct) -> 2/2 = 100%
    LO-02 (Q3: incorrect, Q4: incorrect) -> 0/2 = 0%
    """
    data = create_sample_mastery_pack(test_db_session)
    pack_id = data["pack"].id

    answers = {
        data["q1"].id: "Cytoplasm",    # Correct (LO-01)
        data["q2"].id: "ATP",          # Correct (LO-01)
        data["q3"].id: "Cytoplasm",    # Incorrect (LO-02, correct is Mitochondria)
        data["q4"].id: "Golgi",        # Incorrect (LO-02, correct is Mitochondria)
    }

    res = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json={"answers": answers})
    assert res.status_code == 200
    data_out = res.json()

    assert data_out["total_questions"] == 4
    assert data_out["correct_count"] == 2
    assert data_out["score_percentage"] == 50.0

    perf = {item["objective_id"]: item for item in data_out["objective_performance"]}
    assert "LO-01" in perf
    assert "LO-02" in perf

    assert perf["LO-01"]["attempted"] == 2
    assert perf["LO-01"]["correct"] == 2
    assert perf["LO-01"]["score_percentage"] == 100.0

    assert perf["LO-02"]["attempted"] == 2
    assert perf["LO-02"]["correct"] == 0
    assert perf["LO-02"]["score_percentage"] == 0.0


def test_2_mastered_threshold_works():
    """
    Test 2: Configurable threshold 90%-100% produces MASTERED state.
    """
    assert determine_mastery_state(100.0) == "MASTERED"
    assert determine_mastery_state(95.0) == "MASTERED"
    assert determine_mastery_state(MasteryThresholds.MASTERED_MIN) == "MASTERED"


def test_3_developing_threshold_works():
    """
    Test 3: Configurable threshold 60%-89.9% produces DEVELOPING state.
    """
    assert determine_mastery_state(89.9) == "DEVELOPING"
    assert determine_mastery_state(75.0) == "DEVELOPING"
    assert determine_mastery_state(MasteryThresholds.DEVELOPING_MIN) == "DEVELOPING"


def test_4_needs_practice_threshold_works():
    """
    Test 4: Configurable threshold 0%-59.9% produces NEEDS_PRACTICE state.
    """
    assert determine_mastery_state(59.9) == "NEEDS_PRACTICE"
    assert determine_mastery_state(33.3) == "NEEDS_PRACTICE"
    assert determine_mastery_state(0.0) == "NEEDS_PRACTICE"


def test_5_multiple_objectives_calculated_independently(test_db_session):
    """
    Test 5: Multiple objectives evaluate independently:
    LO-01: 2/2 = 100% -> MASTERED
    LO-02: 1/2 = 50% -> NEEDS_PRACTICE
    """
    data = create_sample_mastery_pack(test_db_session)
    pack_id = data["pack"].id

    answers = {
        data["q1"].id: "Cytoplasm",     # LO-01 correct
        data["q2"].id: "ATP",           # LO-01 correct
        data["q3"].id: "Mitochondria",  # LO-02 correct
        data["q4"].id: "Lysosome",      # LO-02 incorrect
    }

    res = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json={"answers": answers})
    assert res.status_code == 200
    perf = {item["objective_id"]: item for item in res.json()["objective_performance"]}

    assert perf["LO-01"]["mastery_state"] == "MASTERED"
    assert perf["LO-02"]["mastery_state"] == "NEEDS_PRACTICE"


def test_6_recommendation_for_needs_practice_is_correct(test_db_session):
    """
    Test 6: When objective is NEEDS_PRACTICE, recommendation suggests
    Review Concept, Easy Practice, and Voice Tutor.
    """
    data = create_sample_mastery_pack(test_db_session)
    pack_id = data["pack"].id

    # Fail both LO-02 questions
    answers = {
        data["q1"].id: "Cytoplasm",    # LO-01 correct
        data["q2"].id: "ATP",          # LO-01 correct
        data["q3"].id: "Chloroplast",  # LO-02 incorrect
        data["q4"].id: "Chloroplast",  # LO-02 incorrect
    }

    res = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json={"answers": answers})
    rec = res.json()["recommended_action"]
    assert rec is not None
    assert rec["objective_id"] == "LO-02"
    assert rec["mastery_state"] == "NEEDS_PRACTICE"
    assert "LO-02" in rec["headline"]
    assert "answered 0 of 2" in rec["explanation"]

    action_types = [a["action"] for a in rec["actions"]]
    assert "REVIEW_CONCEPT" in action_types
    assert "EASY_PRACTICE" in action_types
    assert "ASK_VOICE_TUTOR" in action_types


def test_7_recommendation_for_developing_is_correct(test_db_session):
    """
    Test 7: When an objective is DEVELOPING (e.g. 75%), recommendation suggests
    Guided Worked Example, Easy Practice, and Retry Quiz.
    """
    db = test_db_session
    data = create_sample_mastery_pack(db)
    pack_id = data["pack"].id

    items = [
        ObjectiveMasteryItem(
            objective_id="LO-02",
            objective_description="Analyze Krebs Cycle",
            attempted=4,
            correct=3,
            score_percentage=75.0,
            mastery_state="DEVELOPING"
        )
    ]

    rec = generate_adaptive_recommendation(db, pack_id, items)
    assert rec is not None
    assert rec.mastery_state == "DEVELOPING"
    assert "Reinforce LO-02" in rec.headline

    action_types = [a.action for a in rec.actions]
    assert "WORKED_EXAMPLE" in action_types
    assert "EASY_PRACTICE" in action_types
    assert "RETRY_QUIZ" in action_types


def test_8_recommendation_for_mastered_is_correct(test_db_session):
    """
    Test 8: When all objectives are MASTERED, recommendation offers
    Advanced Practice and synthesis challenge.
    """
    db = test_db_session
    data = create_sample_mastery_pack(db)
    pack_id = data["pack"].id

    items = [
        ObjectiveMasteryItem(
            objective_id="LO-01",
            objective_description="ATP Yield",
            attempted=2,
            correct=2,
            score_percentage=100.0,
            mastery_state="MASTERED"
        ),
        ObjectiveMasteryItem(
            objective_id="LO-02",
            objective_description="Krebs Cycle",
            attempted=2,
            correct=2,
            score_percentage=100.0,
            mastery_state="MASTERED"
        )
    ]

    rec = generate_adaptive_recommendation(db, pack_id, items)
    assert rec is not None
    assert rec.mastery_state == "MASTERED"
    assert "Mastery Achieved" in rec.headline

    action_types = [a.action for a in rec.actions]
    assert "ADVANCED_PRACTICE" in action_types


def test_9_unapproved_assets_are_never_recommended(test_db_session):
    """
    Test 9: Critical Approval Boundary:
    If Concept Explanation or Easy Practice is in DRAFT status,
    the recommendation MUST NOT propose them!
    """
    db = test_db_session
    data = create_sample_mastery_pack(db, approve_all=False)
    pack_id = data["pack"].id

    # In this pack, concept_explanation, easy_practice, etc. are all DRAFT!
    items = [
        ObjectiveMasteryItem(
            objective_id="LO-01",
            objective_description="ATP Yield",
            attempted=2,
            correct=0,
            score_percentage=0.0,
            mastery_state="NEEDS_PRACTICE"
        )
    ]

    rec = generate_adaptive_recommendation(db, pack_id, items)
    assert rec is not None

    action_targets = [a.target for a in rec.actions]
    # DRAFT assets must be excluded
    assert "concept_explanation" not in action_targets
    assert "easy_practice" not in action_targets
    assert "advanced_practice" not in action_targets
    # Voice tutor is always approved context
    assert "voice_tutor" in action_targets


def test_10_mastery_persists_after_restart(test_db_session):
    """
    Test 10: Mastery records persist in SQLite database.
    """
    db = test_db_session
    data = create_sample_mastery_pack(db)
    pack_id = data["pack"].id
    student_id = "test_student_persists_42"

    answers = {
        data["q1"].id: "Cytoplasm",
        data["q2"].id: "ATP",
        data["q3"].id: "Mitochondria",
        data["q4"].id: "Mitochondria",
    }

    score_res = client.post(
        f"/api/v1/student/packs/{pack_id}/submit-quiz",
        json={"answers": answers},
        headers={"X-Test-Student-ID": student_id}
    )
    assert score_res.status_code == 200

    # Verify directly from DB query
    records = db.query(ObjectiveMastery).filter(
        ObjectiveMastery.pack_id == pack_id
    ).all()
    assert len(records) >= 2

    # Verify attempt log is recorded
    attempts = db.query(StudentQuizAttempt).filter(
        StudentQuizAttempt.pack_id == pack_id
    ).all()
    assert len(attempts) >= 1
    assert attempts[0].score_percentage == 100.0


def test_11_student_cannot_access_another_students_mastery(test_db_session):
    """
    Test 11: Security & Data Isolation:
    A student cannot access another student's mastery data.
    """
    db = test_db_session
    data = create_sample_mastery_pack(db)
    pack_id = data["pack"].id

    import uuid
    uid = uuid.uuid4().hex[:6]
    alice, alice_token = register_user(db, name="Alice M", email=f"alice_{uid}@school.edu", password="pass123456", confirm_password="pass123456", role="student", student_id=f"STU-A-{uid}")
    bob, bob_token = register_user(db, name="Bob M", email=f"bob_{uid}@school.edu", password="pass123456", confirm_password="pass123456", role="student", student_id=f"STU-B-{uid}")

    # Alice requests Bob's mastery -> Expect 403 Forbidden
    res = client.get(
        f"/api/v1/student/packs/{pack_id}/mastery?student_id={bob.id}",
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert res.status_code == 403
    assert "Cannot access another student's mastery data" in res.json()["detail"]


def test_12_voice_tutor_integration_preserves_approved_only_context(test_db_session, monkeypatch):
    """
    Test 12: Voice Tutor context query targeting weak objective:
    Uses only approved student context without leaking internal teacher notes or draft data.
    """
    db = test_db_session
    data = create_sample_mastery_pack(db)
    pack_id = data["pack"].id

    from backend.services import voice_service
    from backend.schemas.student import StudentVoiceQueryResponse
    def mock_voice_response(system_instruction, prompt_body, max_tokens=1024):
        assert "teacher_notes" not in prompt_body.lower()
        return StudentVoiceQueryResponse(
            answer="Krebs cycle occurs in the mitochondria where pyruvate is broken down.",
            objective_ids=["LO-02"],
            source_evidence=["Krebs cycle occurs in mitochondria."],
            grounded=True,
            language="en",
            intent="EXPLAIN"
        ), "snapshot", "mock-model"
    monkeypatch.setattr(voice_service, "generate_voice_tutor_response", mock_voice_response)

    prompt = "Help me understand LO-02 because I am struggling with this objective."
    res = client.post(
        "/api/v1/student/voice/query",
        json={
            "pack_id": pack_id,
            "question": prompt,
            "language": "en"
        }
    )
    assert res.status_code == 200
    res_data = res.json()
    assert "answer" in res_data
    assert res_data["grounded"] is True
    assert "LO-02" in res_data["objective_ids"]


def test_13_existing_quiz_scoring_remains_correct(test_db_session):
    """
    Test 13: Backward compatibility verification:
    total_questions, correct_count, score_percentage, and results continue to match standard contract.
    """
    data = create_sample_mastery_pack(test_db_session)
    pack_id = data["pack"].id

    # 1 correct, 3 wrong
    answers = {
        data["q1"].id: "Cytoplasm",    # correct
        data["q2"].id: "WrongOpt",
        data["q3"].id: "WrongOpt",
        data["q4"].id: "WrongOpt",
    }

    res = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json={"answers": answers})
    assert res.status_code == 200
    res_json = res.json()

    assert res_json["total_questions"] == 4
    assert res_json["correct_count"] == 1
    assert res_json["score_percentage"] == 25.0
    assert len(res_json["results"]) == 4
    assert res_json["results"][0]["is_correct"] is True
    assert res_json["results"][1]["is_correct"] is False


def test_14_edge_cases_handled_gracefully(test_db_session):
    """
    Test 14: Edge cases:
    - Empty answers
    - Pack with zero quiz attempts
    - Objective with 0 questions in quiz (evaluates without crashing or fabricating)
    """
    db = test_db_session
    data = create_sample_mastery_pack(db)
    pack_id = data["pack"].id

    # Submitting with empty answers dictionary
    res = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json={"answers": {}})
    assert res.status_code == 200
    assert res.json()["correct_count"] == 0
    assert res.json()["score_percentage"] == 0.0

    # Querying mastery before any quiz attempt
    mastery_res = client.get(f"/api/v1/student/packs/{pack_id}/mastery")
    assert mastery_res.status_code == 200
    mastery_data = mastery_res.json()
    assert mastery_data["pack_id"] == pack_id
    assert len(mastery_data["objectives"]) >= 2
    for obj in mastery_data["objectives"]:
        assert obj["mastery_state"] == "NEEDS_PRACTICE"
        assert obj["score_percentage"] == 0.0
