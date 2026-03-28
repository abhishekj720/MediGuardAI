from shared.ai import chat_completion_json
from shared.schemas import InsuranceQuote, PatientSummary

PATIENT_SYSTEM_PROMPT = """You are a compassionate medical communication assistant. Your job is to take
clinical doctor notes and insurance information, then explain everything to the patient in plain,
easy-to-understand language.

RULES:
- Write at an 8th grade reading level (Flesch-Kincaid grade level ~8)
- Use short sentences. Avoid medical jargon — if you must use a medical term, define it in parentheses
- Be warm and reassuring, but honest
- Always explain what the patient needs to DO next (action items)
- Explain insurance coverage in dollars, not percentages when possible
- If prior authorization is needed, explain what that means in plain language

CRITICAL - OUTPUT FORMAT:
You MUST return ONLY a JSON object with exactly these two fields and no other fields:
{
  "summary": "A 2-3 paragraph plain-language explanation of the visit and costs",
  "key_points": ["3-5 actionable bullet points the patient should remember"]
}

Do NOT include any other fields like 'procedure', 'cost', 'next_steps', etc.
Return ONLY the JSON object, no markdown formatting, no code blocks."""


async def explain_to_patient(
    doctor_note: str, insurance_quote: InsuranceQuote
) -> PatientSummary:
    """Take a doctor's clinical note and insurance quote, return a patient-friendly explanation."""

    user_message = f"""Here is the doctor's note about the patient's visit:

--- DOCTOR'S NOTE ---
{doctor_note}
--- END NOTE ---

Here is the insurance coverage information:
- Procedure: {insurance_quote.procedure_name} (Code: {insurance_quote.procedure_code})
- Insurance covers: {insurance_quote.coverage_percent}% of the cost
- Estimated out-of-pocket cost to patient: ${insurance_quote.out_of_pocket_estimate:.2f}
- Prior authorization required: {"Yes" if insurance_quote.prior_auth_required else "No"}
- Insurance notes: {insurance_quote.notes}

Please explain all of this to the patient in plain language. Return your response as JSON."""

    try:
        parsed = await chat_completion_json(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=PATIENT_SYSTEM_PROMPT,
        )
        
        # Handle case where AI returns unexpected format
        if "summary" not in parsed or "key_points" not in parsed:
            # Try to extract from common alternative formats
            summary = parsed.get("summary", parsed.get("explanation", str(parsed)))
            key_points = parsed.get("key_points", parsed.get("action_items", parsed.get("next_steps", ["Please review the summary above."])))
            if isinstance(key_points, str):
                key_points = [key_points]
            return PatientSummary(summary=summary, key_points=key_points)
        
        return PatientSummary(
            summary=parsed["summary"],
            key_points=parsed["key_points"],
        )
    except Exception as e:
        # Fallback: generate a simple summary without LLM
        summary = f"Your doctor has ordered a {insurance_quote.procedure_name}. "
        summary += f"Your insurance covers {insurance_quote.coverage_percent}% of the cost, "
        summary += f"and your estimated out-of-pocket cost is ${insurance_quote.out_of_pocket_estimate:.2f}."
        if insurance_quote.prior_auth_required:
            summary += " Prior authorization is required before scheduling."
        
        return PatientSummary(
            summary=summary,
            key_points=[
                f"Procedure: {insurance_quote.procedure_name}",
                f"Insurance covers: {insurance_quote.coverage_percent}%",
                f"Your cost: ${insurance_quote.out_of_pocket_estimate:.2f}",
                "Contact your doctor's office for next steps"
            ]
        )
