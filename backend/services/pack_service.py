import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models.source import SourceVersion
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.pack import LearningPack, GeneratedAsset, AssetVersion
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.models.validation import ValidationReport
from backend.models.decision import TeacherDecision
from backend.config import (
    get_effective_llm_provider,
    get_effective_groq_model,
    get_effective_gemini_model,
)
from backend.services.llm_gateway import generate_complete_learning_pack, regenerate_single_quiz_question
from backend.services.validation_service import (
    validate_key_integrity,
    validate_grounding_evidence,
    validate_objective_alignment,
    validate_answer_key_consistency,
    validate_cognitive_difficulty,
    validate_duplicate_questions,
    validate_answer_leakage,
    validate_revision_sheet_grounding,
    validate_cross_asset_contradiction,
    validate_terminology_consistency,
    compute_alignment_matrix_and_audit
)

def create_or_update_asset(
    db: Session,
    pack_id: str,
    asset_type: str,
    content_data: dict,
    source_ver_id: str,
    model_name: str,
    prompt_snapshot: str | None = None,
    provider: str | None = None
) -> tuple[GeneratedAsset, AssetVersion]:
    asset = db.query(GeneratedAsset).filter(
        GeneratedAsset.learning_pack_id == pack_id,
        GeneratedAsset.asset_type == asset_type
    ).first()

    if not asset:
        asset = GeneratedAsset(
            learning_pack_id=pack_id,
            asset_type=asset_type
        )
        db.add(asset)
        db.flush()

    if provider:
        content_data["_provider"] = provider
        content_data["_model"] = model_name

    ver = AssetVersion(
        asset_id=asset.id,
        source_version_id=source_ver_id,
        version_number=1,
        content_json=json.dumps(content_data),
        review_status="DRAFT",
        model_identifier=model_name,
        prompt_snapshot=prompt_snapshot
    )
    db.add(ver)
    db.flush()
    asset.active_version_id = ver.id
    return asset, ver

