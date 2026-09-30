import os
import json
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.source import SourceDocument, SourceVersion
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.pack import LearningPack, GeneratedAsset, AssetVersion
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.models.validation import ValidationReport
from backend.models.decision import TeacherDecision
from backend.schemas.generation import GeneratedQuizQuestion
from backend.schemas.contract import ContractCreate, ObjectiveItem
from backend.schemas.decision import TeacherDecisionCreate
from backend.services.source_service import create_source_document_and_version
from backend.services.contract_service import create_objective_contract
from backend.services.pack_service import regenerate_quiz_question, get_pack_details, serialize_quiz_question
from backend.services.decision_service import record_question_version_decision
from backend.services.student_service import get_student_approved_projection

TEST_DB_URL = "sqlite:///./test_milestone2.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def cleanup_m2_test_db():
    yield
    test_engine.dispose()
    if os.path.exists("./test_milestone2.db"):
        try:
            os.remove("./test_milestone2.db")
        except Exception:
            pass

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def sample_quiz_pack(db_session):
    """
    Creates a sample pack with 3 quiz questions:
    - Q1: APPROVED
    - Q2: APPROVED
    - Q3: DRAFT
    """
    source_text = (
        "Photosynthesis takes place primarily in chloroplasts containing chlorophyll pigments. "
        "The light reactions produce ATP and NADPH. "
        "Cellular respiration occurs in mitochondria, releasing energy in the form of ATP."
    )
    src = create_source_document_and_version(db_session, "Bio Curriculum", source_text)

    contract = create_objective_contract(
        db_session,
        ContractCreate(
            source_version_id=src.id,
            title="Bio Energetics",
            target_learner_level="Grade 10",
            expected_difficulty="Medium",
            objectives=[
                ObjectiveItem(code="LO-01", description="Explain chloroplast role in photosynthesis", bloom_level="Understand"),
                ObjectiveItem(code="LO-02", description="Describe ATP production in mitochondria", bloom_level="Apply")
            ]
        )
    )

    pack = LearningPack(contract_id=contract.id, source_version_id=src.id)
    db_session.add(pack)
    db_session.flush()

    quiz_asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="formative_quiz")
    db_session.add(quiz_asset)
    db_session.flush()

    # Question 1: APPROVED
    q1 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=1)
    db_session.add(q1)
    db_session.flush()

    q1_v1 = QuizQuestionVersion(
        question_id=q1.id,
        source_version_id=src.id,
        version_number=1,
        question_text="Where does photosynthesis primarily take place?",
        options_json=json.dumps(["Mitochondria", "Chloroplasts", "Ribosomes", "Nucleus"]),
        correct_answer="Chloroplasts",
        objective_ids_json=json.dumps(["LO-01"]),
        supporting_quote="Photosynthesis takes place primarily in chloroplasts containing chlorophyll pigments.",
        grounding_status="VERIFIED",
        review_status="APPROVED",
        model_identifier="test-model"
    )
    db_session.add(q1_v1)
    db_session.flush()
    q1.active_version_id = q1_v1.id

    # Question 2: APPROVED
    q2 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=2)
    db_session.add(q2)
    db_session.flush()

    q2_v1 = QuizQuestionVersion(
        question_id=q2.id,
        source_version_id=src.id,
        version_number=1,
        question_text="What do the light reactions produce?",
        options_json=json.dumps(["Glucose only", "ATP and NADPH", "Carbon dioxide", "Water"]),
        correct_answer="ATP and NADPH",
        objective_ids_json=json.dumps(["LO-01"]),
        supporting_quote="The light reactions produce ATP and NADPH.",
        grounding_status="VERIFIED",
        review_status="APPROVED",
        model_identifier="test-model"
    )
    db_session.add(q2_v1)
    db_session.flush()
    q2.active_version_id = q2_v1.id

    # Question 3: DRAFT
    q3 = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=3)
    db_session.add(q3)
    db_session.flush()

    q3_v1 = QuizQuestionVersion(
        question_id=q3.id,
        source_version_id=src.id,
        version_number=1,
        question_text="Where does cellular respiration occur?",
        options_json=json.dumps(["Chloroplasts", "Mitochondria", "Vacuoles", "Golgi"]),
        correct_answer="Mitochondria",
        objective_ids_json=json.dumps(["LO-02"]),
        supporting_quote="Cellular respiration occurs in mitochondria, releasing energy in the form of ATP.",
        grounding_status="VERIFIED",
        review_status="DRAFT",
        model_identifier="test-model"
    )
    db_session.add(q3_v1)
    db_session.flush()
    q3.active_version_id = q3_v1.id

    db_session.commit()
    return pack, q1, q2, q3, src

