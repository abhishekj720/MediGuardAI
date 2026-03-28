"""RAG helpers for the insurance agent.

Three-step pipeline:
  1. embed_query()               — Insforge Embeddings API → query vector
  2. search_insurance_docs()     — local cosine similarity (shared.db) → top-k chunks
  3. extract_quote_from_context() — Insforge Chat Completion → InsuranceQuote
"""

import json
from pathlib import Path

from shared.ai import chat_completion_json, generate_embeddings
from shared.db import match_insurance_docs
from shared.schemas import InsuranceQuote

EXTRACTION_SYSTEM_PROMPT = """You are an insurance data extraction assistant.
Given excerpts from insurance policy documents, extract coverage details for a specific CPT procedure code.

IMPORTANT: Return ONLY a raw JSON object. Do not use markdown formatting, do not wrap in code blocks, do not add explanations.

The JSON must have exactly these fields:
{
  "procedure_code": "<the CPT code>",
  "procedure_name": "<full procedure name>",
  "coverage_percent": <number 0-100>,
  "out_of_pocket_estimate": <dollar amount as number>,
  "prior_auth_required": <true or false>,
  "notes": "<any relevant coverage conditions, limits, or requirements>"
}

Rules:
- coverage_percent must be a number (e.g. 80, not "80%")
- out_of_pocket_estimate must be a number in dollars (e.g. 45.00)
- prior_auth_required must be a boolean
- If a field cannot be determined from the excerpts, use sensible defaults:
  coverage_percent: 0, out_of_pocket_estimate: 0, prior_auth_required: true, notes: "Coverage details not found"
- Return ONLY the JSON object, nothing else
"""


async def embed_query(text: str) -> list[float]:
    """Embed a search query via Insforge POST /api/ai/embeddings.

    Returns a single 1536-dim float vector.
    """
    vectors = await generate_embeddings([text])
    return vectors[0]


def search_insurance_docs(
    query_embedding: list[float],
    procedure_code: str | None = None,
    top_k: int = 5,
    threshold: float = 0.70,
) -> list[dict]:
    """Search local documents.json + embeddings.json via cosine similarity.

    Optionally post-filters by procedure_code to ensure CPT-relevant chunks
    are prioritised. Falls back to similarity-only results if the CPT filter
    yields nothing.
    """
    results = match_insurance_docs(
        query_embedding=query_embedding,
        match_count=top_k * 10,   # fetch many more so CPT filter has room to work
        match_threshold=threshold,
    )

    if procedure_code:
        filtered = [r for r in results if procedure_code in r.get("procedure_codes", [])]
        # Only use CPT-filtered results if we actually got some
        if filtered:
            return filtered[:top_k]

    return results[:top_k]


async def extract_quote_from_context(
    procedure_code: str,
    patient_id: str,
    context_chunks: list[dict],
) -> InsuranceQuote:
    """Extract a structured InsuranceQuote from retrieved context chunks
    via Insforge POST /api/ai/chat/completion.
    """
    # Build context string from retrieved chunks, labelled by source
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        source = chunk.get("source_file", "unknown")
        section = chunk.get("section_type", "")
        content = chunk.get("content", "")
        context_parts.append(f"[Excerpt {i} — {source} ({section})]\n{content}")

    context = "\n\n".join(context_parts)

    user_message = (
        f"Extract insurance coverage details for CPT code {procedure_code} "
        f"from the following policy document excerpts:\n\n{context}\n\n"
        f"Respond with ONLY a JSON object for CPT {procedure_code}. No markdown, no explanations."
    )

    parsed = await chat_completion_json(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        temperature=0.1,   # low temp for deterministic extraction
        max_tokens=512,
    )

    # Handle flexible field names and nested structures from AI response
    def get_nested_value(data: dict, path: list[str], default=None):
        """Get a value from a nested dict using a path of keys."""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    # Extract procedure code
    proc_code = parsed.get("cpt_code") or parsed.get("procedure_code") or parsed.get("code") or procedure_code
    
    # Extract procedure name
    proc_name = parsed.get("procedure") or parsed.get("procedure_name") or parsed.get("name") or f"Procedure {procedure_code}"
    
    # Extract coverage percent - handle multiple possible formats
    coverage = parsed.get("coverage", {})
    cost_sharing = parsed.get("cost_sharing", {})
    
    coverage_pct = 0
    if isinstance(coverage, dict):
        # Try various possible field locations
        coverage_pct = (coverage.get("in_network_percentage") or
                       coverage.get("in_network", {}).get("coverage_percentage") or
                       coverage.get("coverage_percentage") or
                       parsed.get("coverage_percent") or
                       parsed.get("reimbursement_percentage") or 0)
    else:
        coverage_pct = parsed.get("coverage_percent") or parsed.get("reimbursement_percentage") or 0
    
    # Extract out of pocket estimate - handle multiple possible formats
    oop_str = "0"
    
    # Try cost_sharing first if it has data
    if isinstance(cost_sharing, dict) and cost_sharing:
        oop_val = (cost_sharing.get("estimated_patient_responsibility_in_network_facility") or
                  cost_sharing.get("estimated_patient_responsibility") or
                  cost_sharing.get("patient_responsibility"))
        if oop_val:
            oop_str = str(oop_val)
    
    # Try coverage.in_network if cost_sharing didn't have it
    if oop_str == "0" and isinstance(coverage, dict):
        in_network = coverage.get("in_network", {})
        if isinstance(in_network, dict):
            oop_val = in_network.get("estimated_patient_responsibility")
            if oop_val:
                oop_str = str(oop_val)
    
    # Try top-level fields
    if oop_str == "0":
        oop_val = parsed.get("out_of_pocket_estimate") or parsed.get("patient_responsibility")
        if oop_val:
            oop_str = str(oop_val)
    
    # Parse out of pocket (handle string with $)
    if isinstance(oop_str, str):
        oop_str = oop_str.replace("$", "").replace(",", "")
    try:
        oop_estimate = float(oop_str or 0)
    except (ValueError, TypeError):
        oop_estimate = 0
    
    # Extract prior auth required - try nested structure first
    prior_auth = parsed.get("prior_authorization", {})
    if isinstance(prior_auth, dict):
        prior_auth_req = prior_auth.get("required")
    else:
        prior_auth_req = None
    if prior_auth_req is None:
        prior_auth_req = parsed.get("prior_auth_required") or parsed.get("prior_authorization_required") or True
    
    # Extract notes - try to build from nested medical_necessity_criteria if no top-level notes
    notes = parsed.get("notes") or ""
    if not notes:
        # Try to extract relevant info from nested structures
        med_criteria = parsed.get("medical_necessity_criteria", {})
        if isinstance(med_criteria, dict) and med_criteria:
            criteria_parts = []
            if "conservative_treatment_failure" in med_criteria:
                ctf = med_criteria["conservative_treatment_failure"]
                if isinstance(ctf, dict):
                    months = ctf.get("minimum_duration_months")
                    if months:
                        criteria_parts.append(f"Requires {months} months conservative treatment failure")
            if "bmi_requirement" in med_criteria:
                criteria_parts.append(f"BMI {med_criteria['bmi_requirement']}")
            if criteria_parts:
                notes = "; ".join(criteria_parts)

    return InsuranceQuote(
        procedure_code=proc_code,
        procedure_name=proc_name,
        coverage_percent=float(coverage_pct or 0),
        out_of_pocket_estimate=oop_estimate,
        prior_auth_required=bool(prior_auth_req),
        notes=notes,
    )