def generate_and_save_learning_pack(db: Session, contract_id: str) -> LearningPack:
    contract = db.query(ObjectiveContract).filter(ObjectiveContract.id == contract_id).first()
    if not contract:
        raise ValueError(f"Contract {contract_id} not found.")

    source_ver = db.query(SourceVersion).filter(SourceVersion.id == contract.source_version_id).first()
    if not source_ver:
        raise ValueError(f"Source version {contract.source_version_id} not found.")

    objectives = db.query(LearningObjective).filter(LearningObjective.contract_id == contract_id).all()
    objectives_list = [{"code": o.code, "description": o.description, "bloom_level": o.bloom_level} for o in objectives]
    valid_codes = [o["code"] for o in objectives_list]

    constraints = {}
    if contract.constraints_json:
        try:
            constraints = json.loads(contract.constraints_json)
        except Exception:
            constraints = {}

    # Call active LLM provider (Groq or Gemini) for complete 7-asset pack
    pack_output, prompt_snapshot, model_name = generate_complete_learning_pack(
        source_text=source_ver.cleaned_text,
        source_version_id=source_ver.id,
        source_hash=source_ver.sha256_hash,
        contract_title=contract.title,
        target_learner_level=contract.target_learner_level,
        expected_difficulty=contract.expected_difficulty,
        objectives_list=objectives_list,
        constraints=constraints
    )
    provider_name = get_effective_llm_provider()

    # 1. Create LearningPack Container
    pack = LearningPack(
        contract_id=contract.id,
        source_version_id=source_ver.id
    )
    db.add(pack)
    db.flush()

    all_validation_reports: List[ValidationReport] = []
    mapped_items_for_matrix: List[Dict[str, Any]] = []

    # 2. Asset: Concept Explanation
    exp_dict = pack_output.concept_explanation.model_dump()
    exp_asset, exp_ver = create_or_update_asset(
        db, pack.id, "concept_explanation", exp_dict, source_ver.id, model_name, prompt_snapshot, provider=provider_name
    )
    mapped_items_for_matrix.append({
        "id": exp_asset.id,
        "type": "Concept Explanation",
        "objective_ids": exp_dict.get("objective_ids", [])
    })

    # Grounding & Alignment on Explanation
    g_rep, _ = validate_grounding_evidence(
        pack_output.concept_explanation.supporting_quote, source_ver.cleaned_text,
        exp_ver.id, asset_version_id=exp_ver.id
    )
    al_rep = validate_objective_alignment(
        pack_output.concept_explanation.objective_ids, valid_codes,
        exp_ver.id, asset_version_id=exp_ver.id
    )
    all_validation_reports.extend(g_rep + al_rep)

    # 3. Asset: Worked Example
    we_dict = pack_output.worked_example.model_dump()
    we_asset, we_ver = create_or_update_asset(
        db, pack.id, "worked_example", we_dict, source_ver.id, model_name, provider=provider_name
    )
    mapped_items_for_matrix.append({
        "id": we_asset.id,
        "type": "Worked Example",
        "objective_ids": we_dict.get("objective_ids", [])
    })

    g_rep, _ = validate_grounding_evidence(
        pack_output.worked_example.supporting_quote, source_ver.cleaned_text,
        we_ver.id, asset_version_id=we_ver.id
    )
    al_rep = validate_objective_alignment(
        pack_output.worked_example.objective_ids, valid_codes,
        we_ver.id, asset_version_id=we_ver.id
    )
    all_validation_reports.extend(g_rep + al_rep)

    # Cross-Asset Contradiction (Explanation vs Worked Example)
    con_rep = validate_cross_asset_contradiction(
        pack_output.concept_explanation.explanation, we_dict, asset_version_id=we_ver.id
    )
    all_validation_reports.extend(con_rep)

    # 4. Asset: Formative Quiz (and individual questions)
    quiz_questions_dicts = [q.model_dump() for q in pack_output.quiz_questions]
    quiz_asset, quiz_ver = create_or_update_asset(
        db, pack.id, "formative_quiz", {"questions": quiz_questions_dicts}, source_ver.id, model_name, provider=provider_name
    )

    for idx, q in enumerate(pack_output.quiz_questions):
        q_entity = QuizQuestion(asset_id=quiz_asset.id, ordinal_position=idx + 1)
        db.add(q_entity)
        db.flush()

        g_rep, q_status = validate_grounding_evidence(
            q.supporting_quote, source_ver.cleaned_text, q_entity.id
        )

        q_ver = QuizQuestionVersion(
            question_id=q_entity.id,
            source_version_id=source_ver.id,
            version_number=1,
            question_text=q.question,
            options_json=json.dumps(q.options),
            correct_answer=q.correct_answer,
            objective_ids_json=json.dumps(q.objective_ids),
            supporting_quote=q.supporting_quote,
            grounding_status=q_status,
            review_status="DRAFT",
            model_identifier=model_name
        )
        db.add(q_ver)
        db.flush()
        q_entity.active_version_id = q_ver.id

        # Attach reports
        for r in g_rep:
            r.question_version_id = q_ver.id
            all_validation_reports.append(r)

        key_reps = validate_key_integrity(
            q.question, q.options, q.correct_answer, q_ver.id, question_version_id=q_ver.id
        )
        all_validation_reports.extend(key_reps)

        al_reps = validate_objective_alignment(
            q.objective_ids, valid_codes, q_ver.id, question_version_id=q_ver.id
        )
        all_validation_reports.extend(al_reps)

        mapped_items_for_matrix.append({
            "id": q_entity.id,
            "type": f"Quiz Question {idx + 1}",
            "objective_ids": q.objective_ids
        })

    # Quiz Question Duplicates & Near-Duplicates
    dup_reps = validate_duplicate_questions(quiz_questions_dicts, asset_version_id=quiz_ver.id)
    all_validation_reports.extend(dup_reps)

    # Answer Leakage Check
    leak_reps = validate_answer_leakage(
        quiz_questions_dicts, worked_example_scenario=we_dict.get("scenario", ""), asset_version_id=quiz_ver.id
    )
    all_validation_reports.extend(leak_reps)

    # 5. Asset: Dedicated Quiz Answer Key
    ak_dict = pack_output.quiz_answer_key.model_dump()
    ak_asset, ak_ver = create_or_update_asset(
        db, pack.id, "quiz_answer_key", ak_dict, source_ver.id, model_name, provider=provider_name
    )
    mapped_items_for_matrix.append({
        "id": ak_asset.id,
        "type": "Quiz Answer Key",
        "objective_ids": [lo for item in ak_dict.get("items", []) for lo in item.get("objective_ids", [])]
    })

    # Consistency between Quiz and Answer Key
    ak_consist_reps = validate_answer_key_consistency(
        quiz_questions_dicts, ak_dict.get("items", []), asset_version_id=ak_ver.id
    )
    all_validation_reports.extend(ak_consist_reps)

    # 6. Asset: Easy Practice
    easy_dict = pack_output.easy_practice.model_dump()
    easy_asset, easy_ver = create_or_update_asset(
        db, pack.id, "easy_practice", easy_dict, source_ver.id, model_name, provider=provider_name
    )
    mapped_items_for_matrix.append({
        "id": easy_asset.id,
        "type": "Easy Practice",
        "objective_ids": easy_dict.get("objective_ids", [])
    })

    g_rep, _ = validate_grounding_evidence(
        pack_output.easy_practice.supporting_quote, source_ver.cleaned_text,
        easy_ver.id, asset_version_id=easy_ver.id
    )
    al_rep = validate_objective_alignment(
        pack_output.easy_practice.objective_ids, valid_codes,
        easy_ver.id, asset_version_id=easy_ver.id
    )
    all_validation_reports.extend(g_rep + al_rep)

    # 7. Asset: Advanced Practice
    adv_dict = pack_output.advanced_practice.model_dump()
    adv_asset, adv_ver = create_or_update_asset(
        db, pack.id, "advanced_practice", adv_dict, source_ver.id, model_name, provider=provider_name
    )
    mapped_items_for_matrix.append({
        "id": adv_asset.id,
        "type": "Advanced Practice",
        "objective_ids": adv_dict.get("objective_ids", [])
    })

    g_rep, _ = validate_grounding_evidence(
        pack_output.advanced_practice.supporting_quote, source_ver.cleaned_text,
        adv_ver.id, asset_version_id=adv_ver.id
    )
    al_rep = validate_objective_alignment(
        pack_output.advanced_practice.objective_ids, valid_codes,
        adv_ver.id, asset_version_id=adv_ver.id
    )
    all_validation_reports.extend(g_rep + al_rep)

    # Cognitive Difficulty Validation (Easy vs Advanced)
    diff_reps = validate_cognitive_difficulty(
        easy_dict, adv_dict, easy_version_id=easy_ver.id, adv_version_id=adv_ver.id
    )
    all_validation_reports.extend(diff_reps)

    # 8. Asset: Concise Revision Sheet
    rev_dict = pack_output.revision_sheet.model_dump()
    rev_asset, rev_ver = create_or_update_asset(
        db, pack.id, "revision_sheet", rev_dict, source_ver.id, model_name, provider=provider_name
    )
    mapped_items_for_matrix.append({
        "id": rev_asset.id,
        "type": "Revision Sheet",
        "objective_ids": rev_dict.get("objective_ids", [])
    })

    g_rep, _ = validate_grounding_evidence(
        pack_output.revision_sheet.supporting_quote, source_ver.cleaned_text,
        rev_ver.id, asset_version_id=rev_ver.id
    )
    al_rep = validate_objective_alignment(
        pack_output.revision_sheet.objective_ids, valid_codes,
        rev_ver.id, asset_version_id=rev_ver.id
    )
    all_validation_reports.extend(g_rep + al_rep)

    rev_ground_reps = validate_revision_sheet_grounding(
        rev_dict, source_ver.cleaned_text, asset_version_id=rev_ver.id
    )
    all_validation_reports.extend(rev_ground_reps)

    term_reps = validate_terminology_consistency(
        exp_dict, rev_dict, asset_version_id=rev_ver.id
    )
    all_validation_reports.extend(term_reps)

    # 9. Alignment Matrix & Imbalance Evaluation
    align_summary, align_reps = compute_alignment_matrix_and_audit(valid_codes, mapped_items_for_matrix)
    all_validation_reports.extend(align_reps)

    # Persist all collected validation reports
    for rep in all_validation_reports:
        db.add(rep)

    db.commit()
    db.refresh(pack)
    return pack

