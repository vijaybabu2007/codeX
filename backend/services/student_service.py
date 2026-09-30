import json
from sqlalchemy.orm import Session
from backend.models.pack import LearningPack, GeneratedAsset, AssetVersion
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.schemas.student import (
    StudentPackResponse,
    StudentExplanationItem,
    StudentQuestionItem,
    StudentWorkedExampleItem,
    StudentPracticeTaskItem,
    StudentRevisionSheetItem,
    StudentQuizResultItem,
    StudentQuizScoreResponse
)

ALLOWED_STUDENT_STATUSES = {"APPROVED", "OVERRIDE"}

def get_student_approved_projection(db: Session, pack_id: str) -> StudentPackResponse:
    pack = db.query(LearningPack).filter(LearningPack.id == pack_id).first()
    if not pack:
        raise ValueError(f"Learning Pack with ID {pack_id} not found.")

    contract = pack.contract

    def get_approved_asset_content(asset_type: str):
        asset = db.query(GeneratedAsset).filter(
            GeneratedAsset.learning_pack_id == pack_id,
            GeneratedAsset.asset_type == asset_type
        ).first()
        if not asset or not asset.active_version_id:
            return None, None
        ver = db.query(AssetVersion).filter(AssetVersion.id == asset.active_version_id).first()
        # SERVER-ENFORCED FILTER: Only APPROVED or OVERRIDE
        if ver and ver.review_status in ALLOWED_STUDENT_STATUSES:
            return ver.id, json.loads(ver.content_json)
        return None, None

    # 1. Concept Explanation
    exp_id, exp_content = get_approved_asset_content("concept_explanation")
    student_explanation = None
    if exp_content:
        student_explanation = StudentExplanationItem(
            id=exp_id,
            title=exp_content.get("title", ""),
            explanation=exp_content.get("explanation", ""),
            objective_ids=exp_content.get("objective_ids", [])
        )

    # 2. Worked Example
    we_id, we_content = get_approved_asset_content("worked_example")
    student_worked_example = None
    if we_content:
        student_worked_example = StudentWorkedExampleItem(
            id=we_id,
            title=we_content.get("title", ""),
            scenario=we_content.get("scenario", ""),
            steps=we_content.get("steps", []),
            final_answer=we_content.get("final_answer", ""),
            objective_ids=we_content.get("objective_ids", [])
        )

    # 3. Formative Quiz Questions (Approved Only)
    quiz_asset = db.query(GeneratedAsset).filter(
        GeneratedAsset.learning_pack_id == pack_id,
        GeneratedAsset.asset_type == "formative_quiz"
    ).first()

    student_questions = []
    if quiz_asset:
        questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.asset_id == quiz_asset.id)
            .order_by(QuizQuestion.ordinal_position)
            .all()
        )
        for q in questions:
            if q.active_version_id:
                q_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == q.active_version_id).first()
                if q_ver and q_ver.review_status in ALLOWED_STUDENT_STATUSES:
                    student_questions.append(
                        StudentQuestionItem(
                            id=q.id,
                            question_text=q_ver.question_text,
                            options=json.loads(q_ver.options_json),
                            objective_ids=json.loads(q_ver.objective_ids_json)
                        )
                    )

    # 4. Easy Practice
    ep_id, ep_content = get_approved_asset_content("easy_practice")
    student_easy = None
    if ep_content:
        student_easy = StudentPracticeTaskItem(
            id=ep_id,
            title=ep_content.get("title", ""),
            problem_statement=ep_content.get("problem_statement", ""),
            solution_guidance=ep_content.get("solution_guidance", ""),
            objective_ids=ep_content.get("objective_ids", []),
            bloom_level=ep_content.get("bloom_level", "Understand"),
            difficulty_label=ep_content.get("difficulty_label", "Easy")
        )

    # 5. Advanced Practice
    ap_id, ap_content = get_approved_asset_content("advanced_practice")
    student_advanced = None
    if ap_content:
        student_advanced = StudentPracticeTaskItem(
            id=ap_id,
            title=ap_content.get("title", ""),
            problem_statement=ap_content.get("problem_statement", ""),
            solution_guidance=ap_content.get("solution_guidance", ""),
            objective_ids=ap_content.get("objective_ids", []),
            bloom_level=ap_content.get("bloom_level", "Analyze"),
            difficulty_label=ap_content.get("difficulty_label", "Advanced")
        )

    # 6. Revision Sheet
    rev_id, rev_content = get_approved_asset_content("revision_sheet")
    student_revision = None
    if rev_content:
        student_revision = StudentRevisionSheetItem(
            id=rev_id,
            title=rev_content.get("title", ""),
            key_concepts=rev_content.get("key_concepts", []),
            definitions=rev_content.get("definitions", []),
            important_relationships=rev_content.get("important_relationships", []),
            key_example=rev_content.get("key_example", ""),
            common_mistakes=rev_content.get("common_mistakes", []),
            objective_ids=rev_content.get("objective_ids", [])
        )

    message = None
    total_approved = sum([
        1 if student_explanation else 0,
        1 if student_worked_example else 0,
        len(student_questions),
        1 if student_easy else 0,
        1 if student_advanced else 0,
        1 if student_revision else 0
    ])

    if total_approved == 0:
        message = "No approved learning materials are currently published for this pack. Content is pending instructor review."

    return StudentPackResponse(
        pack_id=pack.id,
        contract_title=contract.title,
        target_learner_level=contract.target_learner_level,
        source_version_id=pack.source_version_id,
        concept_explanation=student_explanation,
        worked_example=student_worked_example,
        quiz_questions=student_questions,
        easy_practice=student_easy,
        advanced_practice=student_advanced,
        revision_sheet=student_revision,
        message=message
    )

