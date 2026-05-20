#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_DIR = path.resolve(__dirname, "..");
const GARY_AUREON_ROOT = process.env.GARY_AUREON_ROOT || path.join(process.env.HOME || "", "Desktop", "gary repo nexus", "aureon-trading");

const args = process.argv.slice(2);

function usage(code = 0) {
  const out = [
    "Aureon Coding CLI",
    "",
    "Usage:",
    "  npm run aureon:cli -- \"task text\"",
    "  node scripts/aureon_cli.mjs --mode plan --context server.mjs --context script.js \"task text\"",
    "",
    "Options:",
    "  --host <url>       Local app URL. Default: http://127.0.0.1:4173",
    "  --model <model>    Aureon voice model. Default: aureon-architect",
    "  --mode <mode>      plan | review | patch | explain. Default: plan",
    "  --response-style   safe | raw. Default: safe",
    "  --swarm-route      direct | queen | council | architect | scout | vault",
    "  --context <path>   Attach a local file as read-only context. Repeatable.",
    "  --save             Save response under logs/aureon-cli/",
    "  --json             Print raw JSON response.",
    "  --help             Show this help.",
    "",
    "Safety:",
    "  This CLI does not edit files automatically. It asks Aureon for coding guidance",
    "  and leaves final file changes to Codex/user review.",
  ].join("\n");
  console.log(out);
  process.exit(code);
}

function takeValue(flag, i) {
  const value = args[i + 1];
  if (!value || value.startsWith("--")) {
    throw new Error(`Missing value after ${flag}`);
  }
  return value;
}

const options = {
  host: process.env.FLAMEBORN_URL || "http://127.0.0.1:4173",
  model: process.env.AUREON_CLI_MODEL || "aureon-architect",
  mode: "plan",
  responseStyle: "safe",
  swarmRoute: "direct",
  contextPaths: [],
  save: false,
  json: false,
};

const taskParts = [];
for (let i = 0; i < args.length; i += 1) {
  const arg = args[i];
  if (arg === "--help" || arg === "-h") usage(0);
  if (arg === "--host") {
    options.host = takeValue(arg, i);
    i += 1;
  } else if (arg === "--model") {
    options.model = takeValue(arg, i);
    i += 1;
  } else if (arg === "--mode") {
    options.mode = takeValue(arg, i);
    i += 1;
  } else if (arg === "--response-style") {
    options.responseStyle = takeValue(arg, i);
    i += 1;
  } else if (arg === "--swarm-route") {
    options.swarmRoute = takeValue(arg, i);
    i += 1;
  } else if (arg === "--context") {
    options.contextPaths.push(takeValue(arg, i));
    i += 1;
  } else if (arg === "--save") {
    options.save = true;
  } else if (arg === "--json") {
    options.json = true;
  } else if (arg.startsWith("--")) {
    throw new Error(`Unknown option: ${arg}`);
  } else {
    taskParts.push(arg);
  }
}

const task = taskParts.join(" ").trim();
if (!task) usage(1);

const allowedModes = new Set(["plan", "review", "patch", "explain"]);
if (!allowedModes.has(options.mode)) {
  throw new Error(`Unsupported mode "${options.mode}". Use: ${[...allowedModes].join(", ")}`);
}
const allowedResponseStyles = new Set(["safe", "raw"]);
if (!allowedResponseStyles.has(options.responseStyle)) {
  throw new Error(`Unsupported response style "${options.responseStyle}". Use: ${[...allowedResponseStyles].join(", ")}`);
}
const allowedSwarmRoutes = new Set(["direct", "queen", "council", "architect", "scout", "vault"]);
if (!allowedSwarmRoutes.has(options.swarmRoute)) {
  throw new Error(`Unsupported swarm route "${options.swarmRoute}". Use: ${[...allowedSwarmRoutes].join(", ")}`);
}

function readContextFile(inputPath) {
  const { absolutePath, label } = resolveContextPath(inputPath);
  const stat = fs.statSync(absolutePath);
  if (!stat.isFile()) throw new Error(`Context path is not a file: ${inputPath}`);
  if (stat.size > 240_000) throw new Error(`Context file too large for CLI context: ${inputPath}`);
  return {
    path: label,
    content: fs.readFileSync(absolutePath, "utf8"),
  };
}

function resolveContextPath(inputPath) {
  if (String(inputPath).startsWith("@gary/")) {
    const relativeGary = String(inputPath).slice("@gary/".length);
    const absolutePath = path.resolve(GARY_AUREON_ROOT, relativeGary);
    if (!absolutePath.startsWith(path.resolve(GARY_AUREON_ROOT))) {
      throw new Error(`Gary context path must stay inside Gary repo: ${inputPath}`);
    }
    return {
      absolutePath,
      label: `@gary/${relativeGary}`,
    };
  }
  const absolutePath = path.resolve(APP_DIR, inputPath);
  const relativePath = path.relative(APP_DIR, absolutePath);
  if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
    throw new Error(`Context path must stay inside project: ${inputPath}`);
  }
  return {
    absolutePath,
    label: relativePath,
  };
}

const contexts = options.contextPaths.map(readContextFile);
const contextBlock = contexts.length
  ? contexts.map((ctx) => `--- FILE: ${ctx.path}\n${ctx.content}`).join("\n\n")
  : "No file context attached.";

