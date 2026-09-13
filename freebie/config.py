"""Configuration management for Freebie."""
import json
import os
from typing import Any, Dict, List, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 8080,
    "api_keys": [],
    "proxy": None,
    "default_model": "auto",
    "access_token": None,
    "session_token": None,
    "cookie_file": None,
    "request_timeout_sec": 120,
    "history_and_training_disabled": True,
    "impersonate": "chrome124",
    "log_requests": True,
}

CONFIG: Dict[str, Any] = dict(DEFAULT_CONFIG)


def _get_env(*keys: str) -> Optional[str]:
    """Retrieve first matched environment variable."""
    for k in keys:
        if k in os.environ:
            return os.environ[k]
    return None


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file and environment variables."""
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            CONFIG.update(file_data)

    # Environment variable overrides (supports both FREEBIE_* and FREEGPT_*)
    port_env = _get_env("FREEBIE_PORT", "FREEGPT_PORT")
    if port_env:
        CONFIG["port"] = int(port_env)

    host_env = _get_env("FREEBIE_HOST", "FREEGPT_HOST")
    if host_env:
        CONFIG["host"] = host_env

    proxy_env = _get_env("FREEBIE_PROXY", "FREEGPT_PROXY")
    if proxy_env:
        CONFIG["proxy"] = proxy_env
    elif "HTTPS_PROXY" in os.environ and not CONFIG.get("proxy"):
        CONFIG["proxy"] = os.environ["HTTPS_PROXY"]
    elif "HTTP_PROXY" in os.environ and not CONFIG.get("proxy"):
        CONFIG["proxy"] = os.environ["HTTP_PROXY"]

    access_token_env = _get_env("FREEBIE_ACCESS_TOKEN", "FREEGPT_ACCESS_TOKEN")
    if access_token_env:
        CONFIG["access_token"] = access_token_env

    session_token_env = _get_env("FREEBIE_SESSION_TOKEN", "FREEGPT_SESSION_TOKEN")
    if session_token_env:
        CONFIG["session_token"] = session_token_env

    cookie_file_env = _get_env("FREEBIE_COOKIE_FILE", "FREEGPT_COOKIE_FILE")
    if cookie_file_env:
        CONFIG["cookie_file"] = cookie_file_env

    api_keys_env = _get_env("FREEBIE_API_KEYS", "FREEGPT_API_KEYS")
    if api_keys_env:
        CONFIG["api_keys"] = [k.strip() for k in api_keys_env.split(",") if k.strip()]

    return CONFIG


def find_config() -> Optional[str]:
    """Search for configuration file in common standard paths."""
    candidates = [
        "./config.json",
        os.path.expanduser("~/.config/freebie/config.json"),
        os.path.expanduser("~/.config/freegpt/config.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None
