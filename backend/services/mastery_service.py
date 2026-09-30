import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models.pack import LearningPack, GeneratedAsset
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.mastery import ObjectiveMastery, StudentQuizAttempt
from backend.schemas.student import (
    ObjectiveMasteryItem,
    ActionLinkItem,
    RecommendedActionItem,
    StudentMasteryResponse,
    StudentQuizResultItem,
)
from backend.services.student_service import get_student_approved_projection, ALLOWED_STUDENT_STATUSES


class MasteryThresholds:
    """
    Central configurable mastery threshold boundaries.
    Single source of truth for deterministic state assignment.
    """
    MASTERED_MIN: float = 90.0      # 90% - 100% -> MASTERED
    DEVELOPING_MIN: float = 60.0    # 60% - 89.9% -> DEVELOPING
    # 0% - 59.9% -> NEEDS_PRACTICE


def determine_mastery_state(score_percentage: float) -> str:
    """
    Deterministically computes the mastery level from percentage.
    """
    if score_percentage >= MasteryThresholds.MASTERED_MIN:
        return "MASTERED"
    elif score_percentage >= MasteryThresholds.DEVELOPING_MIN:
        return "DEVELOPING"
    else:
        return "NEEDS_PRACTICE"


def calculate_and_save_mastery(
    db: Session,
    pack_id: str,
    results: List[StudentQuizResultItem],
    answers: Dict[str, str],
    student_id: str = "default_student",
    total_approved_questions: int = 0,
    overall_percentage: float = 0.0,
    overall_correct: int = 0
) -> tuple[List[ObjectiveMasteryItem], Optional[RecommendedActionItem]]:
    """
    Calculates objective-level performance from quiz results,
    persists records to SQLite, logs attempt history, and generates
    adaptive recommendations strictly within the approved student projection boundary.
    """
    pack = db.query(LearningPack).filter(LearningPack.id == pack_id).first()
    if not pack:
        return [], None

    # Load contract objectives to ensure all objectives are recognized
    contract_objectives: Dict[str, LearningObjective] = {}
    if pack.contract and pack.contract.objectives:
        for obj in pack.contract.objectives:
            contract_objectives[obj.code] = obj

    # Map question_id to approved question versions and their objectives
    quiz_asset = db.query(GeneratedAsset).filter(
        GeneratedAsset.learning_pack_id == pack_id,
        GeneratedAsset.asset_type == "formative_quiz"
    ).first()

    question_objective_map: Dict[str, List[str]] = {}
    if quiz_asset:
        questions = db.query(QuizQuestion).filter(QuizQuestion.asset_id == quiz_asset.id).all()
        for q in questions:
            if q.active_version_id:
                q_ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == q.active_version_id).first()
                if q_ver and q_ver.review_status in ALLOWED_STUDENT_STATUSES:
                    try:
                        lo_list = json.loads(q_ver.objective_ids_json) if q_ver.objective_ids_json else []
                        question_objective_map[q.id] = lo_list
                    except Exception:
                        question_objective_map[q.id] = []

    # Aggregate performance per objective
    # Structure: obj_id -> {"attempted": int, "correct": int}
    obj_stats: Dict[str, Dict[str, int]] = {}

    # Initialize stats for all contract objectives so every objective is evaluated
    for obj_code in contract_objectives.keys():
        obj_stats[obj_code] = {"attempted": 0, "correct": 0}

    # Attribute quiz result outcomes to corresponding objectives
    for item in results:
        mapped_los = question_objective_map.get(item.question_id, [])
        for lo in mapped_los:
            if lo not in obj_stats:
                obj_stats[lo] = {"attempted": 0, "correct": 0}
            obj_stats[lo]["attempted"] += 1
            if item.is_correct:
                obj_stats[lo]["correct"] += 1

    # Convert to ObjectiveMasteryItem list & persist to database
    objective_items: List[ObjectiveMasteryItem] = []
    now = datetime.now(timezone.utc)

    for obj_id, stats in sorted(obj_stats.items()):
        att = stats["attempted"]
        corr = stats["correct"]
        score_pct = round((corr / att * 100.0), 1) if att > 0 else 0.0
        state = determine_mastery_state(score_pct)

        obj_meta = contract_objectives.get(obj_id)
        desc = obj_meta.description if obj_meta else None
        bloom = obj_meta.bloom_level if obj_meta else None

        item_dto = ObjectiveMasteryItem(
            objective_id=obj_id,
            objective_description=desc,
            bloom_level=bloom,
            attempted=att,
            correct=corr,
            score_percentage=score_pct,
            mastery_state=state,
        )
        objective_items.append(item_dto)

        # Upsert persistent record
        existing = db.query(ObjectiveMastery).filter(
            ObjectiveMastery.student_id == student_id,
            ObjectiveMastery.pack_id == pack_id,
            ObjectiveMastery.objective_id == obj_id,
        ).first()

        if existing:
            existing.attempted_count = att
            existing.correct_count = corr
            existing.score_percentage = score_pct
            existing.mastery_state = state
            existing.last_updated = now
        else:
            new_record = ObjectiveMastery(
                student_id=student_id,
                pack_id=pack_id,
                objective_id=obj_id,
                attempted_count=att,
                correct_count=corr,
                score_percentage=score_pct,
                mastery_state=state,
                last_updated=now,
            )
            db.add(new_record)

    # Persist attempt log for audit and progress history
    attempt_log = StudentQuizAttempt(
        student_id=student_id,
        pack_id=pack_id,
        total_questions=total_approved_questions,
        correct_count=overall_correct,
        score_percentage=overall_percentage,
        answers_json=json.dumps(answers),
        created_at=now,
    )
    db.add(attempt_log)
    db.commit()

    # Generate adaptive recommendation based on approved projection
    recommendation = generate_adaptive_recommendation(db, pack_id, objective_items)
    return objective_items, recommendation


