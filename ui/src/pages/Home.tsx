import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { createWorkflow, getSLAs, getSLA } from "../api/client";

interface SLOSummary {
  metric: string;
  target_value: number;
  unit: string;
  description: string;
  event_type: string;
}

interface SLAOption {
  id: string;
  name: string;
  description: string;
  slo_count: number;
}

export default function Home() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [slas, setSlas] = useState<SLAOption[]>([]);
  const [selectedSla, setSelectedSla] = useState<SLAOption | null>(null);
  const [sloDetail, setSloDetail] = useState<SLOSummary[]>([]);
  const [autoPopulated, setAutoPopulated] = useState(false);

  const [form, setForm] = useState({
    event_type: "latency_violation",
    observed_value: 0,
    agreed_value: 0,
    unit: "ms",
    sla_id: "",
    max_rounds: 10,
  });

  useEffect(() => {
    getSLAs().then((list) => {
      setSlas(list);
      const slaParam = searchParams.get("sla");
      if (slaParam) {
        const match = list.find((s) => s.id === slaParam);
        if (match) {
          handleSlaSelect(slaParam, list);
        }
      }
    });
  }, []);

  const handleSlaSelect = async (id: string, list?: SLAOption[]) => {
    const slaList = list || slas;
    const match = slaList.find((s) => s.id === id) || null;
    setSelectedSla(match);
    setForm((f) => ({ ...f, sla_id: id }));

    if (id) {
      const detail = await getSLA(id);
      setSloDetail(detail.slos);
      applySloDefaults(detail.slos, form.event_type);
    } else {
      setSloDetail([]);
      setAutoPopulated(false);
    }
  };

  const applySloDefaults = (slos: SLOSummary[], eventType: string) => {
    const match = slos.find((slo) => slo.event_type === eventType);
    if (match) {
      setForm((f) => ({
        ...f,
        agreed_value: match.target_value,
        unit: match.unit,
      }));
      setAutoPopulated(true);
    }
  };

  const handleEventTypeChange = (eventType: string) => {
    setForm((f) => ({ ...f, event_type: eventType }));
    if (sloDetail.length > 0) {
      applySloDefaults(sloDetail, eventType);
    }
  };

  const handleSlaDropdownChange = (id: string) => {
    handleSlaSelect(id);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const wf = await createWorkflow(form);
    navigate(`/workflows/${wf.id}/context`);
  };

  const matchingSlo = selectedSla
    ? sloDetail.find((s) => s.event_type === form.event_type)
    : null;

  return (
    <div className="max-w-lg mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-2">New SLA Renegotiation</h1>
      <p className="text-sm text-gray-500 mb-6">
        Describe the violation to initialize the renegotiation workflow.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">SLA Template (optional)</label>
          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={form.sla_id}
            onChange={(e) => handleSlaDropdownChange(e.target.value)}
          >
            <option value="">-- No SLA --</option>
            {slas.map((sla) => (
              <option key={sla.id} value={sla.id}>
                {sla.name}
              </option>
            ))}
          </select>
        </div>

        {selectedSla && (
          <div className="border rounded-lg bg-blue-50 px-4 py-3 text-sm">
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-blue-800">{selectedSla.name}</span>
              <span className="text-blue-600 text-xs">{selectedSla.slo_count} SLOs</span>
            </div>
            <p className="text-blue-700 text-xs mb-2">{selectedSla.description}</p>
            {matchingSlo && autoPopulated && (
              <p className="text-blue-600 text-xs">
                Agreed value auto-populated from {matchingSlo.metric} SLO ({matchingSlo.target_value} {matchingSlo.unit})
              </p>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Event Type</label>
          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={form.event_type}
            onChange={(e) => handleEventTypeChange(e.target.value)}
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
              className={`w-full border rounded-lg px-3 py-2 text-sm ${autoPopulated ? "bg-blue-50 border-blue-200" : ""}`}
              value={form.agreed_value}
              onChange={(e) => setForm({ ...form, agreed_value: parseFloat(e.target.value) })}
              required
            />
            {autoPopulated && (
              <p className="text-xs text-blue-500 mt-0.5">Auto-filled from SLA</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Unit</label>
            <input
              className={`w-full border rounded-lg px-3 py-2 text-sm ${autoPopulated ? "bg-blue-50 border-blue-200" : ""}`}
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
