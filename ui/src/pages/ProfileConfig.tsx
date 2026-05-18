import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { setSLAProfile, generateSLAProfile, getSLAProfile, initWorkflow } from "../api/client";

const TONE_OPTIONS = ["neutral", "collaborative", "diplomatic", "formal", "aggressive", "urgent"];

interface ProfileForm {
  objectives: string;
  priorities: string;
  flexibility_margins: string;
  context_description: string;
  tone: string;
}

const defaultForm: ProfileForm = {
  objectives: "",
  priorities: "",
  flexibility_margins: "",
  context_description: "",
  tone: "neutral",
};

function parseProfileForm(form: ProfileForm) {
  return {
    objectives: form.objectives
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean),
    priorities: parseFloatPairs(form.priorities),
    flexibility_margins: parseFloatPairs(form.flexibility_margins),
    context_description: form.context_description,
    tone: form.tone,
  };
}

function parseFloatPairs(input: string): Record<string, number> {
  const result: Record<string, number> = {};
  for (const line of input.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const parts = trimmed.split(":");
    if (parts.length === 2) {
      const key = parts[0].trim();
      const val = parseFloat(parts[1].trim());
      if (key && !isNaN(val)) {
        result[key] = val;
      }
    }
  }
  return result;
}

function formatFloatPairs(data: Record<string, number>): string {
  return Object.entries(data)
    .map(([k, v]) => `${k}: ${v}`)
    .join("\n");
}

function formatList(data: string[]): string {
  return data.join("\n");
}

export default function ProfileConfig() {
  const { slaId } = useParams();
  const navigate = useNavigate();
  const [step, setStep] = useState<"client" | "provider">("client");
  const [clientForm, setClientForm] = useState<ProfileForm>(defaultForm);
  const [providerForm, setProviderForm] = useState<ProfileForm>(defaultForm);
  const [genContext, setGenContext] = useState("");
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slaId) return;
    getSLAProfile(slaId, "client").then((p) => {
      if (p) {
        setClientForm({
          objectives: formatList(p.objectives || []),
          priorities: formatFloatPairs(p.priorities || {}),
          flexibility_margins: formatFloatPairs(p.flexibility_margins || {}),
          context_description: p.context_description || "",
          tone: p.tone || "neutral",
        });
      }
      // pre-fetch provider for when user advances
      getSLAProfile(slaId, "provider").then((pp) => {
        if (pp) {
          setProviderForm({
            objectives: formatList(pp.objectives || []),
            priorities: formatFloatPairs(pp.priorities || {}),
            flexibility_margins: formatFloatPairs(pp.flexibility_margins || {}),
            context_description: pp.context_description || "",
            tone: pp.tone || "neutral",
          });
        }
        setLoading(false);
      });
    });
  }, [slaId]);

  const currentForm = step === "client" ? clientForm : providerForm;
  const setCurrentForm = step === "client" ? setClientForm : setProviderForm;

  const handleGenerate = async () => {
    if (!slaId || !genContext.trim()) return;
    setGenerating(true);
    try {
      const profile = await generateSLAProfile(slaId, step, genContext);
      setCurrentForm({
        objectives: formatList(profile.objectives || []),
        priorities: formatFloatPairs(profile.priorities || {}),
        flexibility_margins: formatFloatPairs(profile.flexibility_margins || {}),
        context_description: profile.context_description || "",
        tone: profile.tone || "neutral",
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!slaId) return;
    setSaving(true);
    try {
      const parsed = parseProfileForm(currentForm);
      await setSLAProfile(slaId, step, parsed);

      if (step === "client") {
        setStep("provider");
        setGenContext("");
      } else {
        const wf = await initWorkflow({ sla_id: slaId, max_rounds: 10 });
        navigate(`/workflows/${wf.id}/simulate`);
      }
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field: keyof ProfileForm, value: string) => {
    setCurrentForm((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto mt-8 text-center text-gray-500">
        Loading profiles...
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <div className="flex items-center gap-2 mb-6">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            step === "client"
              ? "bg-blue-600 text-white"
              : "bg-green-100 text-green-700"
          }`}
        >
          1
        </div>
        <span className="text-sm">Client Profile</span>
        <div className="h-px flex-1 bg-gray-300 mx-2" />
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            step === "provider"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-400"
          }`}
        >
          2
        </div>
        <span className="text-sm">Provider Profile</span>
      </div>

      <h2 className="text-xl font-semibold mb-1 capitalize">{step} Profile</h2>
      <p className="text-sm text-gray-500 mb-4">
        Fill in the profile fields manually, or use AI generation with a brief context.
      </p>

      {/* AI Generation */}
      <div className="border rounded-lg p-4 mb-6 bg-gray-50">
        <label className="block text-sm font-medium mb-1">
          Generate with AI (optional)
        </label>
        <div className="flex gap-2">
          <textarea
            className="flex-1 border rounded-lg px-3 py-2 text-sm"
            rows={2}
            placeholder={`Describe the ${step}'s situation, e.g. "Low-latency gaming app requiring sub-50ms response times"`}
            value={genContext}
            onChange={(e) => setGenContext(e.target.value)}
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating || !genContext.trim()}
          className="mt-2 bg-purple-600 text-white rounded-lg px-4 py-1.5 text-xs font-medium hover:bg-purple-700 disabled:opacity-50"
        >
          {generating ? "Generating..." : "Generate"}
        </button>
      </div>

      {/* Manual Fields */}
      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1">Context Description</label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm"
            rows={2}
            value={currentForm.context_description}
            onChange={(e) => updateField("context_description", e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Objectives (one per line)
          </label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm"
            rows={3}
            value={currentForm.objectives}
            onChange={(e) => updateField("objectives", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Priorities (metric: weight, one per line)
            </label>
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm"
              rows={3}
              value={currentForm.priorities}
              onChange={(e) => updateField("priorities", e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Flexibility Margins (metric: margin, one per line)
            </label>
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm"
              rows={3}
              value={currentForm.flexibility_margins}
              onChange={(e) => updateField("flexibility_margins", e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Negotiation Tone</label>
          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={currentForm.tone}
            onChange={(e) => updateField("tone", e.target.value)}
          >
            {TONE_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? "Saving..." : step === "client" ? "Save Client & Continue to Provider" : "Save Provider & Continue to Violation"}
      </button>
    </div>
  );
}
