#!/usr/bin/env python3
"""
Dynamic execution fallback for voice commands.

When the intent layer is uncertain or marks a request as an external skill,
this executor uses the Aureon knowledge base (Wikipedia-backed) to gather
context and turn the request into an actionable local task/result.
"""

from __future__ import annotations

from dataclasses import dataclass
import queue
import threading
from typing import Any, Dict, Optional

from aureon.autonomous.aureon_local_task_queue import LocalTask, LocalTaskQueue, build_default_task_queue

try:
    import wikipediaapi  # type: ignore
except Exception:
    wikipediaapi = None  # type: ignore


@dataclass
class DynamicWikiArticle:
    title: str
    summary: str
    url: str
    sections: list[str]


class DynamicVoiceExecutor:
    def __init__(
        self,
        task_queue: Optional[LocalTaskQueue] = None,
    ) -> None:
        self.task_queue = task_queue or build_default_task_queue()
        self.wiki = None
        if wikipediaapi is not None:
            try:
                self.wiki = wikipediaapi.Wikipedia(
                    user_agent="AureonVoiceDynamicExecutor/1.0",
                    language="en",
                )
            except Exception:
                self.wiki = None

    def execute(self, transcript: str, intent: Dict[str, Any], source: str = "voice") -> Dict[str, Any]:
        route = str(intent.get("route") or "")
        params = dict(intent.get("params") or {})
        target = str(intent.get("target") or transcript).strip()
        external_skill = str(params.get("external_skill") or "")

        if external_skill:
            return self._execute_external_skill(external_skill, target, transcript, source)
        if route in {"generic_task", "meta_clarify"}:
            return self._ground_with_wiki(transcript=transcript, target=target, source=source)
        return {"ok": False, "reason": "dynamic_executor_not_applicable"}

    def _execute_external_skill(self, skill: str, target: str, transcript: str, source: str) -> Dict[str, Any]:
        wiki = self._wiki_context(target)
        task = self.task_queue.enqueue(LocalTask(
            title=f"Dynamic skill: {skill}",
            message=transcript,
            source=f"voice:{source}",
            kind="dynamic_skill",
            target_files=[],
        ))
        return {
            "ok": True,
            "route": "dynamic_external_skill",
            "skill": skill,
            "target": target,
            "wiki_context": wiki,
            "task": task,
            "message": self._skill_message(skill, target, wiki),
        }

    def _ground_with_wiki(self, transcript: str, target: str, source: str) -> Dict[str, Any]:
        query = target or transcript
        wiki = self._wiki_context(query)
        task = self.task_queue.enqueue(LocalTask(
            title=f"Dynamic wiki grounding: {query[:80]}",
            message=transcript,
            source=f"voice:{source}",
            kind="dynamic_wiki_grounding",
        ))
        if wiki.get("found"):
            return {
                "ok": True,
                "route": "dynamic_wiki_grounding",
                "query": query,
                "wiki_context": wiki,
                "task": task,
                "message": f"I grounded that with Wikipedia context for {wiki.get('title')}.",
            }
        return {
            "ok": False,
            "route": "dynamic_wiki_grounding",
            "query": query,
            "wiki_context": wiki,
            "task": task,
            "reason": "wikipedia_grounding_failed",
        }

    def _wiki_context(self, query: str) -> Dict[str, Any]:
        article = self._get_article(query)
        if article:
            return {
                "found": True,
                "title": article.title,
                "summary": article.summary[:200] + ("..." if len(article.summary) > 200 else ""),
                "url": article.url,
                "sections": article.sections[:5],
            }
        for fallback in self._fallback_terms(query):
            article = self._get_article(fallback)
            if article:
                top = article
                alternatives = [term for term in self._fallback_terms(query) if term != fallback][:2]
                return {
                    "found": True,
                    "title": top.title,
                    "summary": top.summary[:200] + ("..." if len(top.summary) > 200 else ""),
                    "url": top.url,
                    "sections": top.sections[:5],
                    "alternatives": alternatives,
                }
        return {"found": False, "query": query}

    def _get_article(self, query: str) -> Optional[DynamicWikiArticle]:
        if self.wiki is None:
            return None
        result_queue: "queue.Queue[Optional[DynamicWikiArticle]]" = queue.Queue(maxsize=1)

        def worker() -> None:
            result_queue.put(self._fetch_page(query))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=5.0)
        if thread.is_alive():
            return None
        try:
            return result_queue.get_nowait()
        except queue.Empty:
            return None

    def _fallback_terms(self, query: str) -> list[str]:
        q = query.strip()
        lower = q.lower()
        terms = [q]
        aliases = {
            "btc": "Bitcoin",
            "eth": "Ethereum",
            "apple": "Apple Inc.",
            "google": "Google",
            "tesla": "Tesla, Inc.",
        }
        if lower in aliases:
            terms.append(aliases[lower])
        if lower.endswith(" stock price"):
            terms.append(q[:-12].strip())
        if lower.endswith(" price"):
            terms.append(q[:-6].strip())
        return list(dict.fromkeys([term for term in terms if term]))

    def _fetch_page(self, query: str) -> Optional[DynamicWikiArticle]:
        if self.wiki is None:
            return None
        try:
            page = self.wiki.page(query)
            if not page.exists():
                return None
            return DynamicWikiArticle(
                title=page.title,
                summary=page.summary or "",
                url=page.fullurl,
                sections=[section.title for section in page.sections[:5]],
            )
        except Exception:
            return None

    def _skill_message(self, skill: str, target: str, wiki: Dict[str, Any]) -> str:
        if skill == "stock_price":
            return f"I identified a stock-price request for {target} and grounded it with Wikipedia context."
        if skill == "crypto_price":
            return f"I identified a crypto-price request for {target} and grounded it with Wikipedia context."
        if skill == "paper_search":
            return f"I identified a paper-search request for {target} and prepared it with knowledge context."
        if skill == "news_search":
            return f"I identified a news-search request for {target} and prepared it with knowledge context."
        return f"I prepared the {skill} request for {target}."
