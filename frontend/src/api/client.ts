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
    const result = await insforge.database
      .from("profiles")
      .select("*")
      .eq("role", "patient");

    console.log("Patients query full result:", result);
    console.log("Patients data:", result.data);
    console.log("Patients error:", result.error);

    const { data, error } = result;

    if (error) {
      console.error("Failed to fetch patients:", error);
      return [];
    }

    if (!data || !Array.isArray(data)) {
      console.warn("Unexpected data format:", typeof data, data);
      return [];
    }
    
    return data.map((row: { user_id: string; name: string }) => ({
      id: row.user_id,
      name: row.name || "Unknown",
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
