import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getWorkflow, acceptRC, rejectRC } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import ReactMarkdown from "react-markdown";

export default function Validation() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<Record<string, unknown> | null>(null);
  const [feedback, setFeedback] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!id) return;
    getWorkflow(id).then(setWorkflow);
  }, [id]);

  if (!workflow) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  const rc = workflow.rc as Record<string, unknown> | null;

  const handleAccept = async () => {
    if (!id) return;
    await acceptRC(id, feedback);
    setDone(true);
  };

  const handleReject = async () => {
    if (!id) return;
    await rejectRC(id, feedback);
    setDone(true);
  };

  if (done) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center">
        <h1 className="text-2xl font-bold mb-2">Thank You</h1>
        <p className="text-gray-500 mb-6">Your response has been recorded.</p>
        <button onClick={() => navigate("/")} className="text-blue-600 text-sm hover:underline">
          Start new renegotiation
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Validate Renegotiation Clause</h1>
        <StatusBadge status={workflow.status as string} />
      </div>

      <div className="border rounded-lg p-6 bg-white shadow-sm mb-6">
        <h2 className="font-semibold mb-2">Negotiation Summary</h2>
        <p className="text-sm text-gray-600 mb-4">
          {workflow.current_round as number} of {workflow.max_rounds as number} rounds completed.
        </p>

        {rc && (
          <div className="bg-gray-50 rounded p-4">
            <h3 className="text-sm font-medium mb-2">Proposed Renegotiation Clause</h3>
            <div className="text-gray-800 text-sm [&_p]:m-0">
              <ReactMarkdown>{rc.clause_text as string}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium mb-1">Feedback (optional)</label>
        <textarea
          className="w-full border rounded-lg px-3 py-2 text-sm"
          rows={3}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Any comments or concerns about the proposed clause..."
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleAccept}
          className="flex-1 bg-green-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-green-700"
        >
          Accept Clause
        </button>
        <button
          onClick={handleReject}
          className="flex-1 bg-red-100 text-red-700 rounded-lg py-2.5 text-sm font-medium hover:bg-red-200"
        >
          Reject &amp; Request Changes
        </button>
      </div>
    </div>
  );
}
