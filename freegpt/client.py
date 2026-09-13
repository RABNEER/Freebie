"""ChatGPT Web HTTP client utilizing curl_cffi for Cloudflare TLS impersonation."""
import json
import re
import time
import uuid
from typing import AsyncGenerator, Dict, Optional, Tuple

from curl_cffi import requests

from .config import CONFIG
from .pow import solve_pow
from .auth import auth_manager


class ChatGPTClient:
    """Async client communicating with ChatGPT Web backend."""

    DEFAULT_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy or CONFIG.get("proxy")
        self.impersonate = CONFIG.get("impersonate", "chrome124")
        self._session: Optional[requests.AsyncSession] = None
        self._build_id = "prod-75afbc79cc892d58982f98cde20fbf205800b19a"
        self._device_id = str(uuid.uuid4())
        self._last_init_time = 0.0

    async def get_session(self) -> requests.AsyncSession:
        """Get or initialize the underlying AsyncSession with browser impersonation."""
        if self._session is None:
            self._session = requests.AsyncSession(impersonate=self.impersonate)
        return self._session

    async def init_session(self) -> None:
        """Fetch landing page to establish device cookies and extract build metadata."""
        now = time.time()
        if now - self._last_init_time < 1800:  # Refresh every 30 mins
            return

        session = await self.get_session()
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            r = await session.get(
                "https://chatgpt.com",
                proxies=proxies,
                timeout=CONFIG["request_timeout_sec"],
            )
            if r.status_code == 200:
                m_build = re.search(r'data-build="([^"]+)"', r.text)
                if m_build:
                    self._build_id = m_build.group(1)

                cookies = session.cookies.get_dict()
                if "oai-did" in cookies:
                    self._device_id = cookies["oai-did"]

                self._last_init_time = now
        except Exception:
            pass

    async def get_chat_requirements(
        self, access_token: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Fetch sentinel token and solve Proof-of-Work challenge."""
        await self.init_session()
        session = await self.get_session()

        headers = {
            "Origin": "https://chatgpt.com",
            "Referer": "https://chatgpt.com/",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": self.DEFAULT_UA,
            "OAI-Device-Id": self._device_id,
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        r = await session.post(
            "https://chatgpt.com/backend-api/sentinel/chat-requirements",
            headers=headers,
            json={},
            proxies=proxies,
            timeout=CONFIG["request_timeout_sec"],
        )

        if r.status_code != 200:
            raise RuntimeError(f"Sentinel requirements failed with status {r.status_code}: {r.text[:200]}")

        data = r.json()
        token = data.get("token", "")
        pow_info = data.get("proofofwork", {})

        proof_token = None
        if pow_info.get("required"):
            seed = pow_info.get("seed", "")
            diff = pow_info.get("difficulty", "")
            if seed and diff:
                proof_token = solve_pow(
                    seed,
                    diff,
                    self.DEFAULT_UA,
                    self._build_id,
                    session_id=self._device_id,
                )

        return token, proof_token

    async def stream_conversation(
        self,
        payload: Dict[str, Any],
        access_token: Optional[str] = None,
    ) -> AsyncGenerator[Tuple[str, str, bool], None]:
        """Stream response chunks from ChatGPT backend.

        Yields: (content_delta, reasoning_delta, is_done)
        """
        token, proof_token = await self.get_chat_requirements(access_token)
        session = await self.get_session()

        headers = {
            "Origin": "https://chatgpt.com",
            "Referer": "https://chatgpt.com/",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": self.DEFAULT_UA,
            "OAI-Device-Id": self._device_id,
            "OpenAI-Sentinel-Chat-Requirements-Token": token,
        }
        if proof_token:
            headers["OpenAI-Sentinel-Proof-Token"] = proof_token
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        url = "https://chatgpt.com/backend-api/conversation"

        r = await session.post(
            url,
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=CONFIG["request_timeout_sec"],
            stream=True,
        )

        if r.status_code != 200:
            error_body = r.text
            if r.status_code == 403 and not access_token:
                raise RuntimeError(
                    "ChatGPT upstream rejected anonymous access (HTTP 403: Unusual activity). "
                    "OpenAI requires account authentication. Please provide your ChatGPT access_token "
                    "or session_token via --session-token, --access-token, config.json, or client Authorization header."
                )
            raise RuntimeError(f"ChatGPT upstream error (HTTP {r.status_code}): {error_body}")

        last_content = ""
        last_reasoning = ""

        async for line in r.aiter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8", errors="replace").strip()
            if not decoded.startswith("data:"):
                continue

            data_str = decoded[5:].strip()
            if data_str == "[DONE]":
                yield ("", "", True)
                break

            try:
                data = json.loads(data_str)
            except Exception:
                continue

            if "error" in data and data["error"]:
                raise RuntimeError(f"ChatGPT error: {data['error']}")

            message = data.get("message")
            if not message or not isinstance(message, dict):
                continue

            content_obj = message.get("content", {})
            content_type = content_obj.get("content_type", "")
            parts = content_obj.get("parts", [])
            current_part = parts[0] if parts and isinstance(parts[0], str) else ""

            if content_type == "thought":
                if len(current_part) > len(last_reasoning):
                    delta = current_part[len(last_reasoning):]
                    last_reasoning = current_part
                    yield ("", delta, False)
            else:
                if len(current_part) > len(last_content):
                    delta = current_part[len(last_content):]
                    last_content = current_part
                    yield (delta, "", False)

    async def generate_text(
        self,
        payload: Dict[str, Any],
        access_token: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Non-streaming generation. Returns (full_content, full_reasoning)."""
        content_parts = []
        reasoning_parts = []

        async for content_delta, reasoning_delta, is_done in self.stream_conversation(payload, access_token):
            if content_delta:
                content_parts.append(content_delta)
            if reasoning_delta:
                reasoning_parts.append(reasoning_delta)
            if is_done:
                break

        return "".join(content_parts), "".join(reasoning_parts)
