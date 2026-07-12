"""
Aureon SaaS platform layer.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Makes the whole repo a coherent product surface — connected, working, and
categorized — by composing what already exists:

  • catalog  — the categorized service catalog (12 capability categories × 24
               filesystem domains × 6 product domains) from SystemRegistry, plus
               the manifest JSONs the React catalog UI consumes.
  • domains  — the domain → capability adapter table (canonical singletons).
  • status   — live health/readiness aggregation (honest, often degraded).
  • gateway  — HTTP routes (/api/catalog, /api/domains, /api/status) mounted on
               the operator server, behind the same security envelope.

Import light: submodules pull heavier deps only when used.
"""

from aureon.saas.catalog import build_catalog, write_frontend_manifests
from aureon.saas.domains import PRODUCT_DOMAINS, domain_report

__all__ = ["build_catalog", "write_frontend_manifests", "domain_report", "PRODUCT_DOMAINS"]
