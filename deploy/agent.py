import json
from datetime import datetime, timezone

from insurance.agent import get_insurance_quote
from patient.agent import explain_to_patient
from shared.ai import chat_completion_json
from shared.schemas import (
    AgentTraceStep,
    DemoRequest,
    DemoResponse,
    InsuranceQuote,
)

ORCHESTRATOR_SYSTEM_PROMPT = """You are a medical workflow orchestrator. Your job is to coordinate
between an insurance verification agent and a patient communication agent to process a doctor's
visit efficiently.

When you receive a doctor's note with a procedure code and patient ID, decide what to do next.

CRITICAL: You MUST respond with ONLY a JSON object. No markdown, no explanations, no code blocks.
Just raw JSON.

Step 1 - First, call the insurance agent:
{"action": "call_insurance_agent", "procedure_code": "<code>", "patient_id": "<id>"}

Step 2 - After receiving insurance results, call the patient agent:
{"action": "call_patient_agent", "doctor_notes": "<notes>", "insurance_quote": <quote_object>}

Step 3 - When both agents have returned results:
{"action": "done", "summary": "Brief summary of what was processed"}

Always call insurance FIRST, then patient. Return ONLY raw JSON, nothing else."""


async def run_orchestrator(request: DemoRequest) -> DemoResponse:
    """Run the full orchestration flow: insurance lookup -> patient explanation.
    
    This is a deterministic sequential orchestrator - no LLM decision making.
    The flow is always: Insurance Agent -> Patient Agent.
    """

    trace: list[AgentTraceStep] = []

    # Step 1: Start orchestration
    trace.append(
        AgentTraceStep(
            agent_name="orchestrator",
            action="start",
            input_summary=f"Processing procedure {request.procedure_code} for patient {request.patient_id}",
            output_summary="Starting orchestration flow: Insurance -> Patient",
            timestamp=datetime.now(timezone.utc),
        )
    )

    # Step 2: Execute insurance lookup (deterministic, no LLM)
    trace.append(
        AgentTraceStep(
            agent_name="insurance",
            action="lookup",
            input_summary=f"CPT: {request.procedure_code}, Patient: {request.patient_id}",
            output_summary="Looking up coverage...",
            timestamp=datetime.now(timezone.utc),
        )
    )

    insurance_quote = get_insurance_quote(
        request.procedure_code,
        request.patient_id,
    )

    trace[-1].output_summary = (
        f"Coverage: {insurance_quote.coverage_percent}%, "
        f"OOP: ${insurance_quote.out_of_pocket_estimate:.2f}, "
        f"Prior Auth: {'Yes' if insurance_quote.prior_auth_required else 'No'}"
    )

    # Step 3: Execute patient explanation (uses LLM for plain language)
    trace.append(
        AgentTraceStep(
            agent_name="patient",
            action="explain",
            input_summary="Generating patient-friendly explanation",
            output_summary="Processing...",
            timestamp=datetime.now(timezone.utc),
        )
    )

    patient_summary = await explain_to_patient(
        request.doctor_notes,
        insurance_quote,
    )

    trace[-1].output_summary = (
        f"Generated summary with {len(patient_summary.key_points)} key points"
    )

    # Step 4: Complete
    trace.append(
        AgentTraceStep(
            agent_name="orchestrator",
            action="complete",
            input_summary="All agents finished",
            output_summary="Orchestration complete",
            timestamp=datetime.now(timezone.utc),
        )
    )

    return DemoResponse(
        insurance_quote=insurance_quote,
        patient_summary=patient_summary,
        agent_trace=trace,
    )
