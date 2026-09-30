from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.contract import ObjectiveContract
from backend.schemas.contract import ContractCreate, ContractResponse, ObjectiveResponse
from backend.services.contract_service import create_objective_contract

router = APIRouter(prefix="/contracts", tags=["Objective Contracts"])

@router.post("", response_model=ContractResponse)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    try:
        contract = create_objective_contract(db, payload)
        return ContractResponse(
            id=contract.id,
            source_version_id=contract.source_version_id,
            title=contract.title,
            target_learner_level=contract.target_learner_level,
            expected_difficulty=contract.expected_difficulty,
            constraints={},
            objectives=[ObjectiveResponse.model_validate(o) for o in contract.objectives],
            created_at=contract.created_at
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract creation failed: {str(e)}")

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(ObjectiveContract).filter(ObjectiveContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return ContractResponse(
        id=contract.id,
        source_version_id=contract.source_version_id,
        title=contract.title,
        target_learner_level=contract.target_learner_level,
        expected_difficulty=contract.expected_difficulty,
        constraints={},
        objectives=[ObjectiveResponse.model_validate(o) for o in contract.objectives],
        created_at=contract.created_at
    )
