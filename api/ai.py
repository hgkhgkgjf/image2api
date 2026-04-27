from __future__ import annotations

from datetime import datetime
import time

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from api.support import raise_image_quota_error, require_identity, resolve_image_base_url
from services.account_service import account_service
from services.auth_service import InsufficientBalanceError, auth_service
from services.chatgpt_service import ChatGPTService, ImageGenerationError
from services.image_prompt_templates import list_image_prompt_category_groups
from services.image_history_service import image_history_service
from services.log_service import (
    LOG_TYPE_CALL,
    log_service,
)
from utils.helper import anthropic_sse_stream, is_image_chat_request, sse_json_stream

PRICE_PROMPT_STANDARDIZE = 0.1
PRICE_IMAGE_GENERATE = 1.0
PRICE_IMAGE_EDIT = 2.0
PRICE_TEXT_CALL = 0.1
PRICE_IMAGE_CHAT = 1.0


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = "gpt-image-2"
    n: int = Field(default=1, ge=1, le=4)
    size: str | None = None
    response_format: str = "b64_json"
    history_disabled: bool = True
    stream: bool | None = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str | None = None
    prompt: str | None = None
    n: int | None = None
    stream: bool | None = None
    modalities: list[str] | None = None
    messages: list[dict[str, object]] | None = None


class ResponseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str | None = None
    input: object | None = None
    tools: list[dict[str, object]] | None = None
    tool_choice: object | None = None
    stream: bool | None = None


class ImageConversationsRequest(BaseModel):
    items: list[dict[str, object]] = Field(default_factory=list)


class ImagePromptStandardizeRequest(BaseModel):
    input: str | None = None
    prompt: str | None = None
    category: str | None = "auto"
    mode: str | None = "generate"
    size: str | None = None


class AnthropicMessageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str | None = None
    messages: list[dict[str, object]] | None = None
    system: object | None = None
    stream: bool | None = None


def _money(value: object) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return 0.0


def _identity_detail(identity: dict[str, object]) -> dict[str, object]:
    return {"key_id": identity.get("id"), "key_name": identity.get("name"), "role": identity.get("role")}


def _is_billable(identity: dict[str, object]) -> bool:
    return identity.get("role") == "user" and bool(str(identity.get("id") or "").strip())


def _reserve_billing(identity: dict[str, object], amount: float, reason: str) -> dict[str, object] | None:
    cost = _money(amount)
    if not _is_billable(identity) or cost <= 0:
        return None
    key_id = str(identity.get("id") or "").strip()
    try:
        item = auth_service.charge_key(key_id, cost)
    except InsufficientBalanceError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "error": f"余额不足，需要 {exc.required:g} 点，当前 {exc.balance:g} 点，请联系管理员充值",
                "code": "insufficient_balance",
                "required": exc.required,
                "balance": exc.balance,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"error": "user key not found"}) from exc
    return {
        "amount": cost,
        "reason": reason,
        "status": "charged",
        "balance_after": item.get("balance"),
    }


def _refund_billing(identity: dict[str, object], billing: dict[str, object] | None) -> dict[str, object] | None:
    if not billing or billing.get("status") == "refunded":
        return billing
    amount = _money(billing.get("amount"))
    if amount <= 0 or not _is_billable(identity):
        return billing
    try:
        item = auth_service.refund_key(str(identity.get("id") or "").strip(), amount)
    except Exception:
        return {**billing, "status": "refund_failed"}
    return {
        **billing,
        "status": "refunded",
        "balance_after": item.get("balance") if item else billing.get("balance_after"),
    }


def _collect_urls(value: object) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "url" and isinstance(item, str):
                urls.append(item)
            elif key == "urls" and isinstance(item, list):
                urls.extend(str(url) for url in item if isinstance(url, str))
            else:
                urls.extend(_collect_urls(item))
    elif isinstance(value, list):
        for item in value:
            urls.extend(_collect_urls(item))
    return urls


