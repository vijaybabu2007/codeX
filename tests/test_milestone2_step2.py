import os
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.source import SourceDocument, SourceVersion
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.pack import LearningPack, GeneratedAsset, AssetVersion
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.models.validation import ValidationReport
from backend.models.decision import TeacherDecision
from backend.schemas.contract import ContractCreate, ObjectiveItem
from backend.schemas.decision import TeacherDecisionCreate
from backend.services.source_service import create_source_document_and_version
from backend.services.contract_service import create_objective_contract
from backend.services.pack_service import (
    edit_quiz_question,
    diff_quiz_question_versions,
    get_pack_details,
    serialize_quiz_question
)
from backend.services.decision_service import record_question_version_decision
from backend.services.student_service import get_student_approved_projection, score_student_quiz

TEST_DB_URL = "sqlite:///./test_milestone2_step2.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def cleanup_m2_s2_test_db():
    yield
    test_engine.dispose()
    if os.path.exists("./test_milestone2_step2.db"):
        try:
            os.remove("./test_milestone2_step2.db")
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
        question_text="In which organelle does cellular respiration primarily occur?",
        options_json=json.dumps(["Chloroplast", "Mitochondria", "Endoplasmic Reticulum", "Vacuole"]),
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


# TEST 1: Warning acknowledgement persists
def test_1_warning_acknowledgement_persists(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack
    v1_id = q3.active_version_id

    # Add a non-critical warning report
    warn_rep = ValidationReport(
        question_version_id=v1_id,
        affected_entity_id=v1_id,
        validation_type="duplicate",
        severity="WARNING",
        rule_code="NEAR_DUPLICATE_WARNING",
        message="Item has conceptual similarity to classroom practice set",
        is_blocking=False
    )
    db_session.add(warn_rep)
    db_session.commit()

    # Teacher acknowledges warning and approves
    decision = record_question_version_decision(
        db_session, v1_id,
        TeacherDecisionCreate(
            action="APPROVED",
            acknowledged_warning_ids=["NEAR_DUPLICATE_WARNING"],
            teacher_notes="Acknowledged: terminology verified with curriculum standard"
        )
    )

    assert decision is not None
    assert decision.action == "APPROVED"
    assert "NEAR_DUPLICATE_WARNING" in decision.acknowledged_warning_ids_json
    assert "Acknowledged: terminology verified" in decision.teacher_notes
    assert decision.timestamp is not None

    # Verify persisted in database
    saved = db_session.query(TeacherDecision).filter(TeacherDecision.id == decision.id).first()
    assert saved is not None
    ack_list = json.loads(saved.acknowledged_warning_ids_json)
    assert "NEAR_DUPLICATE_WARNING" in ack_list


# TEST 2: Critical warning still blocks normal approval
def test_2_critical_warning_still_blocks_normal_approval(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    # Edit Q3 to introduce key mismatch
    res = edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="Defective question",
        options=["Option A", "Option B", "Option C"],
        correct_answer="Missing Option Z"
    )
    v2_id = res["active_version_id"]

    # Verify critical validation was generated
    crit_report = db_session.query(ValidationReport).filter(
        ValidationReport.question_version_id == v2_id,
        ValidationReport.severity == "CRITICAL"
    ).first()
    assert crit_report is not None
    assert crit_report.rule_code == "KEY_INTEGRITY_MISMATCH"

    # Normal approval must be rejected
    with pytest.raises(ValueError, match="Approval blocked: Critical validation error"):
        record_question_version_decision(
            db_session, v2_id, TeacherDecisionCreate(action="APPROVED", acknowledged_warning_ids=[])
        )


# TEST 3: Manual correction creates a new immutable version
def test_3_manual_correction_creates_new_immutable_version(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    all_vers_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q3.id).all()
    assert len(all_vers_before) == 1

    res = edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="How is energy released in mitochondria during respiration?",
        options=["As glucose", "As ATP", "As lipids", "As starch"],
        correct_answer="As ATP",
        rationale="Cellular respiration synthesizes ATP as the universal cellular energy currency."
    )

    all_vers_after = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q3.id).all()
    assert len(all_vers_after) == 2
    assert res["version_number"] == 2
    assert q3.active_version_id == res["active_version_id"]


