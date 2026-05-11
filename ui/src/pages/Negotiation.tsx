import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ChatMessage from "../components/ChatMessage";
import StatusBadge from "../components/StatusBadge";
import { connectNegotiationWS } from "../api/client";

export default function Negotiation() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<
    { role: string; message: string; round: number }[]
  >([]);
  const [streamingMessage, setStreamingMessage] = useState<{
    role: string;
    content: string;
    round: number;
  } | null>(null);
  const [profilingStatus, setProfilingStatus] = useState("");
  const [status, setStatus] = useState("pending");
  const [rc, setRc] = useState<Record<string, unknown> | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const connectedRef = useRef(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    const ws = connectNegotiationWS(id);
    wsRef.current = ws;

    const timeout = setTimeout(() => {
      if (ws !== wsRef.current) return;
      if (ws.readyState !== WebSocket.OPEN) {
        setError(
          "Connection timed out. Make sure the backend server is running on port 8000.",
        );
        ws.close();
      }
    }, 15000);

    ws.onopen = () => {
      if (ws !== wsRef.current) return;
      clearTimeout(timeout);
      connectedRef.current = true;
      setConnected(true);
      ws.send(JSON.stringify({ type: "start" }));
    };

    ws.onerror = () => {
      if (ws !== wsRef.current) return;
      clearTimeout(timeout);
      setError("Failed to connect to the negotiation server.");
    };

    ws.onclose = () => {
      if (ws !== wsRef.current) return;
      clearTimeout(timeout);
      if (!connectedRef.current) {
        setError("Connection closed before negotiation could start.");
      }
    };

    ws.onmessage = (event) => {
      if (ws !== wsRef.current) return;
      const data = JSON.parse(event.data);

      if (data.type === "profiling.progress") {
        setProfilingStatus(data.status);
      } else if (data.type === "profiling.complete") {
        setStatus("profiling");
        setProfilingStatus("");
      } else if (data.type === "negotiation.token") {
        setProfilingStatus("");
        setStreamingMessage((prev) => {
          if (prev && prev.role === data.role && prev.round === data.round) {
            return { ...prev, content: prev.content + data.token };
          }
          return { role: data.role, content: data.token, round: data.round };
        });
      } else if (data.type === "negotiation.token.done") {
        setMessages((prev) => [
          ...prev,
          {
            role: data.proposal.role,
            message: data.proposal.content,
            round: data.round,
          },
        ]);
        setStreamingMessage((prev) =>
          prev && prev.role === data.role && prev.round === data.round
            ? null
            : prev,
        );
      } else if (data.type === "negotiation.round") {
        setStatus(data.status);
      } else if (data.type === "negotiation.complete") {
        setProfilingStatus("");
        setStatus(data.status);
        setRc(data.rc);
      }
    };

    return () => {
      clearTimeout(timeout);
    };
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Negotiation</h1>
        <StatusBadge status={status} />
      </div>

      {error && (
        <div className="text-center py-12 text-red-500">
          <p>{error}</p>
        </div>
      )}

      {!connected && !error && (
        <div className="text-center py-12 text-gray-500">
          <p>Connecting to negotiation server...</p>
        </div>
      )}

      {connected && messages.length === 0 && !streamingMessage && (
        <div className="text-center py-12 text-gray-500">
          <p>{profilingStatus || "Profiling stakeholders and computing ZOPA..."}</p>
        </div>
      )}

      <div className="space-y-4 mb-6">
        {messages.map((msg, i) => (
          <ChatMessage
            key={i}
            role={msg.role as "client" | "provider"}
            message={msg.message}
            round={msg.round}
          />
        ))}
        {streamingMessage && (
          <div className="animate-pulse">
            <ChatMessage
              role={streamingMessage.role as "client" | "provider"}
              message={streamingMessage.content}
              round={streamingMessage.round}
            />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {streamingMessage && (
        <div className="text-center py-2 text-xs text-blue-500 animate-pulse">
          Agent is typing...
        </div>
      )}

      {!streamingMessage && profilingStatus && (
        <div className="text-center py-4">
          <div className="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="ml-2 text-sm text-gray-500">{profilingStatus}</span>
        </div>
      )}

      {rc && (
        <div className="border rounded-lg p-6 bg-green-50">
          <h2 className="font-semibold text-lg mb-3">
            Renegotiation Clause Generated
          </h2>
          <pre className="text-xs bg-white rounded p-4 overflow-x-auto border">
            {JSON.stringify(rc, null, 2)}
          </pre>
          <button
            onClick={() => navigate(`/workflows/${id}/validation`)}
            className="mt-4 bg-green-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-green-700"
          >
            Review & Validate
          </button>
        </div>
      )}
    </div>
  );
}
