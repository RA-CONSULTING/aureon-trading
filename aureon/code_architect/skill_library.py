"""
SkillLibrary — the persistent registry of learned skills
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Persists skills to JSON under state/skills/. Supports:
  - by-name lookup (fast path)
  - by-level filter
  - by-category filter
  - by-tag filter
  - dependency resolution (given a skill, return the full tree of deps)
  - execution-stat updates (success/failure/duration)
  - atomic bulk save/load
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from aureon.code_architect.skill import Skill, SkillLevel, SkillStatus

logger = logging.getLogger("aureon.code_architect.library")


class SkillLibrary:
    """Thread-safe persistent skill registry."""

    DEFAULT_STORAGE_DIR = Path("state/skills")
    LIBRARY_FILE = "skill_library.json"

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = Path(storage_dir or self.DEFAULT_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.library_path = self.storage_dir / self.LIBRARY_FILE

        self._skills: Dict[str, Skill] = {}              # name → Skill
        self._lock = threading.RLock()

        self._load()

    # ─────────────────────────────────────────────────────────────────────
    # Load / save
    # ─────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self.library_path.exists():
            return
        try:
            with open(self.library_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                skills = data.get("skills", [])
            elif isinstance(data, list):
                skills = data
            else:
                skills = []
            with self._lock:
                for skill_data in skills:
                    try:
                        skill = Skill.from_dict(skill_data)
                        self._skills[skill.name] = skill
                    except Exception as e:
                        logger.warning("Failed to load skill %s: %s", skill_data.get("name"), e)
            logger.info("Loaded %d skills from %s", len(self._skills), self.library_path)
        except Exception as e:
            logger.warning("Library load failed: %s", e)

    def save(self) -> None:
        with self._lock:
            data = {
                "version": 1,
                "saved_at": time.time(),
                "count": len(self._skills),
                "skills": [s.to_dict() for s in self._skills.values()],
            }
        try:
            tmp = self.library_path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.library_path)
        except Exception as e:
            logger.warning("Library save failed: %s", e)

    # ─────────────────────────────────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────────────────────────────────

    def add(self, skill: Skill, persist: bool = True) -> Skill:
        """Add or overwrite a skill."""
        if not skill.name:
            raise ValueError("skill.name is required")
        with self._lock:
            self._skills[skill.name] = skill
        if persist:
            self.save()
        return skill

    def get(self, name: str) -> Optional[Skill]:
        with self._lock:
            return self._skills.get(name)

    def remove(self, name: str, persist: bool = True) -> bool:
        with self._lock:
            removed = self._skills.pop(name, None) is not None
        if removed and persist:
            self.save()
        return removed

    def contains(self, name: str) -> bool:
        with self._lock:
            return name in self._skills

    def __contains__(self, name: str) -> bool:
        return self.contains(name)

    def __len__(self) -> int:
        with self._lock:
            return len(self._skills)

    # ─────────────────────────────────────────────────────────────────────
    # Filters
    # ─────────────────────────────────────────────────────────────────────

    def all(self) -> List[Skill]:
        with self._lock:
            return list(self._skills.values())

    def by_level(self, level: SkillLevel) -> List[Skill]:
        with self._lock:
            return [s for s in self._skills.values() if s.level == level]

    def by_category(self, category: str) -> List[Skill]:
        with self._lock:
            return [s for s in self._skills.values() if s.category == category]

    def by_tag(self, tag: str) -> List[Skill]:
        with self._lock:
            return [s for s in self._skills.values() if tag in s.tags]

    def by_status(self, status: SkillStatus) -> List[Skill]:
        with self._lock:
            return [s for s in self._skills.values() if s.status == status]

    def search(self, substring: str) -> List[Skill]:
        substring = substring.lower()
        with self._lock:
            return [
                s for s in self._skills.values()
                if substring in s.name.lower() or substring in s.description.lower()
            ]

    # ─────────────────────────────────────────────────────────────────────
    # Dependency resolution
    # ─────────────────────────────────────────────────────────────────────

    def resolve_dependencies(self, name: str, _visited: Optional[set] = None) -> List[Skill]:
        """
        Return the full transitive dependency closure of a skill (topologically
        sorted: dependencies before the skill itself). Detects cycles.
        """
        if _visited is None:
            _visited = set()
        if name in _visited:
            return []  # cycle guard
        _visited.add(name)

        skill = self.get(name)
        if not skill:
            return []

        ordered: List[Skill] = []
        for dep_name in skill.dependencies:
            for dep in self.resolve_dependencies(dep_name, _visited):
                if dep.name not in {s.name for s in ordered}:
                    ordered.append(dep)
        ordered.append(skill)
        return ordered

    def has_cycles(self) -> bool:
        """Check if the skill graph contains cycles."""
        with self._lock:
            for name in self._skills:
                visited: set = set()
                stack: set = set()
                if self._detect_cycle(name, visited, stack):
                    return True
        return False

    def _detect_cycle(self, name: str, visited: set, stack: set) -> bool:
        if name in stack:
            return True
        if name in visited:
            return False
        visited.add(name)
        stack.add(name)
        skill = self._skills.get(name)
        if skill:
            for dep in skill.dependencies:
                if self._detect_cycle(dep, visited, stack):
                    return True
        stack.discard(name)
        return False

    # ─────────────────────────────────────────────────────────────────────
    # Execution stat updates
    # ─────────────────────────────────────────────────────────────────────

    def record_execution(
        self,
        name: str,
        success: bool,
        duration_s: float,
        error: Optional[str] = None,
        persist: bool = False,
    ) -> None:
        with self._lock:
            skill = self._skills.get(name)
            if not skill:
                return
            skill.execution_count += 1
            if success:
                skill.success_count += 1
            else:
                skill.failure_count += 1
                skill.last_error = error
            skill.last_execution_at = time.time()
            # Online mean
            if skill.execution_count == 1:
                skill.mean_duration_s = duration_s
            else:
                n = skill.execution_count
                skill.mean_duration_s = skill.mean_duration_s + (duration_s - skill.mean_duration_s) / n

        if persist:
            self.save()

    # ─────────────────────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            by_level: Dict[str, int] = {}
            by_status: Dict[str, int] = {}
            by_category: Dict[str, int] = {}
            total_exec = 0
            total_success = 0
            for s in self._skills.values():
                by_level[s.level.name] = by_level.get(s.level.name, 0) + 1
                by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
                by_category[s.category] = by_category.get(s.category, 0) + 1
                total_exec += s.execution_count
                total_success += s.success_count

            return {
                "total_skills": len(self._skills),
                "by_level": by_level,
                "by_status": by_status,
                "by_category": by_category,
                "total_executions": total_exec,
                "total_successes": total_success,
                "overall_success_rate": (
                    total_success / total_exec if total_exec > 0 else 0.0
                ),
                "has_cycles": self.has_cycles(),
                "storage_path": str(self.library_path),
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────


_library_instance: Optional[SkillLibrary] = None
_library_lock = threading.Lock()


def get_skill_library(storage_dir: Optional[Path] = None) -> SkillLibrary:
    """Get or create the singleton SkillLibrary."""
    global _library_instance
    with _library_lock:
        if _library_instance is None:
            _library_instance = SkillLibrary(storage_dir=storage_dir)
        return _library_instance
