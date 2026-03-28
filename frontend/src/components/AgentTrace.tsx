import type { AgentTraceStep } from "../types";

const AGENT_COLORS: Record<string, string> = {
  orchestrator: "bg-purple-100 text-purple-800 border-purple-300",
  insurance: "bg-green-100 text-green-800 border-green-300",
  patient: "bg-blue-100 text-blue-800 border-blue-300",
};

interface Props {
  trace: AgentTraceStep[];
}

export default function AgentTrace({ trace }: Props) {
  if (trace.length === 0) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Agent Trace
      </h3>
      <div className="space-y-2">
        {trace.map((step, i) => (
          <div
            key={i}
            className={`rounded-md border p-3 text-sm ${AGENT_COLORS[step.agent_name] ?? "bg-gray-100 text-gray-800 border-gray-300"}`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold capitalize">
                {step.agent_name}
              </span>
              <span className="text-xs opacity-70">{step.action}</span>
            </div>
            <p className="text-xs opacity-80">{step.input_summary}</p>
            <p className="text-xs font-medium mt-1">{step.output_summary}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
