import { useEffect, useMemo, useState } from "react";
import { Activity, Archive, CheckCircle2, Lock, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

type JsonMap = Record<string, any>;

async function fetchJson(url: string): Promise<JsonMap> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return {};
    return await response.json();
  } catch {
    return {};
  }
}

function compact(value: unknown): string {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString() : String(value || "0");
}

function tone(status: string): string {
  if (status.includes("blocker")) return "border-yellow-500/40 bg-yellow-500/10 text-yellow-100";
  if (status.includes("archive")) return "border-slate-500/40 bg-slate-500/10 text-slate-100";
  if (status.includes("adapter") || status.includes("link")) return "border-green-500/40 bg-green-500/10 text-green-100";
  return "border-border bg-muted/20 text-muted-foreground";
}

function iconFor(status: string) {
  if (status.includes("blocker")) return ShieldAlert;
  if (status.includes("archive")) return Archive;
  if (status.includes("adapter") || status.includes("link")) return CheckCircle2;
  return Activity;
}

export function AureonWorkOrderExecutionConsole() {
  const [report, setReport] = useState<JsonMap>({});

  useEffect(() => {
    let cancelled = false;
    fetchJson("/aureon_frontend_work_order_execution.json").then((payload) => {
      if (!cancelled) setReport(payload);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const executions = Array.isArray(report.executions) ? report.executions : [];
  const summary = report.summary || {};
  const top = useMemo(() => executions.slice(0, 80), [executions]);

  return (
    <Card className="mb-5 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-primary" />
          Aureon Work Order Execution
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="border-green-500/40 bg-green-500/10 text-green-100">{report.status || "pending"}</Badge>
          <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">updated {report.generated_at ? new Date(report.generated_at).toLocaleTimeString() : "pending"}</Badge>
        </div>
        <div className="grid gap-2 md:grid-cols-5">
          <Stat label="orders executed" value={summary.executed_count} />
          <Stat label="adapters" value={summary.adapter_record_count} />
          <Stat label="blocker cards" value={summary.blocker_card_count} />
          <Stat label="archive decisions" value={summary.archive_decision_count} />
          <Stat label="screens" value={summary.target_screen_count} />
        </div>
        <ScrollArea className="h-[420px] pr-3">
          <div className="space-y-2">
            {top.length ? top.map((item: JsonMap) => {
              const Icon = iconFor(String(item.execution_status || ""));
              return (
                <div key={item.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <Icon className="h-4 w-4 text-primary" />
                        {item.title}
                      </div>
                      <div className="mt-1 truncate font-mono text-[11px] text-muted-foreground">{item.source_path}</div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <Badge variant="outline" className={tone(String(item.execution_status || ""))}>{item.execution_status}</Badge>
                      <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">{item.target_screen}</Badge>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">{item.next_action}</div>
                  <div className="mt-2 text-[11px] text-yellow-100">{item.safety_boundary}</div>
                </div>
              );
            }) : (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">No work-order execution manifest loaded.</div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
      <div className="text-[11px] uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">{compact(value)}</div>
    </div>
  );
}
