import json
from pathlib import Path

from shared.schemas import InsuranceQuote

MOCK_DATA_PATH = Path(__file__).parent / "data" / "mock_insurance.json"

_insurance_data: dict | None = None


def _load_data() -> dict:
    global _insurance_data
    if _insurance_data is None:
        with open(MOCK_DATA_PATH) as f:
            _insurance_data = json.load(f)
    return _insurance_data


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
