export interface InsuranceQuote {
  procedure_code: string;
  procedure_name: string;
  coverage_percent: number;
  out_of_pocket_estimate: number;
  prior_auth_required: boolean;
  notes: string;
}

export interface PatientSummary {
  summary: string;
  key_points: string[];
}

export interface AgentTraceStep {
  agent_name: string;
  action: string;
  input_summary: string;
  output_summary: string;
  timestamp: string;
}

export interface DemoRequest {
  doctor_notes: string;
  procedure_code: string;
  patient_id: string;
}

export interface DemoResponse {
  insurance_quote: InsuranceQuote;
  patient_summary: PatientSummary;
  agent_trace: AgentTraceStep[];
}

export interface Procedure {
  code: string;
  name: string;
}
