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
from backend.services.source_service import create_source_document_and_version
from backend.services.contract_service import create_objective_contract
from backend.schemas.contract import ContractCreate, ObjectiveItem
from backend.services.validation_service import (
    validate_key_integrity,
    validate_answer_key_consistency,
    validate_cognitive_difficulty,
    validate_duplicate_questions,
    validate_answer_leakage,
    validate_grounding_evidence,
    validate_revision_sheet_grounding,
    validate_cross_asset_contradiction,
    validate_terminology_consistency,
    validate_objective_alignment,
    compute_alignment_matrix_and_audit
)
from backend.services.decision_service import record_asset_version_decision
from backend.schemas.decision import TeacherDecisionCreate
from backend.services.student_service import get_student_approved_projection

TEST_DB_URL = "sqlite:///./test_milestone1.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def cleanup_m1_test_db():
    yield
    test_engine.dispose()
    if os.path.exists("./test_milestone1.db"):
        try:
            os.remove("./test_milestone1.db")
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

# TEST 1: Complete 7-asset pack structure
def test_m1_1_complete_7_asset_pack_structure(db_session):
    src = create_source_document_and_version(db_session, "Source", "Photosynthesis produces glucose and oxygen.")
    contract = create_objective_contract(
        db_session,
        ContractCreate(
            source_version_id=src.id, title="Bio", target_learner_level="Grade 10",
            objectives=[ObjectiveItem(code="LO-01", description="Explain equation"), ObjectiveItem(code="LO-02", description="Describe Calvin cycle")]
        )
    )
    pack = LearningPack(contract_id=contract.id, source_version_id=src.id)
    db_session.add(pack)
    db_session.flush()

    asset_types = [
        "concept_explanation", "worked_example", "formative_quiz",
        "quiz_answer_key", "easy_practice", "advanced_practice", "revision_sheet"
    ]
    for atype in asset_types:
        asset = GeneratedAsset(learning_pack_id=pack.id, asset_type=atype)
        db_session.add(asset)
        db_session.flush()
        ver = AssetVersion(
            asset_id=asset.id, source_version_id=src.id, version_number=1,
            content_json=json.dumps({"title": atype, "objective_ids": ["LO-01"]}),
            review_status="DRAFT", model_identifier="gemini-3.8-flash"
        )
        db_session.add(ver)
        asset.active_version_id = ver.id

    db_session.commit()
    persisted_assets = db_session.query(GeneratedAsset).filter(GeneratedAsset.learning_pack_id == pack.id).all()
    assert len(persisted_assets) == 7
    types_found = {a.asset_type for a in persisted_assets}
    assert types_found == set(asset_types)

# TEST 2: Every asset has objective IDs
def test_m1_2_every_asset_has_objective_ids():
    asset_objs = ["LO-01", "LO-02"]
    reports = validate_objective_alignment(asset_objs, ["LO-01", "LO-02"], "asset-1")
    assert len(reports) == 0

# TEST 3: Every asset references source_version_id
def test_m1_3_every_asset_references_source_version_id(db_session):
    src = create_source_document_and_version(db_session, "Bio", "Cells and energy.")
    asset = GeneratedAsset(learning_pack_id="pack-x", asset_type="worked_example")
    db_session.add(asset)
    db_session.flush()
    ver = AssetVersion(
        asset_id=asset.id, source_version_id=src.id, version_number=1,
        content_json="{}", review_status="DRAFT", model_identifier="gemini-3.8-flash"
    )
    db_session.add(ver)
    db_session.commit()
    assert ver.source_version_id == src.id

# TEST 4: Uncovered objective detection
def test_m1_4_uncovered_objective_detection():
    contract_objectives = ["LO-01", "LO-02", "LO-03"]
    mapped_items = [
        {"id": "item-1", "type": "Explanation", "objective_ids": ["LO-01"]},
        {"id": "item-2", "type": "Quiz", "objective_ids": ["LO-02"]}
    ]
    summary, reports = compute_alignment_matrix_and_audit(contract_objectives, mapped_items)
    uncovered = [r for r in reports if r.rule_code == "UNCOVERED_OBJECTIVE"]
    assert len(uncovered) == 1
    assert uncovered[0].affected_entity_id == "LO-03"

