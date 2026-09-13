# Freebie ⚡

<div align="center">

![Freebie Banner](https://img.shields.io/badge/Freebie-v0.1.0-blue?style=for-the-badge&logo=openai&logoColor=white)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-brightgreen?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![CI Tests](https://img.shields.io/badge/Tests-15%20Passed-success?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)

**Production-grade, high-performance OpenAI-compatible REST & SSE API proxy.**  
*Reverse-engineers ChatGPT Web (`chatgpt.com`) with automated Cloudflare TLS impersonation and native Sentinel PoW solving, coupled with an instant, zero-authentication Google Gemini Flash fallback engine.*

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Zero-Auth Gemini](#-zero-auth-instant-gemini-mode) • [ChatGPT Auth](#-chatgpt-authenticated-mode) • [Extension](#-companion-chrome-extension) • [Configuration](#-configuration) • [API Reference](#-api-reference) • [Docker](#-docker-deployment)

</div>

---

## 🌟 Why Freebie?

Standard reverse-engineered proxies often face Cloudflare Turnstile blocks, brittle session extractors, or IP blocks on anonymous endpoints. **Freebie** solves this with a dual-engine architecture:

1. **Instant Out-of-the-Box Zero-Auth Mode:**  
   Don't have a ChatGPT session token? No problem. Freebie incorporates a native Google Gemini Web client. Send requests immediately without any login, token, or session cookie—enjoying blazing-fast responses and deep reasoning.
2. **Full ChatGPT Web Capabilities:**  
   Provide your ChatGPT `__Secure-next-auth.session-token`, and unlock `gpt-4o`, `gpt-4.5`, `o1`, and `o3-mini` with real-time reasoning extraction (`delta.reasoning_content`) and tool/function calling.
3. **Native Sentinel Proof-of-Work (PoW) Engine:**  
   Custom pure-Python implementation of OpenAI's client Sentinel algorithm (`FNV-1a` hashing + Murmur3 bit mixing), solving dynamic difficulty challenges in < 1ms.
4. **Browser TLS Fingerprint Impersonation:**  
   Powered by `curl_cffi` using Chrome JA3/HTTP2 TLS profiles, eliminating Cloudflare bot detection.

---

## 🚀 Key Features

- 🎯 **100% OpenAI Drop-In Compatible**: Seamlessly works with the official `openai` Python/Node SDKs, LangChain, LlamaIndex, LiteLLM, Cherry Studio, ChatBox, OpenWebUI, and NextChat.
- ⚡ **Zero-Auth Immediate Responses**: Default `auto` model falls back automatically to `gemini-3.6-flash` when unauthenticated.
- 🧠 **Deep Reasoning Stream**: Supports real-time reasoning and thought streaming for `o1`, `o3-mini`, and `gemini-3.5-flash-thinking`.
- 🛠️ **Full Function Calling**: Translates OpenAI `tools` definitions into model instructions and reconstructs `tool_calls` JSON from outputs.
- 🔄 **Autonomous Token Refresh**: Session manager continuously refreshes OAuth Bearer tokens from ChatGPT's session endpoint before expiry.
- 🧩 **1-Click Companion Chrome Extension**: Easily extract session tokens and cookies from `chatgpt.com` into Freebie with a single click.
- 🧪 **Production Quality**: Complete automated test suite covering PoW, protocol translation, routing, and SSE streaming.

---

## 🏗️ Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │             Client Application               │
                               │  (OpenAI SDK / LangChain / OpenWebUI / curl) │
                               └──────────────────────┬───────────────────────┘
                                                      │ HTTP / SSE (/v1/chat/completions)
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             Freebie Server                                              │
│                                                                                                         │
│  ┌────────────────────────┐         ┌────────────────────────┐         ┌─────────────────────────────┐  │
│  │   FastAPI ASGI Engine  │ ──────> │    Model Dispatcher    │ ──────> │   OpenAI Protocol Mapper    │  │
│  └────────────────────────┘         └───────────┬────────────┘         └─────────────────────────────┘  │
│                                                 │                                                       │
│                   ┌─────────────────────────────┴─────────────────────────────┐                         │
│                   ▼                                                           ▼                         │
│   ┌───────────────────────────────┐                           ┌───────────────────────────────┐         │
│   │     ChatGPT Web Provider      │                           │      Gemini Web Provider      │         │
│   │  (curl_cffi Chrome124 TLS)    │                           │    (Zero-Auth StreamRPC)      │         │
│   ├───────────────────────────────┤                           ├───────────────────────────────┤         │
│   │ • Sentinel PoW Solver (FNV1a) │                           │ • No credentials required     │         │
│   │ • Auto Session Token Refresh  │                           │ • Sub-second TTFT             │         │
│   │ • Reasoning Process Streamer  │                           │ • Deep Thinking Mode          │         │
│   └───────────────┬───────────────┘                           └───────────────┬───────────────┘         │
└───────────────────┼───────────────────────────────────────────────────────────┼─────────────────────────┘
                    │                                                           │
                    ▼                                                           ▼
         https://chatgpt.com/backend-api                             https://gemini.google.com/_/
```

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install freebie-api
```

### From Source

```bash
git clone https://github.com/RABNEER/Freebie.git
cd Freebie
pip install -e .
```

---

## 🏃 Quick Start

### 1. Launch Server

Start the Freebie API server:

```bash
freebie --port 8080
```

Or run via Python module:

```bash
python -m freebie --port 8080
```

The server binds to `http://127.0.0.1:8080` with documentation at `http://127.0.0.1:8080/docs`.

### 2. Verify Connectivity & Diagnostics

Run built-in automated diagnostics to test upstream connections:

```bash
freebie --check
```

---

## ⚡ Zero-Auth Instant Mode (Gemini Flash)

No account or API key? Freebie is immediately functional!

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="none"  # Any dummy key works
)

