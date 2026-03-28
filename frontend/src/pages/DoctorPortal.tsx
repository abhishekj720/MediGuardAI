import { useState, useEffect } from "react";
import { fetchProcedures, fetchPatients, submitDemo } from "../api/client";
import AgentTrace from "../components/AgentTrace";
import type { DemoResponse, Procedure, Patient } from "../types";

export default function DoctorPortal() {
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [doctorNotes, setDoctorNotes] = useState("");
  const [procedureCode, setProcedureCode] = useState("");
  const [patientId, setPatientId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchProcedures(), fetchPatients()])
      .then(([procs, pats]) => {
        setProcedures(procs);
        setPatients(pats);
      })
      .catch(() => setError("Failed to load data"));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await submitDemo({
        doctor_notes: doctorNotes,
        procedure_code: procedureCode,
        patient_id: patientId,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Doctor Portal</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <div className="lg:col-span-2">
          <form
            onSubmit={handleSubmit}
            className="bg-white rounded-lg border border-gray-200 p-6 space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Patient
              </label>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
                disabled={patients.length === 0}
              >
                <option value="">
                  {patients.length === 0 ? "No patients available" : "Select a patient..."}
                </option>
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Procedure
              </label>
              <select
                value={procedureCode}
                onChange={(e) => setProcedureCode(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select a procedure...</option>
                {procedures.map((p) => (
                  <option key={p.code} value={p.code}>
                    {p.code} — {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Clinical Notes
              </label>
              <textarea
                value={doctorNotes}
                onChange={(e) => setDoctorNotes(e.target.value)}
                placeholder="Enter clinical notes for this visit..."
                rows={6}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Processing..." : "Submit for Review"}
            </button>
          </form>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Insurance Quote Result */}
          {result && (
            <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Insurance Quote
              </h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Procedure:</span>
                  <p className="font-medium">
                    {result.insurance_quote.procedure_name}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Coverage:</span>
                  <p className="font-medium">
                    {result.insurance_quote.coverage_percent}%
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Out-of-Pocket:</span>
                  <p className="font-medium text-lg">
                    ${result.insurance_quote.out_of_pocket_estimate.toFixed(2)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Prior Auth:</span>
                  <p
                    className={`font-medium ${result.insurance_quote.prior_auth_required ? "text-amber-600" : "text-green-600"}`}
                  >
                    {result.insurance_quote.prior_auth_required
                      ? "Required"
                      : "Not Required"}
                  </p>
                </div>
              </div>
              {result.insurance_quote.notes && (
                <p className="mt-3 text-sm text-gray-600 bg-gray-50 rounded p-3">
                  {result.insurance_quote.notes}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Agent Trace Sidebar */}
        <div>{result && <AgentTrace trace={result.agent_trace} />}</div>
      </div>
    </div>
  );
}
