interface Props {
  role: string;
  round: number;
  content: string;
  adjustments?: Record<string, number> | null;
}

export default function ProposalCard({ role, round, content, adjustments }: Props) {
  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {role} · Round {round}
        </span>
      </div>
      <p className="text-sm text-gray-800 mb-3">{content}</p>
      {adjustments && Object.keys(adjustments).length > 0 && (
        <div className="bg-gray-50 rounded p-2 text-xs space-y-1">
          {Object.entries(adjustments).map(([metric, value]) => (
            <div key={metric} className="flex justify-between">
              <span className="text-gray-600">{metric}</span>
              <span className="font-mono font-medium">{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
