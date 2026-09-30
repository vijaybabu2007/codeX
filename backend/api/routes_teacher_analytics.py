from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import require_teacher
from backend.models.user import User
from backend.services.teacher_analytics_service import (
    get_teacher_student_analytics,
    get_teacher_student_detail
)

router = APIRouter(prefix="/teacher/analytics", tags=["Teacher Analytics & Student Performance"])


@router.get("/overview")
def get_teacher_student_performance_overview(
    pack_id: Optional[str] = Query(None, description="Optional filter by learning pack ID, or 'all'"),
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Teacher Executive Dashboard: Student Performance & Curricular Analytics.
    - Protected: strictly accessible only to authenticated users with the TEACHER role.
    - Returns class-wide average scores, mastery distribution tiers, objective analysis, student roster, and recent attempt logs.
    """
    try:
        return get_teacher_student_analytics(db, teacher_id=teacher.id, pack_id=pack_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch student performance analytics: {str(e)}"
        )


@router.get("/student/{student_id}")
def get_teacher_student_detail_report(
    student_id: str,
    pack_id: Optional[str] = Query(None, description="Optional pack ID context"),
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Teacher Student Diagnostic Dossier:
    - Detailed drilldown for an individual student: objective breakdowns, chronological quiz attempts with question responses, and adaptive intervention recommendations.
    - Protected: strictly accessible only to authenticated users with the TEACHER role.
    """
    try:
        return get_teacher_student_detail(db, student_id=student_id, pack_id=pack_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch student diagnostic report: {str(e)}"
        )
