import json
import os
from datetime import datetime, timezone

from anthropic import Anthropic
from dotenv import load_dotenv

from insurance.agent import get_insurance_quote
from orchestrator.tools import TOOLS
from patient.agent import explain_to_patient
from shared.schemas import (
    AgentTraceStep,
    DemoRequest,
    DemoResponse,
    InsuranceQuote,
)

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ORCHESTRATOR_SYSTEM_PROMPT = """You are a medical workflow orchestrator. Your job is to coordinate
between an insurance verification agent and a patient communication agent to process a doctor's
visit efficiently.

When you receive a doctor's note with a procedure code and patient ID, you should:
1. FIRST call the insurance agent to get coverage information for the procedure
2. THEN call the patient agent with the doctor's notes AND the insurance quote to generate
   a patient-friendly explanation

Always call the insurance agent before the patient agent, because the patient explanation
needs the insurance information to be complete and accurate.

Be systematic and thorough. Process one step at a time."""


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

    user_message = (
        f"Process this medical visit:\n\n"
        f"Doctor's Notes: {request.doctor_notes}\n\n"
        f"Procedure Code: {request.procedure_code}\n"
        f"Patient ID: {request.patient_id}\n\n"
        f"Please coordinate the insurance check and patient explanation."
    )

    messages = [{"role": "user", "content": user_message}]

    insurance_quote: InsuranceQuote | None = None
    patient_summary = None

    # Agentic loop — let Claude decide tool calls
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Check if we're done (no more tool calls)
        if response.stop_reason == "end_turn":
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "call_insurance_agent":
                    trace.append(
                        AgentTraceStep(
                            agent_name="insurance",
                            action="lookup",
                            input_summary=f"CPT: {block.input['procedure_code']}, Patient: {block.input['patient_id']}",
                            output_summary="Looking up coverage...",
                            timestamp=datetime.now(timezone.utc),
                        )
                    )

                    insurance_quote = get_insurance_quote(
                        block.input["procedure_code"],
                        block.input["patient_id"],
                    )

                    trace[-1].output_summary = (
                        f"Coverage: {insurance_quote.coverage_percent}%, "
                        f"OOP: ${insurance_quote.out_of_pocket_estimate:.2f}, "
                        f"Prior Auth: {'Yes' if insurance_quote.prior_auth_required else 'No'}"
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": insurance_quote.model_dump_json(),
                        }
                    )

                elif block.name == "call_patient_agent":
                    trace.append(
                        AgentTraceStep(
                            agent_name="patient",
                            action="explain",
                            input_summary="Generating patient-friendly explanation",
                            output_summary="Processing...",
                            timestamp=datetime.now(timezone.utc),
                        )
                    )

                    quote_data = json.loads(block.input["insurance_quote_json"])
                    quote = InsuranceQuote(**quote_data)

                    patient_summary = await explain_to_patient(
                        block.input["doctor_notes"],
                        quote,
                    )

                    trace[-1].output_summary = (
                        f"Generated summary with {len(patient_summary.key_points)} key points"
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": patient_summary.model_dump_json(),
                        }
                    )

        # Add assistant response and tool results to conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Fallback if orchestrator didn't call agents (shouldn't happen)
    if insurance_quote is None:
        insurance_quote = get_insurance_quote(
            request.procedure_code, request.patient_id
        )
    if patient_summary is None:
        patient_summary = await explain_to_patient(
            request.doctor_notes, insurance_quote
        )

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