def serialize_quiz_question(db: Session, question: QuizQuestion) -> dict | None:
    active_ver = None
    if question.active_version_id:
        active_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == question.active_version_id).first()
    if not active_ver:
        active_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == question.id).order_by(QuizQuestionVersion.version_number.desc()).first()

    if not active_ver:
        return None

    all_vers = (
        db.query(QuizQuestionVersion)
        .filter(QuizQuestionVersion.question_id == question.id)
        .order_by(QuizQuestionVersion.version_number.desc())
        .all()
    )
    versions_history = []
    for v in all_vers:
        v_validations = db.query(ValidationReport).filter(ValidationReport.question_version_id == v.id).all()
        versions_history.append({
            "id": v.id,
            "version_id": v.id,
            "version_number": v.version_number,
            "question_text": v.question_text,
            "options": json.loads(v.options_json),
            "correct_answer": v.correct_answer,
            "objective_ids": json.loads(v.objective_ids_json),
            "supporting_quote": v.supporting_quote,
            "grounding_status": v.grounding_status,
            "review_status": v.review_status,
            "source_version_id": v.source_version_id,
            "teacher_notes": v.teacher_notes,
            "rationale": getattr(v, "rationale", None),
            "model_identifier": v.model_identifier,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "validations": [
                {
                    "id": val.id,
                    "validation_type": val.validation_type,
                    "severity": val.severity,
                    "rule_code": val.rule_code,
                    "message": val.message,
                    "evidence_snippet": val.evidence_snippet,
                    "is_blocking": val.is_blocking
                }
                for val in v_validations
            ],
            "decisions": [
                {
                    "id": d.id,
                    "action": d.action,
                    "acknowledged_warning_ids": json.loads(d.acknowledged_warning_ids_json or "[]"),
                    "teacher_notes": d.teacher_notes,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in v.decisions
            ]
        })

    q_validations = db.query(ValidationReport).filter(ValidationReport.question_version_id == active_ver.id).all()
    q_provider = "groq" if ("openai" in active_ver.model_identifier or "groq" in active_ver.model_identifier) else "gemini"

    return {
        "question_id": question.id,
        "version_id": active_ver.id,
        "version_number": active_ver.version_number,
        "ordinal_position": question.ordinal_position,
        "question_text": active_ver.question_text,
        "options": json.loads(active_ver.options_json),
        "correct_answer": active_ver.correct_answer,
        "objective_ids": json.loads(active_ver.objective_ids_json),
        "supporting_quote": active_ver.supporting_quote,
        "rationale": getattr(active_ver, "rationale", None),
        "grounding_status": active_ver.grounding_status,
        "review_status": active_ver.review_status,
        "source_version_id": active_ver.source_version_id,
        "teacher_notes": active_ver.teacher_notes,
        "created_at": active_ver.created_at.isoformat() if active_ver.created_at else None,
        "provider": q_provider,
        "model": active_ver.model_identifier,
        "model_identifier": active_ver.model_identifier,
        "validations": [
            {
                "id": v.id,
                "validation_type": v.validation_type,
                "severity": v.severity,
                "rule_code": v.rule_code,
                "message": v.message,
                "evidence_snippet": v.evidence_snippet,
                "is_blocking": v.is_blocking
            }
            for v in q_validations
        ],
        "decisions": [
            {
                "id": d.id,
                "action": d.action,
                "acknowledged_warning_ids": json.loads(d.acknowledged_warning_ids_json or "[]"),
                "teacher_notes": d.teacher_notes,
                "timestamp": d.timestamp.isoformat()
            }
            for d in active_ver.decisions
        ],
        "versions": versions_history
    }

def get_pack_details(db: Session, pack_id: str) -> dict:
    pack = db.query(LearningPack).filter(LearningPack.id == pack_id).first()
    if not pack:
        raise ValueError(f"Pack {pack_id} not found.")

    contract = pack.contract
    source_ver = db.query(SourceVersion).filter(SourceVersion.id == pack.source_version_id).first()
    contract_objectives = [o.code for o in contract.objectives]

    # Helper to serialize an asset
    def serialize_asset(asset_type: str):
        asset = db.query(GeneratedAsset).filter(
            GeneratedAsset.learning_pack_id == pack_id,
            GeneratedAsset.asset_type == asset_type
        ).first()
        if not asset or not asset.active_version_id:
            return None
        ver = db.query(AssetVersion).filter(AssetVersion.id == asset.active_version_id).first()
        if not ver:
            return None
        validations = db.query(ValidationReport).filter(ValidationReport.asset_version_id == ver.id).all()
        content_dict = json.loads(ver.content_json)
        asset_provider = content_dict.get("_provider") or ("groq" if ("openai" in ver.model_identifier or "groq" in ver.model_identifier) else "gemini")
        return {
            "asset_id": asset.id,
            "version_id": ver.id,
            "version_number": ver.version_number,
            "content": content_dict,
            "review_status": ver.review_status,
            "source_version_id": ver.source_version_id,
            "provider": asset_provider,
            "model": ver.model_identifier,
            "model_identifier": ver.model_identifier,
            "validations": [
                {
                    "id": v.id,
                    "validation_type": v.validation_type,
                    "severity": v.severity,
                    "rule_code": v.rule_code,
                    "message": v.message,
                    "evidence_snippet": v.evidence_snippet,
                    "is_blocking": v.is_blocking
                }
                for v in validations
            ],
            "decisions": [
                {
                    "id": d.id,
                    "action": d.action,
                    "acknowledged_warning_ids": json.loads(d.acknowledged_warning_ids_json or "[]"),
                    "teacher_notes": d.teacher_notes,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in ver.decisions
            ]
        }

    # Concept Explanation (Milestone 0 format preserved)
    exp_serialized = serialize_asset("concept_explanation")
    explanation_data = None
    if exp_serialized:
        explanation_data = {
            "asset_id": exp_serialized["asset_id"],
            "version_id": exp_serialized["version_id"],
            "version_number": exp_serialized["version_number"],
            "title": exp_serialized["content"].get("title", ""),
            "explanation": exp_serialized["content"].get("explanation", ""),
            "objective_ids": exp_serialized["content"].get("objective_ids", []),
            "supporting_quote": exp_serialized["content"].get("supporting_quote", ""),
            "review_status": exp_serialized["review_status"],
            "source_version_id": exp_serialized["source_version_id"],
            "provider": exp_serialized["provider"],
            "model": exp_serialized["model"],
            "model_identifier": exp_serialized["model_identifier"],
            "validations": exp_serialized["validations"],
            "decisions": exp_serialized["decisions"]
        }

    # Quiz Questions
    quiz_asset = db.query(GeneratedAsset).filter(
        GeneratedAsset.learning_pack_id == pack_id,
        GeneratedAsset.asset_type == "formative_quiz"
    ).first()

    questions_data = []
    if quiz_asset:
        questions = db.query(QuizQuestion).filter(QuizQuestion.asset_id == quiz_asset.id).order_by(QuizQuestion.ordinal_position).all()
        for q in questions:
            q_data = serialize_quiz_question(db, q)
            if q_data:
                questions_data.append(q_data)

    # Remaining 5 assets
    worked_example_data = serialize_asset("worked_example")
    quiz_answer_key_data = serialize_asset("quiz_answer_key")
    easy_practice_data = serialize_asset("easy_practice")
    advanced_practice_data = serialize_asset("advanced_practice")
    revision_sheet_data = serialize_asset("revision_sheet")

    # Build Alignment Matrix dynamically
    matrix_items = []
    if explanation_data:
        matrix_items.append({"id": explanation_data["asset_id"], "type": "Concept Explanation", "objective_ids": explanation_data["objective_ids"]})
    if worked_example_data:
        matrix_items.append({"id": worked_example_data["asset_id"], "type": "Worked Example", "objective_ids": worked_example_data["content"].get("objective_ids", [])})
    for q in questions_data:
        matrix_items.append({"id": q["question_id"], "type": f"Quiz Question {q['ordinal_position']}", "objective_ids": q["objective_ids"]})
    if quiz_answer_key_data:
        matrix_items.append({"id": quiz_answer_key_data["asset_id"], "type": "Quiz Answer Key", "objective_ids": [lo for item in quiz_answer_key_data["content"].get("items", []) for lo in item.get("objective_ids", [])]})
    if easy_practice_data:
        matrix_items.append({"id": easy_practice_data["asset_id"], "type": "Easy Practice", "objective_ids": easy_practice_data["content"].get("objective_ids", [])})
    if advanced_practice_data:
        matrix_items.append({"id": advanced_practice_data["asset_id"], "type": "Advanced Practice", "objective_ids": advanced_practice_data["content"].get("objective_ids", [])})
    if revision_sheet_data:
        matrix_items.append({"id": revision_sheet_data["asset_id"], "type": "Revision Sheet", "objective_ids": revision_sheet_data["content"].get("objective_ids", [])})

    alignment_matrix, matrix_reps = compute_alignment_matrix_and_audit(contract_objectives, matrix_items)

    # General Pack Validation Warnings (uncovered objectives, imbalance, cross-asset flags)
    pack_validations = db.query(ValidationReport).filter(
        ValidationReport.asset_version_id.in_([
            ver_id for ver_id in [
                exp_serialized["version_id"] if exp_serialized else None,
                worked_example_data["version_id"] if worked_example_data else None,
                quiz_asset.active_version_id if quiz_asset else None,
                quiz_answer_key_data["version_id"] if quiz_answer_key_data else None,
                easy_practice_data["version_id"] if easy_practice_data else None,
                advanced_practice_data["version_id"] if advanced_practice_data else None,
                revision_sheet_data["version_id"] if revision_sheet_data else None
            ] if ver_id
        ])
    ).all()

    detected_provider = (
        explanation_data.get("provider") if explanation_data else get_effective_llm_provider()
    )
    detected_model = (
        explanation_data.get("model") if explanation_data else (
            get_effective_groq_model() if detected_provider == "groq" else get_effective_gemini_model()
        )
    )

    return {
        "pack_id": pack.id,
        "provider": detected_provider,
        "model": detected_model,
        "contract": {
            "id": contract.id,
            "title": contract.title,
            "target_learner_level": contract.target_learner_level,
            "expected_difficulty": contract.expected_difficulty,
            "objectives": [{"code": o.code, "description": o.description, "bloom_level": o.bloom_level} for o in contract.objectives]
        },
        "source": {
            "id": source_ver.id,
            "document_id": source_ver.source_document_id,
            "version_number": source_ver.version_number,
            "sha256": source_ver.sha256_hash,
            "char_count": source_ver.char_count,
            "cleaned_text": source_ver.cleaned_text
        },
        "concept_explanation": explanation_data,
        "worked_example": worked_example_data,
        "quiz_questions": questions_data,
        "quiz_answer_key": quiz_answer_key_data,
        "easy_practice": easy_practice_data,
        "advanced_practice": advanced_practice_data,
        "revision_sheet": revision_sheet_data,
        "alignment_matrix": alignment_matrix
    }

def get_question_details(db: Session, question_id: str) -> dict:
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise ValueError(f"Quiz question '{question_id}' not found.")
    q_data = serialize_quiz_question(db, question)
    if not q_data:
        raise ValueError(f"Failed to serialize quiz question '{question_id}'.")
    return q_data

def regenerate_quiz_question(
    db: Session,
    question_id: str,
    teacher_notes: str = "",
    reason: str = ""
) -> dict:
    """
    Surgically regenerates ONE individual quiz question:
    - Retains previous question version(s) immutably.
    - Sibling questions (e.g. Q1, Q2) and their approval states remain 100% unchanged.
    - Uses live configured LLM provider adhering to trusted source boundaries and objective contract.
    - Creates a new question version (starts as DRAFT).
    - Executes deterministic validation suite (grounding, alignment, key integrity, duplicate check, leakage).
    - Persists validation results, version increment, and teacher notes.
    """
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise ValueError(f"Quiz question '{question_id}' not found.")

    # Find active or latest version
    active_ver = None
    if question.active_version_id:
        active_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == question.active_version_id).first()
    if not active_ver:
        active_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == question.id).order_by(QuizQuestionVersion.version_number.desc()).first()

    if not active_ver:
        raise ValueError(f"No existing version found for question '{question_id}'.")

    # Load parent learning pack, source version, and contract
    asset = db.query(GeneratedAsset).filter(GeneratedAsset.id == question.asset_id).first()
    if not asset or not asset.learning_pack_id:
        raise ValueError(f"Parent asset or learning pack not found for question '{question_id}'.")

    pack = db.query(LearningPack).filter(LearningPack.id == asset.learning_pack_id).first()
    if not pack:
        raise ValueError(f"Learning pack '{asset.learning_pack_id}' not found.")

    source_ver = db.query(SourceVersion).filter(SourceVersion.id == active_ver.source_version_id).first()
    if not source_ver:
        source_ver = db.query(SourceVersion).filter(SourceVersion.id == pack.source_version_id).first()
    if not source_ver:
        raise ValueError("Source version not found.")

    contract = db.query(ObjectiveContract).filter(ObjectiveContract.id == pack.contract_id).first()
    if not contract:
        raise ValueError("Objective contract not found.")

    valid_codes = [obj.code for obj in contract.objectives]
    all_contract_objectives = [
        {"code": obj.code, "description": obj.description, "bloom_level": obj.bloom_level}
        for obj in contract.objectives
    ]

    target_objective_ids = json.loads(active_ver.objective_ids_json) if active_ver.objective_ids_json else valid_codes[:1]

    # Gather sibling questions in the same pack to prevent duplicate generation
    # NOTE: Sibling questions are read-only and MUST NOT be modified!
    siblings = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.asset_id == question.asset_id, QuizQuestion.id != question.id)
        .order_by(QuizQuestion.ordinal_position)
        .all()
    )
    sibling_texts = []
    sibling_dicts = []
    for sib in siblings:
        if sib.active_version_id:
            s_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == sib.active_version_id).first()
            if s_ver:
                sibling_texts.append(s_ver.question_text)
                sibling_dicts.append({
                    "question_id": f"Q{sib.ordinal_position}",
                    "question": s_ver.question_text,
                    "correct_answer": s_ver.correct_answer
                })

    # Call LLM gateway for single question regeneration
    gen_q, prompt_snapshot, model_name = regenerate_single_quiz_question(
        source_text=source_ver.cleaned_text,
        source_version_id=source_ver.id,
        source_hash=source_ver.sha256_hash,
        contract_title=contract.title,
        target_learner_level=contract.target_learner_level,
        expected_difficulty=contract.expected_difficulty,
        question_ordinal=question.ordinal_position,
        target_objective_ids=target_objective_ids,
        all_contract_objectives=all_contract_objectives,
        current_question_text=active_ver.question_text,
        other_questions_text=sibling_texts,
        teacher_notes=teacher_notes,
        reason=reason,
        constraints=json.loads(contract.constraints_json) if contract.constraints_json else {}
    )

    # Determine next version number
    existing_versions = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == question.id).all()
    next_ver_num = max([v.version_number for v in existing_versions], default=0) + 1

    # Validate Grounding Evidence
    g_reps, q_status = validate_grounding_evidence(
        gen_q.supporting_quote, source_ver.cleaned_text, question.id
    )

    # Create new immutable question version (starts as DRAFT)
    new_ver = QuizQuestionVersion(
        question_id=question.id,
        source_version_id=source_ver.id,
        version_number=next_ver_num,
        question_text=gen_q.question,
        options_json=json.dumps(gen_q.options),
        correct_answer=gen_q.correct_answer,
        objective_ids_json=json.dumps(gen_q.objective_ids),
        supporting_quote=gen_q.supporting_quote,
        rationale=getattr(active_ver, "rationale", None),
        grounding_status=q_status,
        review_status="DRAFT", # Newly regenerated question starts strictly as DRAFT
        model_identifier=model_name,
        teacher_notes=teacher_notes or reason
    )
    db.add(new_ver)
    db.flush()

    # Link new active version
    question.active_version_id = new_ver.id

    # Run deterministic validations and link to new_ver.id
    new_validation_reports = []

    # 1. Grounding reports
    for r in g_reps:
        r.question_version_id = new_ver.id
        new_validation_reports.append(r)

    # 2. Key integrity
    key_reps = validate_key_integrity(
        gen_q.question, gen_q.options, gen_q.correct_answer, new_ver.id, question_version_id=new_ver.id
    )
    new_validation_reports.extend(key_reps)

    # 3. Objective alignment
    al_reps = validate_objective_alignment(
        gen_q.objective_ids, valid_codes, new_ver.id, question_version_id=new_ver.id
    )
    new_validation_reports.extend(al_reps)

    # 4. Duplicate checks against sibling questions
    combined_questions_for_dup = sibling_dicts + [{
        "question_id": f"Q{question.ordinal_position}",
        "question": gen_q.question,
        "correct_answer": gen_q.correct_answer
    }]
    dup_reps = validate_duplicate_questions(combined_questions_for_dup, asset_version_id=None)
    for dr in dup_reps:
        dr.question_version_id = new_ver.id
        new_validation_reports.append(dr)

    # 5. Answer leakage check
    leak_reps = validate_answer_leakage(
        [{"question_id": f"Q{question.ordinal_position}", "question": gen_q.question, "correct_answer": gen_q.correct_answer}],
        worked_example_scenario="",
        asset_version_id=None
    )
    for lr in leak_reps:
        lr.question_version_id = new_ver.id
        new_validation_reports.append(lr)

    for rep in new_validation_reports:
        db.add(rep)

    # Log TeacherDecision record for audit trail
    decision = TeacherDecision(
        question_version_id=new_ver.id,
        action="REGENERATED",
        acknowledged_warning_ids_json="[]",
        teacher_notes=teacher_notes or reason or f"Regenerated to version {next_ver_num}"
    )
    db.add(decision)

    db.commit()
    db.refresh(new_ver)
    db.refresh(question)

    serialized_q = serialize_quiz_question(db, question)
    pack_data = get_pack_details(db, pack.id)

    return {
        "status": "success",
        "question_id": question.id,
        "active_version_id": new_ver.id,
        "version_number": new_ver.version_number,
        "review_status": new_ver.review_status,
        "source_version_id": new_ver.source_version_id,
        "teacher_notes": new_ver.teacher_notes,
        "rationale": new_ver.rationale,
        "question": serialized_q,
        "pack_id": pack.id,
        "pack": pack_data
    }

