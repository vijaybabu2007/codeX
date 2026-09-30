from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SourceTextCreate(BaseModel):
    name: str = Field(..., description="Friendly title/name for the source")
    text: str = Field(..., min_length=10, description="Raw source text")

class SourceVersionResponse(BaseModel):
    id: str
    source_document_id: str
    version_number: int
    raw_text: str
    cleaned_text: str
    sha256_hash: str
    char_count: int
    mime_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SourceDocumentResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    active_version: SourceVersionResponse | None = None
    versions: list[SourceVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)
