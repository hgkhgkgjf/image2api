from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path
from threading import Lock
from typing import Any

from services.config import DATA_DIR, config


class ImageHistoryService:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _clean_subject(value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_", ":"} else "_" for ch in str(value or ""))[:120] or "default"

    @staticmethod
    def _save_history_image(image_data: bytes) -> str:
        config.cleanup_old_images()
        file_hash = hashlib.md5(image_data).hexdigest()
        timestamp = int(time.time())
        relative_dir = Path(time.strftime("%Y"), time.strftime("%m"), time.strftime("%d"))
        file_path = config.images_dir / relative_dir / f"{timestamp}_{file_hash}.png"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_bytes(image_data)
        base_url = config.base_url
        prefix = base_url if base_url else ""
        return f"{prefix}/images/{relative_dir.as_posix()}/{file_path.name}"

    @classmethod
    def _data_url_to_image_url(cls, data_url: str) -> str | None:
        if not data_url.startswith("data:") or ";base64," not in data_url:
            return None
        _, _, encoded = data_url.partition(",")
        if not encoded:
            return None
        try:
            return cls._save_history_image(base64.b64decode(encoded))
        except Exception:
            return None

    @classmethod
    def _b64_to_image_url(cls, b64_json: str) -> str | None:
        if not b64_json:
            return None
        try:
            return cls._save_history_image(base64.b64decode(b64_json))
        except Exception:
            return None

    @classmethod
    def _compact_item(cls, value: Any) -> Any:
        """Strip heavy base64 payloads from saved history.

        Images are already served from /images. Keeping b64_json/dataUrl inside the
        conversation JSON makes every history load and save grow by megabytes.
        """
        if isinstance(value, list):
            return [cls._compact_item(item) for item in value]
        if not isinstance(value, dict):
            return value

        item = {str(key): cls._compact_item(child) for key, child in value.items()}

        b64_json = item.get("b64_json")
        if isinstance(b64_json, str) and b64_json:
            if not item.get("url"):
                image_url = cls._b64_to_image_url(b64_json)
                if image_url:
                    item["url"] = image_url
            item.pop("b64_json", None)

        data_url = item.get("dataUrl")
        if isinstance(data_url, str) and data_url.startswith("data:"):
            if not item.get("url"):
                image_url = cls._data_url_to_image_url(data_url)
                if image_url:
                    item["url"] = image_url
            item.pop("dataUrl", None)

        return item

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
            subjects = self._load_all()
            items = subjects.get(subject_key, [])
            compacted = [self._compact_item(item) for item in items]
            if compacted != items:
                subjects[subject_key] = compacted
                self._save_all(subjects)
            return list(compacted)

    def save_items(self, subject: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        subject_key = self._clean_subject(subject)
        normalized_items = [self._compact_item(item) for item in items if isinstance(item, dict)]
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