def edit_quiz_question(
    db: Session,
    question_id: str,
    question_text: str,
    options: list[str],
    correct_answer: str,
    supporting_quote: str | None = None,
    rationale: str | None = None,
    teacher_notes: str | None = None,
    reason: str | None = None,
    objective_ids: list[str] | None = None
) -> dict:
    """
    Manually edits an individual quiz question:
    - Never modifies existing versions in place.
    - Creates a new immutable version (v_next) starting as DRAFT.
    - Preserves previous versions permanently.
    - Sibling questions (e.g. Q1, Q2) remain untouched.
    - Preserves source_version_id and objective alignment.
    - Automatically runs the full deterministic validation suite (grounding, alignment, key integrity, duplicate detection, answer leakage).
    - If critical errors are found, normal approval is blocked.
    - Logs TeacherDecision(action='EDITED') with teacher notes/reason in audit history.
    """
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise ValueError(f"Quiz question '{question_id}' not found.")

    if not question_text or not question_text.strip():
        raise ValueError("Question text cannot be empty.")
    if not options or len(options) < 2:
        raise ValueError("Question must have at least 2 options.")
    if not correct_answer or not correct_answer.strip():
        raise ValueError("Correct answer cannot be empty.")

    # Find active or latest version
    active_ver = None
    if question.active_version_id:
        active_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == question.active_version_id).first()
    if not active_ver:
        active_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == question.id).order_by(QuizQuestionVersion.version_number.desc()).first()

    if not active_ver:
        raise ValueError(f"No existing version found for question '{question_id}'.")

    # Load parent learning pack, source version, and contract
    asset = db.query(GeneratedAsset).filter(GeneratedAsset.id == question.asset_id).first()
    if not asset or not asset.learning_pack_id:
        raise ValueError(f"Parent asset or learning pack not found for question '{question_id}'.")

    pack = db.query(LearningPack).filter(LearningPack.id == asset.learning_pack_id).first()
    if not pack:
        raise ValueError(f"Learning pack '{asset.learning_pack_id}' not found.")

    source_ver = db.query(SourceVersion).filter(SourceVersion.id == active_ver.source_version_id).first()
    if not source_ver:
        source_ver = db.query(SourceVersion).filter(SourceVersion.id == pack.source_version_id).first()
    if not source_ver:
        raise ValueError("Source version not found.")

    contract = db.query(ObjectiveContract).filter(ObjectiveContract.id == pack.contract_id).first()
    if not contract:
        raise ValueError("Objective contract not found.")

    valid_codes = [obj.code for obj in contract.objectives]

    # Target objectives: preserve existing unless explicitly supplied
    if objective_ids and len(objective_ids) > 0:
        target_objective_ids = objective_ids
    else:
        target_objective_ids = json.loads(active_ver.objective_ids_json) if active_ver.objective_ids_json else valid_codes[:1]

    # Supporting quote: preserve existing if not supplied
    target_quote = supporting_quote if supporting_quote is not None else active_ver.supporting_quote

    # Rationale: preserve existing if not supplied
    target_rationale = rationale if rationale is not None else getattr(active_ver, "rationale", None)

    # Determine next version number
    existing_versions = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == question.id).all()
    next_ver_num = max([v.version_number for v in existing_versions], default=0) + 1

    # Validate Grounding Evidence
    g_reps, q_status = validate_grounding_evidence(
        target_quote or "", source_ver.cleaned_text, question.id
    )

    # Create new immutable question version (starts as DRAFT)
    new_ver = QuizQuestionVersion(
        question_id=question.id,
        source_version_id=source_ver.id,
        version_number=next_ver_num,
        question_text=question_text.strip(),
        options_json=json.dumps([opt.strip() for opt in options]),
        correct_answer=correct_answer.strip(),
        objective_ids_json=json.dumps(target_objective_ids),
        supporting_quote=target_quote,
        rationale=target_rationale,
        grounding_status=q_status,
        review_status="DRAFT", # Starts as DRAFT
        model_identifier="teacher-edited",
        teacher_notes=teacher_notes or reason or f"Teacher edit to version {next_ver_num}"
    )
    db.add(new_ver)
    db.flush()

    # Link new active version
    question.active_version_id = new_ver.id

    # Run deterministic validations and link to new_ver.id
    new_validation_reports = []

    # 1. Grounding reports
    for r in g_reps:
        r.question_version_id = new_ver.id
        new_validation_reports.append(r)

    # 2. Key integrity (validates correct_answer is in options)
    clean_options = [opt.strip() for opt in options]
    key_reps = validate_key_integrity(
        new_ver.question_text, clean_options, new_ver.correct_answer, new_ver.id, question_version_id=new_ver.id
    )
    new_validation_reports.extend(key_reps)

    # 3. Objective alignment
    al_reps = validate_objective_alignment(
        target_objective_ids, valid_codes, new_ver.id, question_version_id=new_ver.id
    )
    new_validation_reports.extend(al_reps)

    # 4. Duplicate checks against sibling questions in the pack
    siblings = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.asset_id == question.asset_id, QuizQuestion.id != question.id)
        .order_by(QuizQuestion.ordinal_position)
        .all()
    )
    sibling_dicts = []
    for sib in siblings:
        if sib.active_version_id:
            s_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == sib.active_version_id).first()
            if s_ver:
                sibling_dicts.append({
                    "question_id": f"Q{sib.ordinal_position}",
                    "question": s_ver.question_text,
                    "correct_answer": s_ver.correct_answer
                })

    combined_questions_for_dup = sibling_dicts + [{
        "question_id": f"Q{question.ordinal_position}",
        "question": new_ver.question_text,
        "correct_answer": new_ver.correct_answer
    }]
    dup_reps = validate_duplicate_questions(combined_questions_for_dup, asset_version_id=None)
    for dr in dup_reps:
        dr.question_version_id = new_ver.id
        new_validation_reports.append(dr)

    # 5. Answer leakage check
    leak_reps = validate_answer_leakage(
        [{"question_id": f"Q{question.ordinal_position}", "question": new_ver.question_text, "correct_answer": new_ver.correct_answer}],
        worked_example_scenario="",
        asset_version_id=None
    )
    for lr in leak_reps:
        lr.question_version_id = new_ver.id
        new_validation_reports.append(lr)

    for rep in new_validation_reports:
        db.add(rep)

    # Log TeacherDecision record for audit trail
    decision = TeacherDecision(
        question_version_id=new_ver.id,
        action="EDITED",
        acknowledged_warning_ids_json="[]",
        teacher_notes=teacher_notes or reason or f"Teacher edited version {next_ver_num}"
    )
    db.add(decision)

    db.commit()
    db.refresh(new_ver)
    db.refresh(question)

    serialized_q = serialize_quiz_question(db, question)
    pack_data = get_pack_details(db, pack.id)

    return {
        "status": "success",
        "question_id": question.id,
        "active_version_id": new_ver.id,
        "version_number": new_ver.version_number,
        "review_status": new_ver.review_status,
        "source_version_id": new_ver.source_version_id,
        "teacher_notes": new_ver.teacher_notes,
        "rationale": new_ver.rationale,
        "question": serialized_q,
        "active_version": serialized_q,
        "pack_id": pack.id,
        "pack": pack_data
    }

