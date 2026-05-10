import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { submitClientForm, submitProviderForm } from "../api/client";

type FormData = Record<string, unknown>;

const TONE_OPTIONS = ["neutral", "collaborative", "diplomatic", "formal", "aggressive", "urgent"];

const defaultClient: FormData = {
  business_context: "Low-latency gaming application requiring consistent sub-50ms response times",
  objectives: ["Maintain low latency", "Ensure high availability", "Control costs"],
  priorities: { latency: 0.5, availability: 0.3, cost: 0.2 },
  flexibility_margins: { latency: 0.2, availability: 0.1, cost: 0.3 },
  constraints: ["Cannot exceed 100ms p99 latency", "Require 99.9% uptime"],
  batna: 150,
  tone: "neutral",
};

const defaultProvider: FormData = {
  resource_limitations: ["Limited east-coast capacity", "Peak-hour bandwidth constraints"],
  operational_constraints: ["Maintenance windows every 2 weeks", "Max 3 concurrent high-compute tenants per node"],
  priorities: { latency: 0.3, availability: 0.2, cost: 0.5 },
  flexibility_margins: { latency: 0.15, availability: 0.15, cost: 0.25 },
  cost_considerations: "Infrastructure costs increased 15% due to hardware refresh cycle",
  batna: 125,
};

export default function ContextForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [step, setStep] = useState<"client" | "provider">("client");
  const [clientData, setClientData] = useState(defaultClient);
  const [providerData, setProviderData] = useState(defaultProvider);
  const [loading, setLoading] = useState(false);

  const handleClientSubmit = async () => {
    if (!id) return;
    setLoading(true);
    await submitClientForm(id, clientData);
    setLoading(false);
    setStep("provider");
  };

  const handleProviderSubmit = async () => {
    if (!id) return;
    setLoading(true);
    await submitProviderForm(id, providerData);
    setLoading(false);
    navigate(`/workflows/${id}/negotiation`);
  };

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <div className="flex items-center gap-2 mb-6">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step === "client" ? "bg-blue-600 text-white" : "bg-green-100 text-green-700"}`}>1</div>
        <span className="text-sm">Client Context</span>
        <div className="h-px flex-1 bg-gray-300 mx-2" />
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step === "provider" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-400"}`}>2</div>
        <span className="text-sm">Provider Context</span>
      </div>

      {step === "client" ? (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Client Context</h2>
          <FormSection label="Business Context">
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm" rows={3} value={clientData.business_context as string} onChange={(e) => setClientData({ ...clientData, business_context: e.target.value })} />
          </FormSection>
          <FormSection label="BATNA (walk-away absolute value)">
            <input
              type="number"
              step="any"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="e.g. 150"
              value={clientData.batna as number}
              onChange={(e) => setClientData({ ...clientData, batna: parseFloat(e.target.value || "0") })}
            />
          </FormSection>
          <FormSection label="Negotiation Tone">
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={clientData.tone as string}
              onChange={(e) => setClientData({ ...clientData, tone: e.target.value })}
            >
              {TONE_OPTIONS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </FormSection>
          <button onClick={handleClientSubmit} disabled={loading} className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {loading ? "Submitting..." : "Submit Client Context"}
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Provider Context</h2>
          <FormSection label="Cost Considerations">
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm" rows={3} value={providerData.cost_considerations as string} onChange={(e) => setProviderData({ ...providerData, cost_considerations: e.target.value })} />
          </FormSection>
          <FormSection label="BATNA (walk-away absolute value)">
            <input
              type="number"
              step="any"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="e.g. 80"
              value={providerData.batna as number}
              onChange={(e) => setProviderData({ ...providerData, batna: parseFloat(e.target.value || "0") })}
            />
          </FormSection>
          <button onClick={handleProviderSubmit} disabled={loading} className="w-full bg-emerald-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-emerald-700 disabled:opacity-50">
            {loading ? "Submitting..." : "Submit Provider Context & Start"}
          </button>
        </div>
      )}
    </div>
  );
}

function FormSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      {children}
    </div>
  );
}
