const BASE = "";

export async function createWorkflow(data: {
  event_type: string;
  observed_value: number;
  agreed_value: number;
  unit?: string;
  max_rounds?: number;
}) {
  const res = await fetch(`${BASE}/workflows`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getWorkflow(id: string) {
  const res = await fetch(`${BASE}/workflows/${id}`);
  return res.json();
}

export async function submitClientForm(id: string, data: Record<string, unknown>) {
  const res = await fetch(`${BASE}/workflows/${id}/context/client`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function submitProviderForm(id: string, data: Record<string, unknown>) {
  const res = await fetch(`${BASE}/workflows/${id}/context/provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export function connectNegotiationWS(id: string): WebSocket {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return new WebSocket(`${protocol}//${host}/workflows/${id}/negotiation/ws`);
}

export async function acceptRC(id: string, feedback = "") {
  const res = await fetch(`${BASE}/workflows/${id}/rc/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accepted: true, feedback }),
  });
  return res.json();
}

export async function rejectRC(id: string, feedback = "") {
  const res = await fetch(`${BASE}/workflows/${id}/rc/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accepted: false, feedback }),
  });
  return res.json();
}
