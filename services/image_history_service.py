from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from services.config import DATA_DIR


class ImageHistoryService:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _clean_subject(value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_", ":"} else "_" for ch in str(value or ""))[:120] or "default"

    def _load_all(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}
        subjects = data.get("subjects") if isinstance(data.get("subjects"), dict) else data
        result: dict[str, list[dict[str, Any]]] = {}
        if isinstance(subjects, dict):
            for subject, items in subjects.items():
                if isinstance(items, list):
                    result[self._clean_subject(str(subject))] = [item for item in items if isinstance(item, dict)]
        return result

    def _save_all(self, subjects: dict[str, list[dict[str, Any]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps({"subjects": subjects}, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(self.path)

    def get_items(self, subject: str) -> list[dict[str, Any]]:
        subject_key = self._clean_subject(subject)
        with self._lock:
            return list(self._load_all().get(subject_key, []))

    def save_items(self, subject: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        subject_key = self._clean_subject(subject)
        normalized_items = [item for item in items if isinstance(item, dict)]
        with self._lock:
            subjects = self._load_all()
            subjects[subject_key] = normalized_items
            self._save_all(subjects)
        return normalized_items

    def clear_items(self, subject: str) -> None:
        subject_key = self._clean_subject(subject)
        with self._lock:
            subjects = self._load_all()
            subjects[subject_key] = []
            self._save_all(subjects)


image_history_service = ImageHistoryService(DATA_DIR / "image_conversations.json")