# TEST 5: Orphan content detection
def test_m1_5_orphan_content_detection():
    reports = validate_objective_alignment([], ["LO-01", "LO-02"], "orphan-item-1")
    assert len(reports) == 1
    assert reports[0].rule_code == "ALIGNMENT_ORPHAN_ITEM"

# TEST 6: Coverage imbalance detection
def test_m1_6_coverage_imbalance_detection():
    contract_objectives = ["LO-01", "LO-02"]
    # 7 items on LO-01, only 1 item on LO-02 (ratio 7:1 > 3:1)
    mapped_items = [
        {"id": f"item-{i}", "type": "Quiz", "objective_ids": ["LO-01"]} for i in range(7)
    ] + [{"id": "item-8", "type": "Quiz", "objective_ids": ["LO-02"]}]

    summary, reports = compute_alignment_matrix_and_audit(contract_objectives, mapped_items)
    imbalance = [r for r in reports if r.rule_code == "OBJECTIVE_COVERAGE_IMBALANCE"]
    assert len(imbalance) == 1

# TEST 7: Answer-key mismatch detection
def test_m1_7_answer_key_mismatch_detection():
    quiz = [{"question_id": "Q1", "correct_answer": "Chloroplast"}]
    key = [{"question_id": "Q1", "correct_option": "Mitochondria"}]
    reports = validate_answer_key_consistency(quiz, key)
    assert len(reports) == 1
    assert reports[0].rule_code == "ANSWER_KEY_CONSISTENCY_MISMATCH"
    assert reports[0].severity == "CRITICAL"
    assert reports[0].is_blocking is True

# TEST 8: Duplicate question detection
def test_m1_8_duplicate_question_detection():
    quiz = [
        {"question_id": "Q1", "question": "Where does photosynthesis take place?"},
        {"question_id": "Q2", "question": "Where does photosynthesis take place?"}
    ]
    reports = validate_duplicate_questions(quiz)
    assert len(reports) == 1
    assert reports[0].rule_code == "DUPLICATE_QUESTION"
    assert reports[0].severity == "CRITICAL"

# TEST 9: Near-duplicate question detection
def test_m1_9_near_duplicate_question_detection():
    quiz = [
        {"question_id": "Q1", "question": "In which cellular organelle does photosynthesis take place?"},
        {"question_id": "Q2", "question": "Which cellular organelle is where photosynthesis takes place?"}
    ]
    reports = validate_duplicate_questions(quiz)
    assert len(reports) == 1
    assert reports[0].rule_code == "NEAR_DUPLICATE_QUESTION"
    assert reports[0].severity == "WARNING"

# TEST 10: Answer leakage detection
def test_m1_10_answer_leakage_detection():
    quiz = [
        {
            "question_id": "Q1",
            "question": "Since the chloroplast absorbs sunlight to make sugar, which organelle is responsible?",
            "correct_answer": "Chloroplast"
        }
    ]
    reports = validate_answer_leakage(quiz)
    assert len(reports) == 1
    assert reports[0].rule_code == "ANSWER_LEAKAGE_IN_STEM"
    assert reports[0].severity == "CRITICAL"

# TEST 11: Unsupported revision-sheet concept detection
def test_m1_11_unsupported_revision_concept_detection():
    source_text = "Photosynthesis occurs in chloroplasts and uses chlorophyll."
    revision_sheet = {
        "definitions": [
            {"term": "Chloroplast", "definition": "Organelle for photosynthesis"},
            {"term": "Quantum Entanglement", "definition": "Physics phenomenon"}
        ]
    }
    reports = validate_revision_sheet_grounding(revision_sheet, source_text)
    assert len(reports) == 1
    assert reports[0].rule_code == "REVISION_UNGROUNDED_CONCEPT"
    assert "Quantum Entanglement" in reports[0].message

