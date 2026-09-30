import hashlib
import re
from io import BytesIO
from pypdf import PdfReader
from sqlalchemy.orm import Session
from backend.models.source import SourceDocument, SourceVersion

def normalize_text(text: str) -> str:
    """Normalize text: convert windows newlines, normalize spaces, strip null bytes."""
    text = text.replace("\x00", "")
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def compute_sha256(text: str) -> str:
    """Compute standard SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract readable text from PDF bytes."""
    reader = PdfReader(BytesIO(pdf_bytes))
    extracted = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted.append(page_text)
    return "\n\n".join(extracted)

def create_source_document_and_version(
    db: Session,
    name: str,
    raw_text: str,
    mime_type: str = "text/plain",
    document_id: str | None = None
) -> SourceVersion:
    cleaned = normalize_text(raw_text)
    if not cleaned:
        raise ValueError("Source text cannot be empty or only whitespace.")

    sha256 = compute_sha256(cleaned)
    char_count = len(cleaned)

    if document_id:
        doc = db.query(SourceDocument).filter(SourceDocument.id == document_id).first()
        if not doc:
            raise ValueError(f"Source document with ID {document_id} not found.")
        # Find next version number
        max_ver = (
            db.query(SourceVersion.version_number)
            .filter(SourceVersion.source_document_id == document_id)
            .order_by(SourceVersion.version_number.desc())
            .first()
        )
        next_ver = (max_ver[0] + 1) if max_ver else 1
    else:
        doc = SourceDocument(name=name)
        db.add(doc)
        db.flush()
        next_ver = 1

    version = SourceVersion(
        source_document_id=doc.id,
        version_number=next_ver,
        raw_text=raw_text,
        cleaned_text=cleaned,
        sha256_hash=sha256,
        char_count=char_count,
        mime_type=mime_type
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version
