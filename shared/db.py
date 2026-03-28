import json
import math
from pathlib import Path

# Local storage paths
DATA_DIR = Path(__file__).parent.parent / "insurance" / "data"
DOCUMENTS_FILE = DATA_DIR / "documents.json"
EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"


# ── Local Storage Helpers ────────────────────────────────────────────────

def load_documents() -> list[dict]:
    """Load all insurance documents from local JSON file."""
    if not DOCUMENTS_FILE.exists():
        return []
    with open(DOCUMENTS_FILE, 'r') as f:
        return json.load(f)


def load_embeddings() -> dict[str, list[float]]:
    """Load all embeddings from local JSON file.
    
    Returns:
        Dict mapping document ID (as string) to embedding vector.
    """
    if not EMBEDDINGS_FILE.exists():
        return {}
    
    with open(EMBEDDINGS_FILE, 'r') as f:
        return json.load(f)


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def match_insurance_docs(
    query_embedding: list[float],
    match_count: int = 5,
    match_threshold: float = 0.70,
) -> list[dict]:
    """Find similar insurance documents using cosine similarity.
    
    Both documents and embeddings are loaded from local JSON files.
    
    Args:
        query_embedding: The query embedding vector
        match_count: Maximum number of matches to return
        match_threshold: Minimum similarity threshold (0-1)
    
    Returns:
        List of matching documents with similarity scores
    """
    # Load embeddings and documents from local files
    embeddings = load_embeddings()
    documents = load_documents()
    
    # Calculate similarity for each document
    results = []
    for doc in documents:
        doc_id = str(doc.get("id"))
        doc_embedding = embeddings.get(doc_id)
        
        if doc_embedding:
            similarity = _cosine_similarity(query_embedding, doc_embedding)
            
            if similarity > match_threshold:
                results.append({
                    "id": doc["id"],
                    "content": doc["content"],
                    "source_file": doc["source_file"],
                    "section_type": doc["section_type"],
                    "procedure_codes": doc["procedure_codes"],
                    "similarity": similarity,
                })
    
    # Sort by similarity (descending) and return top matches
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:match_count]
