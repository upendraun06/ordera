"""
RAG (Retrieval-Augmented Generation) Service
Handles document processing, chunking, and keyword-based search.
Phase 2 will upgrade to semantic vector search via pgvector.
"""
import re
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.document import Document, KnowledgeChunk

# Chunk configuration
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 100     # overlap between chunks for context continuity


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    text = text.strip()
    if not text:
        return []

    # If text fits in one chunk, return as-is
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary (only if not the last chunk)
        if end < len(text):
            last_period = chunk.rfind(". ")
            if last_period > chunk_size // 2:
                chunk = chunk[: last_period + 1]

        stripped = chunk.strip()
        if stripped:
            chunks.append(stripped)

        # If this chunk reaches the end of text, we're done
        if end >= len(text):
            break

        # Advance: step forward by (chunk_length - overlap)
        # Minimum step is (chunk_size - overlap) to prevent tiny chunks
        step = max(len(chunk) - overlap, chunk_size - overlap)
        start += step

    return chunks


def store_chunks(
    db: Session,
    document_id: str,
    owner_id: str,
    restaurant_id: str,
    chunks: List[str],
    doc_type: str,
) -> int:
    """Store text chunks into knowledge_chunks table."""
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).delete()

    for idx, chunk_text_val in enumerate(chunks):
        chunk = KnowledgeChunk(
            document_id=document_id,
            owner_id=owner_id,
            restaurant_id=restaurant_id,
            chunk_text=chunk_text_val,
            doc_type=doc_type,
            chunk_index=idx,
        )
        db.add(chunk)

    db.flush()
    return len(chunks)


def keyword_search(
    db: Session,
    owner_id: str,
    query: str,
    top_k: int = 5,
    restaurant_id: str = None,
) -> List[Tuple[KnowledgeChunk, float]]:
    """
    Keyword-based search over knowledge chunks.
    Returns list of (chunk, score) tuples sorted by relevance.
    Score = number of matching keywords / total keywords.
    """
    if not query.strip():
        return []

    # Tokenize query
    stop_words = {"is", "the", "a", "an", "and", "or", "for", "of", "to", "in", "do", "i", "we", "you"}
    query_tokens = [
        w.lower()
        for w in re.findall(r"\b\w+\b", query)
        if w.lower() not in stop_words and len(w) > 2
    ]

    if not query_tokens:
        return []

    # Fetch all chunks for this owner
    q = db.query(KnowledgeChunk).filter(KnowledgeChunk.owner_id == owner_id)
    if restaurant_id:
        q = q.filter(KnowledgeChunk.restaurant_id == restaurant_id)
    chunks = q.all()

    # Score each chunk
    scored = []
    for chunk in chunks:
        text_lower = chunk.chunk_text.lower()
        matches = sum(1 for token in query_tokens if token in text_lower)
        if matches > 0:
            score = matches / len(query_tokens)
            scored.append((chunk, score))

    # Sort by score descending, return top_k
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def build_rag_context(
    db: Session,
    owner_id: str,
    query: str,
    restaurant_id: str = None,
) -> str:
    """
    Run RAG search and format results as context string for Claude system prompt.
    """
    results = keyword_search(db, owner_id, query, top_k=5, restaurant_id=restaurant_id)
    if not results:
        return ""

    context_parts = []
    for chunk, score in results:
        context_parts.append(
            f"[{chunk.doc_type.upper()} DOCUMENT]\n{chunk.chunk_text}"
        )

    return "\n\n---\n\n".join(context_parts)
