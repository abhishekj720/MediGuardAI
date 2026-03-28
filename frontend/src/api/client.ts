import type { DemoRequest, DemoResponse, Procedure, Patient } from "../types";
import { insforge } from "../lib/insforge";

// InsForge Edge Function URL for MedGuardAI API
const API_BASE = "https://em6x2e4c.functions.insforge.app/mediguard-api/api";

export async function fetchProcedures(): Promise<Procedure[]> {
  const res = await fetch(`${API_BASE}/procedures`);
  if (!res.ok) throw new Error("Failed to fetch procedures");
  return res.json();
}

export async function fetchPatients(): Promise<Patient[]> {
  try {
    const { data, error } = await insforge.database
      .from("profiles")
      .select("user_id, name, role")
      .eq("role", "patient");

    if (error) {
      console.error("Failed to fetch patients:", error);
      return [];
    }

    if (!data || (Array.isArray(data) && data.length === 0)) {
      return [];
    }

    const rows = Array.isArray(data) ? data : [data];
    
    return rows
      .filter((row): row is { user_id: string; name: string; role: string } => 
        row && typeof row.user_id === 'string'
      )
      .map((row) => ({
        id: row.user_id,
        name: row.name || "Unknown Patient",
      }));
  } catch (err) {
    console.error("Error fetching patients:", err);
    return [];
  }
}

export async function submitDemo(request: DemoRequest): Promise<DemoResponse> {
  const res = await fetch(`${API_BASE}/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Demo request failed: ${detail}`);
  }
  return res.json();
}

export interface Visit {
  id: string;
  patient_id: string;
  doctor_id: string;
  procedure_code: string;
  diagnosis: string;
  release_notes: string;
  visit_date: string;
  created_at: string;
}

export async function createVisit(visit: {
  patient_id: string;
  doctor_id: string;
  procedure_code: string;
  diagnosis: string;
  release_notes: string;
}): Promise<Visit> {
  // Write directly to InsForge database using SDK
  const { data, error } = await insforge.database
    .from('patient_visits')
    .insert([{
      patient_id: visit.patient_id,
      doctor_id: visit.doctor_id,
      procedure_code: visit.procedure_code,
      diagnosis: visit.diagnosis,
      release_notes: visit.release_notes,
      visit_date: new Date().toISOString()
    }])
    .select();
  
  if (error) {
    throw new Error(`Failed to create visit: ${error.message}`);
  }
  
  return data?.[0] as Visit;
}

export async function fetchVisits(patientId: string): Promise<Visit[]> {
  // Read directly from InsForge database using SDK
  const { data, error } = await insforge.database
    .from('patient_visits')
    .select('*')
    .eq('patient_id', patientId)
    .order('visit_date', { ascending: false });
  
  if (error) {
    throw new Error(`Failed to fetch visits: ${error.message}`);
  }
  
  return (data || []) as Visit[];
}
