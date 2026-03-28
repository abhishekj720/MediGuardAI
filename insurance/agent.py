import json
import os
import httpx
from pathlib import Path
from shared.schemas import InsuranceQuote

MOCK_DATA_PATH = Path(__file__).parent / "data" / "mock_insurance.json"

_insurance_data: dict | None = None

# InsForge database configuration
INSFORGE_API_KEY = os.getenv("INSFORGE_API_KEY", "")
INSFORGE_API_BASE_URL = os.getenv("INSFORGE_API_BASE_URL", "http://localhost:7130")


def _load_data() -> dict:
    global _insurance_data
    if _insurance_data is None:
        with open(MOCK_DATA_PATH) as f:
            _insurance_data = json.load(f)
    return _insurance_data


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
        notes=entry.get("notes", ""),
    )


def list_available_procedures() -> list[dict]:
    """Return all available procedure codes and names for UI dropdowns."""
    data = _load_data()
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
