import os
import tempfile
import json
import pytest
from freegpt.config import CONFIG, DEFAULT_CONFIG, load_config, find_config

def test_default_config():
    assert DEFAULT_CONFIG["port"] == 8080
    assert DEFAULT_CONFIG["host"] == "0.0.0.0"
    assert DEFAULT_CONFIG["history_and_training_disabled"] is True
    assert DEFAULT_CONFIG["impersonate"] == "chrome124"

def test_load_config_file():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump({"port": 9090, "default_model": "gpt-4o"}, f)
        temp_path = f.name

    try:
        cfg = load_config(temp_path)
        assert cfg["port"] == 9090
        assert cfg["default_model"] == "gpt-4o"
    finally:
        os.remove(temp_path)

def test_env_override(monkeypatch):
    monkeypatch.setenv("FREEGPT_PORT", "7777")
    monkeypatch.setenv("FREEGPT_API_KEYS", "key1,key2")
    cfg = load_config()
    assert cfg["port"] == 7777
    assert cfg["api_keys"] == ["key1", "key2"]
