import json
from sqlalchemy.orm import Session
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.source import SourceVersion
from backend.schemas.contract import ContractCreate

def create_objective_contract(db: Session, contract_in: ContractCreate) -> ObjectiveContract:
    # Verify source version exists
    src_ver = db.query(SourceVersion).filter(SourceVersion.id == contract_in.source_version_id).first()
    if not src_ver:
        raise ValueError(f"Source version {contract_in.source_version_id} does not exist.")

    if len(contract_in.objectives) < 2:
        raise ValueError("An Objective Contract must define at least 2 learning objectives.")

    contract = ObjectiveContract(
        source_version_id=contract_in.source_version_id,
        title=contract_in.title,
        target_learner_level=contract_in.target_learner_level,
        expected_difficulty=contract_in.expected_difficulty,
        constraints_json=json.dumps(contract_in.constraints)
    )
    db.add(contract)
    db.flush()

    for idx, obj in enumerate(contract_in.objectives):
        code = obj.code.strip() or f"LO-{idx+1:02d}"
        lo = LearningObjective(
            contract_id=contract.id,
            code=code,
            description=obj.description.strip(),
            bloom_level=obj.bloom_level
        )
        db.add(lo)

    db.commit()
    db.refresh(contract)
    return contract