# TEST 4: Historical version remains unchanged
def test_4_historical_version_remains_unchanged(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack
    v1_record_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q3.id).first()
    v1_id = v1_record_before.id
    v1_stem = v1_record_before.question_text
    v1_opts = v1_record_before.options_json
    v1_ans = v1_record_before.correct_answer

    edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="Brand new question text",
        options=["X", "Y", "Z", "W"],
        correct_answer="X"
    )

    v1_record_after = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == v1_id).first()
    assert v1_record_after.version_number == 1
    assert v1_record_after.question_text == v1_stem
    assert v1_record_after.options_json == v1_opts
    assert v1_record_after.correct_answer == v1_ans


# TEST 5: Edited version starts as DRAFT
def test_5_edited_version_starts_as_draft(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    # Approve Q3 v1 first
    record_question_version_decision(db_session, q3.active_version_id, TeacherDecisionCreate(action="APPROVED", acknowledged_warning_ids=[]))

    res = edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="Edited Q3 text",
        options=["A", "B", "C", "D"],
        correct_answer="A"
    )

    assert res["review_status"] == "DRAFT"
    new_v = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == res["active_version_id"]).first()
    assert new_v.review_status == "DRAFT"


# TEST 6: Edited version is validated
def test_6_edited_version_is_validated(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    # 1. Valid edit sets verified grounding status
    res = edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="What cellular organelle generates ATP?",
        options=["Chloroplast", "Mitochondria", "Ribosome", "Golgi"],
        correct_answer="Mitochondria"
    )
    v2 = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == res["active_version_id"]).first()
    assert v2.grounding_status == "VERIFIED"

    # 2. Edit with invalid objective triggers objective alignment validation report
    res_inv = edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="What cellular organelle generates ATP?",
        options=["Chloroplast", "Mitochondria", "Ribosome", "Golgi"],
        correct_answer="Mitochondria",
        objective_ids=["INVALID_LO_CODE_99"]
    )
    v3_id = res_inv["active_version_id"]
    val_reports = db_session.query(ValidationReport).filter(ValidationReport.question_version_id == v3_id).all()
    assert len(val_reports) > 0
    assert any(r.rule_code == "ALIGNMENT_UNKNOWN_CODE" for r in val_reports)


# TEST 7: Student endpoint hides edited DRAFT
def test_7_student_endpoint_hides_edited_draft(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="Secret draft question text",
        options=["A", "B", "C", "D"],
        correct_answer="A"
    )

    student_res = get_student_approved_projection(db_session, pack.id)
    assert len(student_res.quiz_questions) == 2
    student_q_ids = [q.id for q in student_res.quiz_questions]
    assert q3.id not in student_q_ids
    for q in student_res.quiz_questions:
        assert q.question_text != "Secret draft question text"


# TEST 8: Approved edited version becomes visible
def test_8_approved_edited_version_becomes_visible(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    res = edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="Teacher finalized question stem",
        options=["Opt 1", "Opt 2", "Opt 3", "Opt 4"],
        correct_answer="Opt 1"
    )

    # Approve the newly edited version
    record_question_version_decision(
        db_session, res["active_version_id"],
        TeacherDecisionCreate(action="APPROVED", acknowledged_warning_ids=[])
    )

    student_res = get_student_approved_projection(db_session, pack.id)
    assert len(student_res.quiz_questions) == 3
    q3_item = next(q for q in student_res.quiz_questions if q.id == q3.id)
    assert q3_item.question_text == "Teacher finalized question stem"
    assert q3_item.options == ["Opt 1", "Opt 2", "Opt 3", "Opt 4"]


