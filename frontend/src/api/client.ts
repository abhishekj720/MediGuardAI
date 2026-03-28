import type { DemoRequest, DemoResponse, Procedure } from "../types";

const API_BASE = "/api";

export async function fetchProcedures(): Promise<Procedure[]> {
  const res = await fetch(`${API_BASE}/procedures`);
  if (!res.ok) throw new Error("Failed to fetch procedures");
  return res.json();
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
