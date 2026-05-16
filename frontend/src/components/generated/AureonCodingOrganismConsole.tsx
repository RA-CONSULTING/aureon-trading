import { useEffect, useState, type ChangeEvent } from "react";
import { BrainCircuit, CheckCircle2, Code2, FileText, MousePointer2, Send, ShieldCheck, TestTube2, Upload } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

type JsonMap = Record<string, any>;

const HUB_BASE = "http://127.0.0.1:13002";
const FULL_ORGANISM_COMMAND = ".\\AUREON_PRODUCTION_LIVE.cmd -WaitForRefresh -MarketStatusPort 8791";
const TERMINAL_PROMPT_COMMAND =
  "Invoke-RestMethod http://127.0.0.1:13002/api/coding/prompt -Method Post -ContentType \"application/json\" -Body $body";

async function fetchJson(url: string): Promise<JsonMap> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return {};
    return await response.json();
  } catch {
    return {};
  }
}

function fmt(value: unknown): string {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString() : String(value || "0");
}

function compactEvidence(stage: JsonMap): string {
  const evidence = stage.evidence || {};
  const parts: string[] = [];
  if (evidence.intent) parts.push(`intent ${evidence.intent}`);
  if (evidence.tool_used) parts.push(`tool ${evidence.tool_used}`);
  if (evidence.plan_status) parts.push(`plan ${evidence.plan_status}`);
  if (evidence.proposal_status) parts.push(`proposal ${evidence.proposal_status}`);
  if (typeof evidence.vm_tool_count !== "undefined") parts.push(`VM tools ${evidence.vm_tool_count}`);
  if (Array.isArray(evidence.commands)) parts.push(`${evidence.commands.length} command(s)`);
  if (Array.isArray(evidence.published_files)) parts.push(`${evidence.published_files.length} file(s) published`);
  if (evidence.validation?.confidence) parts.push(`confidence ${Math.round(Number(evidence.validation.confidence) * 100)}%`);
  return parts.join(" | ") || "evidence attached";
}

