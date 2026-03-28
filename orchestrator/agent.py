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

You MUST respond with a JSON object indicating which action to take:

Step 1 - First, call the insurance agent:
{"action": "call_insurance_agent", "procedure_code": "<code>", "patient_id": "<id>"}

Step 2 - After receiving insurance results, call the patient agent:
{"action": "call_patient_agent", "doctor_notes": "<notes>", "insurance_quote": <quote_object>}

Step 3 - When both agents have returned results:
{"action": "done", "summary": "Brief summary of what was processed"}

Always call insurance FIRST, then patient. Respond with exactly one JSON object per turn."""


async def run_orchestrator(request: DemoRequest) -> DemoResponse:
    """Run the full orchestration flow: insurance lookup -> patient explanation."""

    trace: list[AgentTraceStep] = []

    trace.append(
        AgentTraceStep(
            agent_name="orchestrator",
            action="start",
            input_summary=f"Processing procedure {request.procedure_code} for patient {request.patient_id}",
            output_summary="Starting orchestration flow",
            timestamp=datetime.now(timezone.utc),
        )
    )

    # Step 1: Ask orchestrator what to do first
    messages = [
        {
            "role": "user",
            "content": (
                f"Process this medical visit:\n\n"
                f"Doctor's Notes: {request.doctor_notes}\n\n"
                f"Procedure Code: {request.procedure_code}\n"
                f"Patient ID: {request.patient_id}\n\n"
                f"What is the first step?"
            ),
        }
    ]

    decision = await chat_completion_json(
        messages=messages,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    )

    # Step 2: Execute insurance lookup
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
        decision.get("procedure_code", request.procedure_code),
        decision.get("patient_id", request.patient_id),
    )

    trace[-1].output_summary = (
        f"Coverage: {insurance_quote.coverage_percent}%, "
        f"OOP: ${insurance_quote.out_of_pocket_estimate:.2f}, "
        f"Prior Auth: {'Yes' if insurance_quote.prior_auth_required else 'No'}"
    )

    # Step 3: Ask orchestrator for next step (with insurance results)
    messages.append({"role": "assistant", "content": json.dumps(decision)})
    messages.append(
        {
            "role": "user",
            "content": (
                f"Insurance agent returned:\n"
                f"{insurance_quote.model_dump_json(indent=2)}\n\n"
                f"What is the next step?"
            ),
        }
    )

    decision2 = await chat_completion_json(
        messages=messages,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    )

    # Step 4: Execute patient explanation
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

    # Done
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
