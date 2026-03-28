"""Tool definitions for the orchestrator agent.

These are the Claude tool-use schemas that the orchestrator uses to route
requests to the insurance and patient sub-agents.
"""

TOOLS = [
    {
        "name": "call_insurance_agent",
        "description": (
            "Look up insurance coverage and cost information for a medical procedure. "
            "Returns coverage percentage, out-of-pocket estimate, and whether prior "
            "authorization is required."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "procedure_code": {
                    "type": "string",
                    "description": "The CPT procedure code (e.g., '99213' for an office visit, '27447' for knee replacement)",
                },
                "patient_id": {
                    "type": "string",
                    "description": "The patient's ID number",
                },
            },
            "required": ["procedure_code", "patient_id"],
        },
    },
    {
        "name": "call_patient_agent",
        "description": (
            "Generate a plain-language explanation of clinical notes and insurance "
            "information for the patient. The explanation will be written at an 8th grade "
            "reading level with actionable takeaways."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doctor_notes": {
                    "type": "string",
                    "description": "The raw clinical notes from the doctor's visit",
                },
                "insurance_quote_json": {
                    "type": "string",
                    "description": "JSON string of the insurance quote returned by call_insurance_agent",
                },
            },
            "required": ["doctor_notes", "insurance_quote_json"],
        },
    },
]
