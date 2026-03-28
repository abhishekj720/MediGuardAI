import json
import logging
from pathlib import Path

from shared.schemas import InsuranceQuote

from insurance.rag import embed_query, extract_quote_from_context, search_insurance_docs

logger = logging.getLogger(__name__)

MOCK_DATA_PATH = Path(__file__).parent / "data" / "mock_insurance.json"
DOCUMENTS_PATH = Path(__file__).parent / "data" / "documents.json"

_mock_data: dict | None = None


def _load_mock_data() -> dict:
    global _mock_data
    if _mock_data is None:
        with open(MOCK_DATA_PATH) as f:
            _mock_data = json.load(f)
    return _mock_data


def _mock_fallback(procedure_code: str) -> InsuranceQuote:
    """Return a quote from mock_insurance.json as a fallback."""
    data = _load_mock_data()
    if procedure_code not in data:
        return InsuranceQuote(
            procedure_code=procedure_code,
            procedure_name="Unknown Procedure",
            coverage_percent=0,
            out_of_pocket_estimate=0,
            prior_auth_required=True,
            notes=f"Procedure code '{procedure_code}' not found in coverage database. Please verify the CPT code.",
        )
    entry = data[procedure_code]
    return InsuranceQuote(
        procedure_code=procedure_code,
        procedure_name=entry["procedure_name"],
        coverage_percent=entry["coverage_percent"],
        out_of_pocket_estimate=entry["out_of_pocket_estimate"],
        prior_auth_required=entry["prior_auth_required"],
        notes=entry.get("notes", "") + " [source: mock data fallback]",
    )


async def get_insurance_quote(procedure_code: str, patient_id: str) -> InsuranceQuote:
    """Look up insurance coverage for a given CPT procedure code using RAG.

    Flow:
      1. Embed the search query via Insforge Embeddings API
      2. Search local documents.json + embeddings.json via cosine similarity
      3. If chunks found → extract InsuranceQuote via Insforge Chat Completion
      4. If no chunks (cold start or miss) → fallback to mock_insurance.json

    patient_id is accepted for future extensibility (e.g. plan-specific rates).
    """
    # Cold-start guard: if ingest hasn't been run yet, go straight to fallback
    if not DOCUMENTS_PATH.exists():
        logger.warning(
            "documents.json not found — RAG index not built. "
            "Run `python insurance/ingest.py` to build it. Using mock fallback."
        )
        return _mock_fallback(procedure_code)

    try:
        # Step 1: embed the query
        query = f"CPT {procedure_code} coverage percentage out-of-pocket cost prior authorization"
        embedding = await embed_query(query)

        # Step 2: retrieve relevant chunks
        chunks = search_insurance_docs(
            query_embedding=embedding,
            procedure_code=procedure_code,
            top_k=5,
            threshold=0.0,  # Include all matching procedure codes
        )

        if not chunks:
            logger.warning(
                f"RAG returned no chunks for CPT {procedure_code} "
                f"(threshold 0.70). Using mock fallback."
            )
            return _mock_fallback(procedure_code)

        # Step 3: extract structured quote from retrieved context
        logger.info(
            f"RAG: {len(chunks)} chunks retrieved for CPT {procedure_code} "
            f"(top similarity: {chunks[0].get('similarity', 0):.3f})"
        )
        return await extract_quote_from_context(procedure_code, patient_id, chunks)

    except Exception as e:
        logger.error(f"RAG lookup failed for CPT {procedure_code}: {e}. Using mock fallback.")
        return _mock_fallback(procedure_code)


def list_available_procedures() -> list[dict]:
    """Return all available procedure codes and names for UI dropdowns.

    Reads from mock_insurance.json — this is intentional so the dropdown
    is always available even before the RAG index is built.
    """
    data = _load_mock_data()
    return [
        {"code": code, "name": entry["procedure_name"]}
        for code, entry in data.items()
    ]
