"""Configuration management for FreeGPT."""
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


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file and environment variables."""
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            CONFIG.update(file_data)

    # Environment variable overrides
    if "FREEGPT_PORT" in os.environ:
        CONFIG["port"] = int(os.environ["FREEGPT_PORT"])
    if "FREEGPT_HOST" in os.environ:
        CONFIG["host"] = os.environ["FREEGPT_HOST"]
    if "FREEGPT_PROXY" in os.environ:
        CONFIG["proxy"] = os.environ["FREEGPT_PROXY"]
    elif "HTTPS_PROXY" in os.environ and not CONFIG.get("proxy"):
        CONFIG["proxy"] = os.environ["HTTPS_PROXY"]
    elif "HTTP_PROXY" in os.environ and not CONFIG.get("proxy"):
        CONFIG["proxy"] = os.environ["HTTP_PROXY"]

    if "FREEGPT_ACCESS_TOKEN" in os.environ:
        CONFIG["access_token"] = os.environ["FREEGPT_ACCESS_TOKEN"]
    if "FREEGPT_SESSION_TOKEN" in os.environ:
        CONFIG["session_token"] = os.environ["FREEGPT_SESSION_TOKEN"]
    if "FREEGPT_COOKIE_FILE" in os.environ:
        CONFIG["cookie_file"] = os.environ["FREEGPT_COOKIE_FILE"]

    api_keys_env = os.environ.get("FREEGPT_API_KEYS")
    if api_keys_env:
        CONFIG["api_keys"] = [k.strip() for k in api_keys_env.split(",") if k.strip()]

    return CONFIG


def find_config() -> Optional[str]:
    """Search for configuration file in common standard paths."""
    candidates = [
        "./config.json",
        os.path.expanduser("~/.config/freegpt/config.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None
