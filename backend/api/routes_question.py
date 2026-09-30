from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.dependencies import require_teacher
from backend.models.user import User
from backend.services.pack_service import (
    regenerate_quiz_question,
    get_question_details,
    edit_quiz_question,
    diff_quiz_question_versions
)

router = APIRouter(prefix="/questions", tags=["Quiz Questions"])

class QuestionRegenerateRequest(BaseModel):
    teacher_notes: Optional[str] = ""
    reason: Optional[str] = ""

class QuestionEditRequest(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    supporting_quote: Optional[str] = None
    rationale: Optional[str] = None
    teacher_notes: Optional[str] = None
    reason: Optional[str] = None
    objective_ids: Optional[List[str]] = None

@router.post("/{question_id}/regenerate")
def regenerate_question_endpoint(
    question_id: str,
    payload: QuestionRegenerateRequest = QuestionRegenerateRequest(),
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    try:
        result = regenerate_quiz_question(
            db=db,
            question_id=question_id,
            teacher_notes=payload.teacher_notes or "",
            reason=payload.reason or ""
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question regeneration failed: {str(e)}")

@router.post("/{question_id}/edit")
def edit_question_endpoint(
    question_id: str,
    payload: QuestionEditRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    try:
        result = edit_quiz_question(
            db=db,
            question_id=question_id,
            question_text=payload.question_text,
            options=payload.options,
            correct_answer=payload.correct_answer,
            supporting_quote=payload.supporting_quote,
            rationale=payload.rationale,
            teacher_notes=payload.teacher_notes,
            reason=payload.reason,
            objective_ids=payload.objective_ids
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question edit failed: {str(e)}")

@router.get("/{question_id}/diff")
def diff_question_endpoint(
    question_id: str,
    v1: Optional[int] = Query(None, description="First version number (default: previous version)"),
    v2: Optional[int] = Query(None, description="Second version number (default: active/latest version)"),
    db: Session = Depends(get_db)
):
    try:
        return diff_quiz_question_versions(db, question_id, v1_number=v1, v2_number=v2)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{question_id}")
def get_question_endpoint(
    question_id: str,
    db: Session = Depends(get_db)
):
    try:
        return get_question_details(db, question_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