export function AureonCodingOrganismConsole() {
  const [status, setStatus] = useState<JsonMap>({});
  const [prompt, setPrompt] = useState("Connect Aureon coding systems, inspect the repo, propose the smallest safe patch, and run focused tests.");
  const [runTests, setRunTests] = useState(true);
  const [includeDesktop, setIncludeDesktop] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadedFileName, setLoadedFileName] = useState("");
  const [scopeAnswers, setScopeAnswers] = useState<Record<string, string>>({});

  const refresh = async () => {
    const publicState = await fetchJson("/aureon_coding_organism_bridge.json");
    if (Object.keys(publicState).length) {
      setStatus(publicState);
      return;
    }
    const hubState = await fetchJson(`${HUB_BASE}/api/coding/status`);
    setStatus(hubState.last_run || hubState);
  };

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 15000);
    return () => window.clearInterval(timer);
  }, []);

  const submitPrompt = async (extraBody: JsonMap = {}) => {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${HUB_BASE}/api/coding/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, run_tests: runTests, include_desktop: includeDesktop, ...extraBody }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "coding prompt failed");
      }
      setStatus(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const approveScope = async () => {
    await submitPrompt({
      scope_approved: true,
      scope_answers: scopeAnswers,
      base_job_id: status.client_job?.job_id || "",
    });
  };

  const sendFullCodingJob = async () => {
    await submitPrompt({
      scope_approved: true,
      scope_answers: {
        goal: prompt,
        deliverables: "Repo changes or reports, code proposal, focused tests, proof checklist, snagging result, and client handover.",
        target_system: "Aureon repository, coding organism bridge, generated console evidence, and target files named by the prompt.",
        constraints: "Preserve live trading, payment, filing, credential, and destructive OS boundaries. Do not expose secrets.",
        acceptance: "Goal route is clean, focused tests pass or are explicitly skipped, HNC/Auris proof is recorded, and blocking snags are zero.",
        ...scopeAnswers,
      },
      base_job_id: status.client_job?.job_id || "",
    });
  };

  const loadPromptFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setLoadedFileName(file.name);
    setPrompt(
      `Aureon must ingest ${file.name}, marry up what Codex can do with Aureon, write bridge work orders, test itself, and publish a completion report.\n\n` +
      `Source document uploaded through the coding organism UI:\n\n${text}`
    );
    event.target.value = "";
  };

  const summary = status.summary || {};
  const route = status.goal_route || {};
  const plan = route.plan || {};
  const safeCode = status.safe_code_status || {};
  const tests = status.tests || {};
  const desktop = status.desktop_run_flow || {};
  const desktopController = desktop.local_desktop_controller || {};
  const productAudit = status.finished_product_audit || {};
  const clientJob = status.client_job || {};
  const scopeOfWorks = clientJob.scope_of_works || {};
  const clientQuestions = Array.isArray(clientJob.client_questions) ? clientJob.client_questions : [];
  const agentTeam = Array.isArray(clientJob.agent_team) ? clientJob.agent_team : [];
  const phaseTimers = Array.isArray(clientJob.phase_timers) ? clientJob.phase_timers : [];
  const proofChecklist = Array.isArray(clientJob.proof_checklist) ? clientJob.proof_checklist : productAudit.proof_checklist || [];
  const snaggingList = Array.isArray(clientJob.snagging_list) ? clientJob.snagging_list : productAudit.snagging_list || [];
  const handoverStatus = clientJob.handover_status || productAudit.handover_status || {};
  const finalHandoverVisible = Boolean(handoverStatus.client_visible_product || productAudit.ready_to_run);
  const journal = status.work_journal || {};
  const journalStages = Array.isArray(journal.stages) ? journal.stages : [];
  const steps = Array.isArray(plan.steps) ? plan.steps : [];
  const systemActive = Boolean(route.ok || summary.goal_engine_routed || status.status);
  const hubActive = status.status !== "coding_organism_waiting_for_prompt" && !error;
  const fullCodingReady = Boolean(summary.goal_route_clean && summary.tests_ok && summary.ready_to_run && !summary.blocking_snag_count);

  return (
    <Card className="mb-5 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Code2 className="h-4 w-4 text-primary" />
          Aureon Coding Organism
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant={status.ok ? "success" : "warning"}>{status.status || "waiting for prompt"}</Badge>
          <Badge variant="outline">updated {status.generated_at ? new Date(status.generated_at).toLocaleTimeString() : "pending"}</Badge>
          <Badge variant={summary.goal_engine_routed ? "success" : "warning"}>goal route {summary.goal_engine_routed ? "live" : "pending"}</Badge>
          <Badge variant={summary.scope_locked ? "success" : "warning"}>scope {String(summary.scope_status || "waiting").replace(/_/g, " ")}</Badge>
          <Badge variant={summary.safe_code_proposal_created ? "success" : "outline"}>code queue {summary.safe_code_proposal_created ? "written" : "waiting"}</Badge>
          <Badge variant={summary.tests_ok ? "success" : summary.tests_requested ? "warning" : "outline"}>tests {summary.tests_requested ? (summary.tests_ok ? "passed" : "attention") : "off"}</Badge>
          <Badge variant={summary.ready_to_run ? "success" : "warning"}>product {String(summary.finished_product_status || "audit pending").replace(/_/g, " ")}</Badge>
          <Badge variant={summary.blocking_snag_count ? "warning" : "success"}>snags {summary.blocking_snag_count || 0}</Badge>
          <Badge variant={summary.desktop_handoff_created ? "success" : "outline"}>desktop handoff {summary.desktop_handoff_created ? "ready" : "off"}</Badge>
        </div>

        <div className="rounded-md border border-cyan-500/30 bg-cyan-500/10 p-3">
          <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
            <div>
              <div className="text-sm font-medium text-cyan-50">Human Coding Cockpit</div>
              <div className="mt-1 text-xs text-cyan-50/75">
                Start the full organism in PowerShell, then use this panel as the human prompt terminal while Aureon scopes, recruits, builds, tests, snags, and hands over.
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={systemActive ? "success" : "warning"}>system {systemActive ? "active" : "waiting"}</Badge>
              <Badge variant={hubActive ? "success" : "warning"}>hub {hubActive ? "reachable" : "checking"}</Badge>
              <Badge variant={fullCodingReady ? "success" : "warning"}>handover {fullCodingReady ? "ready" : "gated"}</Badge>
            </div>
          </div>
          <div className="grid gap-2 text-xs md:grid-cols-3">
            <div>
              <div className="uppercase text-cyan-100/70">Full organism terminal</div>
              <div className="mt-1 font-mono text-cyan-50">{FULL_ORGANISM_COMMAND}</div>
            </div>
            <div>
              <div className="uppercase text-cyan-100/70">Local coding endpoint</div>
              <div className="mt-1 font-mono text-cyan-50">{HUB_BASE}/api/coding/prompt</div>
            </div>
            <div>
              <div className="uppercase text-cyan-100/70">PowerShell prompt call</div>
              <div className="mt-1 font-mono text-cyan-50">{TERMINAL_PROMPT_COMMAND}</div>
            </div>
          </div>
        </div>

        <div className="grid gap-2 md:grid-cols-6">
          <Stat icon={BrainCircuit} label="plan steps" value={plan.step_count || summary.target_file_count || 0} />
          <Stat icon={ShieldCheck} label="pending proposals" value={safeCode.pending_count || summary.pending_code_proposal_count || 0} />
          <Stat icon={Code2} label="target files" value={summary.target_file_count || 0} />
          <Stat icon={TestTube2} label="test commands" value={tests.command_count || 0} />
          <Stat icon={MousePointer2} label="VM tools" value={summary.remote_vm_tool_count || 0} />
          <Stat icon={CheckCircle2} label="route ok" value={route.ok ? "yes" : "no"} />
        </div>

        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-amber-50">Scope Of Works</div>
              <div className="mt-1 text-xs text-amber-50/75">
                Aureon treats each prompt as a client job: scope first, team handoff second, HNC/Auris drift proof, then snagging before client handover.
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={clientJob.scope_locked ? "success" : "warning"}>
                {String(clientJob.scope_status || "waiting_for_prompt").replace(/_/g, " ")}
              </Badge>
              <Badge variant="outline">questions {clientQuestions.length}</Badge>
              <Badge variant={finalHandoverVisible ? "success" : "warning"}>
                handover {finalHandoverVisible ? "visible" : "held"}
              </Badge>
            </div>
          </div>

          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <Mini label="Goal" value={scopeOfWorks.goal || "waiting"} />
            <Mini label="Deliverables" value={scopeOfWorks.deliverables || "waiting"} />
            <Mini label="Target" value={scopeOfWorks.target_system || "waiting"} />
            <Mini label="Acceptance" value={scopeOfWorks.acceptance || "waiting"} />
          </div>

          {clientQuestions.length ? (
            <div className="mt-3 space-y-2">
              {clientQuestions.map((question: JsonMap) => (
                <div key={question.id} className="rounded-md border border-amber-400/30 bg-background/30 p-3">
                  <div className="text-xs font-medium text-amber-50">{question.question}</div>
                  <div className="mt-1 text-[11px] text-amber-50/70">{question.why_needed}</div>
                  <Textarea
                    value={scopeAnswers[question.id] || ""}
                    onChange={(event) =>
                      setScopeAnswers((current) => ({ ...current, [question.id]: event.target.value }))
                    }
                    className="mt-2 min-h-[64px] bg-background/60 text-xs"
                    placeholder="Client answer for this scope item"
                  />
                </div>
              ))}
              <Button size="sm" onClick={approveScope} disabled={busy}>
                <Send className="mr-2 h-4 w-4" />
                Approve Scope And Send To Team
              </Button>
            </div>
          ) : null}

          <div className="mt-3 grid gap-2 lg:grid-cols-3">
            <div className="rounded-md border border-border/30 bg-background/25 p-3">
              <div className="text-xs font-medium">Agent Team</div>
              <div className="mt-2 space-y-1">
                {agentTeam.slice(0, 6).map((agent: JsonMap) => (
                  <div key={`${agent.role}-${agent.phase}`} className="flex items-center justify-between gap-2 text-[11px]">
                    <span>{agent.role}</span>
                    <Badge variant={agent.status === "active" ? "success" : "outline"}>{String(agent.status || "waiting").replace(/_/g, " ")}</Badge>
                  </div>
                ))}
                {!agentTeam.length ? <div className="text-xs text-muted-foreground">Team appears after first client job intake.</div> : null}
              </div>
            </div>
            <div className="rounded-md border border-border/30 bg-background/25 p-3">
              <div className="text-xs font-medium">Phase Timers</div>
              <div className="mt-2 space-y-1">
                {phaseTimers.slice(0, 7).map((phase: JsonMap) => (
                  <div key={phase.phase} className="flex items-center justify-between gap-2 text-[11px]">
                    <span>{String(phase.phase || "").replace(/_/g, " ")}</span>
                    <Badge variant={phase.status === "completed" ? "success" : phase.status === "waiting_client" ? "warning" : "outline"}>
                      {String(phase.status || "pending").replace(/_/g, " ")}
                    </Badge>
                  </div>
                ))}
                {!phaseTimers.length ? <div className="text-xs text-muted-foreground">Timers start when a prompt enters the client lane.</div> : null}
              </div>
            </div>
            <div className="rounded-md border border-border/30 bg-background/25 p-3">
              <div className="text-xs font-medium">Handover Gate</div>
              <div className="mt-2 text-xs text-muted-foreground">
                {handoverStatus.reason || "Finished products stay hidden until proof and snagging are clear."}
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <Mini label="Proof" value={`${proofChecklist.filter((item: JsonMap) => item.ok).length}/${proofChecklist.length || 0}`} />
                <Mini label="Snags" value={snaggingList.filter((item: JsonMap) => item.severity === "blocking").length} />
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-md border border-primary/30 bg-primary/5 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <div>
                <div className="text-sm font-medium">Work Journal: Prompt To Finished Files</div>
                <div className="text-xs text-muted-foreground">
                  Aureon shows every stage it went through, with evidence and verification.
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={journal.status === "complete" ? "success" : "warning"}>
                {journal.status || "waiting"}
              </Badge>
              <Badge variant="outline">{journal.completed_count || 0}/{journal.stage_count || 0} stages</Badge>
              <Badge variant={journal.attention_count ? "warning" : "outline"}>
                attention {journal.attention_count || 0}
              </Badge>
            </div>
          </div>

          <ScrollArea className="mt-3 h-[300px] pr-3">
            <div className="space-y-2">
              {journalStages.map((stage: JsonMap, index: number) => (
                <div key={stage.id || stage.title || index} className="rounded-md border border-border/40 bg-background/50 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-primary/40 bg-primary/10 text-[11px] font-semibold">
                          {index + 1}
                        </span>
                        <div className="text-sm font-medium">{stage.title || stage.id}</div>
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground">{stage.summary || "No summary published."}</div>
                      <div className="mt-2 font-mono text-[11px] text-muted-foreground">{compactEvidence(stage)}</div>
                    </div>
                    <Badge variant={stage.ok ? "success" : "warning"}>{String(stage.status || "pending").replace(/_/g, " ")}</Badge>
                  </div>
                  {Array.isArray(stage.evidence?.published_files) && stage.evidence.published_files.length ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {stage.evidence.published_files.slice(0, 4).map((file: string) => (
                        <Badge key={file} variant="outline" className="max-w-full truncate font-mono text-[10px]">
                          {file}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                  {Array.isArray(stage.evidence?.commands) && stage.evidence.commands.length ? (
                    <div className="mt-2 space-y-1">
                      {stage.evidence.commands.slice(0, 2).map((command: JsonMap, commandIndex: number) => (
                        <div key={`${stage.id}-command-${commandIndex}`} className="rounded border border-border/30 bg-muted/20 px-2 py-1 font-mono text-[10px] text-muted-foreground">
                          {command.ok ? "PASS" : "ATTN"} {command.command}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
              {!journalStages.length ? (
                <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                  No work journal has been published yet. Send a prompt to Aureon to produce one.
                </div>
              ) : null}
            </div>
          </ScrollArea>
        </div>

        <div className="grid gap-3 lg:grid-cols-[1fr_0.8fr]">
          <div className="space-y-2">
            <Textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="min-h-[130px] font-mono text-xs"
            />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className="flex items-center gap-2 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={runTests}
                  onChange={(event) => setRunTests(event.target.checked)}
                  className="h-4 w-4"
                />
                Run focused coding tests
              </label>
              <label className="flex items-center gap-2 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={includeDesktop}
                  onChange={(event) => setIncludeDesktop(event.target.checked)}
                  className="h-4 w-4"
                />
                Prepare desktop/run handoff
              </label>
              <div className="flex gap-2">
                <label className="inline-flex cursor-pointer items-center rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-accent hover:text-accent-foreground">
                  <Upload className="mr-2 h-4 w-4" />
                  {loadedFileName ? loadedFileName : "Load MD"}
                  <input type="file" accept=".md,.txt" className="hidden" onChange={loadPromptFile} />
                </label>
                <Button size="sm" variant="outline" onClick={refresh} disabled={busy}>
                  Refresh
                </Button>
                <Button size="sm" variant="outline" onClick={sendFullCodingJob} disabled={busy || !prompt.trim()}>
                  Full Coding Job
                </Button>
                <Button size="sm" onClick={() => submitPrompt()} disabled={busy || !prompt.trim()}>
                  <Send className="mr-2 h-4 w-4" />
                  Send To Aureon
                </Button>
              </div>
            </div>
            {error ? <div className="rounded-md border border-red-500/30 bg-red-500/10 p-2 text-xs text-red-100">{error}</div> : null}
          </div>

          <div className="space-y-2 rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-sm font-medium">Who What Where When How Act</div>
            {["who", "what", "where", "when", "how", "act"].map((key) => (
              <div key={key} className="rounded-md border border-border/30 bg-background/20 px-3 py-2">
                <div className="text-[10px] uppercase text-muted-foreground">{key}</div>
                <div className="mt-1 truncate font-mono text-[11px]">{JSON.stringify(status[key] || {})}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <div className="space-y-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-medium text-emerald-50">Finished Product Audit</div>
              <Badge variant={finalHandoverVisible ? "success" : "warning"}>
                {finalHandoverVisible ? "ready for client" : "handover held"}
              </Badge>
            </div>
            {finalHandoverVisible ? (
              (productAudit.stages || []).slice(0, 8).map((stage: JsonMap) => (
                <div key={stage.stage} className="flex items-center justify-between rounded-md border border-emerald-400/20 bg-background/30 px-3 py-2 text-xs">
                  <span>{String(stage.stage || "").replace(/_/g, " ")}</span>
                  <span className={stage.ok ? "text-emerald-200" : "text-yellow-100"}>{stage.ok ? "pass" : "attention"}</span>
                </div>
              ))
            ) : (
              <div className="rounded-md border border-yellow-400/30 bg-yellow-500/10 p-3 text-xs text-yellow-50">
                Final handover is hidden until scope, route, proof, and snagging gates pass.
              </div>
            )}
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="space-y-1">
                <div className="text-[11px] uppercase text-emerald-50/70">Proof checklist</div>
                {proofChecklist.slice(0, 6).map((item: JsonMap) => (
                  <div key={item.id} className="flex items-center justify-between rounded border border-emerald-400/20 bg-background/20 px-2 py-1 text-[11px]">
                    <span>{item.label}</span>
                    <span className={item.ok ? "text-emerald-200" : "text-yellow-100"}>{item.ok ? "pass" : "hold"}</span>
                  </div>
                ))}
              </div>
              <div className="space-y-1">
                <div className="text-[11px] uppercase text-emerald-50/70">Snagging list</div>
                {snaggingList.slice(0, 6).map((snag: JsonMap) => (
                  <div key={snag.id} className="rounded border border-emerald-400/20 bg-background/20 px-2 py-1 text-[11px]">
                    <div className="flex items-center justify-between gap-2">
                      <span>{snag.title}</span>
                      <span className={snag.severity === "blocking" ? "text-yellow-100" : "text-emerald-200"}>{snag.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-2 rounded-md border border-blue-500/30 bg-blue-500/10 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-medium text-blue-50">Desktop And Remote Run Handoff</div>
              <Badge variant={desktopController.emergency_stopped ? "destructive" : "outline"}>
                {desktopController.dry_run === false ? "live" : "dry run"}
              </Badge>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <Mini label="Armed" value={desktopController.armed ? "yes" : "no"} />
              <Mini label="Pending" value={(desktopController.pending_actions || []).length} />
              <Mini label="VM tools" value={desktop.remote_vm_control?.tool_count || 0} />
            </div>
            <div className="text-xs text-blue-50/75">
              {desktop.safety?.desktop_default || "Desktop control is dry-run unless the operator arms it."}
            </div>
          </div>
        </div>

        <ScrollArea className="h-[220px] pr-3">
          <div className="space-y-2">
            {steps.map((step: JsonMap) => (
              <div key={step.step_id || step.title} className="rounded-md border border-border/40 bg-muted/10 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-medium">{step.title || step.intent}</div>
                    <div className="mt-1 font-mono text-[11px] text-muted-foreground">{step.intent}</div>
                  </div>
                  <Badge variant={step.status === "completed" ? "success" : "outline"}>{step.status || "pending"}</Badge>
                </div>
              </div>
            ))}
            {!steps.length ? (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                No coding route has been published yet.
              </div>
            ) : null}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function Stat({ icon: Icon, label, value }: { icon: any; label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
      <div className="flex items-center gap-2 text-[11px] uppercase text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold">{typeof value === "number" ? fmt(value) : String(value || "0")}</div>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-border/30 bg-background/20 px-3 py-2 text-xs">
      <div className="text-[10px] uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 font-semibold">{typeof value === "number" ? fmt(value) : String(value || "0")}</div>
    </div>
  );
}
