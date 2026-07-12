# ─────────────────────────────────────────────────────────────────────────────
# Aureon Operator / Cognition — standalone production image.
# Serves the switchboard + agentic cognition + phone PoC under waitress.
#
#   docker build -t aureon-operator -f deploy/operator.Dockerfile .
#   docker run -p 8790:8790 \
#     -e OPENAI_API_KEY=sk-... -e AUREON_OPERATOR_API_KEY=secret \
#     aureon-operator
#
# Guardrails carry over: hard authority boundaries always blocked; set
# AUREON_LLM_OFFLINE=1 for a fully offline (no-network) deployment.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Build a self-contained venv with just the operator's runtime deps — mirrors
# the `operator` + core extras in pyproject.toml, not the heavy trading/GUI stack.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel \
    && pip install flask waitress "prometheus-client>=0.24.0" "anthropic>=0.40.0" \
                   "requests>=2.32.0" "python-dotenv>=1.0.0" "rich>=13.7.0"

# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    AUREON_OPERATOR_PORT=8790 \
    AUREON_OPERATOR_HOST=0.0.0.0 \
    AUREON_OPERATOR_THREADS=8

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r aureon && useradd -r -g aureon aureon

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
# The repo-wide grounding index reads docs/ + aureon/ from PYTHONPATH root (/app),
# so ship the source trees the operator actually needs — not the whole repo.
COPY --chown=aureon:aureon aureon/ /app/aureon/
COPY --chown=aureon:aureon docs/ /app/docs/
COPY --chown=aureon:aureon data/datasets/ /app/data/datasets/
COPY --chown=aureon:aureon data/research/ /app/data/research/
COPY --chown=aureon:aureon pyproject.toml README.md conftest.py /app/
RUN mkdir -p /app/state && chown -R aureon:aureon /app/state

USER aureon
EXPOSE 8790

# Liveness probe (readiness is /readyz; scrape metrics at /metrics).
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
    CMD curl -fsS "http://localhost:${AUREON_OPERATOR_PORT}/healthz" || exit 1

# waitress serves the fully-wired WSGI app (config validated, cognition joined
# to the mesh at import). Threads via AUREON_OPERATOR_THREADS.
CMD ["sh", "-c", "waitress-serve --host=0.0.0.0 --port=${AUREON_OPERATOR_PORT} --threads=${AUREON_OPERATOR_THREADS} aureon.operator.wsgi:app"]