# TEST 9: Version diff contains changed fields
def test_9_version_diff_contains_changed_fields(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    edit_quiz_question(
        db=db_session,
        question_id=q3.id,
        question_text="Different question stem?",
        options=["Alpha", "Beta", "Gamma", "Delta"],
        correct_answer="Alpha",
        rationale="New rationale distinguishing biological pathways"
    )

    diff = diff_quiz_question_versions(db_session, q3.id, v1_number=1, v2_number=2)
    assert diff["has_changes"] is True
    assert "question_text" in diff["changed_fields"]
    assert "options" in diff["changed_fields"]
    assert "correct_answer" in diff["changed_fields"]
    assert "rationale" in diff["changed_fields"]
    assert diff["field_diffs"]["question_text"]["changed"] is True
    assert diff["v1"]["version_number"] == 1
    assert diff["v2"]["version_number"] == 2


# TEST 10: Student quiz scoring works
def test_10_student_quiz_scoring_works(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    # Approve Q3 so all 3 questions are in the approved student projection
    record_question_version_decision(
        db_session, q3.active_version_id,
        TeacherDecisionCreate(action="APPROVED", acknowledged_warning_ids=[])
    )

    # Submit 2 correct answers (Q1: Chloroplasts, Q2: ATP and NADPH) and 1 wrong answer (Q3: Chloroplast instead of Mitochondria)
    answers = {
        q1.id: "Chloroplasts",
        q2.id: "ATP and NADPH",
        q3.id: "Chloroplast"
    }

    score_res = score_student_quiz(db_session, pack.id, answers)
    assert score_res.total_questions == 3
    assert score_res.correct_count == 2
    assert score_res.score_percentage == 66.7

    q1_result = next(r for r in score_res.results if r.question_id == q1.id)
    assert q1_result.is_correct is True
    assert q1_result.correct_answer == "Chloroplasts"

    q3_result = next(r for r in score_res.results if r.question_id == q3.id)
    assert q3_result.is_correct is False
    assert q3_result.correct_answer == "Mitochondria"


# TEST 11: Student endpoint never exposes teacher metadata
def test_11_student_endpoint_never_exposes_teacher_metadata(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    # Add teacher notes and validations to Q1 and Q2
    db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q1.id).update(
        {"teacher_notes": "Internal teacher pedagogical reminder: watch for distractor C confusion"}
    )
    db_session.commit()

    student_res = get_student_approved_projection(db_session, pack.id)
    res_dict = student_res.model_dump()

    # Verify no teacher metadata exists in the serialized student model
    json_str = json.dumps(res_dict)
    assert "Internal teacher pedagogical reminder" not in json_str
    assert "teacher_notes" not in res_dict
    for q in res_dict.get("quiz_questions", []):
        assert "teacher_notes" not in q
        assert "validations" not in q
        assert "decisions" not in q
        assert "grounding_status" not in q


# TEST 12: Existing sibling questions remain unchanged
def test_12_existing_sibling_questions_remain_unchanged(db_session, sample_quiz_pack):
    pack, q1, q2, q3, src = sample_quiz_pack

    q1_ver_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q1.id).first()
    q2_ver_before = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q2.id).first()

    # Modify Q3 multiple times
    edit_quiz_question(db=db_session, question_id=q3.id, question_text="Edit Q3 once", options=["A", "B"], correct_answer="A")
    edit_quiz_question(db=db_session, question_id=q3.id, question_text="Edit Q3 twice", options=["C", "D"], correct_answer="C")

    # Verify sibling versions remain untouched
    q1_vers = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q1.id).all()
    q2_vers = db_session.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q2.id).all()

    assert len(q1_vers) == 1
    assert q1_vers[0].id == q1_ver_before.id
    assert q1_vers[0].question_text == q1_ver_before.question_text
    assert q1_vers[0].review_status == "APPROVED"

    assert len(q2_vers) == 1
    assert q2_vers[0].id == q2_ver_before.id
    assert q2_vers[0].question_text == q2_ver_before.question_text
    assert q2_vers[0].review_status == "APPROVED"
