export interface StakeholderProfile {
  role: "client" | "provider";
  objectives: string[];
  priorities: Record<string, number>;
  flexibility_margins: Record<string, number>;
  constraints: string[];
  batna: number | null;
  context_description: string;
  tone: string;
}

interface Props {
  profile: StakeholderProfile;
  children: React.ReactNode;
}

export default function ProfileTooltip({ profile, children }: Props) {
  return (
    <div className="group relative inline-block">
      {children}
      <div className="absolute z-50 left-1/2 -translate-x-1/2 bottom-full mb-2 w-80 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none">
        <div className="bg-white border border-gray-200 rounded-xl shadow-xl p-4 text-xs space-y-3 -z-20 overflow-y-auto">
          <h3 className="font-semibold text-sm capitalize flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                profile.role === "client" ? "bg-blue-500" : "bg-emerald-500"
              }`}
            />
            {profile.role} Profile
            <span className="ml-auto text-[10px] uppercase tracking-wider text-gray-400 border border-gray-200 rounded px-1.5 py-0.5">
              {profile.tone}
            </span>
          </h3>

          <p className="text-gray-600 leading-relaxed">
            {profile.context_description}
          </p>

          <div>
            <div className="font-medium text-gray-700 mb-1">Objectives</div>
            <ul className="space-y-0.5 text-gray-600">
              {profile.objectives.map((o, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-blue-400 mt-0.5 shrink-0">&#8226;</span>
                  <span>{o}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div className="font-medium text-gray-700 mb-1">Priorities</div>
            <div className="space-y-1">
              {Object.entries(profile.priorities).map(([k, v]) => (
                <div key={k} className="flex items-center gap-2">
                  <span className="capitalize text-gray-600 w-24 shrink-0">
                    {k}
                  </span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        profile.role === "client"
                          ? "bg-blue-400"
                          : "bg-emerald-400"
                      }`}
                      style={{ width: `${v * 100}%` }}
                    />
                  </div>
                  <span className="text-gray-500 w-8 text-right">
                    {v.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="font-medium text-gray-700 mb-1">
              Flexibility Margins
            </div>
            <div className="space-y-0.5 text-gray-600">
              {Object.entries(profile.flexibility_margins).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="capitalize">{k}</span>
                  <span className="text-gray-500">+{v * 100}%</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="font-medium text-gray-700 mb-1">Constraints</div>
            <ul className="space-y-0.5 text-gray-600">
              {profile.constraints.map((c, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-amber-400 mt-0.5 shrink-0">
                    &#9888;
                  </span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex justify-between text-gray-700 pt-1 border-t border-gray-100">
            <span className="font-medium">BATNA</span>
            <span className="font-mono">
              {profile.batna !== null ? profile.batna : "None"}
            </span>
          </div>
        </div>
        <div className="absolute left-1/2 -translate-x-1/2 top-full -mt-1 w-2.5 h-2.5 bg-white border-r border-b border-gray-200 z-10 rotate-45" />
      </div>
    </div>
  );
}
