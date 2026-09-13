# FreeGPT Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build FreeGPT, a high-performance, reverse-engineered ChatGPT Web to OpenAI-compatible API proxy server supporting anonymous and authenticated access, Proof-of-Work solving, Cloudflare TLS impersonation, streaming SSE, and PyPI packaging.

**Architecture:** An asynchronous FastAPI/Uvicorn backend using `curl_cffi` for browser TLS fingerprint impersonation to bypass Cloudflare WAF, a native Python Sentinel Proof-of-Work (PoW) engine, an internal SSE-to-OpenAI stream transformer, and a modular architecture structured for immediate PyPI publication.

**Tech Stack:** Python 3.9+, FastAPI, Uvicorn, curl_cffi, Pydantic v2, sse-starlette, pytest.

---

### Task 1: Project Scaffolding & PyPI Packaging Setup
**Files:**
- Create: `D:/FreeGPT/pyproject.toml`
- Create: `D:/FreeGPT/README.md`
- Create: `D:/FreeGPT/freegpt/__init__.py`
- Create: `D:/FreeGPT/freegpt/config.py`
- Test: `D:/FreeGPT/tests/test_config.py`

**Details:**
1. Configure modern `pyproject.toml` with entry points (`freegpt = "freegpt.__main__:main"`), metadata, dependencies (`curl_cffi`, `fastapi`, `uvicorn`, `pydantic`).
2. Implement configuration loader (`config.py`) supporting environment variables, `config.json`, proxy settings, and port configuration.
3. Write unit tests validating default configs, JSON loading, and env overrides.

---

### Task 2: OpenAI Sentinel Proof-of-Work (PoW) & Requirements Engine
**Files:**
- Create: `D:/FreeGPT/freegpt/pow.py`
- Test: `D:/FreeGPT/tests/test_pow.py`

**Details:**
1. Implement the mathematical Proof-of-Work algorithm required by OpenAI's `/backend-api/sentinel/chat-requirements` endpoint.
2. The algorithm searches for a nonce combining `seed`, `difficulty`, and screen/navigator config that satisfies the hash requirement (FNV-1a / SHA-3 / SHA256 configuration as expected by ChatGPT frontend).
3. Test with sample seeds and verify generated tokens against expected PoW formats.

---

### Task 3: ChatGPT Web Client & TLS Impersonator
**Files:**
- Create: `D:/FreeGPT/freegpt/client.py`
- Create: `D:/FreeGPT/freegpt/auth.py`
- Test: `D:/FreeGPT/tests/test_client.py`

**Details:**
1. Implement `ChatGPTClient` using `curl_cffi.requests.AsyncSession` impersonating `chrome124` / `chrome120` to bypass Cloudflare.
2. Implement session management in `auth.py`:
   - Anonymous mode: generate `oai-did` (device ID) and fetch anonymous sentinel tokens.
   - Authenticated mode: support session tokens (`__Secure-next-auth.session-token`) or access tokens (`Bearer eyJ...`) from `cookie.txt` or `config.json`.
3. Implement `fetch_chat_requirements()` to obtain the Sentinel token and solve PoW automatically.

---

### Task 4: Conversation Engine & SSE Stream Transformer
**Files:**
- Create: `D:/FreeGPT/freegpt/protocol.py`
- Create: `D:/FreeGPT/freegpt/models.py`
- Test: `D:/FreeGPT/tests/test_protocol.py`

**Details:**
1. Define model registry in `models.py`: map OpenAI model aliases (`gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini`, `auto`) to ChatGPT backend model slugs.
2. Build request payloads for `POST https://chatgpt.com/backend-api/conversation`:
   - Parent message IDs, message trees, history-disabled flags (temporary chat mode).
3. Implement streaming parser:
   - Reads upstream ChatGPT SSE lines (`data: {"message": ...}`).
   - Extracts cumulative text and calculates delta text.
   - For reasoning models (e.g. `o1`, `o3-mini`), extracts thought blocks and formats as `delta.reasoning_content`.

---

### Task 5: FastAPI Application & OpenAI Compatible Endpoints
**Files:**
- Create: `D:/FreeGPT/freegpt/server.py`
- Create: `D:/FreeGPT/freegpt/__main__.py`
- Test: `D:/FreeGPT/tests/test_server.py`

**Details:**
1. Build FastAPI application with CORS middleware and API key authentication.
2. Implement endpoints:
   - `POST /v1/chat/completions` (handles both `stream=true` with SSE and `stream=false` with JSON).
   - `GET /v1/models` (returns standard OpenAI models list).
   - `GET /health` (server health, current IP/proxy status, auth status).
3. Implement CLI runner with `argparse` in `__main__.py` (`freegpt --port 8080 --proxy ...`).

---

### Task 6: Docker, CI/CD, and PyPI Release Action
**Files:**
- Create: `D:/FreeGPT/Dockerfile`
- Create: `D:/FreeGPT/docker-compose.yml`
- Create: `D:/FreeGPT/.github/workflows/ci.yml`
- Create: `D:/FreeGPT/.github/workflows/publish.yml`
- Create: `D:/FreeGPT/config.example.json`

**Details:**
1. Multi-stage lightweight `Dockerfile` based on `python:3.11-slim` with `curl_cffi` pre-compiled wheels.
2. GitHub Actions CI for running `pytest` across Python 3.9 - 3.13.
3. Automated PyPI Trusted Publishing workflow triggered on release tags (`v*`).
