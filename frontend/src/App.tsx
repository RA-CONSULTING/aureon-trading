import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Card } from "@/components/ui/card";
import { LiveTerminalStats } from "@/components/LiveTerminalStats";
import { useTerminalSync } from "@/hooks/useTerminalSync";
import { useGlobalState } from "@/hooks/useGlobalState";
import { CinematicObservatory } from "@/components/cinema/CinematicObservatory";

const queryClient = new QueryClient();

function StatusBlock() {
  const state = useGlobalState();
  const statusLines = Array.isArray(state.statusLines) ? state.statusLines : [];
  const latestMonitorLine = String(state.latestMonitorLine || "").trim();

  return (
    <Card className="border-border/50 bg-background/95 p-4">
      <div className="mb-3 flex items-center justify-between gap-3 border-b border-border/40 pb-3">
        <div>
          <div className="text-sm font-semibold text-foreground">Terminal Mirror</div>
          <div className="text-xs text-muted-foreground">
            Live runtime output from Kraken and Capital only
          </div>
        </div>
        <div className="font-mono text-[11px] text-muted-foreground">
          {state.wsConnected ? `Feed live (${state.wsMessageCount})` : "Polling local terminal"}
        </div>
      </div>

      <div className="space-y-3">
        {latestMonitorLine ? (
          <div className="rounded border border-border/40 bg-muted/20 p-3 font-mono text-[11px] text-foreground">
            {latestMonitorLine}
          </div>
        ) : null}

        <div className="rounded border border-border/40 bg-black/40 p-3">
          {statusLines.length > 0 ? (
            <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[11px] leading-5 text-foreground">
              {statusLines.join("\n")}
            </pre>
          ) : (
            <div className="font-mono text-[11px] text-muted-foreground">
              Waiting for terminal status...
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

function TerminalMirrorApp() {
  useTerminalSync(true, 2000);

  return (
    <div className="min-h-screen bg-background">
      <main className="mx-auto max-w-6xl p-4 md:p-6">
        <div className="mb-5 flex items-center justify-between gap-3 border-b border-border/50 pb-4">
          <div>
            <h1 className="text-xl font-semibold text-foreground">Aureon Terminal Mirror</h1>
            <p className="text-sm text-muted-foreground">
              Single-screen monitor for the live unified trader
            </p>
          </div>
          <div className="font-mono text-[11px] text-muted-foreground">
            `unified_market_trader.py`
          </div>
        </div>

        <div className="space-y-4">
          <LiveTerminalStats />
          <StatusBlock />
        </div>
      </main>
    </div>
  );
}

const App = () => {
  const [view, setView] = useState<'terminal' | 'observatory'>('terminal');

  return (
    <ThemeProvider defaultTheme="dark">
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          {view === 'observatory' ? (
            <CinematicObservatory onExit={() => setView('terminal')} />
          ) : (
            <>
              <TerminalMirrorApp />
              <div className="fixed bottom-4 right-4 z-50">
                <button
                  onClick={() => setView('observatory')}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600/80 to-purple-600/80 backdrop-blur-xl border border-white/10 text-white/90 text-sm font-medium shadow-[0_4px_20px_rgba(99,102,241,0.3)] hover:shadow-[0_4px_30px_rgba(99,102,241,0.5)] hover:scale-105 transition-all cursor-pointer"
                >
                  Enter Observatory
                </button>
              </div>
            </>
          )}
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
