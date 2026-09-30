from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.dependencies import (
    require_student,
    require_authenticated_user,
    get_current_user_optional
)
from backend.models.user import User
from backend.models.pack import LearningPack
from backend.schemas.student import (
    StudentPackResponse,
    StudentQuizSubmissionRequest,
    StudentQuizScoreResponse,
    StudentVoiceQueryRequest,
    StudentVoiceQueryResponse,
    StudentMasteryResponse
)
from backend.services.student_service import (
    get_student_approved_projection,
    score_student_quiz
)
from backend.services.mastery_service import get_student_mastery
from backend.services.voice_service import query_voice_tutor

router = APIRouter(prefix="/student", tags=["Student Projection"])

@router.get("/dashboard")
def get_student_dashboard(
    user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Dedicated Student Dashboard:
    - Accessible to authenticated users (both students and educators previewing student experience)
    - Lists available approved learning packs
    - Excludes teacher notes, draft assets, validation reports, and audit metadata
    """
    packs = db.query(LearningPack).order_by(LearningPack.created_at.desc()).all()
    available_packs = []
    for p in packs:
        try:
            proj = get_student_approved_projection(db, p.id)
            available_packs.append({
                "pack_id": p.id,
                "title": proj.contract_title,
                "target_learner_level": proj.target_learner_level,
                "has_quiz": len(proj.quiz_questions) > 0,
                "question_count": len(proj.quiz_questions),
                "created_at": p.created_at.isoformat()
            })
        except Exception:
            continue

    return {
        "student_name": user.name,
        "email": user.email,
        "available_packs": available_packs,
        "count": len(available_packs)
    }

@router.get("/packs/{pack_id}", response_model=StudentPackResponse)
def get_student_pack(
    pack_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    try:
        # Server-enforced: only approved and override items are returned
        return get_student_approved_projection(db, pack_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch student projection: {str(e)}")

@router.post("/packs/{pack_id}/submit-quiz", response_model=StudentQuizScoreResponse)
def submit_student_quiz_endpoint(
    pack_id: str,
    payload: StudentQuizSubmissionRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Enforce role boundary: Teachers cannot submit student quizzes
    if user and user.role == "teacher":
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: Teacher role cannot submit student quizzes."
        )

    student_id = user.id if user else "default_student"
    try:
        return score_student_quiz(db, pack_id, payload.answers, student_id=student_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to score quiz: {str(e)}")

@router.get("/packs/{pack_id}/mastery", response_model=StudentMasteryResponse)
def get_student_mastery_endpoint(
    pack_id: str,
    student_id: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Returns objective-level learning progress, mastery states, and next-learning recommendation.
    Enforces student isolation: students can only view their own mastery records.
    """
    if user and user.role == "student":
        if student_id and student_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: Cannot access another student's mastery data."
            )
        effective_student_id = user.id
    elif student_id:
        effective_student_id = student_id
    elif user:
        effective_student_id = user.id
    else:
        effective_student_id = "default_student"

    try:
        return get_student_mastery(db, pack_id, effective_student_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch student mastery: {str(e)}")

@router.post("/voice/query", response_model=StudentVoiceQueryResponse)
def voice_tutor_query_endpoint(
    payload: StudentVoiceQueryRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Student-facing Voice Tutor query endpoint:
    - Only accesses approved/override content
    - Excludes draft, needs-revision, and teacher metadata
    - Answers concisely for browser SpeechSynthesis audio playback
    - Rejects teacher role bypass
    """
    if user and user.role == "teacher":
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: Teachers cannot use Student Voice Tutor as a bypass mechanism."
        )

    try:
        return query_voice_tutor(db, payload)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice Tutor query failed: {str(e)}")
