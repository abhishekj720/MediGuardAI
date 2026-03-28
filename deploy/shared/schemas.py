from pydantic import BaseModel
from datetime import datetime


class InsuranceQuote(BaseModel):
    procedure_code: str
    procedure_name: str
    coverage_percent: float
    out_of_pocket_estimate: float
    prior_auth_required: bool
    notes: str = ""


class PatientSummary(BaseModel):
    summary: str
    key_points: list[str]


class AgentTraceStep(BaseModel):
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    timestamp: datetime


class DemoRequest(BaseModel):
    doctor_notes: str
    procedure_code: str
    patient_id: str


class DemoResponse(BaseModel):
    insurance_quote: InsuranceQuote
    patient_summary: PatientSummary
    agent_trace: list[AgentTraceStep]
