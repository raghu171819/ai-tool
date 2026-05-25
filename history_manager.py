"""
utils/history_manager.py
========================
PURPOSE:
  Saves every task the user runs to a local JSON file so they can
  review what they did earlier, even after restarting the app.

KEY CONCEPTS FOR BEGINNERS:
  - JSON (JavaScript Object Notation) is a simple text format for storing
    structured data.  Python's `json` module reads and writes it easily.
  - We treat the JSON file like a simple database.
  - Each task is one "record" stored as a Python dictionary.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class HistoryManager:
    """
    Stores, retrieves, and analyses task history.

    The data is kept in  data/task_history.json  which is created
    automatically if it doesn't exist.
    """

    FILE_PATH = Path("data/task_history.json")
    MAX_RECORDS = 500  # Prevent the file from growing too large

    def __init__(self):
        # Make sure the data/ directory exists
        self.FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Load existing history into memory
        self._history: List[Dict[str, Any]] = self._load()

    # ── public API ────────────────────────────────────────────────────

    def add(self, task_result) -> None:
        """
        Save one TaskResult to history.

        Args:
            task_result : A TaskResult dataclass instance from task_engine.py
        """
        record = {
            "id":              len(self._history) + 1,
            "timestamp":       datetime.now().isoformat(),
            "task_type":       task_result.task_type,
            "input":           task_result.input_text[:300],   # truncate for storage
            "success":         task_result.success,
            "category":        task_result.category,
            "complexity":      task_result.complexity,
            "processing_time": task_result.processing_time,
            "confidence":      task_result.confidence,
            "error":           task_result.error_message,
        }
        self._history.append(record)

        # Trim if over the limit (keep the newest records)
        if len(self._history) > self.MAX_RECORDS:
            self._history = self._history[-self.MAX_RECORDS:]

        self._save()

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all history records (newest first)."""
        return list(reversed(self._history))

    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        """Return the n most recent records."""
        return self.get_all()[:n]

    def clear(self) -> None:
        """Delete all history records."""
        self._history = []
        self._save()

    def delete_record(self, record_id: int) -> bool:
        """Remove one record by its id.  Returns True if found."""
        before = len(self._history)
        self._history = [r for r in self._history if r["id"] != record_id]
        if len(self._history) < before:
            self._save()
            return True
        return False

    # ── analytics helpers ─────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        Compute summary statistics from the history.
        Used by the Analytics tab in the UI.
        """
        if not self._history:
            return self._empty_stats()

        total         = len(self._history)
        successful    = sum(1 for r in self._history if r["success"])
        failed        = total - successful
        avg_time      = (
            sum(r.get("processing_time", 0) for r in self._history) / total
        )
        success_rate  = round((successful / total) * 100, 1) if total else 0

        # Count tasks per category
        category_counts: Dict[str, int] = {}
        for r in self._history:
            cat = r.get("category", "general")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Count tasks per day (last 7 days)
        daily_counts: Dict[str, int] = {}
        for r in self._history:
            day = r["timestamp"][:10]   # "YYYY-MM-DD"
            daily_counts[day] = daily_counts.get(day, 0) + 1

        return {
            "total":           total,
            "successful":      successful,
            "failed":          failed,
            "success_rate":    success_rate,
            "avg_time":        round(avg_time, 2),
            "category_counts": category_counts,
            "daily_counts":    daily_counts,
        }

    def get_complexity_distribution(self) -> Dict[str, int]:
        """Returns {"low": N, "medium": N, "high": N}."""
        dist = {"low": 0, "medium": 0, "high": 0}
        for r in self._history:
            level = r.get("complexity", "medium")
            if level in dist:
                dist[level] += 1
        return dist

    # ── private helpers ───────────────────────────────────────────────

    def _load(self) -> List[Dict[str, Any]]:
        """Read the JSON file from disk.  Return [] if not found."""
        if not self.FILE_PATH.exists():
            return []
        try:
            with open(self.FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure we always return a list
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            # Corrupted file → start fresh
            return []

    def _save(self) -> None:
        """Write the in-memory history list back to the JSON file."""
        try:
            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except OSError as e:
            # Can't crash the app just because saving failed
            print(f"Warning: Could not save history – {e}")

    @staticmethod
    def _empty_stats() -> Dict[str, Any]:
        return {
            "total":           0,
            "successful":      0,
            "failed":          0,
            "success_rate":    0,
            "avg_time":        0,
            "category_counts": {},
            "daily_counts":    {},
        }
