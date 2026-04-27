from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from services.config import config
from services.storage.base import StorageBackend

AuthRole = Literal["admin", "user"]

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_@.\-]{3,40}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_password(password: str, salt: str) -> str:
    pepper = str(config.auth_key or "")
    return hashlib.pbkdf2_hmac(
        "sha256",
        f"{password}{pepper}".encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()


def _amount(value: object, default: float = 0.0) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return round(float(default), 3)


class InsufficientBalanceError(RuntimeError):
    def __init__(self, required: float, balance: float) -> None:
        self.required = _amount(required)
        self.balance = _amount(balance)
        super().__init__("insufficient_balance")


class AuthService:
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self._lock = Lock()
        self._items = self._load()
        self._last_used_flush_at: dict[str, datetime] = {}

    @staticmethod
    def _clean(value: object) -> str:
        return str(value or "").strip()

    @classmethod
    def _normalize_username(cls, value: object) -> str:
        return cls._clean(value).lower()

    @staticmethod
    def _new_session_token() -> str:
        return f"sess-{secrets.token_urlsafe(32)}"

    def _normalize_item(self, raw: object) -> dict[str, object] | None:
        if not isinstance(raw, dict):
            return None
        role = self._clean(raw.get("role")).lower()
        if role not in {"admin", "user"}:
            return None
        key_hash = self._clean(raw.get("key_hash"))
        if not key_hash:
            return None
        item_id = self._clean(raw.get("id")) or uuid.uuid4().hex[:12]
        name = self._clean(raw.get("name")) or ("管理员密钥" if role == "admin" else "普通用户")
        created_at = self._clean(raw.get("created_at")) or _now_iso()
        last_used_at = self._clean(raw.get("last_used_at")) or None
        balance = max(0.0, _amount(raw.get("balance", raw.get("credit", 0))))
        total_used = max(0.0, _amount(raw.get("total_used", 0)))
        total_recharged = max(0.0, _amount(raw.get("total_recharged", 0)))
        username = self._normalize_username(raw.get("username"))
        password_hash = self._clean(raw.get("password_hash"))
        password_salt = self._clean(raw.get("password_salt"))
        session_token_hash = self._clean(raw.get("session_token_hash"))
        session_created_at = self._clean(raw.get("session_created_at")) or None
        source = self._clean(raw.get("source")) or ("registered" if username and password_hash else "key")
        return {
            "id": item_id,
            "name": name,
            "role": role,
            "key_hash": key_hash,
            "enabled": bool(raw.get("enabled", True)),
            "created_at": created_at,
            "last_used_at": last_used_at,
            "balance": balance,
            "total_used": total_used,
            "total_recharged": total_recharged,
            "username": username,
            "password_hash": password_hash,
            "password_salt": password_salt,
            "session_token_hash": session_token_hash,
            "session_created_at": session_created_at,
            "source": source,
        }

    def _load(self) -> list[dict[str, object]]:
        try:
            items = self.storage.load_auth_keys()
        except Exception:
            return []
        if not isinstance(items, list):
            return []
        return [normalized for item in items if (normalized := self._normalize_item(item)) is not None]

    def _save(self) -> None:
        self.storage.save_auth_keys(self._items)

    @staticmethod
    def _public_item(item: dict[str, object]) -> dict[str, object]:
        return {
            "id": item.get("id"),
            "name": item.get("name"),
            "role": item.get("role"),
            "enabled": bool(item.get("enabled", True)),
            "created_at": item.get("created_at"),
            "last_used_at": item.get("last_used_at"),
            "balance": _amount(item.get("balance", 0)),
            "total_used": _amount(item.get("total_used", 0)),
            "total_recharged": _amount(item.get("total_recharged", 0)),
            "username": item.get("username") or "",
            "has_password": bool(item.get("password_hash")),
            "source": item.get("source") or "key",
        }

    def list_keys(self, role: AuthRole | None = None) -> list[dict[str, object]]:
        with self._lock:
            items = [item for item in self._items if role is None or item.get("role") == role]
            return [self._public_item(item) for item in items]

    def get_key(self, key_id: str, *, role: AuthRole | None = None) -> dict[str, object] | None:
        normalized_id = self._clean(key_id)
        if not normalized_id:
            return None
        with self._lock:
            for item in self._items:
                if item.get("id") == normalized_id and (role is None or item.get("role") == role):
                    return self._public_item(item)
        return None

    def create_key(self, *, role: AuthRole, name: str = "", initial_balance: float = 0.0) -> tuple[dict[str, object], str]:
        normalized_name = self._clean(name) or ("管理员密钥" if role == "admin" else "普通用户")
        raw_key = f"sk-{secrets.token_urlsafe(24)}"
        balance = max(0.0, _amount(initial_balance)) if role == "user" else 0.0
        item = {
            "id": uuid.uuid4().hex[:12],
            "name": normalized_name,
            "role": role,
            "key_hash": _hash_key(raw_key),
            "enabled": True,
            "created_at": _now_iso(),
            "last_used_at": None,
            "balance": balance,
            "total_used": 0.0,
            "total_recharged": balance,
            "username": "",
            "password_hash": "",
            "password_salt": "",
            "session_token_hash": "",
            "session_created_at": None,
            "source": "key",
        }
        with self._lock:
            self._items.append(item)
            self._save()
            return self._public_item(item), raw_key

    def create_registered_user(self, *, username: str, password: str, name: str = "") -> tuple[dict[str, object], str]:
        normalized_username = self._normalize_username(username)
        if not USERNAME_RE.match(normalized_username):
            raise ValueError("用户名只能包含字母、数字、下划线、点、横线或 @，长度 3-40 位")
        if len(str(password or "")) < 6:
            raise ValueError("密码至少需要 6 位")
        normalized_name = self._clean(name) or normalized_username
        raw_key = f"sk-{secrets.token_urlsafe(24)}"
        session_token = self._new_session_token()
        salt = secrets.token_hex(16)
        now = _now_iso()
        item = {
            "id": uuid.uuid4().hex[:12],
            "name": normalized_name,
            "role": "user",
            "key_hash": _hash_key(raw_key),
            "enabled": True,
            "created_at": now,
            "last_used_at": now,
            "balance": 0.0,
            "total_used": 0.0,
            "total_recharged": 0.0,
            "username": normalized_username,
            "password_hash": _hash_password(password, salt),
            "password_salt": salt,
            "session_token_hash": _hash_key(session_token),
            "session_created_at": now,
            "source": "registered",
        }
        with self._lock:
            if any(self._normalize_username(existing.get("username")) == normalized_username for existing in self._items):
                raise ValueError("用户名已被注册")
            self._items.append(item)
            self._save()
            return self._public_item(item), session_token

    def login_with_password(self, *, username: str, password: str) -> tuple[dict[str, object], str] | None:
        normalized_username = self._normalize_username(username)
        if not normalized_username or not password:
            return None
        with self._lock:
            for index, item in enumerate(self._items):
                if item.get("role") != "user":
                    continue
                if self._normalize_username(item.get("username")) != normalized_username:
                    continue
                if not bool(item.get("enabled", True)):
                    return None
                password_hash = self._clean(item.get("password_hash"))
                password_salt = self._clean(item.get("password_salt"))
                if not password_hash or not password_salt:
                    return None
                candidate_hash = _hash_password(password, password_salt)
                if not hmac.compare_digest(password_hash, candidate_hash):
                    return None
                session_token = self._new_session_token()
                next_item = dict(item)
                now = _now_iso()
                next_item["session_token_hash"] = _hash_key(session_token)
                next_item["session_created_at"] = now
                next_item["last_used_at"] = now
                self._items[index] = next_item
                self._save()
                return self._public_item(next_item), session_token
        return None

    def update_key(
        self,
        key_id: str,
        updates: dict[str, object],
        *,
        role: AuthRole | None = None,
    ) -> dict[str, object] | None:
        normalized_id = self._clean(key_id)
        if not normalized_id:
            return None
        with self._lock:
            for index, item in enumerate(self._items):
                if item.get("id") != normalized_id:
                    continue
                if role is not None and item.get("role") != role:
                    return None
                next_item = dict(item)
                if "name" in updates and updates.get("name") is not None:
                    next_item["name"] = self._clean(updates.get("name")) or next_item.get("name") or "普通用户"
                if "enabled" in updates and updates.get("enabled") is not None:
                    next_item["enabled"] = bool(updates.get("enabled"))
                self._items[index] = next_item
                self._save()
                return self._public_item(next_item)
        return None

    def adjust_balance(self, key_id: str, amount: float, *, role: AuthRole | None = "user") -> dict[str, object] | None:
        normalized_id = self._clean(key_id)
        delta = _amount(amount)
        if not normalized_id or delta == 0:
            return None
        with self._lock:
            for index, item in enumerate(self._items):
                if item.get("id") != normalized_id:
                    continue
                if role is not None and item.get("role") != role:
                    return None
                current_balance = _amount(item.get("balance", 0))
                next_balance = _amount(current_balance + delta)
                if next_balance < 0:
                    raise InsufficientBalanceError(abs(delta), current_balance)
                next_item = dict(item)
                next_item["balance"] = max(0.0, next_balance)
                if delta > 0:
                    next_item["total_recharged"] = _amount(next_item.get("total_recharged", 0)) + delta
                self._items[index] = next_item
                self._save()
                return self._public_item(next_item)
        return None

    def charge_key(self, key_id: str, amount: float) -> dict[str, object]:
        normalized_id = self._clean(key_id)
        cost = _amount(amount)
        if not normalized_id or cost <= 0:
            raise ValueError("invalid billing amount")
        with self._lock:
            for index, item in enumerate(self._items):
                if item.get("id") != normalized_id or item.get("role") != "user":
                    continue
                balance = _amount(item.get("balance", 0))
                if balance + 1e-9 < cost:
                    raise InsufficientBalanceError(cost, balance)
                next_item = dict(item)
                next_item["balance"] = _amount(balance - cost)
                next_item["total_used"] = _amount(next_item.get("total_used", 0)) + cost
                self._items[index] = next_item
                self._save()
                return self._public_item(next_item)
        raise ValueError("user key not found")

    def refund_key(self, key_id: str, amount: float) -> dict[str, object] | None:
        normalized_id = self._clean(key_id)
        refund = _amount(amount)
        if not normalized_id or refund <= 0:
            return None
        with self._lock:
            for index, item in enumerate(self._items):
                if item.get("id") != normalized_id or item.get("role") != "user":
                    continue
                next_item = dict(item)
                next_item["balance"] = _amount(next_item.get("balance", 0)) + refund
                next_item["total_used"] = max(0.0, _amount(next_item.get("total_used", 0)) - refund)
                self._items[index] = next_item
                self._save()
                return self._public_item(next_item)
        return None

    def delete_key(self, key_id: str, *, role: AuthRole | None = None) -> bool:
        normalized_id = self._clean(key_id)
        if not normalized_id:
            return False
        with self._lock:
            before = len(self._items)
            self._items = [
                item
                for item in self._items
                if not (item.get("id") == normalized_id and (role is None or item.get("role") == role))
            ]
            if len(self._items) == before:
                return False
            self._save()
            return True

    def authenticate(self, raw_key: str) -> dict[str, object] | None:
        candidate = self._clean(raw_key)
        if not candidate:
            return None
        candidate_hash = _hash_key(candidate)
        with self._lock:
            for index, item in enumerate(self._items):
                if not bool(item.get("enabled", True)):
                    continue
                key_hash = self._clean(item.get("key_hash"))
                session_token_hash = self._clean(item.get("session_token_hash"))
                matched = bool(key_hash and hmac.compare_digest(key_hash, candidate_hash)) or bool(
                    session_token_hash and hmac.compare_digest(session_token_hash, candidate_hash)
                )
                if not matched:
                    continue
                next_item = dict(item)
                now = datetime.now(timezone.utc)
                next_item["last_used_at"] = now.isoformat()
                self._items[index] = next_item
                item_id = self._clean(next_item.get("id"))
                last_flush_at = self._last_used_flush_at.get(item_id)
                if last_flush_at is None or (now - last_flush_at).total_seconds() >= 60:
                    try:
                        self._save()
                        self._last_used_flush_at[item_id] = now
                    except Exception:
                        pass
                return self._public_item(next_item)
        return None


auth_service = AuthService(config.get_storage_backend())