def diff_quiz_question_versions(
    db: Session,
    question_id: str,
    v1_number: int | None = None,
    v2_number: int | None = None
) -> dict:
    """
    Computes a precise side-by-side diff between two versions of a quiz question:
    - Compares stem, options, correct answer, rationale, teacher notes, timestamps, review status, and validations.
    - If version numbers are not specified, defaults to comparing the previous version against the active/latest version.
    """
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise ValueError(f"Quiz question '{question_id}' not found.")

    all_vers = (
        db.query(QuizQuestionVersion)
        .filter(QuizQuestionVersion.question_id == question.id)
        .order_by(QuizQuestionVersion.version_number.asc())
        .all()
    )
    if not all_vers:
        raise ValueError(f"No versions found for question '{question_id}'.")

    # Select v1 and v2 records
    if v1_number is not None and v2_number is not None:
        v1_record = next((v for v in all_vers if v.version_number == v1_number), None)
        v2_record = next((v for v in all_vers if v.version_number == v2_number), None)
        if not v1_record:
            raise ValueError(f"Version {v1_number} not found for question '{question_id}'.")
        if not v2_record:
            raise ValueError(f"Version {v2_number} not found for question '{question_id}'.")
    elif len(all_vers) >= 2:
        v1_record = all_vers[-2]
        v2_record = all_vers[-1]
    else:
        v1_record = all_vers[0]
        v2_record = all_vers[0]

    v1_opts = json.loads(v1_record.options_json)
    v2_opts = json.loads(v2_record.options_json)
    v1_objs = json.loads(v1_record.objective_ids_json)
    v2_objs = json.loads(v2_record.objective_ids_json)

    v1_vals = db.query(ValidationReport).filter(ValidationReport.question_version_id == v1_record.id).all()
    v2_vals = db.query(ValidationReport).filter(ValidationReport.question_version_id == v2_record.id).all()

    stem_changed = v1_record.question_text != v2_record.question_text
    options_changed = v1_opts != v2_opts
    correct_answer_changed = v1_record.correct_answer != v2_record.correct_answer
    rationale_changed = (v1_record.rationale or "") != (v2_record.rationale or "")
    quote_changed = (v1_record.supporting_quote or "") != (v2_record.supporting_quote or "")
    objectives_changed = v1_objs != v2_objs
    status_changed = v1_record.review_status != v2_record.review_status

    changed_fields = []
    if stem_changed: changed_fields.append("question_text")
    if options_changed: changed_fields.append("options")
    if correct_answer_changed: changed_fields.append("correct_answer")
    if rationale_changed: changed_fields.append("rationale")
    if quote_changed: changed_fields.append("supporting_quote")
    if objectives_changed: changed_fields.append("objective_ids")
    if status_changed: changed_fields.append("review_status")

    def serialize_v(v_rec, opts, objs, vals):
        return {
            "version_id": v_rec.id,
            "version_number": v_rec.version_number,
            "question_text": v_rec.question_text,
            "options": opts,
            "correct_answer": v_rec.correct_answer,
            "rationale": getattr(v_rec, "rationale", None),
            "supporting_quote": v_rec.supporting_quote,
            "objective_ids": objs,
            "review_status": v_rec.review_status,
            "teacher_notes": v_rec.teacher_notes,
            "model_identifier": v_rec.model_identifier,
            "created_at": v_rec.created_at.isoformat() if v_rec.created_at else None,
            "validations": [
                {
                    "id": val.id,
                    "validation_type": val.validation_type,
                    "severity": val.severity,
                    "rule_code": val.rule_code,
                    "message": val.message,
                    "is_blocking": val.is_blocking
                }
                for val in vals
            ]
        }

    return {
        "question_id": question.id,
        "ordinal_position": question.ordinal_position,
        "v1_version_number": v1_record.version_number,
        "v2_version_number": v2_record.version_number,
        "has_changes": len(changed_fields) > 0,
        "changed_fields": changed_fields,
        "field_diffs": {
            "question_text": {"changed": stem_changed, "v1": v1_record.question_text, "v2": v2_record.question_text},
            "options": {"changed": options_changed, "v1": v1_opts, "v2": v2_opts},
            "correct_answer": {"changed": correct_answer_changed, "v1": v1_record.correct_answer, "v2": v2_record.correct_answer},
            "rationale": {"changed": rationale_changed, "v1": getattr(v1_record, "rationale", None), "v2": getattr(v2_record, "rationale", None)},
            "supporting_quote": {"changed": quote_changed, "v1": v1_record.supporting_quote, "v2": v2_record.supporting_quote},
            "objective_ids": {"changed": objectives_changed, "v1": v1_objs, "v2": v2_objs},
            "review_status": {"changed": status_changed, "v1": v1_record.review_status, "v2": v2_record.review_status}
        },
        "v1": serialize_v(v1_record, v1_opts, v1_objs, v1_vals),
        "v2": serialize_v(v2_record, v2_opts, v2_objs, v2_vals),
        "version_a": serialize_v(v1_record, v1_opts, v1_objs, v1_vals),
        "version_b": serialize_v(v2_record, v2_opts, v2_objs, v2_vals)
    }
