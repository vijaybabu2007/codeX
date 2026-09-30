from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.dependencies import require_teacher, get_current_user_optional
from backend.models.user import User
from backend.models.pack import LearningPack
from backend.services.pack_service import generate_and_save_learning_pack, get_pack_details

router = APIRouter(prefix="/packs", tags=["Learning Packs"])

class GeneratePackRequest(BaseModel):
    contract_id: str

@router.post("/generate")
def generate_pack(
    payload: GeneratePackRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    try:
        pack = generate_and_save_learning_pack(db, payload.contract_id)
        # Record pack creator/owner for multi-user isolation
        pack.owner_id = teacher.id
        db.commit()
        return get_pack_details(db, pack.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("/{pack_id}")
def get_pack(
    pack_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Enforce role boundaries: Students must not access raw teacher pack endpoint
    if user and user.role == "student":
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: Students must access learning packs via the Student Portal."
        )

    try:
        pack = db.query(LearningPack).filter(LearningPack.id == pack_id).first()
        if not pack:
            raise HTTPException(status_code=404, detail="Learning pack not found")

        # Multi-user data isolation: If pack is owned by another teacher, enforce ownership
        if user and user.role == "teacher" and pack.owner_id and pack.owner_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: You do not have permission to view or manage another educator's pack."
            )

        return get_pack_details(db, pack_id)
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def list_packs(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Multi-user data isolation: Teachers only list their own packs (plus unassigned legacy demo packs)
    query = db.query(LearningPack)
    if user and user.role == "teacher":
        query = query.filter((LearningPack.owner_id == user.id) | (LearningPack.owner_id == None))
    
    packs = query.order_by(LearningPack.created_at.desc()).all()
    results = []
    for p in packs:
        results.append({
            "id": p.id,
            "contract_id": p.contract_id,
            "contract_title": p.contract.title if p.contract else "Untitled",
            "source_version_id": p.source_version_id,
            "owner_id": p.owner_id,
            "created_at": p.created_at.isoformat()
        })
    return results
