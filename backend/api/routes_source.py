from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.source import SourceDocument, SourceVersion
from backend.schemas.source import SourceTextCreate, SourceVersionResponse, SourceDocumentResponse
from backend.services.source_service import (
    create_source_document_and_version,
    extract_text_from_pdf,
    normalize_text
)

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.post("/text", response_model=SourceVersionResponse)
def upload_source_text(
    payload: SourceTextCreate,
    document_id: str | None = None,
    db: Session = Depends(get_db)
):
    try:
        version = create_source_document_and_version(
            db=db,
            name=payload.name,
            raw_text=payload.text,
            mime_type="text/plain",
            document_id=document_id
        )
        return version
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process source text: {str(e)}")

@router.post("/file", response_model=SourceVersionResponse)
async def upload_source_file(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    document_id: str | None = Form(None),
    db: Session = Depends(get_db)
):
    try:
        content_bytes = await file.read()
        file_name = name or file.filename or "Uploaded Source Document"
        mime = file.content_type or "text/plain"

        if file.filename and file.filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(content_bytes)
            mime = "application/pdf"
        else:
            extracted_text = content_bytes.decode("utf-8", errors="replace")

        version = create_source_document_and_version(
            db=db,
            name=file_name,
            raw_text=extracted_text,
            mime_type=mime,
            document_id=document_id
        )
        return version
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file upload: {str(e)}")

@router.get("", response_model=list[SourceDocumentResponse])
def list_source_documents(db: Session = Depends(get_db)):
    docs = db.query(SourceDocument).order_by(SourceDocument.created_at.desc()).all()
    results = []
    for d in docs:
        active = d.versions[-1] if d.versions else None
        results.append(
            SourceDocumentResponse(
                id=d.id,
                name=d.name,
                created_at=d.created_at,
                active_version=SourceVersionResponse.model_validate(active) if active else None,
                versions=[SourceVersionResponse.model_validate(v) for v in d.versions]
            )
        )
    return results

@router.get("/{document_id}/versions", response_model=list[SourceVersionResponse])
def get_document_versions(document_id: str, db: Session = Depends(get_db)):
    versions = (
        db.query(SourceVersion)
        .filter(SourceVersion.source_document_id == document_id)
        .order_by(SourceVersion.version_number.asc())
        .all()
    )
    if not versions:
        raise HTTPException(status_code=404, detail="Source document not found or has no versions.")
    return versions