# MOCK return for surgical regeneration
def mock_regenerate_q3_v2(*args, **kwargs):
    return GeneratedQuizQuestion(
        question_id="Q3",
        question="Which organelle releases energy as ATP during cellular respiration?",
        options=["Chloroplasts", "Mitochondria", "Ribosomes", "Endoplasmic Reticulum"],
        correct_answer="Mitochondria",
        objective_ids=["LO-02"],
        supporting_quote="Cellular respiration occurs in mitochondria, releasing energy in the form of ATP.",
        cognitive_level="Understand"
    ), "PROMPT_SNAPSHOT", "mock-groq-model"

def mock_regenerate_q3_v3(*args, **kwargs):
    return GeneratedQuizQuestion(
        question_id="Q3",
        question="What cellular process occurring in mitochondria yields energy in the form of ATP?",
        options=["Photosynthesis", "Cellular respiration", "Fermentation", "Transpiration"],
        correct_answer="Cellular respiration",
        objective_ids=["LO-02"],
        supporting_quote="Cellular respiration occurs in mitochondria, releasing energy in the form of ATP.",
        cognitive_level="Apply"
    ), "PROMPT_SNAPSHOT_V3", "mock-groq-model"


# TEST 1: Single question regeneration creates a new version
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_1_single_question_regeneration_creates_new_version(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    result = regenerate_quiz_question(db_session, q3.id, teacher_notes="Make it clearer", reason="Improve wording")
    assert result["status"] == "success"
    assert result["version_number"] == 2

    # Verify Q3 has 2 versions in DB
    versions = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q3.id).all()
    assert len(versions) == 2
    version_numbers = {v.version_number for v in versions}
    assert version_numbers == {1, 2}

    # Verify Q3 active_version_id points to v2
    q3_db = db_session.query(QuizQuestion).filter(QuizQuestion.id == q3.id).first()
    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == q3_db.active_version_id).first()
    assert v2.version_number == 2
    assert v2.question_text == "Which organelle releases energy as ATP during cellular respiration?"


# TEST 2: Previous question version remains unchanged
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_2_previous_version_remains_unchanged(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack
    v1_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q3.id, QuizQuestionVersion.version_number == 1).first()
    v1_text_before = v1_before.question_text
    v1_options_before = v1_before.options_json
    v1_id = v1_before.id

    regenerate_quiz_question(db_session, q3.id, teacher_notes="Regen Q3", reason="Test reason")

    v1_after = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == v1_id).first()
    assert v1_after is not None
    assert v1_after.version_number == 1
    assert v1_after.question_text == v1_text_before
    assert v1_after.options_json == v1_options_before


# TEST 3: Approved questions remain unchanged
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_3_approved_questions_remain_unchanged(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    q1_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q1.id).first()
    q2_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q2.id).first()
    q1_text = q1_before.question_text
    q1_status = q1_before.review_status
    q2_text = q2_before.question_text
    q2_status = q2_before.review_status

    assert q1_status == "APPROVED"
    assert q2_status == "APPROVED"

    # Regenerate Q3
    regenerate_quiz_question(db_session, q3.id, teacher_notes="Update Q3", reason="Testing approved protection")

    # Verify Q1 is completely untouched
    q1_after = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q1.id).all()
    assert len(q1_after) == 1
    assert q1_after[0].question_text == q1_text
    assert q1_after[0].review_status == "APPROVED"

    # Verify Q2 is completely untouched
    q2_after = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q2.id).all()
    assert len(q2_after) == 1
    assert q2_after[0].question_text == q2_text
    assert q2_after[0].review_status == "APPROVED"


# TEST 4: New version preserves source_version_id
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_4_new_version_preserves_source_version_id(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    result = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes", reason="Reason")
    assert result["source_version_id"] == src.id

    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == result["active_version_id"]).first()
    assert v2.source_version_id == src.id


