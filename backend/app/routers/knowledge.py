from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.document import Document, KnowledgeChunk
from app.models.restaurant import Restaurant
from app.schemas.knowledge import DocumentResponse, KnowledgeSearchResult
from app.middleware.auth import get_current_owner
from app.models.owner import Owner
from app.services.document_service import extract_text_sync
from app.services.rag_service import chunk_text, store_chunks, keyword_search

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

ALLOWED_TYPES = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB


@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("general"),
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    """Upload a document, extract text, chunk it, and store in knowledge base."""
    # Validate file extension
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_TYPES}")

    # Read file (sync read via SpooledTemporaryFile)
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    try:
        text = extract_text_sync(content, filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text: {e}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="Document appears to be empty")

    try:
        restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_owner.id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")

        document = Document(
            owner_id=current_owner.id,
            restaurant_id=restaurant.id,
            filename=filename,
            doc_type=doc_type,
            content=text,
        )
        db.add(document)
        db.flush()

        chunks = chunk_text(text)
        count = store_chunks(
            db=db,
            document_id=document.id,
            owner_id=current_owner.id,
            restaurant_id=restaurant.id,
            chunks=chunks,
            doc_type=doc_type,
        )
        document.chunk_count = count
        db.commit()
        db.refresh(document)
        return document
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    return db.query(Document).filter(Document.owner_id == current_owner.id).all()


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.owner_id == current_owner.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)    # Cascades to KnowledgeChunks
    db.commit()
    return {"message": "Document and its chunks deleted"}


@router.get("/search", response_model=List[KnowledgeSearchResult])
def search_knowledge(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    """Test endpoint to search the RAG knowledge base."""
    results = keyword_search(db, current_owner.id, query, top_k=10)
    return [
        KnowledgeSearchResult(
            chunk_text=chunk.chunk_text,
            doc_type=chunk.doc_type,
            document_id=chunk.document_id,
            score=round(score, 3),
        )
        for chunk, score in results
    ]
