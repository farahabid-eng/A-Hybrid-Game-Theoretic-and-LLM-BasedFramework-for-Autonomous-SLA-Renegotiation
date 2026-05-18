import ReactMarkdown from "react-markdown";
import { User, Server } from "lucide-react";
import ProfileTooltip from "./ProfileTooltip";
import type { StakeholderProfile } from "./ProfileTooltip";

interface Props {
  role: "client" | "provider";
  message: string;
  round: number;
  profile?: StakeholderProfile;
}

export default function ChatMessage({ role, message, round, profile }: Props) {
  const isClient = role === "client";

  const icon = (
    <div
      className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${
        isClient ? "bg-blue-500" : "bg-emerald-500"
      }`}
    >
      {isClient ? <User className="w-4 h-4" /> : <Server className="w-4 h-4" />}
    </div>
  );

  return (
    <div className={`flex gap-3 ${isClient ? "" : "flex-row-reverse"}`}>
      {profile ? (
        <ProfileTooltip profile={profile}>{icon}</ProfileTooltip>
      ) : (
        icon
      )}
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 text-sm ${
          isClient ? "bg-blue-50 border border-blue-200" : "bg-emerald-50 border border-emerald-200"
        }`}
      >
        <div className="font-medium text-xs text-gray-500 mb-1">
          {isClient ? "Client" : "Provider"} · Round {round}
        </div>
        <div className="text-gray-800 [&_p]:m-0 [&_ul]:m-0 [&_ul]:pl-4">
          <ReactMarkdown>{message}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
