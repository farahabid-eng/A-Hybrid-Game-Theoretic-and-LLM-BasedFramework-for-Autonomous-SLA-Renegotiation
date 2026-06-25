import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSLAs } from "../api/client";

interface SLAOption {
  id: string;
  name: string;
  description: string;
  slo_count: number;
}

export default function Home() {
  const navigate = useNavigate();
  const [slas, setSlas] = useState<SLAOption[]>([]);
  const [slaId, setSlaId] = useState("");

  useEffect(() => {
    getSLAs().then(setSlas);
  }, []);

  const selectedSla = slas.find((s) => s.id === slaId);

  return (
    <div className="max-w-lg mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-2">SLA Renegotiation</h1>
      <p className="text-sm text-gray-500 mb-6">
        Select an SLA template to configure BATNAs and stakeholder profiles. A workflow will be created before simulating a violation.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">SLA Template</label>
          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={slaId}
            onChange={(e) => setSlaId(e.target.value)}
            required
          >
            <option value="">-- Select an SLA --</option>
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
            <p className="text-blue-700 text-xs">{selectedSla.description}</p>
          </div>
        )}

        <button
          onClick={() => slaId && navigate(`/slas/${slaId}/batnas`)}
          disabled={!slaId}
          className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          Configure BATNAs & Profiles
        </button>
      </div>
    </div>
  );
}
