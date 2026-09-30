from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.dependencies import require_teacher
from backend.models.user import User
from backend.schemas.decision import TeacherDecisionCreate, TeacherDecisionResponse
from backend.services.decision_service import (
    record_asset_version_decision,
    record_question_version_decision
)

router = APIRouter(prefix="/decisions", tags=["Teacher Review Decisions"])

@router.post("/asset-versions/{version_id}", response_model=TeacherDecisionResponse)
def review_asset_version(
    version_id: str,
    payload: TeacherDecisionCreate,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    try:
        decision = record_asset_version_decision(db, version_id, payload)
        return decision
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review decision failed: {str(e)}")

@router.post("/question-versions/{version_id}", response_model=TeacherDecisionResponse)
def review_question_version(
    version_id: str,
    payload: TeacherDecisionCreate,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    try:
        decision = record_question_version_decision(db, version_id, payload)
        return decision
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review decision failed: {str(e)}")