def generate_adaptive_recommendation(
    db: Session,
    pack_id: str,
    objectives: List[ObjectiveMasteryItem]
) -> Optional[RecommendedActionItem]:
    """
    Deterministic Recommendation Engine:
    - NEVER fabricates material
    - Strictly checks the student-approved projection boundary
    - Never recommends an unapproved asset
    - Generates evidence-based, explainable rationale
    """
    if not objectives:
        return None

    # Fetch verified student approved projection
    try:
        projection = get_student_approved_projection(db, pack_id)
    except Exception:
        return None

    # Check available approved assets in student view
    has_concept = projection.concept_explanation is not None
    has_worked_example = projection.worked_example is not None
    has_easy_practice = projection.easy_practice is not None
    has_advanced_practice = projection.advanced_practice is not None
    has_revision_sheet = projection.revision_sheet is not None
    has_quiz = len(projection.quiz_questions) > 0

    # Prioritize lowest performing objective
    # Order: NEEDS_PRACTICE (lowest score) -> DEVELOPING (lowest score) -> MASTERED
    needs_practice = [o for o in objectives if o.mastery_state == "NEEDS_PRACTICE"]
    developing = [o for o in objectives if o.mastery_state == "DEVELOPING"]
    mastered = [o for o in objectives if o.mastery_state == "MASTERED"]

    target_obj: ObjectiveMasteryItem
    if needs_practice:
        # Sort by attempted desc, score asc
        target_obj = sorted(needs_practice, key=lambda x: (x.score_percentage, -x.attempted))[0]
    elif developing:
        target_obj = sorted(developing, key=lambda x: (x.score_percentage, -x.attempted))[0]
    else:
        target_obj = sorted(mastered, key=lambda x: -x.score_percentage)[0]

    actions: List[ActionLinkItem] = []
    headline: str
    explanation: str

    if target_obj.mastery_state == "NEEDS_PRACTICE":
        if target_obj.attempted > 0:
            explanation = (
                f"Recommended because you answered {target_obj.correct} of {target_obj.attempted} "
                f"{target_obj.objective_id} questions correctly ({target_obj.score_percentage}%)."
            )
        else:
            explanation = (
                f"Recommended because {target_obj.objective_id} has not yet been practiced in this quiz."
            )
        headline = f"Strengthen {target_obj.objective_id} before moving to advanced practice."

        # Rule for NEEDS_PRACTICE: 1. Review Concept, 2. Easy Practice, 3. Voice Tutor
        if has_concept:
            actions.append(ActionLinkItem(
                label="Review Concept",
                action="REVIEW_CONCEPT",
                target="concept_explanation"
            ))
        if has_easy_practice:
            actions.append(ActionLinkItem(
                label="Try Easy Practice",
                action="EASY_PRACTICE",
                target="easy_practice"
            ))
        actions.append(ActionLinkItem(
            label=f"Ask Voice Tutor about {target_obj.objective_id}",
            action="ASK_VOICE_TUTOR",
            target="voice_tutor",
            prompt=f"Help me understand {target_obj.objective_id} because I am struggling with this objective."
        ))
        if not has_concept and not has_easy_practice and has_revision_sheet:
            actions.append(ActionLinkItem(
                label="Review Summary Sheet",
                action="REVISION_SHEET",
                target="revision_sheet"
            ))

    elif target_obj.mastery_state == "DEVELOPING":
        explanation = (
            f"Recommended because you answered {target_obj.correct} of {target_obj.attempted} "
            f"{target_obj.objective_id} questions correctly ({target_obj.score_percentage}%)."
        )
        headline = f"Reinforce {target_obj.objective_id} to achieve full mastery."

        # Rule for DEVELOPING: 1. Guided / Worked Example, 2. Easy Practice, 3. Retry Quiz
        if has_worked_example:
            actions.append(ActionLinkItem(
                label="Guided Worked Example",
                action="WORKED_EXAMPLE",
                target="worked_example"
            ))
        if has_easy_practice:
            actions.append(ActionLinkItem(
                label="Try Easy Practice",
                action="EASY_PRACTICE",
                target="easy_practice"
            ))
        if has_quiz:
            actions.append(ActionLinkItem(
                label="Retry Quiz",
                action="RETRY_QUIZ",
                target="quiz"
            ))
        actions.append(ActionLinkItem(
            label=f"Ask Voice Tutor about {target_obj.objective_id}",
            action="ASK_VOICE_TUTOR",
            target="voice_tutor",
            prompt=f"Help me practice {target_obj.objective_id} with another step-by-step example."
        ))

    else:  # MASTERED
        explanation = (
            f"Recommended because you demonstrated {target_obj.score_percentage}% mastery across all "
            f"{target_obj.attempted} question(s) for {target_obj.objective_id}."
        )
        headline = f"Mastery Achieved for {target_obj.objective_id}! Ready for advanced synthesis."

        # Rule for MASTERED: 1. Advanced Practice, 2. Continue to next objective / revision
        if has_advanced_practice:
            actions.append(ActionLinkItem(
                label="Attempt Advanced Practice",
                action="ADVANCED_PRACTICE",
                target="advanced_practice"
            ))
        if has_revision_sheet:
            actions.append(ActionLinkItem(
                label="Review High-Yield Summary",
                action="REVISION_SHEET",
                target="revision_sheet"
            ))
        actions.append(ActionLinkItem(
            label=f"Ask Voice Tutor for Challenge",
            action="ASK_VOICE_TUTOR",
            target="voice_tutor",
            prompt=f"Give me an advanced challenge problem on {target_obj.objective_id} to test my deep understanding."
        ))

    return RecommendedActionItem(
        objective_id=target_obj.objective_id,
        mastery_state=target_obj.mastery_state,
        headline=headline,
        explanation=explanation,
        actions=actions
    )


