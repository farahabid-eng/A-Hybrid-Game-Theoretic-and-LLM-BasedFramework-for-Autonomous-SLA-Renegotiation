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

export async function createWorkflow(data: {
  event_type: string;
  observed_value: number;
  agreed_value?: number | null;
  unit?: string;
  sla_id?: string | null;
  max_rounds?: number;
}) {
  const res = await fetch(`${httpBase()}/workflows`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
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
    }>;
  }>;
}

export async function getWorkflow(id: string) {
  const res = await fetch(`${httpBase()}/workflows/${id}`);
  return res.json();
}

export async function submitClientForm(
  id: string,
  data: Record<string, unknown>,
) {
  const res = await fetch(`${httpBase()}/workflows/${id}/context/client`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function submitProviderForm(
  id: string,
  data: Record<string, unknown>,
) {
  const res = await fetch(`${httpBase()}/workflows/${id}/context/provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
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
