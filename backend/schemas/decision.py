from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict

class TeacherDecisionCreate(BaseModel):
    action: str = Field(..., description="APPROVED, NEEDS_REVISION, or OVERRIDE")
    acknowledged_warning_ids: List[str] = Field(default_factory=list)
    teacher_notes: Optional[str] = Field(default=None, description="Required if action is OVERRIDE")

    @model_validator(mode="after")
    def validate_override_notes(self):
        normalized_action = self.action.upper()
        if normalized_action == "OVERRIDE":
            if not self.teacher_notes or not self.teacher_notes.strip():
                raise ValueError("Teacher notes explaining the reason are strictly required for an OVERRIDE decision.")
            if not self.acknowledged_warning_ids:
                raise ValueError("Acknowledged warning IDs must be provided when executing an OVERRIDE.")
        self.action = normalized_action
        return self

class TeacherDecisionResponse(BaseModel):
    id: str
    action: str
    acknowledged_warning_ids: List[str] = []
    teacher_notes: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
