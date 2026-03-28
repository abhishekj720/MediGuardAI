"""PDF ingestion pipeline for the insurance RAG agent.

Parses legacy insurance PDFs, applies policy-aware chunking, generates
embeddings via Insforge, and stores everything locally in JSON files.

Usage:
    python insurance/ingest.py

Run this once before starting the server, and re-run whenever PDFs change.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ai import generate_embeddings

PDF_DIR = Path(__file__).parent / "fixtures" / "pdfs"
DATA_DIR = Path(__file__).parent / "data"

# Local storage files
DOCUMENTS_FILE = DATA_DIR / "documents.json"
EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"

# Embedding batch size — stay well within Insforge rate limits
BATCH_SIZE = 20

# ── Section type tags (stored in DB for filtered queries) ──────────────
SECTION_TYPES = {
    "policy_coverage_schedule": "coverage_table",
    "fee_schedule_2024": "fee_schedule",
    "prior_auth_guidelines": "prior_auth",
    "plan_benefits_summary": "benefits",
    "medical_policy_bulletin": "policy",
}

# Regex to identify CPT codes in text
CPT_RE = re.compile(r"\b(\d{5})\b")

KNOWN_CPT_CODES = {
    "99213", "99214", "27447", "70553",
    "43239", "93000", "90837", "29881", "36415", "71046",
}


# ── Local storage helpers ──────────────────────────────────────────────

def _load_documents() -> list[dict]:
    """Load documents from local JSON file."""
    if not DOCUMENTS_FILE.exists():
        return []
    with open(DOCUMENTS_FILE, 'r') as f:
        return json.load(f)


def _save_documents(documents: list[dict]):
    """Save documents to local JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DOCUMENTS_FILE, 'w') as f:
        json.dump(documents, f, indent=2)


def _load_embeddings() -> dict[str, list[float]]:
    """Load embeddings from local JSON file."""
    if not EMBEDDINGS_FILE.exists():
        return {}
    with open(EMBEDDINGS_FILE, 'r') as f:
        return json.load(f)


def _save_embeddings(embeddings: dict[str, list[float]]):
    """Save embeddings to local JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings, f)


def setup_local_storage():
    """Clear local storage for fresh ingestion."""
    print("Setting up local storage...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DOCUMENTS_FILE.exists():
        DOCUMENTS_FILE.unlink()
    if EMBEDDINGS_FILE.exists():
        EMBEDDINGS_FILE.unlink()
    print("  Local storage ready.")


# ── CPT code extraction ────────────────────────────────────────────────

def extract_cpt_codes(text: str) -> list[str]:
    """Extract known CPT codes from text via regex."""
    found = CPT_RE.findall(text)
    return sorted({c for c in found if c in KNOWN_CPT_CODES})


# ── Chunking strategies ────────────────────────────────────────────────

def chunk_coverage_table(text: str, source_file: str) -> list[dict]:
    """Table row chunking for coverage_schedule and fee_schedule PDFs.

    Detects lines that look like table data rows (start with a CPT code)
    and makes each row its own chunk, enriched with a header prefix.
    """
    chunks = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Find the header line (contains 'CPT' and 'Coverage' or 'Allowed')
    header = next(
        (l for l in lines if "CPT" in l and ("Coverage" in l or "Allowed" in l or "Procedure" in l)),
        "CPT Code | Procedure | Coverage Details",
    )

    for line in lines:
        # A data row starts with a 5-digit CPT code
        if re.match(r"^\d{5}", line):
            content = f"[{header}]\n{line}"
            chunks.append({
                "content": content,
                "metadata": {"source_line": line, "table_header": header},
            })

    # Fallback: if no row-per-CPT chunks found, split into paragraphs
    if not chunks:
        chunks = chunk_paragraphs(text, source_file, section_heading="Coverage Table")

    return chunks


def chunk_by_section(text: str, source_file: str) -> list[dict]:
    """Section-based chunking for prior_auth and policy bulletins.

    Splits on CPT-code headings or policy headings, making each
    named section its own chunk.
    """
    # Split on lines that look like section headings
    section_re = re.compile(
        r"^(CPT\s*\d{5}.*|Policy[:\s]+.*|MPC-\d{4}-.*|Section\s+\d+.*)",
        re.MULTILINE | re.IGNORECASE,
    )

    parts = section_re.split(text)
    chunks = []
    i = 0

    # parts alternates: [pre-heading text, heading, body, heading, body, ...]
    while i < len(parts):
        if i == 0 and not section_re.match(parts[i].strip()):
            i += 1
            continue
        heading = parts[i].strip() if section_re.match(parts[i].strip()) else ""
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        i += 2

        if not body and not heading:
            continue

        content = f"{heading}\n\n{body}".strip() if heading else body
        if len(content) < 50:
            continue

        # If section is very long, split at paragraph boundaries
        if len(content) > 2000:
            sub_chunks = _split_long_section(content, heading)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                "content": content,
                "metadata": {"heading": heading},
            })

    if not chunks:
        chunks = chunk_paragraphs(text, source_file)

    return chunks


def _split_long_section(text: str, heading: str) -> list[dict]:
    """Split an oversized section at paragraph boundaries with 2-sentence overlap."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = heading + "\n\n" if heading else ""
    prev_sentences: list[str] = []

    for para in paragraphs:
        if len(current) + len(para) > 1800:
            if current.strip():
                chunks.append({"content": current.strip(), "metadata": {"heading": heading}})
            # Start next chunk with 2-sentence overlap from previous paragraph
            overlap = " ".join(prev_sentences[-2:]) if prev_sentences else ""
            current = (f"{heading}\n\n[continued] {overlap}\n\n" if overlap else f"{heading}\n\n")
        current += para + "\n\n"
        prev_sentences = re.split(r"(?<=[.!?])\s+", para)

    if current.strip():
        chunks.append({"content": current.strip(), "metadata": {"heading": heading}})

    return chunks


