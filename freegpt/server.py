"""FastAPI server implementing OpenAI-compatible endpoints with ChatGPT & Gemini support."""
import json
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import __version__
from .auth import auth_manager
from .client import ChatGPTClient
from .config import CONFIG
from .gemini import GeminiClient
from .models import MODELS, resolve_model
from .protocol import build_conversation_payload, messages_to_prompt, parse_tool_calls

app = FastAPI(
    title="FreeGPT",
    version=__version__,
    description="High-performance OpenAI-compatible API proxy for ChatGPT & Gemini Web",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_chatgpt_client: Optional[ChatGPTClient] = None
_gemini_client: Optional[GeminiClient] = None


def get_chatgpt_client() -> ChatGPTClient:
    global _chatgpt_client
    if _chatgpt_client is None:
        _chatgpt_client = ChatGPTClient(proxy=CONFIG.get("proxy"))
    return _chatgpt_client


def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient(proxy=CONFIG.get("proxy"))
    return _gemini_client


# ─── Auth Dependency ──────────────────────────────────────────────────────────


def verify_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
) -> Optional[str]:
    """Verify client API key against configured api_keys."""
    configured_keys = CONFIG.get("api_keys", [])
    if not configured_keys:
        return None

    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif x_api_key:
        token = x_api_key.strip()

    if not token or token not in configured_keys:
        if token and token.startswith("eyJ"):
            return token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return token


def resolve_upstream_token(
    authorization: Optional[str] = Header(None),
    x_access_token: Optional[str] = Header(None),
) -> Optional[str]:
    """Resolve upstream ChatGPT Bearer access token."""
    if x_access_token:
        return x_access_token.strip()

    if authorization and authorization.startswith("Bearer "):
        tok = authorization[7:].strip()
        if tok.startswith("eyJ"):
            return tok

    return auth_manager.refresh_access_token_if_needed(CONFIG.get("proxy"))


# ─── Pydantic Request Models ──────────────────────────────────────────────────


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="auto")
    messages: List[Dict[str, Any]]
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/")
@app.get("/health")
async def health_check():
    """Service status and capability metadata."""
    upstream_auth = bool(auth_manager.refresh_access_token_if_needed(CONFIG.get("proxy")))
    return {
        "status": "ok",
        "service": "FreeGPT",
        "version": __version__,
        "models": list(MODELS.keys()),
        "authenticated_upstream": upstream_auth,
        "proxy_configured": bool(CONFIG.get("proxy")),
        "default_mode": "GPT-4o" if upstream_auth else "Gemini Flash (Zero-auth)",
    }


@app.get("/v1/models")
@app.get("/models")
async def list_models(_: Optional[str] = Depends(verify_api_key)):
    """OpenAI-compatible models listing."""
    now = int(time.time())
    data = [
        {
            "id": name,
            "object": "model",
            "created": now,
            "owned_by": meta.get("provider", "openai"),
            "permission": [],
            "root": name,
            "parent": None,
            "description": meta["desc"],
        }
        for name, meta in MODELS.items()
    ]
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest,
    _: Optional[str] = Depends(verify_api_key),
    upstream_token: Optional[str] = Depends(resolve_upstream_token),
):
    """OpenAI-compatible chat completions endpoint."""
    model_name, model_slug, provider, gemini_id, think_mode = resolve_model(
        req.model,
        CONFIG.get("default_model", "auto"),
        has_openai_auth=bool(upstream_token),
    )
    prompt = messages_to_prompt(req.messages, req.tools)

    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    cid = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())

    # ══════════════════════════════════════════════════════════════════════════
    # PROVIDER: GEMINI (Zero-auth, instantaneous)
    # ══════════════════════════════════════════════════════════════════════════
    if provider == "gemini":
        gemini_client = get_gemini_client()

        if req.stream:
            async def gemini_event_generator() -> AsyncGenerator[str, None]:
                first_chunk = {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(first_chunk)}\n\n"

                try:
                    async for delta_text, is_done in gemini_client.stream_generation(
                        prompt, model_id=gemini_id or 1, think_mode=think_mode or 4
                    ):
                        if is_done:
                            break
                        if delta_text:
                            chunk = {
                                "id": cid,
                                "object": "chat.completion.chunk",
                                "created": created_ts,
                                "model": model_name,
                                "choices": [{"index": 0, "delta": {"content": delta_text}, "finish_reason": None}],
                            }
                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

                    final_chunk = {
                        "id": cid,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    err_chunk = {"error": {"message": str(e), "type": "upstream_error"}}
                    yield f"data: {json.dumps(err_chunk)}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(
                gemini_event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # Non-streaming Gemini
        try:
            raw_text = await gemini_client.generate_text(
                prompt, model_id=gemini_id or 1, think_mode=think_mode or 4
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Gemini upstream error: {e}")

        tool_calls = None
        clean_text = raw_text
        if req.tools and raw_text:
            clean_text, tool_calls = parse_tool_calls(raw_text)

        msg: Dict[str, Any] = {"role": "assistant", "content": clean_text or None}
        if tool_calls:
            msg["tool_calls"] = tool_calls

        finish_reason = "tool_calls" if tool_calls else "stop"
        prompt_tokens = len(prompt) // 4
        comp_tokens = len(clean_text) // 4

        return {
            "id": cid,
            "object": "chat.completion",
            "created": created_ts,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": msg,
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": comp_tokens,
                "total_tokens": prompt_tokens + comp_tokens,
            },
        }

    # ══════════════════════════════════════════════════════════════════════════
    # PROVIDER: CHATGPT (Requires access token or session token)
    # ══════════════════════════════════════════════════════════════════════════
    chatgpt_client = get_chatgpt_client()
    payload = build_conversation_payload(
        prompt=prompt,
        model_slug=model_slug,
        history_disabled=CONFIG.get("history_and_training_disabled", True),
    )

    if req.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            first_chunk = {
                "id": cid,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": model_name,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(first_chunk)}\n\n"

            try:
                async for content_delta, reasoning_delta, is_done in chatgpt_client.stream_conversation(
                    payload, access_token=upstream_token
                ):
                    if is_done:
                        break

                    delta_obj = {}
                    if content_delta:
                        delta_obj["content"] = content_delta
                    if reasoning_delta:
                        delta_obj["reasoning_content"] = reasoning_delta

                    if delta_obj:
                        chunk = {
                            "id": cid,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model_name,
                            "choices": [{"index": 0, "delta": delta_obj, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

                final_chunk = {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                err_chunk = {"error": {"message": str(e), "type": "upstream_error"}}
                yield f"data: {json.dumps(err_chunk)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming ChatGPT response
    try:
        raw_text, raw_reasoning = await chatgpt_client.generate_text(payload, access_token=upstream_token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ChatGPT upstream error: {e}")

    tool_calls = None
    clean_text = raw_text
    if req.tools and raw_text:
        clean_text, tool_calls = parse_tool_calls(raw_text)

    msg: Dict[str, Any] = {"role": "assistant", "content": clean_text or None}
    if raw_reasoning:
        msg["reasoning_content"] = raw_reasoning
    if tool_calls:
        msg["tool_calls"] = tool_calls

    finish_reason = "tool_calls" if tool_calls else "stop"

    prompt_tokens = len(prompt) // 4
    comp_tokens = (len(clean_text) + len(raw_reasoning)) // 4

    return {
        "id": cid,
        "object": "chat.completion",
        "created": created_ts,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": msg,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": comp_tokens,
            "total_tokens": prompt_tokens + comp_tokens,
        },
    }
