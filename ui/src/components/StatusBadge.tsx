interface Props {
  status: string;
}

const colors: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  context_gathering: "bg-blue-100 text-blue-700",
  profiling: "bg-purple-100 text-purple-700",
  negotiating: "bg-yellow-100 text-yellow-700",
  agreed: "bg-green-100 text-green-700",
  max_rounds_reached: "bg-orange-100 text-orange-700",
  failed: "bg-red-100 text-red-700",
  rejected: "bg-red-100 text-red-700",
};

export default function StatusBadge({ status }: Props) {
  const cls = colors[status] || "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
