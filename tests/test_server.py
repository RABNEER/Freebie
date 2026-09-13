import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

from freegpt.server import app
from freegpt.config import CONFIG

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "FreeGPT"
    assert "gpt-4o" in data["models"]
    assert "gemini-3.6-flash" in data["models"]

def test_list_models_endpoint():
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    ids = [m["id"] for m in data["data"]]
    assert "auto" in ids
    assert "gpt-4o" in ids
    assert "gemini-3.6-flash" in ids
    assert "gemini-3.5-flash-thinking" in ids

def test_chat_completions_gemini_zero_auth():
    """Test that requests for Gemini Flash (or auto without token) route to Gemini."""
    with patch("freegpt.server.get_gemini_client") as mock_get_gemini:
        mock_instance = AsyncMock()
        mock_instance.generate_text.return_value = "Hello from Gemini Flash!"
        mock_get_gemini.return_value = mock_instance

        payload = {
            "model": "auto",  # Default without auth routes to Gemini Flash
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False
        }
        resp = client.post("/v1/chat/completions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello from Gemini Flash!"
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert data["choices"][0]["finish_reason"] == "stop"

def test_chat_completions_chatgpt_authenticated():
    """Test that requests for ChatGPT with token route to ChatGPT."""
    with patch("freegpt.server.get_chatgpt_client") as mock_get_chatgpt:
        mock_instance = AsyncMock()
        mock_instance.generate_text.return_value = ("Hello from ChatGPT!", "")
        mock_get_chatgpt.return_value = mock_instance

        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False
        }
        resp = client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer eyJhbGciOiJSUzI1NiIs..."}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello from ChatGPT!"

def test_chat_completions_with_tool_calling():
    with patch("freegpt.server.get_gemini_client") as mock_get_gemini:
        mock_instance = AsyncMock()
        mock_instance.generate_text.return_value = (
            'I will check the weather.\n```tool_call\n{"name": "get_weather", "arguments": {"city": "Berlin"}}\n```'
        )
        mock_get_gemini.return_value = mock_instance

        payload = {
            "model": "gemini-3.6-flash",
            "messages": [{"role": "user", "content": "What is the weather in Berlin?"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current weather",
                        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
                    }
                }
            ],
            "stream": False
        }
        resp = client.post("/v1/chat/completions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["choices"][0]["finish_reason"] == "tool_calls"
        assert len(data["choices"][0]["message"]["tool_calls"]) == 1
        call = data["choices"][0]["message"]["tool_calls"][0]
        assert call["function"]["name"] == "get_weather"
        assert "Berlin" in call["function"]["arguments"]
