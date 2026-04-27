from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict

from api.support import require_admin, require_identity, resolve_image_base_url
from services.config import config
from services.auth_service import auth_service
from services.log_service import LOG_TYPE_ACCOUNT, log_service
from services.image_service import list_images
from services.proxy_service import test_proxy


class SettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")


class ProxyTestRequest(BaseModel):
    url: str = ""


class PasswordLoginRequest(BaseModel):
    username: str = ""
    password: str = ""


class RegisterRequest(BaseModel):
    username: str = ""
    password: str = ""
    name: str = ""


def _login_payload(identity: dict[str, object], app_version: str, key: str | None = None) -> dict[str, object]:
    payload = {
        "ok": True,
        "version": app_version,
        "role": identity.get("role"),
        "subject_id": identity.get("id"),
        "name": identity.get("name"),
        "balance": identity.get("balance"),
        "total_used": identity.get("total_used"),
        "total_recharged": identity.get("total_recharged"),
        "username": identity.get("username"),
    }
    if key:
        payload["key"] = key
    return payload

def create_router(app_version: str) -> APIRouter:
    router = APIRouter()

    @router.post("/auth/login")
    async def login(authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        return _login_payload(identity, app_version)

    @router.post("/auth/password-login")
    async def password_login(body: PasswordLoginRequest):
        result = auth_service.login_with_password(username=body.username, password=body.password)
        if result is None:
            raise HTTPException(status_code=401, detail={"error": "用户名或密码错误"})
        identity, session_token = result
        return _login_payload(identity, app_version, session_token)

    @router.post("/auth/register")
    async def register(body: RegisterRequest):
        try:
            identity, session_token = auth_service.create_registered_user(
                username=body.username,
                password=body.password,
                name=body.name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc
        log_service.add(
            LOG_TYPE_ACCOUNT,
            "用户自助注册",
            {"key_id": identity.get("id"), "key_name": identity.get("name"), "username": identity.get("username")},
        )
        return _login_payload(identity, app_version, session_token)

    @router.get("/api/me")
    async def get_me(authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        return {"item": identity}

    @router.get("/version")
    async def get_version():
        return {"version": app_version}

    @router.get("/api/settings")
    async def get_settings(authorization: str | None = Header(default=None)):
        require_admin(authorization)
        return {"config": config.get()}

    @router.post("/api/settings")
    async def save_settings(body: SettingsUpdateRequest, authorization: str | None = Header(default=None)):
        require_admin(authorization)
        return {"config": config.update(body.model_dump(mode="python"))}

    @router.get("/api/images")
    async def get_images(request: Request, start_date: str = "", end_date: str = "", authorization: str | None = Header(default=None)):
        require_admin(authorization)
        return list_images(resolve_image_base_url(request), start_date=start_date.strip(), end_date=end_date.strip())

    @router.get("/api/logs")
    async def get_logs(type: str = "", start_date: str = "", end_date: str = "", authorization: str | None = Header(default=None)):
        require_admin(authorization)
        return {"items": log_service.list(type=type.strip(), start_date=start_date.strip(), end_date=end_date.strip())}

    @router.post("/api/proxy/test")
    async def test_proxy_endpoint(body: ProxyTestRequest, authorization: str | None = Header(default=None)):
        require_admin(authorization)
        candidate = (body.url or "").strip() or config.get_proxy_settings()
        if not candidate:
            raise HTTPException(status_code=400, detail={"error": "proxy url is required"})
        return {"result": await run_in_threadpool(test_proxy, candidate)}

    @router.get("/api/storage/info")
    async def get_storage_info(authorization: str | None = Header(default=None)):
        require_admin(authorization)
        storage = config.get_storage_backend()
        return {
            "backend": storage.get_backend_info(),
            "health": storage.health_check(),
        }

    return router

