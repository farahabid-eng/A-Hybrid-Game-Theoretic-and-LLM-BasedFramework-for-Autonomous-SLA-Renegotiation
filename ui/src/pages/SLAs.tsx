import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSLAs, getSLA } from "../api/client";

interface SLA {
  id: string;
  name: string;
  description: string;
  slo_count: number;
}

interface SLODetail {
  metric: string;
  target_value: number;
  unit: string;
  description: string;
  event_type: string;
  time_to_repair: number;
}

interface SLADetail {
  id: string;
  name: string;
  description: string;
  slos: SLODetail[];
}

export default function SLAs() {
  const navigate = useNavigate();
  const [slas, setSlas] = useState<SLA[]>([]);
  const [selected, setSelected] = useState<SLADetail | null>(null);

  useEffect(() => {
    getSLAs().then(setSlas);
  }, []);

  const handlePreview = async (id: string) => {
    const detail = await getSLA(id);
    setSelected(detail);
  };

  const handleUse = (id: string) => {
    navigate(`/?sla=${id}`);
  };

  return (
    <div className="max-w-4xl mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-2">Predefined SLA Templates</h1>
      <p className="text-sm text-gray-500 mb-6">
        Browse available SLA templates. Select one to preview its SLOs or use it
        to start a renegotiation.
      </p>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {slas.map((sla) => (
          <div
            key={sla.id}
            className="border rounded-xl p-5 bg-white shadow-sm hover:shadow-md transition-shadow"
          >
            <h3 className="font-semibold text-lg mb-1">{sla.name}</h3>
            <p className="text-sm text-gray-500 mb-3 line-clamp-2">
              {sla.description}
            </p>
            <p className="text-xs text-gray-400 mb-4">
              {sla.slo_count} SLO{sla.slo_count !== 1 ? "s" : ""}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => handlePreview(sla.id)}
                className="flex-1 text-sm border border-blue-600 text-blue-600 rounded-lg py-1.5 hover:bg-blue-50 transition-colors"
              >
                Preview
              </button>
              <button
                onClick={() => handleUse(sla.id)}
                className="flex-1 text-sm bg-blue-600 text-white rounded-lg py-1.5 hover:bg-blue-700 transition-colors"
              >
                Use SLA
              </button>
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <div className="mt-8 border rounded-xl bg-white shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{selected.name}</h2>
              <p className="text-sm text-gray-500">{selected.description}</p>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            >
              &times;
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="px-5 py-3 font-medium text-gray-600">
                    Violation Type
                  </th>
                  <th className="px-5 py-3 font-medium text-gray-600">
                    Metric
                  </th>
                  <th className="px-5 py-3 font-medium text-gray-600">
                    Target
                  </th>
                  <th className="px-5 py-3 font-medium text-gray-600">Unit</th>
                  <th className="px-5 py-3 font-medium text-gray-600">TTR</th>
                  <th className="px-5 py-3 font-medium text-gray-600">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody>
                {selected.slos.map((slo, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-5 py-3 capitalize">
                      {slo.event_type.replace(/_/g, " ")}
                    </td>
                    <td className="px-5 py-3">{slo.metric}</td>
                    <td className="px-5 py-3 font-mono">{slo.target_value}</td>
                    <td className="px-5 py-3">{slo.unit}</td>
                    <td className="px-5 py-3 font-mono">
                      {slo.time_to_repair}min
                    </td>
                    <td className="px-5 py-3 text-gray-500">
                      {slo.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-5 py-3 border-t flex justify-end">
            <button
              onClick={() => handleUse(selected.id)}
              className="text-sm bg-blue-600 text-white rounded-lg px-4 py-1.5 hover:bg-blue-700 transition-colors"
            >
              Use This SLA
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
