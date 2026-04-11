"""
Aureon ↔ Ollama Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Native Ollama client (http://localhost:11434/api/*) plus an LLMAdapter
shim so OllamaBridge is a drop-in replacement for AureonLocalAdapter
inside the in-house AI stack.

The existing AureonLocalAdapter already spoke to Ollama via its
OpenAI-compatible /v1 surface. This module adds:

  • First-class access to Ollama's NATIVE API (/api/chat, /api/generate,
    /api/embed, /api/tags, /api/show, /api/pull, /api/ps, /api/version)
    so the vault can pull models, watch running models, and generate
    embeddings without pretending to be OpenAI.
  • A small OllamaLLMAdapter that routes vault-voice prompts through
    /api/chat directly, honoring Ollama-specific options (keep_alive,
    think mode, format=json).
"""

from aureon.integrations.ollama.ollama_bridge import (
    OllamaBridge,
    OllamaModel,
    OllamaPsEntry,
    OllamaBridgeError,
)
from aureon.integrations.ollama.ollama_adapter import OllamaLLMAdapter

__all__ = [
    "OllamaBridge",
    "OllamaModel",
    "OllamaPsEntry",
    "OllamaBridgeError",
    "OllamaLLMAdapter",
]
