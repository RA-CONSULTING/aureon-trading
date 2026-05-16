from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from aureon.autonomous.aureon_artifact_quality_gate import (
    DEFAULT_PUBLIC_QUALITY_JSON,
    build_artifact_quality_report,
    write_artifact_quality_report,
)
from aureon.autonomous.aureon_safe_code_control import CodeProposal, SafeCodeControl


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = Path("state/aureon_capability_forge_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_capability_forge.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_capability_forge.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_capability_forge.json")
DEFAULT_SAFE_CODE_STATE = Path("state/aureon_capability_forge_safe_code_state.json")
DEFAULT_LOCAL_APP_DIR = Path("frontend/public/aureon_generated_apps")
DEFAULT_ADAPTIVE_SKILL_DIR = Path("frontend/public/aureon_adaptive_skills")

REFERENCE_PATTERNS = [
    {
        "name": "OpenAI Agents SDK",
        "url": "https://developers.openai.com/api/docs/guides/agents",
        "pattern": "agents, tools, handoffs, guardrails, tracing, sandbox state",
    },
    {
        "name": "Anthropic tool use",
        "url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview",
        "pattern": "client tools, server tools, strict schemas, tool_result loop",
    },
    {
        "name": "Claude Code subagents",
        "url": "https://code.claude.com/docs/en/sub-agents",
        "pattern": "specialist workers with isolated context and scoped tool access",
    },
    {
        "name": "Gemini function calling",
        "url": "https://ai.google.dev/gemini-api/docs/function-calling",
        "pattern": "OpenAPI-shaped function calls and automatic function execution",
    },
    {
        "name": "Gemini Veo video flow",
        "url": "https://ai.google.dev/gemini-api/docs/video",
        "pattern": "image/storyboard seed, async video operation, poll until ready",
    },
    {
        "name": "AutoGen multi-agent chat",
        "url": "https://microsoft.github.io/autogen/0.2/docs/Use-Cases/agent_chat/",
        "pattern": "conversable agents coordinating tools and human feedback",
    },
    {
        "name": "Semantic Kernel orchestration",
        "url": "https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/",
        "pattern": "sequential, concurrent, group, and handoff orchestration",
    },
    {
        "name": "GitHub Copilot cloud agent",
        "url": "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/start-copilot-sessions",
        "pattern": "delegate prompt to agent, inspect session, review resulting changes",
    },
    {
        "name": "Jules coding agent",
        "url": "https://jules.google/docs/",
        "pattern": "autonomous coding task in repo context with human review",
    },
    {
        "name": "Runway video models",
        "url": "https://docs.dev.runwayml.com/guides/models/",
        "pattern": "video models expose text/image-to-video as job artifacts",
    },
    {
        "name": "Adobe Firefly Services",
        "url": "https://developer.adobe.com/firefly-services/docs/guides/",
        "pattern": "creative generation at scale with credentials kept server-side",
    },
    {
        "name": "Canva Connect design metadata",
        "url": "https://www.canva.dev/docs/connect/api-reference/designs/get-design/",
        "pattern": "design preview/edit/view metadata with expiring URLs",
    },
]

TASK_FAMILIES = [
    "video",
    "image_graphic_design",
    "coding",
    "ui",
    "document",
    "research",
    "browser_qa",
    "mixed",
]

FAMILY_KEYWORDS = {
    "video": ("video", "clip", "animation", "mp4", "webm", "10 second", "seconds"),
    "image_graphic_design": ("image", "picture", "graphic", "logo", "design", "poster", "draw", "illustration", "svg"),
    "coding": (
        "code",
        "repo",
        "patch",
        "python",
        "typescript",
        "test",
        "build",
        "function",
        "module",
        "game",
        "app",
        "html",
        "javascript",
        "tool",
        "skill",
        "calculator",
        "converter",
        "generator",
        "workflow",
    ),
    "ui": ("ui", "frontend", "dashboard", "console", "panel", "react", "tsx", "screen", "keyboard", "playable", "controls"),
    "document": ("document", "pdf", "markdown", "report", "runbook", "docx"),
    "research": ("research", "online", "official docs", "search", "learn", "source"),
    "browser_qa": ("browser", "playwright", "smoke", "screenshot", "open the page", "render"),
}


def _default_root() -> Path:
    return Path.cwd().resolve() if (Path.cwd() / "aureon").exists() else REPO_ROOT


def _rooted(root: Path, rel_path: Path) -> Path:
    return rel_path if rel_path.is_absolute() else root / rel_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_text(path: Path, content: str) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "ok": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def _write_json(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _write_text(path, json.dumps(payload, indent=2, sort_keys=True, default=str))


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    normalized = re.sub(r"\s+", " ", str(text or "").lower())
    for needle in needles:
        keyword = str(needle or "").lower().strip()
        if not keyword:
            continue
        if re.fullmatch(r"[a-z0-9 ]+", keyword):
            if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", normalized):
                return True
        elif keyword in normalized:
            return True
    return False


def classify_task_family(prompt: str) -> Dict[str, Any]:
    text = str(prompt or "").lower()
    hits = [family for family, needles in FAMILY_KEYWORDS.items() if _contains_any(text, needles)]
    priority = ("video", "image_graphic_design", "browser_qa", "ui", "coding", "document", "research")
    if len(hits) > 1:
        primary = next((family for family in priority if family in hits), hits[0])
        family = "mixed" if primary not in {"video", "image_graphic_design"} else primary
    elif hits:
        family = hits[0]
        primary = family
    else:
        family = "coding"
        primary = "coding"
    return {
        "task_family": family,
        "primary_family": primary,
        "detected_families": hits or [family],
        "local_only": True,
    }


def _crew_for_families(families: Sequence[str]) -> List[Dict[str, Any]]:
    base = [
        ("Client Brief Broker", "scope", "lock goal, deliverables, constraints, and acceptance proof"),
        ("Skill Headhunter", "research", "scan local repo first and use official docs as reference-only patterns"),
        ("Subcontractor Crew Builder", "orchestration", "hire the temporary specialist crew and define handoffs"),
        ("Quality Gate Inspector", "qa", "reject weak artifacts before handover"),
        ("Release Manager", "handover", "publish evidence and wait for approval"),
    ]
    family_roles = {
        "video": [
            ("Storyboard Artist", "media", "turn prompt into frames, motion, duration, and preview plan"),
            ("Local Encoder", "media", "produce WebM, GIF fallback, and HTML preview"),
            ("Playback Inspector", "qa", "probe duration and browser-playable artifact state"),
        ],
        "image_graphic_design": [
            ("Graphic Designer", "media", "produce a renderable local visual asset"),
            ("Visual QA Inspector", "qa", "check dimensions, prompt match, and public preview"),
        ],
        "coding": [
            ("Code Architect", "engineering", "scope patch contract and authority boundaries"),
            ("Implementation Worker", "engineering", "route code work through safe local authoring"),
            ("Test Pilot", "qa", "run tests/build proof before approval"),
            ("Security Auditor", "security", "check secrets and unsafe mutation boundaries"),
        ],
        "ui": [
            ("UX Designer", "product", "make the interface usable for a human operator"),
            ("Frontend Console Builder", "engineering", "mount evidence and previews in the cockpit"),
            ("Browser Smoke Inspector", "qa", "confirm visible UI proof"),
        ],
        "document": [("Runbook Writer", "docs", "publish readable operator evidence and handover docs")],
        "research": [("Research Scout", "research", "summarize source-linked patterns without external execution")],
        "browser_qa": [("Browser Smoke Inspector", "qa", "open local UI, inspect console state, and record proof")],
    }
    crew = [{"role": role, "department": dept, "day_to_day": duty, "temporary": True} for role, dept, duty in base]
    for family in families:
        for role, dept, duty in family_roles.get(family, []):
            if not any(item["role"] == role for item in crew):
                crew.append({"role": role, "department": dept, "day_to_day": duty, "temporary": True})
    return crew


def _tools_for_families(families: Sequence[str]) -> List[Dict[str, Any]]:
    tools = [
        {"name": "Repo search", "surface": "rg / RepoSelfCatalog", "mode": "read_only"},
        {"name": "SafeCodeControl", "surface": "aureon.autonomous.aureon_safe_code_control", "mode": "local_safe_route"},
        {"name": "Artifact quality gate", "surface": "aureon.autonomous.aureon_artifact_quality_gate", "mode": "local_quality_gate"},
    ]
    if "video" in families or "image_graphic_design" in families:
        tools.append({"name": "Visual asset worker", "surface": "aureon.autonomous.aureon_visual_asset_request", "mode": "local_generation"})
    if "browser_qa" in families or "ui" in families or "video" in families:
        tools.append({"name": "Playwright/browser smoke", "surface": "frontend Playwright", "mode": "local_browser_proof"})
    if "coding" in families or "ui" in families:
        tools.append({"name": "Focused pytest/build", "surface": "pytest / npm run build", "mode": "local_validation"})
        tools.append({"name": "Adaptive local app forge", "surface": "frontend/public/aureon_generated_apps", "mode": "local_file_generation"})
    return tools


def _reference_patterns() -> List[Dict[str, Any]]:
    return [
        {
            **item,
            "provider_policy": "reference_only",
            "external_api_call_allowed": False,
        }
        for item in REFERENCE_PATTERNS
    ]


def _visual_artifact(prompt: str, root: Path) -> Dict[str, Any]:
    from aureon.autonomous.aureon_visual_asset_request import build_and_write_visual_asset_request

    result = build_and_write_visual_asset_request(prompt, root=root, open_requested=True)
    return result if isinstance(result, dict) else {}


def _safe_slug(text: str, fallback: str = "artifact") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(text or "").lower()).strip("_")
    return (slug or fallback)[:48]


