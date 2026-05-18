import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getSLASLOs, setSLABatnas } from "../api/client";

interface SLOConfig {
  metric: string;
  unit: string;
  agreed_value: number;
  description: string;
  event_type: string;
  client_batna: number | null;
  provider_batna: number | null;
}

export default function BATNAConfig() {
  const { slaId } = useParams();
  const navigate = useNavigate();
  const [slos, setSlos] = useState<SLOConfig[]>([]);
  const [clientBatnas, setClientBatnas] = useState<Record<string, string>>({});
  const [providerBatnas, setProviderBatnas] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!slaId) return;
    getSLASLOs(slaId).then((data: SLOConfig[]) => {
      setSlos(data);
      const cb: Record<string, string> = {};
      const pb: Record<string, string> = {};
      for (const slo of data) {
        cb[slo.metric] = slo.client_batna?.toString() ?? "";
        pb[slo.metric] = slo.provider_batna?.toString() ?? "";
      }
      setClientBatnas(cb);
      setProviderBatnas(pb);
    });
  }, [slaId]);

  const handleSubmit = async () => {
    if (!slaId) return;
    setLoading(true);
    const parsedClient: Record<string, number> = {};
    const parsedProvider: Record<string, number> = {};
    for (const slo of slos) {
      parsedClient[slo.metric] = parseFloat(clientBatnas[slo.metric] || "0");
      parsedProvider[slo.metric] = parseFloat(providerBatnas[slo.metric] || "0");
    }
    await setSLABatnas(slaId, parsedClient, parsedProvider);
    setLoading(false);
    navigate(`/slas/${slaId}/profiles`);
  };

  if (slos.length === 0) {
    return (
      <div className="max-w-2xl mx-auto mt-8 text-center text-gray-500">
        Loading SLO configuration...
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-2">Configure BATNAs</h1>
      <p className="text-sm text-gray-500 mb-6">
        Set the walk-away values (BATNA) for each SLO. Client and provider each specify the worst acceptable value for every metric.
      </p>

      <div className="space-y-4 mb-6">
        {slos.map((slo) => (
          <div key={slo.metric} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium capitalize">{slo.metric}</span>
              <span className="text-xs text-gray-400">
                Agreed: {slo.agreed_value} {slo.unit}
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-3">{slo.description}</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium mb-1 text-blue-600">
                  Client BATNA
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder={`e.g. ${(slo.agreed_value * 1.3).toFixed(1)}`}
                  value={clientBatnas[slo.metric] ?? ""}
                  onChange={(e) =>
                    setClientBatnas({ ...clientBatnas, [slo.metric]: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1 text-emerald-600">
                  Provider BATNA
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder={`e.g. ${(slo.agreed_value * 1.1).toFixed(1)}`}
                  value={providerBatnas[slo.metric] ?? ""}
                  onChange={(e) =>
                    setProviderBatnas({ ...providerBatnas, [slo.metric]: e.target.value })
                  }
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Saving..." : "Save BATNAs & Configure Profiles"}
      </button>
    </div>
  );
}
