import os

from anthropic import Anthropic
from dotenv import load_dotenv

from shared.schemas import InsuranceQuote, PatientSummary

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PATIENT_SYSTEM_PROMPT = """You are a compassionate medical communication assistant. Your job is to take
clinical doctor notes and insurance information, then explain everything to the patient in plain,
easy-to-understand language.

RULES:
- Write at an 8th grade reading level (Flesch-Kincaid grade level ~8)
- Use short sentences. Avoid medical jargon — if you must use a medical term, define it in parentheses
- Be warm and reassuring, but honest
- Structure your response with clear sections
- Always explain what the patient needs to DO next (action items)
- Explain insurance coverage in dollars, not percentages when possible
- If prior authorization is needed, explain what that means in plain language

OUTPUT FORMAT:
Return a JSON object with exactly these fields:
{
  "summary": "A 2-3 paragraph plain-language explanation",
  "key_points": ["bullet point 1", "bullet point 2", ...]
}

The key_points should be 3-5 actionable takeaways the patient can remember."""


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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=PATIENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    import json

    response_text = response.content[0].text

    # Parse the JSON response
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
        else:
            parsed = {
                "summary": response_text,
                "key_points": ["Please review the full summary above."],
            }

    return PatientSummary(
        summary=parsed["summary"],
        key_points=parsed["key_points"],
    )
