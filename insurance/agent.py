import json
import logging
import os
import httpx
from pathlib import Path
from shared.schemas import InsuranceQuote

from insurance.rag import embed_query, extract_quote_from_context, search_insurance_docs

logger = logging.getLogger(__name__)

MOCK_DATA_PATH = Path(__file__).parent / "data" / "mock_insurance.json"
DOCUMENTS_PATH = Path(__file__).parent / "data" / "documents.json"

_mock_data: dict | None = None

# InsForge database configuration
INSFORGE_API_KEY = os.getenv("INSFORGE_API_KEY", "")
INSFORGE_API_BASE_URL = os.getenv("INSFORGE_API_BASE_URL", "http://localhost:7130")


def _load_mock_data() -> dict:
    global _mock_data
    if _mock_data is None:
        with open(MOCK_DATA_PATH) as f:
            _mock_data = json.load(f)
    return _mock_data


def _mock_fallback(procedure_code: str) -> InsuranceQuote:
    """Return a quote from mock_insurance.json as a fallback."""
    data = _load_mock_data()
def _get_insforge_headers() -> dict:
    return {
        "Authorization": f"Bearer {INSFORGE_API_KEY}",
        "Content-Type": "application/json",
    }


async def _query_database(table: str, filters: dict | None = None) -> list[dict]:
    """Query the InsForge database via REST API."""
    async with httpx.AsyncClient() as client:
        url = f"{INSFORGE_API_BASE_URL}/api/database/records/{table}"
        params = {}
        if filters:
            for key, value in filters.items():
                params[key] = value
        
        response = await client.get(
            url,
            headers=_get_insforge_headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def lookup_cpt_by_disease(disease_name: str) -> dict | None:
    """Look up CPT code by disease name from the database."""
    # Use ilike for case-insensitive partial match
    results = await _query_database(
        "disease_to_cpt",
        {"disease_name": f"ilike.*{disease_name}*"}
    )
    
    if results:
        # Sort by confidence and return the best match
        best_match = max(results, key=lambda x: x.get("confidence", 0))
        return {
            "cpt_code": str(best_match["cpt_code"]),
            "confidence": best_match["confidence"]
        }
    return None


def get_insurance_quote(procedure_code: str, patient_id: str) -> InsuranceQuote:
    """Look up insurance coverage for a given procedure code.

    This is a deterministic lookup — no LLM needed.
    The patient_id is accepted for future extensibility (e.g., plan-specific rates)
    but currently all patients get the same mock coverage.
    """
    data = _load_data()

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


async def get_all_disease_mappings() -> list[dict]:
    """Return all disease-to-CPT mappings from the database."""
    results = await _query_database("disease_to_cpt")
    return [
        {
            "disease_name": row["disease_name"],
            "cpt_code": str(row["cpt_code"]),
            "confidence": row["confidence"]
        }
        for row in results
    ]