def chunk_paragraphs(text: str, source_file: str, section_heading: str = "") -> list[dict]:
    """Paragraph chunking with context prefix for benefits/plan docs.

    Prepends the document title and current section heading to each chunk.
    Max 500 tokens (~2000 chars), 50-token overlap (~200 chars).
    """
    doc_title = Path(source_file).stem.replace("_", " ").title()

    # Track current section heading by detecting ALL-CAPS or title-case short lines
    current_section = section_heading
    chunks = []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    current_content = ""
    current_tail = ""  # last ~200 chars for overlap

    for para in paragraphs:
        # Detect section headings: short lines, no period at end
        if len(para) < 80 and not para.endswith(".") and para[0].isupper():
            current_section = para

        prefix = f"[{doc_title} > {current_section}] " if current_section else f"[{doc_title}] "

        if len(current_content) + len(para) > 2000:
            if current_content.strip():
                chunks.append({
                    "content": (prefix + current_content).strip(),
                    "metadata": {"section_heading": current_section, "doc_title": doc_title},
                })
            current_content = current_tail + para + "\n\n"
        else:
            current_content += para + "\n\n"

        # Keep last ~200 chars as overlap seed
        current_tail = current_content[-200:] if len(current_content) > 200 else current_content

    if current_content.strip():
        prefix = f"[{doc_title} > {current_section}] " if current_section else f"[{doc_title}] "
        chunks.append({
            "content": (prefix + current_content).strip(),
            "metadata": {"section_heading": current_section, "doc_title": doc_title},
        })

    return chunks


# ── PDF dispatcher ─────────────────────────────────────────────────────

def parse_and_chunk(pdf_path: Path) -> list[dict]:
    """Extract text from a PDF and apply the appropriate chunking strategy."""
    doc = fitz.open(str(pdf_path))
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()

    stem = pdf_path.stem
    section_type = SECTION_TYPES.get(stem, "general")

    if section_type in ("coverage_table", "fee_schedule"):
        raw_chunks = chunk_coverage_table(full_text, stem)
    elif section_type in ("prior_auth", "policy"):
        raw_chunks = chunk_by_section(full_text, stem)
    else:  # benefits and anything else
        raw_chunks = chunk_paragraphs(full_text, stem)

    # Attach shared fields to every chunk
    result = []
    for i, chunk in enumerate(raw_chunks):
        content = chunk["content"]
        result.append({
            "content": content,
            "source_file": pdf_path.name,
            "section_type": section_type,
            "chunk_index": i,
            "procedure_codes": extract_cpt_codes(content),
            "metadata": chunk.get("metadata", {}),
        })

    return result


# ── Embedding + storage ────────────────────────────────────────────────

async def embed_and_store(chunks: list[dict]):
    """Batch-embed all chunks via Insforge and store locally in JSON files.
    
    Documents and embeddings are both stored locally - no PostgreSQL needed.
    """
    total = len(chunks)
    stored = 0
    
    # Load existing documents and embeddings
    documents = _load_documents()
    embeddings = _load_embeddings()
    
    # Start from the next ID
    next_id = len(documents) + 1

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]
        texts = [c["content"] for c in batch]

        batch_embeddings = await generate_embeddings(texts)

        for chunk, embedding in zip(batch, batch_embeddings):
            # Create document with local ID
            doc = {
                "id": next_id,
                "content": chunk["content"],
                "source_file": chunk["source_file"],
                "section_type": chunk["section_type"],
                "chunk_index": chunk["chunk_index"],
                "procedure_codes": chunk["procedure_codes"],
                "metadata": chunk["metadata"],
            }
            documents.append(doc)
            
            # Save embedding with the same ID
            embeddings[str(next_id)] = embedding
            
            next_id += 1
            stored += 1
        
        # Save after each batch
        _save_documents(documents)
        _save_embeddings(embeddings)

        print(f"  Stored {stored}/{total} chunks...")

    return stored


# ── Main ───────────────────────────────────────────────────────────────

async def run_ingestion():
    print("=" * 55)
    print("MediGuardAI — Insurance PDF Ingestion Pipeline")
    print("=" * 55)

    setup_local_storage()

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {PDF_DIR}. Run generate_pdfs.py first.")
        sys.exit(1)

    all_chunks: list[dict] = []

    print(f"\nParsing and chunking {len(pdfs)} PDFs...")
    for pdf_path in pdfs:
        chunks = parse_and_chunk(pdf_path)
        print(f"  {pdf_path.name}: {len(chunks)} chunks ({SECTION_TYPES.get(pdf_path.stem, 'general')})")
        all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Generating embeddings and storing locally (batch size {BATCH_SIZE})...")
    stored = await embed_and_store(all_chunks)

    print(f"\nIngestion complete. {stored} chunks stored locally.")
    print(f"  Documents: {DOCUMENTS_FILE}")
    print(f"  Embeddings: {EMBEDDINGS_FILE}")
    print("\nRun 'python insurance/ingest.py' again to re-ingest after PDF changes.")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
