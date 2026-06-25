import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getWorkflowSLOs, simulateViolation } from "../api/client";

interface SLOConfig {
  metric: string;
  unit: string;
  agreed_value: number;
  description: string;
  event_type: string;
}

export default function ViolationSim() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [slos, setSlos] = useState<SLOConfig[]>([]);
  const [selectedMetric, setSelectedMetric] = useState("");
  const [observedValue, setObservedValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    getWorkflowSLOs(id).then((data: SLOConfig[]) => {
      setSlos(data);
      if (data.length > 0) {
        setSelectedMetric(data[0].metric);
      }
    });
  }, [id]);

  const selectedSlo = slos.find((s) => s.metric === selectedMetric);

  const handleSubmit = async () => {
    if (!id || !selectedMetric) return;
    const observed = parseFloat(observedValue);
    if (isNaN(observed)) {
      setError("Enter a valid observed value");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await simulateViolation(id, selectedSlo!.event_type, observed);
      navigate(`/workflows/${id}/negotiation`);
    } catch {
      setError("Failed to simulate violation");
    } finally {
      setLoading(false);
    }
  };

  if (slos.length === 0) {
    return (
      <div className="max-w-lg mx-auto mt-8 text-center text-gray-500">
        Loading...
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-2">Simulate Violation</h1>
      <p className="text-sm text-gray-500 mb-6">
        Select the SLO metric that was violated and enter the observed value. The agreed value is auto-detected from the SLA template.
      </p>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1">Violated Metric</label>
          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
          >
            {slos.map((slo) => (
              <option key={slo.metric} value={slo.metric}>
                {slo.metric} ({slo.description})
              </option>
            ))}
          </select>
        </div>

        {selectedSlo && (
          <div className="border rounded-lg bg-blue-50 px-4 py-3 text-sm">
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-blue-800 capitalize">
                {selectedSlo.metric}
              </span>
              <span className="text-blue-600 text-xs">{selectedSlo.unit}</span>
            </div>
            <p className="text-blue-700 text-xs mb-1">{selectedSlo.description}</p>
            <p className="text-blue-600 text-xs">
              Agreed value: <strong>{selectedSlo.agreed_value}</strong> {selectedSlo.unit}
            </p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Observed Value</label>
          <input
            type="number"
            step="any"
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder={selectedSlo ? `e.g. ${(selectedSlo.agreed_value * 1.5).toFixed(1)}` : ""}
            value={observedValue}
            onChange={(e) => setObservedValue(e.target.value)}
            required
          />
          {selectedSlo && parseFloat(observedValue) > selectedSlo.agreed_value && (
            <p className="text-xs text-amber-600 mt-1">
              Observed value exceeds agreed threshold — this will trigger a violation.
            </p>
          )}
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-500 mb-4">{error}</div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading || !observedValue}
        className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Starting Negotiation..." : "Simulate Violation & Start Negotiation"}
      </button>
    </div>
  );
}