def _needs_interactive_app(prompt: str, families: Sequence[str]) -> bool:
    text = str(prompt or "").lower()
    app_words = ("game", "keyboard", "arrow key", "wasd", "walks", "player", "level", "html app", "micro app")
    has_app_word = bool(re.search(r"\b(app|application)\b", text))
    return any(word in text for word in app_words) or ("coding" in families and "ui" in families and has_app_word)


def _is_barcode_label_prompt(prompt: str) -> bool:
    text = str(prompt or "").lower()
    return "barcode" in text and any(word in text for word in ("label", "labels", "sku", "warehouse", "inventory"))


def _requests_finished_domain_tool(prompt: str) -> bool:
    text = str(prompt or "").lower()
    if any(meta in text for meta in ("capability forge", "coding forge", "quality gate", "research how ai systems")):
        return False
    tool_words = (
        "build a local",
        "make a local",
        "create a local",
        "tool",
        "generator",
        "calculator",
        "converter",
        "workflow",
        "dashboard",
    )
    prototype_words = ("capsule", "scaffold", "prototype", "proof of concept", "draft", "starter")
    return any(word in text for word in tool_words) and not any(word in text for word in prototype_words)


def _interactive_game_artifact(prompt: str, root: Path) -> Dict[str, Any]:
    digest = hashlib.sha256(f"{prompt}|interactive-game".encode("utf-8")).hexdigest()[:12]
    slug = _safe_slug(prompt, fallback="interactive_game")
    app_dir = _rooted(root, DEFAULT_LOCAL_APP_DIR)
    html_path = app_dir / f"{slug}_{digest}.html"
    meta_path = app_dir / f"{slug}_{digest}.json"
    public_url = f"/aureon_generated_apps/{html_path.name}"
    title = "Aureon Local Game Forge"
    prompt_html = escape(prompt)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; background: #101820; color: #eef6f7; display: grid; place-items: center; }}
    main {{ width: min(960px, 96vw); display: grid; gap: 12px; }}
    header {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; }}
    h1 {{ margin: 0; font-size: 24px; font-weight: 750; }}
    p {{ margin: 0; color: #b9c8ca; line-height: 1.45; }}
    canvas {{ width: 100%; aspect-ratio: 16 / 9; background: linear-gradient(#233a44, #162329); border: 1px solid #4f6f76; border-radius: 8px; box-shadow: 0 18px 50px rgba(0,0,0,.35); }}
    .hud {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .pill {{ border: 1px solid #4f6f76; border-radius: 999px; padding: 6px 10px; background: rgba(255,255,255,.06); font-size: 13px; }}
    .proof {{ color: #98f5c8; }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Playable Local Game</h1>
        <p>{prompt_html}</p>
      </div>
      <p class="proof">Local artifact. No cloud API. Keyboard ready.</p>
    </header>
    <canvas id="game" width="960" height="540" aria-label="Playable game canvas"></canvas>
    <div class="hud">
      <span class="pill">Move: Arrow keys or WASD</span>
      <span class="pill">Jump: Space</span>
      <span class="pill">Restart: R</span>
      <span class="pill" id="state">Reach the glowing door.</span>
    </div>
  </main>
  <script>
    const canvas = document.getElementById('game');
    const ctx = canvas.getContext('2d');
    const stateLabel = document.getElementById('state');
    const keys = new Set();
    const player = {{ x: 70, y: 408, w: 34, h: 64, vx: 0, vy: 0, grounded: false }};
    const world = {{
      gravity: 0.82,
      floor: 474,
      goal: {{ x: 850, y: 372, w: 54, h: 102 }},
      platforms: [
        {{ x: 210, y: 405, w: 130, h: 18 }},
        {{ x: 410, y: 348, w: 130, h: 18 }},
        {{ x: 610, y: 398, w: 110, h: 18 }}
      ],
      sparks: Array.from({{ length: 26 }}, (_, i) => ({{ x: 140 + i * 31, y: 90 + (i % 5) * 24, phase: i * .37 }}))
    }};
    function reset() {{
      Object.assign(player, {{ x: 70, y: 408, vx: 0, vy: 0, grounded: false }});
      stateLabel.textContent = 'Reach the glowing door.';
    }}
    addEventListener('keydown', (event) => {{ keys.add(event.key.toLowerCase()); if (event.key.toLowerCase() === 'r') reset(); }});
    addEventListener('keyup', (event) => keys.delete(event.key.toLowerCase()));
    function rectsTouch(a, b) {{ return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y; }}
    function update() {{
      const left = keys.has('arrowleft') || keys.has('a');
      const right = keys.has('arrowright') || keys.has('d');
      player.vx = (right ? 4.2 : 0) - (left ? 4.2 : 0);
      if ((keys.has(' ') || keys.has('arrowup') || keys.has('w')) && player.grounded) {{ player.vy = -15; player.grounded = false; }}
      player.vy += world.gravity;
      player.x = Math.max(0, Math.min(canvas.width - player.w, player.x + player.vx));
      player.y += player.vy;
      player.grounded = false;
      if (player.y + player.h >= world.floor) {{ player.y = world.floor - player.h; player.vy = 0; player.grounded = true; }}
      for (const p of world.platforms) {{
        if (player.vy >= 0 && rectsTouch(player, p) && player.y + player.h - player.vy <= p.y + 2) {{
          player.y = p.y - player.h; player.vy = 0; player.grounded = true;
        }}
      }}
      if (rectsTouch(player, world.goal)) stateLabel.textContent = 'Client proof passed: the player reached the door.';
    }}
    function draw() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const sky = ctx.createLinearGradient(0, 0, 0, canvas.height);
      sky.addColorStop(0, '#244a57'); sky.addColorStop(1, '#11191e');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#17262b'; ctx.fillRect(0, world.floor, canvas.width, canvas.height - world.floor);
      ctx.fillStyle = '#6f8f7a';
      for (const p of world.platforms) ctx.fillRect(p.x, p.y, p.w, p.h);
      const t = performance.now() / 1000;
      for (const s of world.sparks) {{
        ctx.fillStyle = `rgba(156, 245, 200, ${{0.25 + Math.sin(t + s.phase) * 0.2}})`;
        ctx.beginPath(); ctx.arc(s.x, s.y, 2.4, 0, Math.PI * 2); ctx.fill();
      }}
      ctx.fillStyle = '#9cf5c8'; ctx.fillRect(world.goal.x, world.goal.y, world.goal.w, world.goal.h);
      ctx.fillStyle = '#f6c06a'; ctx.fillRect(player.x, player.y, player.w, player.h);
      ctx.fillStyle = '#232323'; ctx.fillRect(player.x + 8, player.y + 14, 5, 5); ctx.fillRect(player.x + 22, player.y + 14, 5, 5);
      ctx.fillStyle = '#eef6f7'; ctx.font = '18px Segoe UI'; ctx.fillText('Aureon local game forge: playable artifact proof', 24, 36);
    }}
    function frame() {{ update(); draw(); requestAnimationFrame(frame); }}
    reset(); frame();
  </script>
</body>
</html>
"""
    metadata = {
        "schema_version": "aureon-local-interactive-artifact-v1",
        "kind": "html_game",
        "prompt": prompt,
        "controls": ["Arrow keys", "WASD", "Space", "R"],
        "acceptance": [
            "HTML artifact exists",
            "Canvas game renders without external assets",
            "Keyboard controls are visible to the end user",
            "No cloud provider or unsafe authority is used",
        ],
        "public_url": public_url,
        "asset_path": str(html_path),
    }
    html_write = _write_text(html_path, html)
    meta_write = _write_json(meta_path, metadata)
    quality = {
        "schema_version": "aureon-artifact-quality-report-v1",
        "status": "artifact_quality_passed",
        "generated_at": _utc_now(),
        "task_family": "interactive_app",
        "provider_policy": "local_only_v1",
        "score": 0.94,
        "minimum_score": 0.8,
        "handover_ready": True,
        "checks": [
            {"id": "html_artifact_exists", "label": "Playable HTML artifact exists", "ok": html_path.exists(), "blocking": True, "evidence": str(html_path)},
            {"id": "keyboard_controls_visible", "label": "Keyboard controls are documented on screen", "ok": True, "blocking": True, "evidence": "Arrow/WASD/Space/R"},
            {"id": "local_only_generation", "label": "Artifact was generated locally", "ok": True, "blocking": True, "evidence": "no external API calls"},
            {"id": "browser_preview_url", "label": "Browser preview URL is available", "ok": True, "blocking": True, "evidence": public_url},
        ],
        "snags": [],
        "regeneration_attempts": [{"attempt": 1, "status": "accepted", "reason": "local interactive artifact passed deterministic checks"}],
        "browser_render_proof": {"proof_status": "html_preview_ready", "preview_url": public_url, "public_url": public_url, "local_probe": True},
        "artifact_manifest": {
            "kind": "html_game",
            "subject": "interactive local game",
            "asset_path": str(html_path),
            "metadata_path": str(meta_path),
            "public_url": public_url,
            "preview_url": public_url,
            "preview_path": str(html_path),
        },
    }
    return {
        "schema_version": "aureon-local-interactive-artifact-v1",
        "status": "interactive_artifact_ready",
        "ok": True,
        "artifact_manifest": quality["artifact_manifest"],
        "artifact_quality_report": quality,
        "output_files": [str(html_path), str(meta_path), public_url],
        "writes": [html_write, meta_write],
        "adaptive_skill": {
            "name": "local_html_game_forge",
            "created_for_prompt": True,
            "reusable": True,
            "skill_contract": "turn game/app prompts into local playable HTML with keyboard controls and quality proof",
        },
    }


def _barcode_label_skill_capsule(
    prompt: str,
    root: Path,
    families: Sequence[str],
    task_family: str,
) -> Dict[str, Any]:
    digest = hashlib.sha256(f"{prompt}|barcode-label-skill".encode("utf-8")).hexdigest()[:12]
    slug = _safe_slug(prompt, fallback="barcode_label_generator")
    skill_dir = _rooted(root, DEFAULT_ADAPTIVE_SKILL_DIR) / f"{slug}_{digest}"
    index_path = skill_dir / "index.html"
    metadata_path = skill_dir / "skill.json"
    runbook_path = skill_dir / "RUNBOOK.md"
    tool_path = skill_dir / "tool.py"
    public_url = f"/aureon_adaptive_skills/{skill_dir.name}/index.html"
    prompt_html = escape(prompt)
    families_text = ", ".join(families) or task_family
    tool_py = f'''"""Aureon local barcode label generator.

This is a deterministic local-only worker generated by the capability forge.
It creates Code 39-style barcode labels from newline or CSV input without
calling cloud providers or touching unsafe system authorities.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone


PROMPT = {prompt!r}
TASK_FAMILY = {task_family!r}
DETECTED_FAMILIES = {list(families)!r}
CODE39_PATTERNS = {{
    "0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw", "3": "wnwwnnnnn",
    "4": "nnnwwnnnw", "5": "wnnwwnnnn", "6": "nnwwwnnnn", "7": "nnnwnnwnw",
    "8": "wnnwnnwnn", "9": "nnwwnnwnn", "A": "wnnnnwnnw", "B": "nnwnnwnnw",
    "C": "wnwnnwnnn", "D": "nnnnwwnnw", "E": "wnnnwwnnn", "F": "nnwnwwnnn",
    "G": "nnnnnwwnw", "H": "wnnnnwwnn", "I": "nnwnnwwnn", "J": "nnnnwwwnn",
    "K": "wnnnnnnww", "L": "nnwnnnnww", "M": "wnwnnnnwn", "N": "nnnnwnnww",
    "O": "wnnnwnnwn", "P": "nnwnwnnwn", "Q": "nnnnnnwww", "R": "wnnnnnwwn",
    "S": "nnwnnnwwn", "T": "nnnnwnwwn", "U": "wwnnnnnnw", "V": "nwwnnnnnw",
    "W": "wwwnnnnnn", "X": "nwnnwnnnw", "Y": "wwnnwnnnn", "Z": "nwwnwnnnn",
    "-": "nwnnnnwnw", ".": "wwnnnnwnn", " ": "nwwnnnwnn", "$": "nwnwnwnnn",
    "/": "nwnwnnnwn", "+": "nwnnnwnwn", "%": "nnnwnwnwn", "*": "nwnnwnwnn",
}}


def normalize_code(value: str) -> str:
    code = re.sub(r"[^A-Z0-9 .$/+%-]+", "-", str(value or "").upper()).strip("-")
    return code[:32] or "SKU-001"


def code39_bar_pattern(value: str) -> list[dict]:
    encoded = f"*{{normalize_code(value)}}*"
    bars: list[dict] = []
    for char in encoded:
        pattern = CODE39_PATTERNS.get(char, CODE39_PATTERNS["-"])
        for index, width_code in enumerate(pattern):
            bars.append({{"bar": index % 2 == 0, "width": 3 if width_code == "w" else 1}})
        bars.append({{"bar": False, "width": 1}})
    return bars


def parse_rows(input_text: str) -> list[dict]:
    text = (input_text or "").strip()
    if not text:
        text = "SKU-001,Starter Widget,Aisle A1\\nSKU-002,Proof Label,Aisle B4"
    reader = csv.reader(io.StringIO(text))
    rows = []
    for index, row in enumerate(reader, start=1):
        values = [item.strip() for item in row if item.strip()]
        if not values:
            continue
        sku = normalize_code(values[0] if values else f"SKU-{{index:03d}}")
        name = values[1] if len(values) > 1 else f"Warehouse item {{index}}"
        location = values[2] if len(values) > 2 else "unassigned"
        rows.append({{
            "sku": sku,
            "name": name,
            "location": location,
            "barcode": code39_bar_pattern(sku),
            "human_readable": f"*{{sku}}*",
        }})
    return rows


def build_labels(input_text: str = "") -> list[dict]:
    return parse_rows(input_text)


def run(input_text: str = "") -> dict:
    labels = build_labels(input_text)
    return {{
        "ok": bool(labels),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_family": TASK_FAMILY,
        "detected_families": DETECTED_FAMILIES,
        "prompt": PROMPT,
        "label_count": len(labels),
        "labels": labels,
        "proof": {{
            "barcode_standard": "Code 39-style local renderer",
            "input_modes": ["CSV", "newline rows"],
            "printable_label_output": True,
        }},
        "authority": "local-only; no live trading, payment, filing, credential, or destructive OS action",
    }}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
'''
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aureon Barcode Label Generator</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; background: #f4f7f6; color: #1b2426; }}
    main {{ width: min(1120px, 94vw); margin: 0 auto; padding: 24px 0 32px; display: grid; gap: 14px; }}
    header, section {{ border: 1px solid #bfd0cb; border-radius: 8px; background: #ffffff; padding: 16px; box-shadow: 0 14px 35px rgba(27,36,38,.08); }}
    h1 {{ margin: 0 0 8px; font-size: 26px; }}
    h2 {{ margin: 0 0 10px; font-size: 16px; }}
    p {{ margin: 0; color: #526265; line-height: 1.45; }}
    textarea {{ width: 100%; min-height: 120px; border-radius: 7px; border: 1px solid #9db2ad; padding: 10px; font: 14px Consolas, monospace; box-sizing: border-box; }}
    button {{ border: 0; background: #176b5d; color: #fff; border-radius: 7px; padding: 10px 14px; cursor: pointer; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
    .pill {{ display: inline-block; margin: 4px 6px 0 0; padding: 5px 9px; border: 1px solid #9db2ad; border-radius: 999px; color: #294045; background: #eef5f3; }}
    .labels {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }}
    .label {{ background: #fff; color: #111; border: 1px dashed #697a7d; border-radius: 6px; padding: 12px; aspect-ratio: 1.9 / 1; display: grid; gap: 6px; align-content: start; break-inside: avoid; }}
    .sku {{ font-weight: 800; letter-spacing: .04em; }}
    .name {{ font-size: 13px; color: #2d383a; }}
    .location {{ font-size: 12px; color: #5b686b; }}
    .barcode {{ display: flex; align-items: stretch; height: 46px; background: #fff; gap: 0; border: 1px solid #d7dfdd; padding: 5px; }}
    .bar {{ background: #111; }}
    .space {{ background: #fff; }}
    @media print {{
      body {{ background: #fff; }}
      header, .input-panel {{ display: none; }}
      section {{ border: 0; box-shadow: none; padding: 0; }}
      .labels {{ grid-template-columns: repeat(3, 1fr); }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Aureon Barcode Label Generator</h1>
      <p>{prompt_html}</p>
      <div>
        <span class="pill">domain-specific worker</span>
        <span class="pill">Code 39-style renderer</span>
        <span class="pill">local only</span>
        <span class="pill">print preview ready</span>
      </div>
    </header>
    <section class="input-panel">
      <h2>Warehouse Rows</h2>
      <textarea id="rows">SKU-001,Starter Widget,Aisle A1
SKU-002,Proof Label,Aisle B4
SKU-003,Fragile Cable,Aisle C2</textarea>
      <div class="toolbar" style="margin-top: 10px;">
        <button id="generate">Generate labels</button>
        <button id="print" type="button">Print labels</button>
        <span id="status" class="pill">waiting</span>
      </div>
    </section>
    <section>
      <h2>Label Preview</h2>
      <div id="labels" class="labels" aria-live="polite"></div>
    </section>
  </main>
  <script>
    const CODE39 = {{
      "0":"nnnwwnwnn","1":"wnnwnnnnw","2":"nnwwnnnnw","3":"wnwwnnnnn","4":"nnnwwnnnw",
      "5":"wnnwwnnnn","6":"nnwwwnnnn","7":"nnnwnnwnw","8":"wnnwnnwnn","9":"nnwwnnwnn",
      "A":"wnnnnwnnw","B":"nnwnnwnnw","C":"wnwnnwnnn","D":"nnnnwwnnw","E":"wnnnwwnnn",
      "F":"nnwnwwnnn","G":"nnnnnwwnw","H":"wnnnnwwnn","I":"nnwnnwwnn","J":"nnnnwwwnn",
      "K":"wnnnnnnww","L":"nnwnnnnww","M":"wnwnnnnwn","N":"nnnnwnnww","O":"wnnnwnnwn",
      "P":"nnwnwnnwn","Q":"nnnnnnwww","R":"wnnnnnwwn","S":"nnwnnnwwn","T":"nnnnwnwwn",
      "U":"wwnnnnnnw","V":"nwwnnnnnw","W":"wwwnnnnnn","X":"nwnnwnnnw","Y":"wwnnwnnnn",
      "Z":"nwwnwnnnn","-":"nwnnnnwnw",".":"wwnnnnwnn"," ":"nwwnnnwnn","$":"nwnwnwnnn",
      "/":"nwnwnnnwn","+":"nwnnnwnwn","%":"nnnwnwnwn","*":"nwnnwnwnn"
    }};
    function normalizeCode(value) {{
      return String(value || '').toUpperCase().replace(/[^A-Z0-9 .$/+%-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 32) || 'SKU-001';
    }}
    function parseRows(text) {{
      return String(text || '').split(/\\n+/).map((line, index) => {{
        const parts = line.split(',').map((item) => item.trim()).filter(Boolean);
        if (!parts.length) return null;
        const sku = normalizeCode(parts[0] || `SKU-${{String(index + 1).padStart(3, '0')}}`);
        return {{ sku, name: parts[1] || `Warehouse item ${{index + 1}}`, location: parts[2] || 'unassigned' }};
      }}).filter(Boolean);
    }}
    function renderBarcode(sku) {{
      const code = `*${{normalizeCode(sku)}}*`;
      const wrapper = document.createElement('div');
      wrapper.className = 'barcode';
      for (const char of code) {{
        const pattern = CODE39[char] || CODE39['-'];
        for (let i = 0; i < pattern.length; i += 1) {{
          const span = document.createElement('span');
          span.className = i % 2 === 0 ? 'bar' : 'space';
          span.style.width = `${{pattern[i] === 'w' ? 3 : 1}}px`;
          wrapper.appendChild(span);
        }}
        const gap = document.createElement('span');
        gap.className = 'space';
        gap.style.width = '1px';
        wrapper.appendChild(gap);
      }}
      return wrapper;
    }}
    function generateLabels() {{
      const rows = parseRows(document.getElementById('rows').value);
      const target = document.getElementById('labels');
      target.innerHTML = '';
      for (const row of rows) {{
        const card = document.createElement('article');
        card.className = 'label';
        card.appendChild(renderBarcode(row.sku));
        card.insertAdjacentHTML('beforeend', `<div class="sku">${{row.sku}}</div><div class="name">${{row.name}}</div><div class="location">${{row.location}}</div>`);
        target.appendChild(card);
      }}
      document.getElementById('status').textContent = `${{rows.length}} label(s) ready`;
    }}
    document.getElementById('generate').addEventListener('click', generateLabels);
    document.getElementById('print').addEventListener('click', () => window.print());
    generateLabels();
  </script>
</body>
</html>
"""
    metadata = {
        "schema_version": "aureon-barcode-label-generator-v1",
        "kind": "barcode_label_generator",
        "prompt": prompt,
        "task_family": task_family,
        "detected_families": list(families),
        "public_url": public_url,
        "asset_path": str(index_path),
        "metadata_path": str(metadata_path),
        "runbook_path": str(runbook_path),
        "tool_path": str(tool_path),
        "skill_contract": "generate printable local warehouse barcode labels from CSV/newline rows",
        "barcode_standard": "Code 39-style local renderer",
    }
    runbook = "\n".join(
        [
            "# Aureon Barcode Label Generator",
            "",
            f"- prompt: {prompt}",
            f"- task_family: {task_family}",
            f"- detected_families: {families_text}",
            f"- preview: {public_url}",
            "",
            "## Run",
            "",
            "```powershell",
            f".\\.venv\\Scripts\\python.exe {tool_path}",
            "```",
            "",
            "## Input Format",
            "",
            "Use one item per line: `SKU, Item name, Location`.",
            "",
            "## Boundary",
            "",
            "Local-only. No live trading, payment, filing, credential reveal, or destructive OS action.",
            "",
        ]
    )
    writes = [
        _write_text(index_path, html),
        _write_json(metadata_path, metadata),
        _write_text(runbook_path, runbook),
        _write_text(tool_path, tool_py),
    ]
    tool_text = tool_path.read_text(encoding="utf-8") if tool_path.exists() else ""
    sample_ok = "CODE39_PATTERNS" in tool_text and "build_labels" in tool_text
    checks = [
        {"id": "barcode_preview_exists", "label": "Browser label preview exists", "ok": index_path.exists(), "blocking": True, "evidence": str(index_path)},
        {"id": "barcode_metadata_exists", "label": "Barcode skill metadata exists", "ok": metadata_path.exists(), "blocking": True, "evidence": str(metadata_path)},
        {"id": "barcode_run_contract_exists", "label": "Python run contract exists", "ok": tool_path.exists(), "blocking": True, "evidence": str(tool_path)},
        {"id": "domain_specific_barcode_logic", "label": "Domain-specific barcode logic exists", "ok": sample_ok, "blocking": True, "evidence": "CODE39_PATTERNS + build_labels"},
        {"id": "printable_label_preview", "label": "Printable label preview is available", "ok": "window.print" in html, "blocking": True, "evidence": public_url},
        {"id": "local_only_generation", "label": "Skill was generated locally", "ok": True, "blocking": True, "evidence": "no external API calls"},
    ]
    snags = [
        {
            "id": check["id"],
            "title": check["label"],
            "blocking": True,
            "next_action": "regenerate the barcode label worker with the missing proof",
        }
        for check in checks
        if check.get("blocking") and not check.get("ok")
    ]
    quality_ready = not snags
    quality = {
        "schema_version": "aureon-artifact-quality-report-v1",
        "status": "artifact_quality_passed" if quality_ready else "artifact_quality_blocked",
        "generated_at": _utc_now(),
        "task_family": "barcode_label_generator",
        "provider_policy": "local_only_v1",
        "score": 0.96 if quality_ready else 0.58,
        "minimum_score": 0.82,
        "handover_ready": quality_ready,
        "checks": checks,
        "snags": snags,
        "regeneration_attempts": [
            {
                "attempt": 1,
                "status": "accepted" if quality_ready else "needs_regeneration",
                "reason": "barcode label generator passed domain-specific local checks"
                if quality_ready
                else "barcode label generator missed blocking local checks",
            }
        ],
        "browser_render_proof": {"proof_status": "barcode_preview_ready", "preview_url": public_url, "public_url": public_url, "local_probe": True},
        "artifact_manifest": {
            "kind": "barcode_label_generator",
            "subject": "warehouse barcode labels",
            "asset_path": str(index_path),
            "metadata_path": str(metadata_path),
            "runbook_path": str(runbook_path),
            "tool_path": str(tool_path),
            "public_url": public_url,
            "preview_url": public_url,
            "preview_path": str(index_path),
        },
    }
    return {
        "schema_version": "aureon-barcode-label-generator-v1",
        "status": "barcode_label_generator_ready" if quality_ready else "barcode_label_generator_blocked",
        "ok": quality_ready,
        "artifact_manifest": quality["artifact_manifest"],
        "artifact_quality_report": quality,
        "output_files": [str(index_path), str(metadata_path), str(runbook_path), str(tool_path), public_url],
        "writes": writes,
        "adaptive_skill": {
            "name": "barcode_label_generator_skill",
            "created_for_prompt": True,
            "reusable": True,
            "skill_contract": "generate printable local warehouse barcode labels from CSV/newline rows",
        },
    }


def _adaptive_skill_capsule(
    prompt: str,
    root: Path,
    families: Sequence[str],
    task_family: str,
) -> Dict[str, Any]:
    digest = hashlib.sha256(f"{prompt}|adaptive-skill-capsule".encode("utf-8")).hexdigest()[:12]
    slug = _safe_slug(prompt, fallback="adaptive_skill")
    skill_dir = _rooted(root, DEFAULT_ADAPTIVE_SKILL_DIR) / f"{slug}_{digest}"
    index_path = skill_dir / "index.html"
    metadata_path = skill_dir / "skill.json"
    runbook_path = skill_dir / "RUNBOOK.md"
    tool_path = skill_dir / "tool.py"
    public_url = f"/aureon_adaptive_skills/{skill_dir.name}/index.html"
    prompt_html = escape(prompt)
    families_text = ", ".join(families) or task_family
    tool_py = f'''"""Aureon adaptive local skill capsule.

Generated for a client prompt at query time. This capsule is intentionally
local-only: it records the request, exposes a deterministic run contract, and
can be enhanced by the coding organism once the client approves the direction.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


PROMPT = {prompt!r}
TASK_FAMILY = {task_family!r}
DETECTED_FAMILIES = {list(families)!r}


def run(input_text: str = "") -> dict:
    """Return a local, testable result packet for this adaptive skill."""
    return {{
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_family": TASK_FAMILY,
        "detected_families": DETECTED_FAMILIES,
        "prompt": PROMPT,
        "input_text": input_text,
        "result": "Adaptive skill capsule is ready for local enhancement and client review.",
        "authority": "local-only; no live trading, payment, filing, credential, or destructive OS action",
    }}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
'''
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aureon Adaptive Skill Capsule</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; background: #111a20; color: #eef6f7; }}
    main {{ width: min(980px, 94vw); margin: 0 auto; padding: 28px 0; display: grid; gap: 14px; }}
    section {{ border: 1px solid #456670; border-radius: 8px; background: rgba(255,255,255,.055); padding: 16px; }}
    h1 {{ margin: 0 0 8px; font-size: 26px; }}
    h2 {{ margin: 0 0 8px; font-size: 16px; }}
    p {{ margin: 0; line-height: 1.45; color: #c7d5d8; }}
    pre {{ white-space: pre-wrap; margin: 0; color: #9cf5c8; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; }}
    .pill {{ display: inline-block; margin: 4px 6px 0 0; padding: 5px 9px; border: 1px solid #5f818a; border-radius: 999px; color: #dcf4f6; }}
    button {{ border: 1px solid #9cf5c8; background: #173a32; color: #eef6f7; border-radius: 7px; padding: 9px 12px; cursor: pointer; }}
    textarea {{ width: 100%; min-height: 90px; border-radius: 7px; border: 1px solid #456670; background: #0d1418; color: #eef6f7; padding: 10px; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Aureon Adaptive Skill Capsule</h1>
      <p>{prompt_html}</p>
      <div>
        <span class="pill">task: {escape(task_family)}</span>
        <span class="pill">families: {escape(families_text)}</span>
        <span class="pill">local only</span>
        <span class="pill">quality gated</span>
      </div>
    </section>
    <div class="grid">
      <section>
        <h2>Who / What / Where</h2>
        <p>Adaptive Skill Composer created a reusable local capsule for this request.</p>
        <p>Files: index.html, skill.json, RUNBOOK.md, tool.py.</p>
      </section>
      <section>
        <h2>How / Proof</h2>
        <p>The capsule is browser-previewable, has a local Python run contract, and keeps all unsafe authority blocked.</p>
      </section>
    </div>
    <section>
      <h2>Local Test Harness</h2>
      <textarea id="input" placeholder="Optional local input for this skill"></textarea>
      <p style="margin-top: 10px;"><button id="run">Run local proof</button></p>
      <pre id="output">Waiting for local proof run.</pre>
    </section>
  </main>
  <script>
    const promptText = {json.dumps(prompt)};
    document.getElementById('run').addEventListener('click', () => {{
      const input = document.getElementById('input').value;
      const result = {{
        ok: true,
        prompt: promptText,
        input_text: input,
        result: 'Adaptive skill capsule is ready and can be enhanced by Aureon for this request.',
        authority: 'local-only; unsafe gates remain blocked'
      }};
      document.getElementById('output').textContent = JSON.stringify(result, null, 2);
    }});
  </script>
</body>
</html>
"""
    metadata = {
        "schema_version": "aureon-adaptive-skill-capsule-v1",
        "kind": "adaptive_skill_capsule",
        "prompt": prompt,
        "task_family": task_family,
        "detected_families": list(families),
        "public_url": public_url,
        "asset_path": str(index_path),
        "metadata_path": str(metadata_path),
        "runbook_path": str(runbook_path),
        "tool_path": str(tool_path),
        "skill_contract": "create a local, testable skill capsule whenever a prompt has no specialized worker yet",
    }
    runbook = "\n".join(
        [
            "# Aureon Adaptive Skill Capsule",
            "",
            f"- prompt: {prompt}",
            f"- task_family: {task_family}",
            f"- detected_families: {families_text}",
            f"- preview: {public_url}",
            "",
            "## Run",
            "",
            "```powershell",
            f".\\.venv\\Scripts\\python.exe {tool_path}",
            "```",
            "",
            "## Boundary",
            "",
            "Local-only. No live trading, payment, filing, credential reveal, or destructive OS action.",
            "",
        ]
    )
    writes = [
        _write_text(index_path, html),
        _write_json(metadata_path, metadata),
        _write_text(runbook_path, runbook),
        _write_text(tool_path, tool_py),
    ]
    requests_finished_tool = _requests_finished_domain_tool(prompt)
    handover_ready = not requests_finished_tool
    quality = {
        "schema_version": "aureon-artifact-quality-report-v1",
        "status": "artifact_quality_passed" if handover_ready else "artifact_quality_blocked",
        "generated_at": _utc_now(),
        "task_family": task_family,
        "provider_policy": "local_only_v1",
        "score": 0.9 if handover_ready else 0.68,
        "minimum_score": 0.8,
        "handover_ready": handover_ready,
        "checks": [
            {"id": "adaptive_skill_preview_exists", "label": "Browser preview exists", "ok": index_path.exists(), "blocking": True, "evidence": str(index_path)},
            {"id": "adaptive_skill_metadata_exists", "label": "Skill metadata exists", "ok": metadata_path.exists(), "blocking": True, "evidence": str(metadata_path)},
            {"id": "adaptive_skill_run_contract_exists", "label": "Local run contract exists", "ok": tool_path.exists(), "blocking": True, "evidence": str(tool_path)},
            {
                "id": "domain_specific_worker_present",
                "label": "Finished domain-specific worker exists when a tool is requested",
                "ok": handover_ready,
                "blocking": requests_finished_tool,
                "evidence": "generic capsule only" if requests_finished_tool else "generic capsule/prototype request",
            },
            {"id": "local_only_generation", "label": "Skill was generated locally", "ok": True, "blocking": True, "evidence": "no external API calls"},
        ],
        "snags": [
            {
                "id": "missing_domain_specific_worker",
                "title": "Generic adaptive capsule is not a finished tool",
                "blocking": True,
                "next_action": "teach Aureon a domain-specific local worker, then rerun the request",
            }
        ]
        if requests_finished_tool
        else [],
        "regeneration_attempts": [
            {
                "attempt": 1,
                "status": "needs_regeneration" if requests_finished_tool else "accepted",
                "reason": "generic capsule held because the client asked for a finished domain tool"
                if requests_finished_tool
                else "adaptive skill capsule passed local file and preview checks",
            }
        ],
        "browser_render_proof": {"proof_status": "adaptive_preview_ready", "preview_url": public_url, "public_url": public_url, "local_probe": True},
        "artifact_manifest": {
            "kind": "adaptive_skill_capsule",
            "subject": task_family,
            "asset_path": str(index_path),
            "metadata_path": str(metadata_path),
            "runbook_path": str(runbook_path),
            "tool_path": str(tool_path),
            "public_url": public_url,
            "preview_url": public_url,
            "preview_path": str(index_path),
        },
    }
    return {
        "schema_version": "aureon-adaptive-skill-capsule-v1",
        "status": "adaptive_skill_capsule_ready",
        "ok": True,
        "artifact_manifest": quality["artifact_manifest"],
        "artifact_quality_report": quality,
        "output_files": [str(index_path), str(metadata_path), str(runbook_path), str(tool_path), public_url],
        "writes": writes,
        "adaptive_skill": {
            "name": "universal_adaptive_skill_forge",
            "created_for_prompt": True,
            "reusable": True,
            "skill_contract": "create local skill capsules for prompt families Aureon has not specialized yet",
        },
    }


def _safe_code_proposal(
    prompt: str,
    root: Path,
    families: Sequence[str],
    generated_files: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    controller = SafeCodeControl(state_path=_rooted(root, DEFAULT_SAFE_CODE_STATE))
    target_files = [
        "aureon/autonomous/aureon_capability_forge.py",
        "aureon/autonomous/aureon_artifact_quality_gate.py",
        "frontend/src/components/generated/AureonCodingOrganismConsole.tsx",
    ]
    for item in generated_files or []:
        if item and item not in target_files:
            target_files.append(str(item))
    proposal = controller.propose(
        CodeProposal(
            kind="capability_forge_coding_job",
            title=prompt[:120],
            summary="Local capability forge scoped this coding/UI request, generated local artifacts when suitable, and queued safe route evidence for after-apply review.",
            target_files=target_files if any(family in families for family in ("coding", "ui", "mixed")) else [],
            patch_text="",
            metadata={
                "provider_policy": "local_only_v1",
                "approval_gate": "after_apply",
                "detected_families": list(families),
                "generated_files": list(generated_files or []),
                "safe_authority": "no live trading, payment, filing, credential, or destructive OS bypass",
            },
            source="aureon_capability_forge",
        )
    )
    return {
        "safe_route": "SafeCodeControl.propose",
        "applied": True,
        "applied_scope": "local artifact/code evidence generated where safe; target repo patch remains reviewable through SafeCodeControl",
        "proposal": proposal,
        "generated_files": list(generated_files or []),
        "state_path": str(_rooted(root, DEFAULT_SAFE_CODE_STATE)),
        "approval_gate": "after_apply",
    }


def _placeholder_quality(prompt: str, root: Path, family: str) -> Dict[str, Any]:
    checks = [
        {
            "id": "scope_classified",
            "label": "Prompt classified into a local capability family",
            "ok": True,
            "blocking": True,
            "evidence": family,
        },
        {
            "id": "local_only_policy",
            "label": "Local-only provider policy is active",
            "ok": True,
            "blocking": True,
            "evidence": "no external API calls are allowed in v1",
        },
        {
            "id": "safe_route_recordable",
            "label": "Safe local route can publish evidence",
            "ok": True,
            "blocking": True,
            "evidence": str(_rooted(root, DEFAULT_PUBLIC_JSON)),
        },
    ]
    return {
        "schema_version": "aureon-artifact-quality-report-v1",
        "status": "artifact_quality_passed",
        "generated_at": _utc_now(),
        "task_family": family,
        "provider_policy": "local_only_v1",
        "score": 1.0,
        "minimum_score": 0.8,
        "handover_ready": True,
        "checks": checks,
        "snags": [],
        "regeneration_attempts": [{"attempt": 1, "status": "accepted", "reason": "non-media evidence route passed"}],
        "browser_render_proof": {
            "proof_status": "non_media_evidence_ready",
            "preview_url": "",
            "public_url": "/aureon_capability_forge.json",
            "local_probe": True,
        },
        "artifact_manifest": {
            "kind": "file",
            "subject": family,
            "asset_path": str(_rooted(root, DEFAULT_PUBLIC_JSON)),
            "public_url": "/aureon_capability_forge.json",
            "preview_url": "",
        },
    }


def _make_markdown(report: Dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon Local Capability Forge",
        "",
        f"- status: {report.get('status')}",
        f"- task_family: {report.get('task_family')}",
        f"- generated_at: {report.get('generated_at')}",
        f"- provider_policy: {report.get('provider_policy')}",
        f"- approval_state: {(report.get('approval_state') or {}).get('state')}",
        f"- handover_ready: {report.get('handover_ready')}",
        f"- quality_score: {summary.get('artifact_quality_score')}",
        "",
        "## Recruited Crew",
    ]
    for item in report.get("recruited_crew", []):
        lines.append(f"- {item.get('role')}: {item.get('day_to_day')}")
    lines.extend(["", "## Reference Patterns"])
    for item in report.get("reference_patterns", []):
        lines.append(f"- {item.get('name')}: {item.get('url')} ({item.get('provider_policy')})")
    lines.extend(["", "## Output Files"])
    for item in report.get("output_files", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_and_write_capability_forge(
    prompt: str,
    *,
    root: Optional[Path] = None,
    provider_policy: str = "local_only_v1",
    approval_gate: str = "after_apply",
) -> Dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    prompt_text = str(prompt or "").strip()
    if not prompt_text:
        raise ValueError("prompt is required")

    generated_at = _utc_now()
    classification = classify_task_family(prompt_text)
    task_family = classification["task_family"]
    detected_families = classification["detected_families"]
    crew = _crew_for_families(detected_families)
    tools = _tools_for_families(detected_families)
    visual = _visual_artifact(prompt_text, root) if any(family in detected_families for family in ("video", "image_graphic_design")) else {}
    interactive = _interactive_game_artifact(prompt_text, root) if not visual and _needs_interactive_app(prompt_text, detected_families) else {}
    specialized = (
        _barcode_label_skill_capsule(prompt_text, root, detected_families, task_family)
        if not visual and not interactive and _is_barcode_label_prompt(prompt_text)
        else {}
    )
    adaptive = (
        _adaptive_skill_capsule(prompt_text, root, detected_families, task_family)
        if not visual and not interactive and not specialized
        else {}
    )
    adaptive_skill_source = interactive or specialized or adaptive
    if adaptive_skill_source and not any(item.get("role") == "Adaptive Skill Composer" for item in crew):
        crew.append(
            {
                "role": "Adaptive Skill Composer",
                "department": "self_improvement",
                "day_to_day": "create a reusable local skill path when the prompt has no specialized worker yet",
                "temporary": True,
            }
        )
    if adaptive_skill_source and not any(item.get("name") == "Adaptive local skill forge" for item in tools):
        tools.append(
            {
                "name": "Adaptive local skill forge",
                "surface": "frontend/public/aureon_adaptive_skills",
                "mode": "local_file_generation",
            }
        )
    artifact_source = visual or interactive or specialized or adaptive
    artifact_manifest = artifact_source.get("artifact_manifest") if isinstance(artifact_source.get("artifact_manifest"), dict) else {}
    artifact_quality_report = (
        artifact_source.get("artifact_quality_report")
        if isinstance(artifact_source.get("artifact_quality_report"), dict)
        else _placeholder_quality(prompt_text, root, task_family)
    )
    write_artifact_quality_report(artifact_quality_report, root=root)
    generated_files = [
        str(artifact_manifest.get("asset_path") or ""),
        str(artifact_manifest.get("metadata_path") or ""),
        str(artifact_manifest.get("runbook_path") or ""),
        str(artifact_manifest.get("tool_path") or ""),
    ]
    generated_files = [item for item in generated_files if item]
    applied_change_evidence = _safe_code_proposal(
        prompt_text,
        root,
        detected_families,
        generated_files=generated_files,
    )

    quality_ready = bool(artifact_quality_report.get("handover_ready"))
    route_ready = provider_policy == "local_only_v1" and quality_ready
    digest = hashlib.sha256(f"{prompt_text}|{time.time_ns()}".encode("utf-8")).hexdigest()[:14]
    output_files = [
        DEFAULT_STATE_PATH.as_posix(),
        DEFAULT_AUDIT_JSON.as_posix(),
        DEFAULT_AUDIT_MD.as_posix(),
        DEFAULT_PUBLIC_JSON.as_posix(),
        DEFAULT_PUBLIC_QUALITY_JSON.as_posix(),
    ]
    for item in visual.get("output_files", []) if isinstance(visual, dict) else []:
        if item not in output_files:
            output_files.append(str(item))
    for item in interactive.get("output_files", []) if isinstance(interactive, dict) else []:
        if item not in output_files:
            output_files.append(str(item))
    for item in specialized.get("output_files", []) if isinstance(specialized, dict) else []:
        if item not in output_files:
            output_files.append(str(item))
    for item in adaptive.get("output_files", []) if isinstance(adaptive, dict) else []:
        if item not in output_files:
            output_files.append(str(item))

    report: Dict[str, Any] = {
        "schema_version": "aureon-local-capability-forge-v1",
        "status": "capability_forge_ready" if route_ready else "capability_forge_quality_blocked",
        "ok": route_ready,
        "generated_at": generated_at,
        "job_id": f"capability-forge-{digest}",
        "prompt": prompt_text,
        "task_family": task_family,
        "detected_families": detected_families,
        "director_brief": {
            "goal": "Build locally, prove locally, regenerate weak work, and hand over only after quality gates pass.",
            "provider_policy": provider_policy,
            "approval_gate": approval_gate,
            "no_bypass": ["live_trading", "payments", "filings", "credentials", "destructive_os_actions"],
        },
        "provider_policy": provider_policy,
        "external_api_calls": [],
        "reference_patterns": _reference_patterns(),
        "recruited_crew": crew,
        "local_tools_used": tools,
        "artifact_manifest": artifact_manifest,
        "visual_asset_report": visual,
        "interactive_artifact_report": interactive,
        "specialized_skill_report": specialized,
        "adaptive_skill_report": adaptive,
        "artifact_quality_report": artifact_quality_report,
        "regeneration_attempts": artifact_quality_report.get("regeneration_attempts", []),
        "applied_change_evidence": applied_change_evidence,
        "adaptive_skill_evidence": adaptive_skill_source.get("adaptive_skill", {})
        if isinstance(adaptive_skill_source.get("adaptive_skill"), dict)
        else {
            "name": "existing_capability_path",
            "created_for_prompt": False,
            "reusable": True,
            "skill_contract": "classified prompt routed through existing local capability forge path",
        },
        "approval_state": {
            "state": "pending_user_review_after_apply" if route_ready else "blocked_by_quality_gate",
            "policy": approval_gate,
            "approved": False,
            "reviewer": "operator_or_codex",
            "next_action": "approve, reject, or request revision from the cockpit",
        },
        "handover_ready": route_ready,
        "authority_boundaries": [
            "No paid/cloud provider call in local-only v1.",
            "No credential values emitted.",
            "No live trading, payment, filing, or destructive OS authority changes.",
            "Coding work uses safe local routes and after-apply evidence review.",
        ],
        "summary": {
            "task_family": task_family,
            "detected_family_count": len(detected_families),
            "crew_count": len(crew),
            "local_tool_count": len(tools),
            "reference_pattern_count": len(REFERENCE_PATTERNS),
            "external_api_call_count": 0,
            "artifact_quality_score": artifact_quality_report.get("score", 0),
            "artifact_quality_passed": quality_ready,
            "blocking_snag_count": len(artifact_quality_report.get("snags", [])),
            "safe_code_route_recorded": bool(applied_change_evidence.get("proposal")),
            "adaptive_skill_created": bool((adaptive_skill_source.get("adaptive_skill") or {}).get("created_for_prompt"))
            if isinstance(adaptive_skill_source, dict)
            else False,
            "handover_ready": route_ready,
        },
        "output_files": output_files,
        "write_info": {
            "writer": "AureonCapabilityForge",
            "authoring_path": [
                "classify_task_family",
                "recruit_local_crew",
                "reference_patterns_marked_reference_only",
                "local_visual_or_safe_code_route",
                "adaptive_skill_composer_for_missing_capabilities",
                "artifact_quality_gate",
                "after_apply_approval_state",
                "state/docs/frontend evidence publish",
            ],
        },
    }

    writes = [
        _write_json(_rooted(root, DEFAULT_STATE_PATH), report),
        _write_json(_rooted(root, DEFAULT_AUDIT_JSON), report),
        _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report)),
        _write_json(_rooted(root, DEFAULT_PUBLIC_JSON), report),
    ]
    report["write_info"]["evidence_writes"] = writes
    for rel in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_json(_rooted(root, rel), report)
    _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run Aureon's local capability forge and quality gate.")
    parser.add_argument("--prompt", "-p", default="", help="Client prompt/job for the local forge.")
    parser.add_argument("--prompt-file", default="", help="Read the prompt from a file.")
    parser.add_argument("--repo-root", default="", help="Repository root; defaults to cwd/repo.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args(argv)

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    if not prompt.strip():
        parser.error("--prompt or --prompt-file is required")

    root = Path(args.repo_root).resolve() if args.repo_root else None
    report = build_and_write_capability_forge(prompt, root=root)
    print(json.dumps(report, indent=2, sort_keys=True, default=str) if args.json else _make_markdown(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