def _log_call(
    summary: str,
    identity: dict[str, object],
    endpoint: str,
    model: str,
    started: float,
    result: object = None,
    status: str = "success",
    billing: dict[str, object] | None = None,
) -> None:
    detail = {
        **_identity_detail(identity),
        "endpoint": endpoint,
        "model": model,
        "started_at": datetime.fromtimestamp(started).strftime("%Y-%m-%d %H:%M:%S"),
        "ended_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration_ms": int((time.time() - started) * 1000),
        "status": status,
    }
    if billing:
        detail.update(
            {
                "billing_amount": billing.get("amount"),
                "billing_reason": billing.get("reason"),
                "billing_status": billing.get("status"),
                "balance_after": billing.get("balance_after"),
            }
        )
    urls = _collect_urls(result)
    if urls:
        detail["urls"] = list(dict.fromkeys(urls))
    log_service.add(LOG_TYPE_CALL, summary, detail)


def _stream_with_log(
    items,
    summary: str,
    identity: dict[str, object],
    endpoint: str,
    model: str,
    started: float,
    billing: dict[str, object] | None = None,
):
    urls: list[str] = []
    failed = False
    try:
        for item in items:
            urls.extend(_collect_urls(item))
            yield item
    except Exception:
        failed = True
        refunded_billing = _refund_billing(identity, billing)
        _log_call(
            summary.replace("结束", "失败"),
            identity,
            endpoint,
            model,
            started,
            {"urls": list(dict.fromkeys(urls))},
            "failed",
            refunded_billing,
        )
        raise
    finally:
        if not failed:
            _log_call(summary, identity, endpoint, model, started, {"urls": list(dict.fromkeys(urls))}, billing=billing)


