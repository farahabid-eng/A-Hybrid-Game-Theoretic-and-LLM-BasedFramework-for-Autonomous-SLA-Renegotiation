import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getSLAs, getSLA, initWorkflow } from "../api/client";

interface SLAOption {
  id: string;
  name: string;
  description: string;
  slo_count: number;
}

interface SLO {
  metric: string;
  target_value: number;
  unit: string;
  description: string;
}

interface SLADetails {
  id: string;
  name: string;
  description: string;
  slos: SLO[];
}

export default function Home() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [slas, setSlas] = useState<SLAOption[]>([]);
  const [slaId, setSlaId] = useState("");
  const [slaDetails, setSlaDetails] = useState<SLADetails | null>(null);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    getSLAs().then((data) => {
      setSlas(data);
      const param = searchParams.get("sla");
      if (param) {
        setSlaId(param);
      }
    });
  }, [searchParams]);

  useEffect(() => {
    if (slaId) {
      getSLA(slaId).then((details) => {
        setSlaDetails(details);
        // Initialize equal weights summing to 1.0
        const numMetrics = details.slos.length;
        if (numMetrics > 0) {
          const equalWeight = parseFloat((1 / numMetrics).toFixed(2));
          const newWeights: Record<string, number> = {};
          let sum = 0;
          details.slos.forEach((slo, index) => {
            if (index === numMetrics - 1) {
              newWeights[slo.metric] = parseFloat((1.0 - sum).toFixed(2));
            } else {
              newWeights[slo.metric] = equalWeight;
              sum += equalWeight;
            }
          });
          setWeights(newWeights);
        }
      });
    } else {
      setSlaDetails(null);
      setWeights({});
    }
  }, [slaId]);

  const handleWeightChange = (metric: string, val: number) => {
    // Round to 2 decimal places to avoid IEEE float issues
    const rounded = parseFloat(val.toFixed(2));
    setWeights((prev) => ({
      ...prev,
      [metric]: isNaN(rounded) ? 0 : rounded,
    }));
  };

  const totalSum = parseFloat(
    Object.values(weights)
      .reduce((sum, w) => sum + w, 0)
      .toFixed(2)
  );

  const isValid = totalSum === 1.0;

  const handleStartWorkflow = async () => {
    if (!isValid || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const res = await initWorkflow({
        sla_id: slaId,
        metric_weights: weights,
      });
      if (res && res.id) {
        navigate(`/workflows/${res.id}/simulate`);
      }
    } catch (err) {
      console.error("Failed to start workflow:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-10 px-4">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-3">
          SLA renegotiation
        </h1>
        <p className="text-slate-500 max-w-lg mx-auto text-sm leading-relaxed">
          Select an SLA template, customize the metric priorities/weights (must sum to exactly 1.0), and start the automated multi-agent negotiation process.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-xl shadow-slate-100/50 p-6 md:p-8 space-y-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">SLA Template</label>
          <select
            className="w-full border border-slate-200 bg-slate-50/50 rounded-xl px-4 py-3 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all cursor-pointer"
            value={slaId}
            onChange={(e) => setSlaId(e.target.value)}
            required
          >
            <option value="">-- Select an SLA Template --</option>
            {slas.map((sla) => (
              <option key={sla.id} value={sla.id}>
                {sla.name} ({sla.slo_count} SLOs)
              </option>
            ))}
          </select>
        </div>

        {slaDetails && (
          <div className="space-y-6 animate-fadeIn">
            {/* Template Info Card */}
            <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-5">
              <h3 className="font-semibold text-blue-900 text-base mb-1">{slaDetails.name}</h3>
              <p className="text-blue-800/80 text-xs leading-relaxed">{slaDetails.description}</p>
            </div>

            {/* Metric Weights Selector */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-700">Metric Weights Configuration</h3>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full transition-all duration-300 ${
                    isValid
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-100"
                      : "bg-amber-50 text-amber-700 border border-amber-100"
                  }`}
                >
                  Sum: {totalSum.toFixed(2)} / 1.00 {isValid ? "✓" : "✗"}
                </span>
              </div>

              <div className="space-y-3">
                {slaDetails.slos.map((slo) => {
                  const w = weights[slo.metric] ?? 0;
                  return (
                    <div
                      key={slo.metric}
                      className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/20 hover:bg-slate-50/50 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-slate-800 capitalize text-sm">
                            {slo.metric}
                          </span>
                          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                            Target: {slo.target_value} {slo.unit}
                          </span>
                        </div>
                        <p className="text-slate-500 text-xs">{slo.description}</p>
                      </div>

                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={w}
                          onChange={(e) =>
                            handleWeightChange(slo.metric, parseFloat(e.target.value))
                          }
                          className="w-32 accent-blue-600 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                        />
                        <div className="relative rounded-lg shadow-sm w-20">
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.01"
                            value={w}
                            onChange={(e) =>
                              handleWeightChange(slo.metric, parseFloat(e.target.value))
                            }
                            className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-right text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {!isValid && (
                <p className="mt-3 text-xs text-amber-600 font-medium animate-pulse">
                  * Please adjust the weights so the sum is exactly 1.00 before starting.
                </p>
              )}
            </div>

            {/* Action Button */}
            <button
              onClick={handleStartWorkflow}
              disabled={!isValid || isSubmitting}
              className={`w-full text-white rounded-xl py-3.5 text-sm font-semibold tracking-wide transition-all shadow-md shadow-blue-500/10 ${
                isValid && !isSubmitting
                  ? "bg-blue-600 hover:bg-blue-700 active:scale-[0.99] cursor-pointer"
                  : "bg-slate-200 text-slate-400 cursor-not-allowed shadow-none"
              }`}
            >
              {isSubmitting ? "Starting workflow..." : "Start Renegotiation"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
