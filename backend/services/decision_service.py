import json
from sqlalchemy.orm import Session
from backend.models.pack import AssetVersion
from backend.models.quiz import QuizQuestionVersion
from backend.models.validation import ValidationReport
from backend.models.decision import TeacherDecision
from backend.schemas.decision import TeacherDecisionCreate

def record_asset_version_decision(
    db: Session,
    asset_version_id: str,
    decision_in: TeacherDecisionCreate
) -> TeacherDecision:
    ver = db.query(AssetVersion).filter(AssetVersion.id == asset_version_id).first()
    if not ver:
        raise ValueError(f"Asset version {asset_version_id} not found.")

    validations = db.query(ValidationReport).filter(ValidationReport.asset_version_id == asset_version_id).all()
    critical_reports = [v for v in validations if v.severity == "CRITICAL"]

    action = decision_in.action.upper()
    if action in ("APPROVED", "APPROVE"):
        if critical_reports:
            blocking_msgs = "; ".join([c.message for c in critical_reports])
            raise ValueError(
                f"Approval blocked: Critical validation error(s) present: {blocking_msgs}. "
                "Resolve the issue or use OVERRIDE with required justification."
            )
        ver.review_status = "APPROVED"

    elif action == "OVERRIDE":
        if not decision_in.teacher_notes or not decision_in.teacher_notes.strip():
            raise ValueError("Teacher notes are required when overriding validation warnings.")
        ver.review_status = "OVERRIDE"

    elif action == "NEEDS_REVISION":
        ver.review_status = "NEEDS_REVISION"
    else:
        ver.review_status = action

    decision = TeacherDecision(
        asset_version_id=ver.id,
        action=ver.review_status,
        acknowledged_warning_ids_json=json.dumps(decision_in.acknowledged_warning_ids),
        teacher_notes=decision_in.teacher_notes
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision

def record_question_version_decision(
    db: Session,
    question_version_id: str,
    decision_in: TeacherDecisionCreate
) -> TeacherDecision:
    ver = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.id == question_version_id).first()
    if not ver:
        raise ValueError(f"Quiz question version {question_version_id} not found.")

    validations = db.query(ValidationReport).filter(ValidationReport.question_version_id == question_version_id).all()
    critical_reports = [v for v in validations if v.severity == "CRITICAL"]

    action = decision_in.action.upper()
    if action in ("APPROVED", "APPROVE"):
        if critical_reports:
            blocking_msgs = "; ".join([c.message for c in critical_reports])
            raise ValueError(
                f"Approval blocked: Critical validation error(s) present: {blocking_msgs}. "
                "Resolve the issue or use OVERRIDE with required justification."
            )
        ver.review_status = "APPROVED"

    elif action == "OVERRIDE":
        if not decision_in.teacher_notes or not decision_in.teacher_notes.strip():
            raise ValueError("Teacher notes are required when overriding validation warnings.")
        ver.review_status = "OVERRIDE"

    elif action == "NEEDS_REVISION":
        ver.review_status = "NEEDS_REVISION"
    else:
        ver.review_status = action

    decision = TeacherDecision(
        question_version_id=ver.id,
        action=ver.review_status,
        acknowledged_warning_ids_json=json.dumps(decision_in.acknowledged_warning_ids),
        teacher_notes=decision_in.teacher_notes
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision
