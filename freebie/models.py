"""Model mapping and multi-provider routing for Freebie."""
from typing import Any, Dict, Optional, Tuple

MODELS: Dict[str, dict] = {
    # ChatGPT Models (requires session/access token)
    "auto": {
        "provider": "auto",
        "slug": "auto",
        "desc": "Auto selector: GPT-4o when authenticated, Gemini Flash when anonymous",
    },
    "gpt-4o": {
        "provider": "openai",
        "slug": "gpt-4o",
        "desc": "GPT-4o flagship model with multimodal and reasoning capabilities",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "slug": "gpt-4o-mini",
        "desc": "Fast and efficient GPT-4o-mini model",
    },
    "gpt-4.5": {
        "provider": "openai",
        "slug": "gpt-4.5-preview",
        "desc": "OpenAI GPT-4.5 flagship research model",
    },
    "o1": {
        "provider": "openai",
        "slug": "o1",
        "desc": "OpenAI o1 reasoning model",
    },
    "o1-mini": {
        "provider": "openai",
        "slug": "o1-mini",
        "desc": "OpenAI o1-mini fast reasoning model",
    },
    "o3-mini": {
        "provider": "openai",
        "slug": "o3-mini",
        "desc": "OpenAI o3-mini latest advanced reasoning model",
    },
    # Gemini Models (Zero-auth, zero-cost, works immediately!)
    "gemini-3.6-flash": {
        "provider": "gemini",
        "slug": "gemini-3.6-flash",
        "model_id": 1,
        "think_mode": 4,
        "desc": "Gemini 3.6 Flash (zero-auth, ultra-fast responses)",
    },
    "gemini-3.7-flash": {
        "provider": "gemini",
        "slug": "gemini-3.7-flash",
        "model_id": 1,
        "think_mode": 4,
        "desc": "Latest Gemini 3.7 Flash (zero-auth)",
    },
    "gemini-3.5-flash": {
        "provider": "gemini",
        "slug": "gemini-3.5-flash",
        "model_id": 1,
        "think_mode": 4,
        "desc": "Gemini 3.5 Flash alias",
    },
    "gemini-3.5-flash-thinking": {
        "provider": "gemini",
        "slug": "gemini-3.5-flash-thinking",
        "model_id": 2,
        "think_mode": 0,
        "desc": "Gemini 3.5 Flash Thinking with deep reasoning (zero-auth)",
    },
    "gemini-flash-lite": {
        "provider": "gemini",
        "slug": "gemini-flash-lite",
        "model_id": 6,
        "think_mode": 4,
        "desc": "Lightweight Gemini Flash Lite (zero-auth)",
    },
}

ALIASES: Dict[str, str] = {
    "gpt-4": "gpt-4o",
    "gpt-3.5-turbo": "gpt-4o-mini",
    "gpt-4-turbo": "gpt-4o",
    "o1-preview": "o1",
    "gemini": "gemini-3.6-flash",
    "gemini-flash": "gemini-3.6-flash",
}


def resolve_model(
    name: str,
    default: str = "auto",
    has_openai_auth: bool = False,
) -> Tuple[str, str, str, Optional[int], Optional[int]]:
    """Resolve model name to (display_name, backend_slug, provider, model_id, think_mode).

    Returns:
      (model_name, slug, provider, gemini_model_id, gemini_think_mode)
      where provider in ("openai", "gemini")
    """
    normalized = name.lower().strip()
    think_override = None
    if "@think=" in normalized:
        normalized, think_str = normalized.rsplit("@think=", 1)
        try:
            think_override = int(think_str)
        except ValueError:
            pass

    if normalized in ALIASES:
        normalized = ALIASES[normalized]

    meta = MODELS.get(normalized)
    if not meta:
        meta = MODELS.get(default, MODELS["auto"])
        normalized = default

    provider = meta["provider"]
    if provider == "auto":
        # If user has a ChatGPT access token, route to GPT-4o; otherwise, route to Gemini Flash!
        if has_openai_auth:
            return "gpt-4o", "gpt-4o", "openai", None, None
        return "gemini-3.6-flash", "gemini-3.6-flash", "gemini", 1, 4

    if provider == "gemini":
        model_id = meta.get("model_id", 1)
        think_mode = think_override if think_override is not None else meta.get("think_mode", 4)
        return normalized, meta["slug"], "gemini", model_id, think_mode

    return normalized, meta["slug"], "openai", None, None
