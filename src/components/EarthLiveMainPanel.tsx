import React, { useState } from "react";
import { Card } from "./EarthLiveUILayout";

const Toggle = ({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label?: string }) => (
  <label className="inline-flex items-center gap-2 cursor-pointer">
    <span className="text-xs text-slate-500">{label}</span>
    <span className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${checked ? "bg-emerald-600" : "bg-slate-300"}`}
      onClick={() => onChange(!checked)}
      role="switch"
      aria-checked={checked}
    >
      <span className={`size-5 rounded-full bg-white transform transition ${checked ? "translate-x-5" : "translate-x-1"}`} />
    </span>
  </label>
);

export default function EarthLiveMainPanel({ section, activeTool }: { section: string; activeTool: string }) {
  const [running, setRunning] = useState(false);
  const [stability, setStability] = useState(78);
  const [intentText, setIntentText] = useState("");

  const renderContent = () => {
    switch (section) {
      case "Simulation":
        return (
          <div className="space-y-4">
            <Card title="Tensor Evolution Control" toolbar={<Toggle checked={running} onChange={setRunning} label="Running" />}>
              <div className="space-y-3">
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>φ: 0.847</div>
                  <div>κ: 1.234</div>
                  <div>ψ: 2.156</div>
                  <div>TSV: 0.923</div>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${stability}%` }} />
                </div>
              </div>
            </Card>
          </div>
        );
      case "Visualization":
        return (
          <Card title="LEV Memory Explorer">
            <div className="h-64 bg-slate-50 rounded-xl flex items-center justify-center">
              <p className="text-slate-500">3D Visualization Panel</p>
            </div>
          </Card>
        );
      case "Compiler":
        return (
          <Card title="Intent → Resonance Broadcaster">
            <div className="space-y-4">
              <textarea
                value={intentText}
                onChange={(e) => setIntentText(e.target.value)}
                placeholder="Send peace and joy..."
                className="w-full p-3 border rounded-xl"
                rows={3}
              />
              <div className="flex gap-2">
                <button className="px-4 py-2 bg-emerald-600 text-white rounded-xl">✨ Hope</button>
                <button className="px-4 py-2 bg-emerald-600 text-white rounded-xl">💗 Compassion</button>
              </div>
            </div>
          </Card>
        );
      default:
        return <Card title={`${section} Panel`}><p>Content for {activeTool}</p></Card>;
    }
  };

  return <div className="flex-1">{renderContent()}</div>;
}