def score_student_quiz(db: Session, pack_id: str, answers: dict[str, str], student_id: str = "default_student") -> StudentQuizScoreResponse:
    """
    Evaluates student quiz responses against approved question versions:
    - Never uses draft or unapproved content.
    - Evaluates each question's selected answer against the immutable correct answer.
    - Returns itemized correct/incorrect outcomes, rationales, and overall percentage score.
    - Integrates Adaptive Mastery Engine to attribute performance to learning objectives,
      persist objective mastery records, and produce deterministic next-learning recommendations.
    """
    pack = db.query(LearningPack).filter(LearningPack.id == pack_id).first()
    if not pack:
        raise ValueError(f"Learning Pack with ID {pack_id} not found.")

    quiz_asset = db.query(GeneratedAsset).filter(
        GeneratedAsset.learning_pack_id == pack_id,
        GeneratedAsset.asset_type == "formative_quiz"
    ).first()

    if not quiz_asset:
        return StudentQuizScoreResponse(
            pack_id=pack_id,
            total_questions=0,
            correct_count=0,
            score_percentage=0.0,
            results=[],
            objective_performance=[],
            recommended_action=None
        )

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.asset_id == quiz_asset.id)
        .order_by(QuizQuestion.ordinal_position)
        .all()
    )

    results = []
    correct_count = 0
    total_approved = 0

    for q in questions:
        if not q.active_version_id:
            continue
        q_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == q.active_version_id).first()
        if not q_ver or q_ver.review_status not in ALLOWED_STUDENT_STATUSES:
            continue

        total_approved += 1
        student_ans = answers.get(q.id) or answers.get(str(q.ordinal_position)) or ""
        correct_ans = q_ver.correct_answer or ""

        # Normalize comparison
        norm_student = student_ans.strip().lower()
        norm_correct = correct_ans.strip().lower()

        is_match = False
        if norm_student and norm_correct:
            if norm_student == norm_correct:
                is_match = True
            elif norm_student in norm_correct or norm_correct in norm_student:
                is_match = True

        if is_match:
            correct_count += 1

        results.append(
            StudentQuizResultItem(
                question_id=q.id,
                question_text=q_ver.question_text,
                selected_answer=student_ans if student_ans else None,
                correct_answer=q_ver.correct_answer,
                is_correct=is_match,
                rationale=getattr(q_ver, "rationale", None)
            )
        )

    percentage = round((correct_count / total_approved * 100.0), 1) if total_approved > 0 else 0.0

    # Deterministic Adaptive Mastery Engine Evaluation
    from backend.services.mastery_service import calculate_and_save_mastery
    objective_perf, recommended_act = calculate_and_save_mastery(
        db=db,
        pack_id=pack_id,
        results=results,
        answers=answers,
        student_id=student_id,
        total_approved_questions=total_approved,
        overall_percentage=percentage,
        overall_correct=correct_count
    )

    return StudentQuizScoreResponse(
        pack_id=pack_id,
        total_questions=total_approved,
        correct_count=correct_count,
        score_percentage=percentage,
        results=results,
        objective_performance=objective_perf,
        recommended_action=recommended_act
    )