# TEST 5: New version preserves objective alignment
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_5_new_version_preserves_objective_alignment(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    result = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes", reason="Reason")
    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == result["active_version_id"]).first()
    obj_ids = json.loads(v2.objective_ids_json)
    assert obj_ids == ["LO-02"]

    # Check validation reports on v2 for alignment
    reports = db_session.query(ValidationReport).filter(
        ValidationReport.question_version_id == v2.id,
        ValidationReport.validation_type == "ALIGNMENT"
    ).all()
    # Zero warnings when objective code is valid
    assert len(reports) == 0


# TEST 6: New version is validated
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_6_new_version_is_validated(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    result = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes", reason="Reason")
    v2_id = result["active_version_id"]

    reports = db_session.query(ValidationReport).filter(ValidationReport.question_version_id == v2_id).all()
    # Reports should exist or key integrity should pass
    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == v2_id).first()
    assert v2.grounding_status == "VERIFIED"


# TEST 7: New version starts as DRAFT
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_7_new_version_starts_as_draft(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    result = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes", reason="Reason")
    assert result["review_status"] == "DRAFT"

    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == result["active_version_id"]).first()
    assert v2.review_status == "DRAFT"


# TEST 8: Draft regenerated question is hidden from Student Mode
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_8_draft_question_hidden_from_student_mode(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    # Before: Q1 APPROVED, Q2 APPROVED, Q3 DRAFT
    student_res_before = get_student_approved_projection(db_session, pack.id)
    # Only 2 approved questions
    assert len(student_res_before.quiz_questions) == 2
    student_q_ids = [q.id for q in student_res_before.quiz_questions]
    assert q1.id in student_q_ids
    assert q2.id in student_q_ids
    assert q3.id not in student_q_ids

    # Regenerate Q3 -> creates Q3 v2 (DRAFT)
    regenerate_quiz_question(db_session, q3.id, teacher_notes="Regen", reason="Draft check")

    # After regeneration: Q3 v2 is STILL DRAFT, so student mode still has only 2 questions!
    student_res_after = get_student_approved_projection(db_session, pack.id)
    assert len(student_res_after.quiz_questions) == 2
    assert q3.id not in [q.id for q in student_res_after.quiz_questions]

    # Teacher approves Q3 v2
    q3_db = db_session.query(QuizQuestion).filter(QuizQuestion.id == q3.id).first()
    record_question_version_decision(db_session, q3_db.active_version_id, TeacherDecisionCreate(action="APPROVED"))

    # Now Student Mode reveals all 3 questions!
    student_res_approved = get_student_approved_projection(db_session, pack.id)
    assert len(student_res_approved.quiz_questions) == 3
    assert q3.id in [q.id for q in student_res_approved.quiz_questions]


# TEST 9: Repeated regeneration creates v3, v4, etc.
def test_m2_9_repeated_regeneration_creates_subsequent_versions(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    with patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2):
        res_v2 = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes v2", reason="Reason v2")
        assert res_v2["version_number"] == 2

    with patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v3):
        res_v3 = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes v3", reason="Reason v3")
        assert res_v3["version_number"] == 3

    with patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2):
        res_v4 = regenerate_quiz_question(db_session, q3.id, teacher_notes="Notes v4", reason="Reason v4")
        assert res_v4["version_number"] == 4

    # Verify all 4 versions exist in database
    all_versions = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q3.id).order_by(QuizQuestionVersion.version_number.asc()).all()
    assert len(all_versions) == 4
    assert [v.version_number for v in all_versions] == [1, 2, 3, 4]


# TEST 10: Teacher regeneration notes are persisted
@patch("backend.services.pack_service.regenerate_single_quiz_question", side_effect=mock_regenerate_q3_v2)
def test_m2_10_teacher_notes_persisted(mock_llm, db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    custom_notes = "Clarify that ATP is energy currency produced in mitochondria."
    custom_reason = "Distractors were ambiguous."

    result = regenerate_quiz_question(db_session, q3.id, teacher_notes=custom_notes, reason=custom_reason)

    # Check QuizQuestionVersion
    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == result["active_version_id"]).first()
    assert v2.teacher_notes == custom_notes

    # Check TeacherDecision record
    decision = db_session.query(TeacherDecision).filter(TeacherDecision.question_version_id == v2.id).first()
    assert decision is not None
    assert decision.action == "REGENERATED"
    assert custom_notes in decision.teacher_notes
