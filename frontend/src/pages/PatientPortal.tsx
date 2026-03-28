import { useState } from "react";
import { submitDemo } from "../api/client";
import type { PatientSummary } from "../types";

export default function PatientPortal() {
  const [patientId, setPatientId] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleLookup(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSummary(null);

    try {
      // In a real app, this would fetch a stored summary by patient ID.
      // For the demo, we use a hardcoded request to show the flow.
      const res = await submitDemo({
        doctor_notes:
          "Patient presents for follow-up of Type 2 Diabetes. A1C improved to 7.1 from 7.8. Continue current metformin regimen. Schedule routine blood work in 3 months. Discussed diet and exercise modifications.",
        procedure_code: "99213",
        patient_id: patientId,
      });
      setSummary(res.patient_summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Patient Portal
      </h1>
      <p className="text-gray-500 mb-6">
        View your visit summary in plain language.
      </p>

      <form
        onSubmit={handleLookup}
        className="bg-white rounded-lg border border-gray-200 p-6 flex gap-3"
      >
        <input
          type="text"
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          placeholder="Enter your Patient ID (e.g., PAT-001)"
          className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white py-2 px-6 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Loading..." : "View Summary"}
        </button>
      </form>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {summary && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Your Visit Summary
          </h2>

          <div className="prose prose-sm max-w-none text-gray-700 mb-6">
            {summary.summary.split("\n").map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>

          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Key Takeaways
          </h3>
          <ul className="space-y-2">
            {summary.key_points.map((point, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="mt-0.5 h-5 w-5 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs font-bold flex-shrink-0">
                  {i + 1}
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