response = client.chat.completions.create(
    model="gemini-3.6-flash",  # or "auto", "gemini-3.5-flash-thinking"
    messages=[
        {"role": "user", "content": "Explain quantum entanglement in 2 sentences."}
    ]
)

print(response.choices[0].message.content)
```

### Real-Time Streaming Output

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="none")

stream = client.chat.completions.create(
    model="gemini-3.6-flash",
    messages=[{"role": "user", "content": "Write a short poem about coding."}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

### cURL

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.6-flash",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### PowerShell

```powershell
$body = @{
    model = "gemini-3.6-flash"
    messages = @(
        @{ role = "user"; content = "What is the speed of light?" }
    )
} | ConvertTo-Json

$res = Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/chat/completions" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$res.choices[0].message.content
```

---

## 🔐 ChatGPT Authenticated Mode (GPT-4o, o1, o3-mini)

To use official OpenAI ChatGPT models (`gpt-4o`, `o3-mini`, `o1`), provide your ChatGPT session token.

### Getting Your Token

1. Go to [chatgpt.com](https://chatgpt.com) and log in.
2. Open DevTools (`F12`) -> **Application** -> **Cookies** -> `https://chatgpt.com`.
3. Copy the value of `__Secure-next-auth.session-token`.
*(Or use our [1-Click Companion Chrome Extension](#-companion-chrome-extension)).*

### Starting with Token

```bash
freebie --port 8080 --session-token "YOUR_SESSION_TOKEN_HERE"
```

Or via environment variable:

```bash
export FREEBIE_SESSION_TOKEN="YOUR_SESSION_TOKEN_HERE"
freebie --port 8080
```

### Reasoning Stream with `o3-mini`

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="none")

stream = client.chat.completions.create(
    model="o3-mini",
    messages=[{"role": "user", "content": "How many r's are in strawberry?"}],
    stream=True
)

for chunk in stream:
    delta = chunk.choices[0].delta
    # Freebie streams thinking process into reasoning_content
    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
        print(f"[Thinking] {delta.reasoning_content}", end="", flush=True)
    if delta.content:
        print(delta.content, end="", flush=True)
print()
```

---

## 🛠️ Tool Calling (Function Calling)

Freebie translates OpenAI functions into system prompt specifications and automatically parses returned markdown `tool_call` blocks back into standard OpenAI `tool_calls` JSON:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="none")

response = client.chat.completions.create(
    model="gemini-3.6-flash",  # or "gpt-4o"
    messages=[{"role": "user", "content": "What is the weather in Tokyo?"}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get current weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
)

choice = response.choices[0]
if choice.finish_reason == "tool_calls":
    print("Tool invoked:", choice.message.tool_calls[0].function.name)
    print("Arguments:", choice.message.tool_calls[0].function.arguments)
```

---

## 🧩 Companion Chrome Extension

Freebie includes a lightweight companion browser extension located in [`freebie-cookie-sync-extension/`](freebie-cookie-sync-extension/):

1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select the `freebie-cookie-sync-extension` folder.
4. Navigate to [chatgpt.com](https://chatgpt.com) and click the Freebie extension icon.
5. Click **"Export Credentials"** to download `chatgpt-auth.json` or copy your token directly into Freebie.

---

## 📋 Supported Models

| Model Slug | Provider | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| **`auto`** | Smart | ❌ None | Automatically routes to `gpt-4o` (if authenticated) or `gemini-3.6-flash` (if zero-auth). |
| **`gemini-3.6-flash`** | Gemini | ❌ None | Ultra-fast responses with clean formatting. |
| **`gemini-3.7-flash`** | Gemini | ❌ None | Latest Gemini Flash edition. |
| **`gemini-3.5-flash-thinking`** | Gemini | ❌ None | Deep step-by-step reasoning with thought chain. |
| **`gemini-flash-lite`** | Gemini | ❌ None | Minimal latency lightweight model. |
| **`gpt-4o`** | ChatGPT | ✅ Session | Flagship multimodal model. |
| **`gpt-4o-mini`** | ChatGPT | ✅ Session | Fast and balanced GPT-4o variant. |
| **`gpt-4.5`** | ChatGPT | ✅ Session | OpenAI GPT-4.5 research preview model. |
| **`o1`** | ChatGPT | ✅ Session | Advanced reasoning model. |
| **`o3-mini`** | ChatGPT | ✅ Session | State-of-the-art fast reasoning model. |

---

## ⚙️ Configuration

Freebie can be configured using a `config.json` file in the working directory:

```json
{
  "host": "0.0.0.0",
  "port": 8080,
  "api_keys": ["sk-your-private-key"],
  "proxy": null,
  "default_model": "auto",
  "access_token": null,
  "session_token": null,
  "cookie_file": null,
  "request_timeout_sec": 120,
  "history_and_training_disabled": true,
  "impersonate": "chrome124"
}
```

### Environment Variables

| Variable | Description |
| :--- | :--- |
| `FREEBIE_PORT` | Port to bind server (default: `8080`) |
| `FREEBIE_HOST` | Host address (default: `0.0.0.0`) |
| `FREEBIE_CONFIG` | Custom path to configuration JSON file |
| `FREEBIE_API_KEYS` | Comma-separated API keys for protecting your endpoint |
| `FREEBIE_PROXY` | HTTP/HTTPS/SOCKS5 proxy (e.g. `http://127.0.0.1:7890`) |
| `FREEBIE_SESSION_TOKEN` | ChatGPT `__Secure-next-auth.session-token` |
| `FREEBIE_ACCESS_TOKEN` | ChatGPT OAuth Bearer access token |
| `FREEBIE_COOKIE_FILE` | Path to cookie file or `chatgpt-auth.json` |

---

## 🐳 Docker Deployment

### Using Docker

```bash
docker run -d \
  --name freebie \
  -p 8080:8080 \
  --restart unless-stopped \
  rabneer/freebie:latest
```

### Using Docker Compose

```yaml
version: "3.9"

services:
  freebie:
    build: .
    container_name: freebie
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - FREEBIE_PORT=8080
      - FREEBIE_HOST=0.0.0.0
```

Run:

```bash
docker compose up -d
```

---

## 🧪 Testing

Run the comprehensive pytest suite:

```bash
pytest tests/ -v
```

```text
============================= test session starts ==============================
tests/test_config.py::test_default_config PASSED                         [  6%]
tests/test_config.py::test_load_config_file PASSED                       [ 13%]
tests/test_config.py::test_env_override PASSED                           [ 20%]
tests/test_pow.py::test_fnv1a_mix PASSED                                 [ 26%]
tests/test_pow.py::test_solve_pow PASSED                                 [ 33%]
tests/test_pow.py::test_requirements_token PASSED                        [ 40%]
tests/test_protocol.py::test_resolve_model PASSED                        [ 46%]
tests/test_protocol.py::test_messages_to_prompt PASSED                   [ 53%]
tests/test_protocol.py::test_parse_tool_calls PASSED                     [ 60%]
tests/test_protocol.py::test_parse_chatgpt_sse_line PASSED               [ 66%]
tests/test_server.py::test_health_endpoint PASSED                        [ 73%]
tests/test_server.py::test_list_models_endpoint PASSED                   [ 80%]
tests/test_server.py::test_chat_completions_gemini_zero_auth PASSED      [ 86%]
tests/test_server.py::test_chat_completions_chatgpt_authenticated PASSED [ 93%]
tests/test_server.py::test_chat_completions_with_tool_calling PASSED     [100%]
============================== 15 passed in 0.33s ==============================
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for feature suggestions and bug reports.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
Made with ❤️ by <a href="https://github.com/RABNEER">Ranveer Kumar (RABNEER)</a>
</div>