# TEST 12: Easy vs Advanced cognitive difference
def test_m1_12_easy_vs_advanced_cognitive_difference():
    # Inverted difficulty: Easy is Analyze (rank 4), Advanced is Remember (rank 1)
    easy = {"bloom_level": "Analyze", "reasoning_step_count": 3}
    adv = {"bloom_level": "Remember", "reasoning_step_count": 1}
    reports = validate_cognitive_difficulty(easy, adv)
    assert len(reports) == 1
    assert reports[0].rule_code == "COGNITIVE_DIFFICULTY_INVERSION"
    assert reports[0].severity == "CRITICAL"

    # Proper difficulty: Easy is Understand (rank 2, 1 step), Advanced is Analyze (rank 4, 3 steps)
    good_easy = {"bloom_level": "Understand", "reasoning_step_count": 1}
    good_adv = {"bloom_level": "Analyze", "reasoning_step_count": 3}
    good_reports = validate_cognitive_difficulty(good_easy, good_adv)
    assert len(good_reports) == 0

# TEST 13: Terminology consistency
def test_m1_13_terminology_consistency():
    explanation = {"explanation": "Photosynthesis produces glucose and oxygen."}
    revision = {"definitions": [{"term": "RuBisCO", "definition": "Calvin cycle enzyme"}]}
    reports = validate_terminology_consistency(explanation, revision)
    assert len(reports) == 1
    assert reports[0].rule_code == "TERMINOLOGY_INCONSISTENCY"

# TEST 14: Cross-asset contradiction detection
def test_m1_14_cross_asset_contradiction_detection():
    exp = "Photosynthesis requires oxygen in trace amounts."
    worked = {"steps": ["Step 1: Notice that this process does not require oxygen under any circumstances."]}
    reports = validate_cross_asset_contradiction(exp, worked)
    assert len(reports) == 1
    assert reports[0].rule_code == "CROSS_ASSET_CONTRADICTION"

# TEST 15: Student endpoint still excludes DRAFT
def test_m1_15_student_endpoint_excludes_draft(db_session):
    src = create_source_document_and_version(db_session, "Doc", "Source text")
    contract = create_objective_contract(
        db_session, ContractCreate(source_version_id=src.id, title="Test Contract", target_learner_level="Grade 10", objectives=[ObjectiveItem(code="LO-01", description="Objective 1 description"), ObjectiveItem(code="LO-02", description="Objective 2 description")])
    )
    pack = LearningPack(contract_id=contract.id, source_version_id=src.id)
    db_session.add(pack)
    db_session.flush()

    asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="worked_example")
    db_session.add(asset)
    db_session.flush()

    ver = AssetVersion(
        asset_id=asset.id, source_version_id=src.id, version_number=1,
        content_json=json.dumps({"title": "Draft Example", "scenario": "S", "steps": ["S1"], "final_answer": "A", "objective_ids": ["LO-01"]}),
        review_status="DRAFT", model_identifier="gemini-3.8-flash"
    )
    db_session.add(ver)
    db_session.flush()
    asset.active_version_id = ver.id
    db_session.commit()

    student_res = get_student_approved_projection(db_session, pack.id)
    assert student_res.worked_example is None

# TEST 16: Student endpoint still excludes NEEDS_REVISION
def test_m1_16_student_endpoint_excludes_needs_revision(db_session):
    src = create_source_document_and_version(db_session, "Doc", "Source text")
    contract = create_objective_contract(
        db_session, ContractCreate(source_version_id=src.id, title="Test Contract", target_learner_level="Grade 10", objectives=[ObjectiveItem(code="LO-01", description="Objective 1 description"), ObjectiveItem(code="LO-02", description="Objective 2 description")])
    )
    pack = LearningPack(contract_id=contract.id, source_version_id=src.id)
    db_session.add(pack)
    db_session.flush()

    asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="easy_practice")
    db_session.add(asset)
    db_session.flush()

    ver = AssetVersion(
        asset_id=asset.id, source_version_id=src.id, version_number=1,
        content_json=json.dumps({"title": "Rev Practice", "problem_statement": "P", "solution_guidance": "G", "objective_ids": ["LO-01"], "bloom_level": "Remember", "difficulty_label": "Easy"}),
        review_status="NEEDS_REVISION", model_identifier="gemini-3.8-flash"
    )
    db_session.add(ver)
    db_session.flush()
    asset.active_version_id = ver.id
    db_session.commit()

    student_res = get_student_approved_projection(db_session, pack.id)
    assert student_res.easy_practice is None

