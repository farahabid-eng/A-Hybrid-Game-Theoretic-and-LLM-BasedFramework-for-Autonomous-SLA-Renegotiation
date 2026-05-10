import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createWorkflow } from "../api/client";

export default function Home() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    event_type: "latency_violation",
    observed_value: 0,
    agreed_value: 0,
    unit: "ms",
    max_rounds: 10,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const wf = await createWorkflow(form);
    navigate(`/workflows/${wf.id}/context`);
  };

  return (
    <div className="max-w-lg mx-auto mt-12">
      <h1 className="text-2xl font-bold mb-2">New SLA Renegotiation</h1>
      <p className="text-sm text-gray-500 mb-6">
        Describe the violation to initialize the renegotiation workflow.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Event Type</label>
          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={form.event_type}
            onChange={(e) => setForm({ ...form, event_type: e.target.value })}
          >
            <option value="latency_violation">Latency Violation</option>
            <option value="throughput_violation">Throughput Violation</option>
            <option value="availability_violation">Availability Violation</option>
            <option value="error_rate_violation">Error Rate Violation</option>
            <option value="cost_overage">Cost Overage</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Observed Value</label>
            <input
              type="number"
              step="any"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={form.observed_value}
              onChange={(e) => setForm({ ...form, observed_value: parseFloat(e.target.value) })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Agreed Value</label>
            <input
              type="number"
              step="any"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={form.agreed_value}
              onChange={(e) => setForm({ ...form, agreed_value: parseFloat(e.target.value) })}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Unit</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={form.unit}
              onChange={(e) => setForm({ ...form, unit: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Max Negotiation Rounds</label>
            <input
              type="number"
              min={1}
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={form.max_rounds}
              onChange={(e) => setForm({ ...form, max_rounds: parseInt(e.target.value) })}
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Start Renegotiation
        </button>
      </form>
    </div>
  );
}
