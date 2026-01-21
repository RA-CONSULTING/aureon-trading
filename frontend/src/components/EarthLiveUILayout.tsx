import React, { useMemo, useState } from "react";
// import { motion, AnimatePresence } from "framer-motion";
import { SimulationEngine } from "./SimulationEngine";
import { VisualizationPanel } from "./VisualizationPanel";
import { SymbolicCompilerPanel } from "./SymbolicCompilerPanel";
import { AnalysisModePanel } from "./AnalysisModePanel";
import { UtilitiesPanel } from "./UtilitiesPanel";

/**
 * Earth-Live-Data App — Ready-made React + Tailwind menu layout
 * ---------------------------------------------------------------
 * - Single-file component you can drop into your project.
 * - Uses Tailwind classes only (no external UI kit required).
 * - Animations via Framer Motion (optional; safe to remove).
 *
 * Sections (top tabs): Simulation, Visualization, Compiler, Analysis, Utilities
 * Sidebar is contextual to each section; main panel shows the active tool.
 */

// Simple icon stubs (replace with lucide-react if desired)
const Dot = ({ className = "" }: { className?: string }) => (
  <span className={`inline-block size-2 rounded-full bg-emerald-500 ${className}`} />
);

const SectionTab = ({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border
      ${active ? "bg-emerald-600 text-white border-emerald-700 shadow" : "bg-white/60 backdrop-blur text-slate-700 hover:bg-white border-slate-200"}
    `}
  >
    {label}
  </button>
);

const SidebarButton = ({
  label,
  active,
  onClick,
  hint,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  hint?: string;
}) => (
  <button
    onClick={onClick}
    className={`group w-full text-left px-3 py-2 rounded-xl border transition-all mb-1
      ${active ? "bg-slate-900 text-white border-slate-900" : "bg-white hover:bg-slate-50 text-slate-800 border-slate-200"}
    `}
  >
    <div className="flex items-center gap-2">
      <Dot className={active ? "bg-white" : "bg-emerald-500/70 group-hover:bg-emerald-500"} />
      <span className="font-medium">{label}</span>
    </div>
    {hint && <div className={`text-xs mt-1 ${active ? "text-emerald-100/90" : "text-slate-500"}`}>{hint}</div>}
  </button>
);

// Reusable card
const Card: React.FC<React.PropsWithChildren<{ title?: string; toolbar?: React.ReactNode }>> = ({ title, toolbar, children }) => (
  <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
    {(title || toolbar) && (
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        <div className="flex items-center gap-2">{toolbar}</div>
      </div>
    )}
    <div className="p-4">{children}</div>
  </div>
);

// Toolbar controls
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

// Main component
export default function EarthLiveUILayout() {
  type Section = "Simulation" | "Visualization" | "Compiler" | "Analysis" | "Utilities";
  const [section, setSection] = useState<Section>("Simulation");
  const [activeTool, setActiveTool] = useState<string>("");

  // Per-section tools (sidebar)
  const toolsBySection: Record<Section, { key: string; label: string; hint?: string }[]> = useMemo(() => ({
    Simulation: [
      { key: "tensor", label: "Run Tensor Evolution", hint: "φ, κ, ψ, TSV over time" },
      { key: "compare", label: "Compare System States", hint: "early vs mid vs late" },
      { key: "stability", label: "Stability Monitor", hint: "MaxPsiAmplitude" },
      { key: "pattern", label: "Pattern Tracker", hint: "correlation vs time" },
    ],
    Visualization: [
      { key: "lev_early", label: "LEV: Early Snapshot (t050)" },
      { key: "lev_mid", label: "LEV: Mid Snapshot (t500)" },
      { key: "lev_late", label: "LEV: Late Snapshot (t950)" },
      { key: "overlay", label: "Overlay LEV Layers" },
      { key: "field3d", label: "3D Field Viewer (ψ/κ)" },
      { key: "plotly", label: "Plotly Chart Panel" },
    ],
    Compiler: [
      { key: "intent", label: "Broadcast Resonance", hint: "Text → frequencies + decay" },
      { key: "presets", label: "Preset Intents", hint: "Hope, Compassion, Healing, Courage" },
    ],
    Analysis: [
      { key: "phase", label: "Phase Dynamics Interpreter", hint: "guardian / anchor / phase" },
      { key: "memory", label: "Symbolic Memory Tracer", hint: "pattern correlation" },
      { key: "stability", label: "Stability Analyst", hint: "chaos vs bounded" },
      { key: "temporal", label: "Temporal Synthesizer", hint: "trend / evolve / compare" },
    ],
    Utilities: [
      { key: "export", label: "Export Data (CSV/JSON)" },
      { key: "saveviz", label: "Save Visualization" },
      { key: "settings", label: "System Settings" },
    ],
  }), []);

  // Set default tool when section changes
  React.useEffect(() => {
    const tools = toolsBySection[section];
    if (tools.length > 0 && !activeTool) {
      setActiveTool(tools[0].key);
    }
  }, [section, toolsBySection, activeTool]);

  const renderMainPanel = () => {
    switch (section) {
      case "Simulation":
        return <SimulationEngine tool={activeTool} />;
      case "Visualization":
        return <VisualizationPanel tool={activeTool} />;
      case "Compiler":
        return <SymbolicCompilerPanel tool={activeTool} />;
      case "Analysis":
        return <AnalysisModePanel tool={activeTool} />;
      case "Utilities":
        return <UtilitiesPanel tool={activeTool} />;
      default:
        return <Card><div className="p-8 text-center text-slate-500">Select a section</div></Card>;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-800">Earth Live Data</h1>
              <p className="text-sm text-slate-500">Harmonic Nexus Core • Real-time Field Analysis</p>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-slate-600">Live Stream Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="border-b border-slate-200 bg-white/60 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex gap-2 overflow-x-auto">
            {(["Simulation", "Visualization", "Compiler", "Analysis", "Utilities"] as Section[]).map((sec) => (
              <SectionTab
                key={sec}
                label={sec}
                active={section === sec}
                onClick={() => {
                  setSection(sec);
                  setActiveTool("");
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white/80 backdrop-blur rounded-2xl border border-slate-200 p-4">
              <h2 className="text-sm font-semibold text-slate-700 mb-3">{section} Tools</h2>
              <div className="space-y-1">
                {toolsBySection[section]?.map((tool) => (
                  <SidebarButton
                    key={tool.key}
                    label={tool.label}
                    hint={tool.hint}
                    active={activeTool === tool.key}
                    onClick={() => setActiveTool(tool.key)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Main Panel */}
          <div className="lg:col-span-3">
            <div key={`${section}-${activeTool}`}>
              {renderMainPanel()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}