# TEST 17: APPROVED remains visible in student endpoint
def test_m1_17_approved_remains_visible(db_session):
    src = create_source_document_and_version(db_session, "Doc", "Source text")
    contract = create_objective_contract(
        db_session, ContractCreate(source_version_id=src.id, title="Test Contract", target_learner_level="Grade 10", objectives=[ObjectiveItem(code="LO-01", description="Objective 1 description"), ObjectiveItem(code="LO-02", description="Objective 2 description")])
    )
    pack = LearningPack(contract_id=contract.id, source_version_id=src.id)
    db_session.add(pack)
    db_session.flush()

    asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="worked_example")
    db_session.add(asset)
    db_session.flush()

    ver = AssetVersion(
        asset_id=asset.id, source_version_id=src.id, version_number=1,
        content_json=json.dumps({"title": "Approved Example", "scenario": "Scenario text", "steps": ["Step 1"], "final_answer": "Final", "objective_ids": ["LO-01"]}),
        review_status="APPROVED", model_identifier="gemini-3.8-flash"
    )
    db_session.add(ver)
    db_session.flush()
    asset.active_version_id = ver.id
    db_session.commit()

    student_res = get_student_approved_projection(db_session, pack.id)
    assert student_res.worked_example is not None
    assert student_res.worked_example.title == "Approved Example"

# TEST 18: OVERRIDE remains visible in student endpoint
def test_m1_18_override_remains_visible(db_session):
    src = create_source_document_and_version(db_session, "Doc", "Source text")
    contract = create_objective_contract(
        db_session, ContractCreate(source_version_id=src.id, title="Test Contract", target_learner_level="Grade 10", objectives=[ObjectiveItem(code="LO-01", description="Objective 1 description"), ObjectiveItem(code="LO-02", description="Objective 2 description")])
    )
    pack = LearningPack(contract_id=contract.id, source_version_id=src.id)
    db_session.add(pack)
    db_session.flush()

    asset = GeneratedAsset(learning_pack_id=pack.id, asset_type="revision_sheet")
    db_session.add(asset)
    db_session.flush()

    ver = AssetVersion(
        asset_id=asset.id, source_version_id=src.id, version_number=1,
        content_json=json.dumps({
            "title": "Overridden Revision Sheet", "key_concepts": ["Concept 1"],
            "definitions": [{"term": "T", "definition": "D"}], "important_relationships": ["Rel"],
            "key_example": "Ex", "common_mistakes": [], "objective_ids": ["LO-01"]
        }),
        review_status="OVERRIDE", model_identifier="gemini-3.8-flash"
    )
    db_session.add(ver)
    db_session.flush()
    asset.active_version_id = ver.id
    db_session.commit()

    student_res = get_student_approved_projection(db_session, pack.id)
    assert student_res.revision_sheet is not None
    assert student_res.revision_sheet.title == "Overridden Revision Sheet"

# TEST 19: Existing Milestone 0 prompt-injection test still passes
def test_m1_19_prompt_injection_defense():
    from tests.test_milestone0 import test_10_prompt_injection_text_treated_as_data
    test_10_prompt_injection_text_treated_as_data()

# TEST 20: Existing source-version isolation test still passes
def test_m1_20_source_version_isolation(db_session):
    from tests.test_milestone0 import test_8_source_version_remains_associated_after_source_update
    test_8_source_version_remains_associated_after_source_update(db_session)
