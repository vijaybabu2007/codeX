from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ValidationReportItem(BaseModel):
    id: str
    validation_type: str  # "GROUNDING", "KEY_INTEGRITY"
    severity: str         # "CRITICAL", "WARNING"
    rule_code: str
    message: str
    evidence_snippet: str | None = None
    affected_entity_id: str
    is_blocking: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
