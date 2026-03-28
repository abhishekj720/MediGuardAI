import type { DemoRequest, DemoResponse, Procedure, Patient } from "../types";
import { insforge } from "../lib/insforge";

const API_BASE = "/api";

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

    if (!data) {
      console.warn("No patient data returned");
      return [];
    }

    // Handle both array and single object responses
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