def get_student_mastery(db: Session, pack_id: str, student_id: str) -> StudentMasteryResponse:
    """
    Fetches persisted objective performance and adaptive recommendation for a student.
    """
    pack = db.query(LearningPack).filter(LearningPack.id == pack_id).first()
    if not pack:
        raise ValueError(f"Learning Pack with ID {pack_id} not found.")

    contract_objectives: Dict[str, LearningObjective] = {}
    if pack.contract and pack.contract.objectives:
        for obj in pack.contract.objectives:
            contract_objectives[obj.code] = obj

    records = db.query(ObjectiveMastery).filter(
        ObjectiveMastery.student_id == student_id,
        ObjectiveMastery.pack_id == pack_id
    ).all()

    record_map = {r.objective_id: r for r in records}
    items: List[ObjectiveMasteryItem] = []

    # Ensure all objectives in contract are represented
    for code, obj in sorted(contract_objectives.items()):
        rec = record_map.get(code)
        if rec:
            items.append(ObjectiveMasteryItem(
                objective_id=code,
                objective_description=obj.description,
                bloom_level=obj.bloom_level,
                attempted=rec.attempted_count,
                correct=rec.correct_count,
                score_percentage=rec.score_percentage,
                mastery_state=rec.mastery_state,
            ))
        else:
            items.append(ObjectiveMasteryItem(
                objective_id=code,
                objective_description=obj.description,
                bloom_level=obj.bloom_level,
                attempted=0,
                correct=0,
                score_percentage=0.0,
                mastery_state="NEEDS_PRACTICE",
            ))

    total_attempts = db.query(StudentQuizAttempt).filter(
        StudentQuizAttempt.student_id == student_id,
        StudentQuizAttempt.pack_id == pack_id
    ).count()

    recommendation = generate_adaptive_recommendation(db, pack_id, items)

    return StudentMasteryResponse(
        pack_id=pack_id,
        student_id=student_id,
        objectives=items,
        recommended_action=recommendation,
        total_attempts=total_attempts
    )
