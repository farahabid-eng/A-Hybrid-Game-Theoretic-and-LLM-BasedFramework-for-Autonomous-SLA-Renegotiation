const API_URL = import.meta.env.VITE_API_URL || "";

function httpBase(): string {
  return API_URL;
}

function wsBase(): string {
  if (!API_URL) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }
  const url = new URL(API_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString().replace(/\/$/, "");
}

export async function initWorkflow(data: { sla_id: string; max_rounds?: number; metric_weights?: Record<string, number> }) {
  const res = await fetch(`${httpBase()}/workflows`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getWorkflow(id: string) {
  const res = await fetch(`${httpBase()}/workflows/${id}`);
  return res.json();
}

export async function getWorkflowSLOs(id: string) {
  const res = await fetch(`${httpBase()}/workflows/${id}/slos`);
  return res.json();
}

export async function setBatnas(
  id: string,
  client_batnas: Record<string, number>,
  provider_batnas: Record<string, number>,
) {
  const res = await fetch(`${httpBase()}/workflows/${id}/batnas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_batnas, provider_batnas }),
  });
  return res.json();
}

export async function setProfile(
  id: string,
  role: "client" | "provider",
  data: {
    objectives: string[];
    priorities: Record<string, number>;
    flexibility_margins: Record<string, number>;
    context_description: string;
    tone: string;
  },
) {
  const res = await fetch(`${httpBase()}/workflows/${id}/profiles/${role}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function generateProfile(
  id: string,
  role: "client" | "provider",
  context: string,
) {
  const res = await fetch(`${httpBase()}/workflows/${id}/profiles/${role}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
  return res.json();
}

export async function simulateViolation(
  id: string,
  event_type: string,
  observed_value: number,
) {
  const res = await fetch(`${httpBase()}/workflows/${id}/violation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_type, observed_value }),
  });
  return res.json();
}

export async function getSLAs() {
  const res = await fetch(`${httpBase()}/slas`);
  return res.json() as Promise<
    Array<{
      id: string;
      name: string;
      description: string;
      slo_count: number;
    }>
  >;
}

export async function getSLA(id: string) {
  const res = await fetch(`${httpBase()}/slas/${id}`);
  return res.json() as Promise<{
    id: string;
    name: string;
    description: string;
    slos: Array<{
      metric: string;
      target_value: number;
      unit: string;
      description: string;
      event_type: string;
      time_to_repair: number;
    }>;
  }>;
}

export async function getSLASLOs(slaId: string) {
  const res = await fetch(`${httpBase()}/slas/${slaId}/slos`);
  return res.json() as Promise<
    Array<{
      metric: string;
      unit: string;
      agreed_value: number;
      description: string;
      event_type: string;
      time_to_repair: number;
      client_batna: number | null;
      provider_batna: number | null;
    }>
  >;
}

export async function setSLABatnas(
  slaId: string,
  client_batnas: Record<string, number>,
  provider_batnas: Record<string, number>,
) {
  const res = await fetch(`${httpBase()}/slas/${slaId}/batnas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_batnas, provider_batnas }),
  });
  if (!res.ok) throw new Error("Failed to set SLA BATNAs");
}

export async function setSLAProfile(
  slaId: string,
  role: "client" | "provider",
  data: {
    objectives: string[];
    priorities: Record<string, number>;
    flexibility_margins: Record<string, number>;
    context_description: string;
    tone: string;
  },
) {
  const res = await fetch(`${httpBase()}/slas/${slaId}/profiles/${role}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to set SLA profile");
}

export async function getSLAProfile(slaId: string, role: "client" | "provider") {
  const res = await fetch(`${httpBase()}/slas/${slaId}/profiles/${role}`);
  if (!res.ok) return null;
  return res.json() as Promise<{
    objectives: string[];
    priorities: Record<string, number>;
    flexibility_margins: Record<string, number>;
    context_description: string;
    tone: string;
  } | null>;
}

export async function generateSLAProfile(
  slaId: string,
  role: "client" | "provider",
  context: string,
) {
  const res = await fetch(`${httpBase()}/slas/${slaId}/profiles/${role}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
  return res.json() as Promise<{
    objectives: string[];
    priorities: Record<string, number>;
    flexibility_margins: Record<string, number>;
    context_description: string;
    tone: string;
  }>;
}

export function connectNegotiationWS(id: string): WebSocket {
  return new WebSocket(`${wsBase()}/workflows/${id}/negotiation/ws`);
}

export async function acceptRC(id: string, feedback = "") {
  const res = await fetch(`${httpBase()}/workflows/${id}/rc/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accepted: true, feedback }),
  });
  return res.json();
}

export async function rejectRC(id: string, feedback = "") {
  const res = await fetch(`${httpBase()}/workflows/${id}/rc/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accepted: false, feedback }),
  });
  return res.json();
}