def create_router(chatgpt_service: ChatGPTService) -> APIRouter:
    router = APIRouter()

    @router.get("/v1/models")
    async def list_models(authorization: str | None = Header(default=None)):
        require_identity(authorization)
        try:
            return await run_in_threadpool(chatgpt_service.list_models)
        except Exception as exc:
            raise HTTPException(status_code=502, detail={"error": str(exc)}) from exc

    @router.get("/api/image-conversations")
    async def get_image_conversations(authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        subject = f"{identity.get('role') or 'user'}:{identity.get('id') or 'default'}"
        return {"items": image_history_service.get_items(subject)}

    @router.post("/api/image-conversations")
    async def save_image_conversations(
            body: ImageConversationsRequest,
            authorization: str | None = Header(default=None),
    ):
        identity = require_identity(authorization)
        subject = f"{identity.get('role') or 'user'}:{identity.get('id') or 'default'}"
        items = image_history_service.save_items(subject, body.items)
        return {"items": items}

    @router.delete("/api/image-conversations")
    async def clear_image_conversations(authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        subject = f"{identity.get('role') or 'user'}:{identity.get('id') or 'default'}"
        image_history_service.clear_items(subject)
        return {"items": []}

    @router.get("/api/image-prompts/categories")
    async def list_image_prompt_categories(authorization: str | None = Header(default=None)):
        require_identity(authorization)
        return {
            "source": "YouMind-OpenLab/awesome-gpt-image-2",
            "groups": list_image_prompt_category_groups(),
        }

    @router.post("/api/image-prompts/standardize")
    async def standardize_image_prompt(
            body: ImagePromptStandardizeRequest,
            authorization: str | None = Header(default=None),
    ):
        identity = require_identity(authorization)
        started = time.time()
        prompt = str(body.input or body.prompt or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail={"error": "prompt is required"})
        billing = _reserve_billing(identity, PRICE_PROMPT_STANDARDIZE, "提示词标准化")
        try:
            result = await run_in_threadpool(
                chatgpt_service.standardize_image_prompt,
                prompt,
                body.category or "auto",
                body.mode or "generate",
                body.size,
            )
            _log_call("GPT5.4 提示词标准化完成", identity, "/api/image-prompts/standardize", "gpt-5.4", started, result, billing=billing)
            return result
        except ValueError as exc:
            billing = _refund_billing(identity, billing)
            _log_call("GPT5.4 提示词标准化失败", identity, "/api/image-prompts/standardize", "gpt-5.4", started, {"error": str(exc)}, "failed", billing)
            raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc
        except Exception as exc:
            billing = _refund_billing(identity, billing)
            _log_call("GPT5.4 提示词标准化失败", identity, "/api/image-prompts/standardize", "gpt-5.4", started, {"error": str(exc)}, "failed", billing)
            raise HTTPException(status_code=502, detail={"error": str(exc)}) from exc

    @router.post("/v1/images/generations")
    async def generate_images(
            body: ImageGenerationRequest,
            request: Request,
            authorization: str | None = Header(default=None),
    ):
        identity = require_identity(authorization)
        started = time.time()
        base_url = resolve_image_base_url(request)
        cost = PRICE_IMAGE_GENERATE * body.n
        if body.stream:
            try:
                await run_in_threadpool(account_service.get_available_access_token)
            except RuntimeError as exc:
                raise_image_quota_error(exc)
            billing = _reserve_billing(identity, cost, f"文生图 {body.n} 张")
            return StreamingResponse(
                sse_json_stream(
                    _stream_with_log(
                        chatgpt_service.stream_image_generation(
                            body.prompt, body.model, body.n, body.size, body.response_format, base_url
                        ),
                        "文生图流式调用结束",
                        identity,
                        "/v1/images/generations",
                        body.model,
                        started,
                        billing,
                    )
                ),
                media_type="text/event-stream",
            )
        billing = _reserve_billing(identity, cost, f"文生图 {body.n} 张")
        try:
            result = await run_in_threadpool(
                chatgpt_service.generate_with_pool, body.prompt, body.model, body.n, body.size, body.response_format, base_url
            )
            _log_call("文生图调用完成", identity, "/v1/images/generations", body.model, started, result, billing=billing)
            return result
        except ImageGenerationError as exc:
            billing = _refund_billing(identity, billing)
            _log_call("文生图调用失败", identity, "/v1/images/generations", body.model, started, {"error": str(exc)}, "failed", billing)
            raise_image_quota_error(exc)

    @router.post("/v1/images/edits")
    async def edit_images(
            request: Request,
            authorization: str | None = Header(default=None),
            image: list[UploadFile] | None = File(default=None),
            image_list: list[UploadFile] | None = File(default=None, alias="image[]"),
            prompt: str = Form(...),
            model: str = Form(default="gpt-image-2"),
            n: int = Form(default=1),
            size: str | None = Form(default=None),
            response_format: str = Form(default="b64_json"),
            stream: bool | None = Form(default=None),
    ):
        identity = require_identity(authorization)
        started = time.time()
        if n < 1 or n > 4:
            raise HTTPException(status_code=400, detail={"error": "n must be between 1 and 4"})
        uploads = [*(image or []), *(image_list or [])]
        if not uploads:
            raise HTTPException(status_code=400, detail={"error": "image file is required"})
        base_url = resolve_image_base_url(request)
        images: list[tuple[bytes, str, str]] = []
        for upload in uploads:
            image_data = await upload.read()
            if not image_data:
                raise HTTPException(status_code=400, detail={"error": "image file is empty"})
            images.append((image_data, upload.filename or "image.png", upload.content_type or "image/png"))
        cost = PRICE_IMAGE_EDIT * n
        if stream:
            if not account_service.has_available_account():
                raise_image_quota_error(RuntimeError("no available image quota"))
            billing = _reserve_billing(identity, cost, f"图生图 {n} 张")
            return StreamingResponse(
                sse_json_stream(_stream_with_log(
                    chatgpt_service.stream_image_edit(prompt, images, model, n, size, response_format, base_url),
                    "图生图流式调用结束",
                    identity,
                    "/v1/images/edits",
                    model,
                    started,
                    billing,
                )),
                media_type="text/event-stream",
            )
        billing = _reserve_billing(identity, cost, f"图生图 {n} 张")
        try:
            result = await run_in_threadpool(
                chatgpt_service.edit_with_pool, prompt, images, model, n, size, response_format, base_url
            )
            _log_call("图生图调用完成", identity, "/v1/images/edits", model, started, result, billing=billing)
            return result
        except ImageGenerationError as exc:
            billing = _refund_billing(identity, billing)
            _log_call("图生图调用失败", identity, "/v1/images/edits", model, started, {"error": str(exc)}, "failed", billing)
            raise_image_quota_error(exc)

    @router.post("/v1/chat/completions")
    async def create_chat_completion(body: ChatCompletionRequest, authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        started = time.time()
        payload = body.model_dump(mode="python")
        model = str(payload.get("model") or "auto")
        image_chat = is_image_chat_request(payload)
        cost = PRICE_IMAGE_CHAT if image_chat else PRICE_TEXT_CALL
        if bool(payload.get("stream")):
            if image_chat:
                try:
                    await run_in_threadpool(account_service.get_available_access_token)
                except RuntimeError as exc:
                    raise_image_quota_error(exc)
            billing = _reserve_billing(identity, cost, "图片聊天调用" if image_chat else "文本聊天调用")
            return StreamingResponse(
                sse_json_stream(_stream_with_log(chatgpt_service.stream_chat_completion(payload), "文本生成流式调用结束", identity, "/v1/chat/completions", model, started, billing)),
                media_type="text/event-stream",
            )
        billing = _reserve_billing(identity, cost, "图片聊天调用" if image_chat else "文本聊天调用")
        try:
            result = await run_in_threadpool(chatgpt_service.create_chat_completion, payload)
            _log_call("文本生成调用完成", identity, "/v1/chat/completions", model, started, result, billing=billing)
            return result
        except Exception as exc:
            billing = _refund_billing(identity, billing)
            _log_call("文本生成调用失败", identity, "/v1/chat/completions", model, started, {"error": str(exc)}, "failed", billing)
            raise

    @router.post("/v1/responses")
    async def create_response(body: ResponseCreateRequest, authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        started = time.time()
        payload = body.model_dump(mode="python")
        model = str(payload.get("model") or "auto")
        billing = _reserve_billing(identity, PRICE_TEXT_CALL, "Responses 调用")
        if bool(payload.get("stream")):
            return StreamingResponse(
                sse_json_stream(_stream_with_log(chatgpt_service.stream_response(payload), "Responses 流式调用结束", identity, "/v1/responses", model, started, billing)),
                media_type="text/event-stream",
            )
        try:
            result = await run_in_threadpool(chatgpt_service.create_response, payload)
            _log_call("Responses 调用完成", identity, "/v1/responses", model, started, result, billing=billing)
            return result
        except Exception as exc:
            billing = _refund_billing(identity, billing)
            _log_call("Responses 调用失败", identity, "/v1/responses", model, started, {"error": str(exc)}, "failed", billing)
            raise

    @router.post("/v1/messages")
    async def create_message(
            body: AnthropicMessageRequest,
            authorization: str | None = Header(default=None),
            x_api_key: str | None = Header(default=None, alias="x-api-key"),
            anthropic_version: str | None = Header(default=None, alias="anthropic-version"),
    ):
        identity = require_identity(authorization or (f"Bearer {x_api_key}" if x_api_key else None))
        started = time.time()
        payload = body.model_dump(mode="python")
        model = str(payload.get("model") or "auto")
        billing = _reserve_billing(identity, PRICE_TEXT_CALL, "Messages 调用")
        if bool(payload.get("stream")):
            return StreamingResponse(
                anthropic_sse_stream(_stream_with_log(chatgpt_service.stream_message(payload), "Messages 流式调用结束", identity, "/v1/messages", model, started, billing)),
                media_type="text/event-stream",
            )
        try:
            result = await run_in_threadpool(chatgpt_service.create_message, payload)
            _log_call("Messages 调用完成", identity, "/v1/messages", model, started, result, billing=billing)
            return result
        except Exception as exc:
            billing = _refund_billing(identity, billing)
            _log_call("Messages 调用失败", identity, "/v1/messages", model, started, {"error": str(exc)}, "failed", billing)
            raise

    return router
