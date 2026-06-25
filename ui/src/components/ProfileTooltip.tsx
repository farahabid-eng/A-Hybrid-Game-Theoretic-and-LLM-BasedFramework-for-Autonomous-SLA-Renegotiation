import { useRef, useState, useCallback } from "react";

export interface StakeholderProfile {
  role: "client" | "provider";
  objectives: string[];
  priorities: Record<string, number>;
  flexibility_margins: Record<string, number>;
  batna: number | null;
  context_description: string;
  tone: string;
}

interface Props {
  profile: StakeholderProfile;
  children: React.ReactNode;
}

const TOOLTIP_WIDTH = 320;
const GAP = 10;

export default function ProfileTooltip({ profile, children }: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [side, setSide] = useState<"left" | "right">("left");
  const [visible, setVisible] = useState(false);

  const handleEnter = useCallback(() => {
    const w = wrapperRef.current;
    if (!w) return;
    const wr = w.getBoundingClientRect();
    const isClient = profile.role === "client";
    const spaceLeft = wr.left;
    const spaceRight = window.innerWidth - wr.right;

    if (
      isClient
        ? spaceLeft >= TOOLTIP_WIDTH + GAP
        : spaceRight >= TOOLTIP_WIDTH + GAP
    ) {
      setSide(isClient ? "left" : "right");
    } else if (
      isClient
        ? spaceRight >= TOOLTIP_WIDTH + GAP
        : spaceLeft >= TOOLTIP_WIDTH + GAP
    ) {
      setSide(isClient ? "right" : "left");
    } else {
      setSide(isClient ? "left" : "right");
    }
    setVisible(true);
  }, [profile.role]);

  const handleLeave = useCallback(() => setVisible(false), []);

  const isClient = profile.role === "client";

  return (
    <div
      ref={wrapperRef}
      className="group relative inline-block"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      {children}
      <div
        className={`absolute z-50 transition-all duration-150 ${
          visible ? "opacity-100 visible" : "opacity-0 invisible"
        }`}
        style={{
          width: TOOLTIP_WIDTH,
          maxHeight: "min(24rem, 60vh)",
          top: "50%",
          transform: "translateY(-50%)",
          ...(side === "left"
            ? { right: "calc(100% + 10px)" }
            : { left: "calc(100% + 10px)" }),
        }}
      >
        <div className="bg-white border border-gray-200 rounded-xl shadow-xl text-xs">
          <div className="overflow-y-auto max-h-[60vh] p-4 space-y-3">
            <h3 className="font-semibold text-sm capitalize flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  isClient ? "bg-blue-500" : "bg-emerald-500"
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
                    <span className="text-blue-400 mt-0.5 shrink-0">
                      &#8226;
                    </span>
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
                          isClient ? "bg-blue-400" : "bg-emerald-400"
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

            <div className="flex justify-between text-gray-700 pt-1 border-t border-gray-100">
              <span className="font-medium">BATNA</span>
              <span className="font-mono">
                {profile.batna !== null ? profile.batna : "None"}
              </span>
            </div>
          </div>
        </div>

        <div
          className="absolute w-2.5 h-2.5 bg-white border-gray-200 -z-10 rotate-45"
          style={{
            top: "calc(50% - 30px)",
            ...(side === "left"
              ? {
                  right: "-5px",
                  borderRight: "1px solid #e5e7eb",
                  borderTop: "1px solid #e5e7eb",
                  borderLeft: "none",
                  borderBottom: "none",
                }
              : {
                  left: "-5px",
                  borderLeft: "1px solid #e5e7eb",
                  borderBottom: "1px solid #e5e7eb",
                  borderRight: "none",
                  borderTop: "none",
                }),
          }}
        />
      </div>
    </div>
  );
}