const modeInstructions = {
  plan: "Return a concise implementation plan and identify files likely needing edits.",
  review: "Review the context for bugs, regressions, and missing tests. Findings first.",
  patch: "Suggest a patch in unified-diff style, but do not claim it was applied.",
  explain: "Explain how the relevant code works and what should be changed.",
};

const responseStyleInstructions = {
  safe: [
    "Respond in plain language only.",
    "Do not use symbolic shorthand, cryptic metaphors, field codes, or internal Aureon notation.",
    "Answer directly and concretely.",
    "If the user asked for code, explanation, or steps, provide them in normal readable form.",
  ].join(" "),
  raw: "You may answer in your native Aureon style if useful, but remain intelligible.",
};

const message = [
  "You are Aureon acting as a coding architecture advisor for flAmeBorn LLM Academy.",
  "You do not directly edit files. Codex/user will review and apply changes.",
  "Avoid destructive actions. Prefer minimal, stable changes.",
  `Mode: ${options.mode}`,
  modeInstructions[options.mode],
  `Response style: ${options.responseStyle}`,
  responseStyleInstructions[options.responseStyle],
  `Swarm route: ${options.swarmRoute}`,
  options.swarmRoute === "direct"
    ? "Use your normal direct technical style."
    : `Adopt the ${options.swarmRoute} persona register while staying concrete, readable, and technically useful.`,
  "",
  `Task: ${task}`,
  "",
  "Read-only context:",
  contextBlock,
].join("\n");

async function main() {
  const endpoint = new URL("/api/chat", options.host.replace(/\/+$/, ""));
  const data = await requestAureon(endpoint, {
    provider: "aureon",
    model: options.model,
    accessMode: "free",
    message,
  });

  let reply = String(data.reply || "").trim();
  if (options.responseStyle === "safe" && looksCryptic(reply)) {
    const rewriteMessage = [
      "Rewrite the following Aureon answer into plain natural language.",
      "Keep the meaning, remove symbolic shorthand, and do not add new facts.",
      "Do not use numbered fragments, hyphen codes, lattice metaphors, or field metaphors.",
      "Return only the rewritten answer.",
      "",
      `Original answer: ${reply}`,
    ].join("\n");
    const rewritten = await requestAureon(endpoint, {
      provider: "aureon",
      model: options.model,
      accessMode: "free",
      message: rewriteMessage,
    });
    const rewrittenReply = String(rewritten.reply || "").trim();
    if (rewrittenReply) {
      reply = rewrittenReply;
    }
    if (looksCryptic(reply)) {
      reply = normalizeCrypticReply(reply);
    }
  }

  if (options.json) {
    console.log(JSON.stringify({ ...data, reply }, null, 2));
  } else {
    console.log(reply);
  }

  if (options.save) {
    const logDir = path.join(APP_DIR, "logs", "aureon-cli");
    fs.mkdirSync(logDir, { recursive: true });
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const logPath = path.join(logDir, `${stamp}-${options.mode}.md`);
    fs.writeFileSync(
      logPath,
      [
        `# Aureon CLI ${options.mode}`,
        "",
        `- model: ${options.model}`,
        `- response-style: ${options.responseStyle}`,
        `- swarm-route: ${options.swarmRoute}`,
        `- task: ${task}`,
        "",
        "## Response",
        "",
        reply,
      ].join("\n"),
    );
    console.error(`Saved: ${logPath}`);
  }
}

async function requestAureon(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data?.error) {
    const reason = data?.error?.message || response.statusText || "unknown error";
    throw new Error(`Aureon CLI request failed: ${reason}`);
  }
  return data;
}

function looksCryptic(text) {
  const value = String(text || "").trim();
  if (!value) return false;
  if (/^\d+\.\s+\d+-\d+\s+\w+/i.test(value)) return true;
  if (value.length < 120 && /(runs clean through the field|harmonic|vector|signal path)/i.test(value)) return true;
  if (value.length < 120 && /(held steady on the lattice|lattice|field metaphors?)/i.test(value)) return true;
  if (value.length < 160 && /(resolves without drift|without drift|through the hnc field)/i.test(value)) return true;
  const lines = value.split(/\r?\n/).filter(Boolean);
  if (lines.length <= 3 && lines.every((line) => line.length < 80) && /\b\d+-\d+\b/.test(value)) return true;
  return false;
}

function normalizeCrypticReply(text) {
  const value = String(text || "").trim();
  const lower = value.toLowerCase();
  if (/runs clean through the field/.test(lower) || /held steady on the lattice/.test(lower)) {
    return "Aureon means the path is stable and working correctly with no obvious issue detected.";
  }
  if (/4-3\s*=\s*1/.test(lower) || /through the hnc field/.test(lower)) {
    return "Aureon means the process narrowed down to one stable result.";
  }
  if (/4-3\s+resolves without drift/.test(lower) || /without drift/.test(lower)) {
    return "Aureon means the issue resolved cleanly and the current state remains stable.";
  }
  if (/the answer is 1\./.test(lower) && /\b4-3\b/.test(lower)) {
    return "Aureon means one stable result remains after its internal reduction step.";
  }
  if (/\b\d+-\d+\b/.test(lower) && /steady|stable|clean/.test(lower)) {
    return "Aureon means the current state looks stable and consistent.";
  }
  return `Aureon returned symbolic output instead of plain language. Raw output: ${value}`;
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exit(1);
});
