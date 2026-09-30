from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

class ObjectiveItem(BaseModel):
    code: str = Field(..., description="Unique code e.g. LO-01")
    description: str = Field(..., min_length=5, description="Clear statement of objective")
    bloom_level: str = Field(default="Understand", description="Bloom's taxonomy level")

class ContractCreate(BaseModel):
    source_version_id: str
    title: str = Field(..., min_length=3)
    target_learner_level: str = Field(..., description="e.g. Grade 10, Undergraduate")
    expected_difficulty: str = Field(default="Medium", description="Introductory, Medium, Advanced")
    objectives: list[ObjectiveItem] = Field(..., min_length=2, description="At least 2 learning objectives")
    constraints: dict = Field(default_factory=dict, description="Vocabulary, length, or reveal constraints")

    @model_validator(mode="after")
    def validate_min_objectives(self):
        if len(self.objectives) < 2:
            raise ValueError("An Objective Contract must define at least 2 learning objectives.")
        return self

class ObjectiveResponse(BaseModel):
    id: str
    code: str
    description: str
    bloom_level: str

    model_config = ConfigDict(from_attributes=True)

class ContractResponse(BaseModel):
    id: str
    source_version_id: str
    title: str
    target_learner_level: str
    expected_difficulty: str
    constraints: dict = Field(default_factory=dict)
    objectives: list[ObjectiveResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
