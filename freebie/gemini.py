"""Gemini Web StreamGenerate provider for zero-auth responses in Freebie."""
import json
import re
import time
import urllib.parse
import uuid
from typing import AsyncGenerator, Dict, Optional, Tuple

import httpx

from .config import CONFIG

GEMINI_BL = "boq_assistant-bard-web-server_20260716.08_p0"


def clean_gemini_text(text: str) -> str:
    """Clean internal Google metadata and code execution cards from output."""
    text = re.sub(
        r"```(?:python|javascript|text)\?code_(?:reference|stdout)&code_event_index=\d+\n.*?```\n?",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"http://googleusercontent\.com/card_content/\d+\n?", "", text)
    return text.strip()


def build_gemini_payload(prompt: str, model_id: int = 1, think_mode: int = 4) -> str:
    """Construct Google Gemini Web RPC payload f.req."""
    inner = [None] * 102
    inner[0] = [prompt, 0, None, None, None, None, 0]
    inner[1] = ["en"]
    inner[2] = ["", "", "", None, None, None, None, None, None, ""]
    inner[6] = [0]
    inner[7] = 1
    inner[10] = 1
    inner[11] = 0
    inner[17] = [[think_mode]]
    inner[18] = 0
    inner[27] = 1
    inner[30] = [4]
    inner[41] = [1]  # Temporary chat / no history pollution
    inner[45] = 1
    inner[53] = 0
    inner[59] = str(uuid.uuid4())
    inner[61] = []
    inner[68] = 1
    inner[79] = model_id

    outer = [None, json.dumps(inner)]
    return urllib.parse.urlencode({"f.req": json.dumps(outer)})


def _extract_texts_from_line(line: str) -> list:
    """Parse single wrb.fr line and extract text deltas."""
    if '"wrb.fr"' not in line or len(line) < 200:
        return []
    try:
        arr = json.loads(line)
        inner_str = arr[0][2]
        if not inner_str or len(inner_str) < 50:
            return []
        inner = json.loads(inner_str)
        if not (isinstance(inner, list) and len(inner) > 4 and inner[4]):
            return []
        texts = []
        for part in inner[4]:
            if isinstance(part, list) and len(part) > 1 and part[1] and isinstance(part[1], list):
                for t in part[1]:
                    if isinstance(t, str) and t:
                        texts.append(t)
        return texts
    except Exception:
        return []


class GeminiClient:
    """Zero-authentication Gemini Web client."""

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy or CONFIG.get("proxy")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://gemini.google.com",
            "Referer": "https://gemini.google.com/app",
            "X-Same-Domain": "1",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    def _get_url(self) -> str:
        reqid = int(time.time()) % 1000000
        return (
            "https://gemini.google.com/_/BardChatUi/data/"
            "assistant.lamda.BardFrontendService/StreamGenerate"
            f"?bl={GEMINI_BL}&hl=en&_reqid={reqid}&rt=c"
        )

    async def stream_generation(
        self, prompt: str, model_id: int = 1, think_mode: int = 4
    ) -> AsyncGenerator[Tuple[str, bool], None]:
        """Stream response text from Gemini Web.

        Yields: (delta_text, is_done)
        """
        payload = build_gemini_payload(prompt, model_id, think_mode)
        url = self._get_url()
        headers = self._get_headers()

        transport = httpx.AsyncHTTPTransport(proxy=self.proxy) if self.proxy else None
        timeout = httpx.Timeout(CONFIG["request_timeout_sec"])

        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
            async with client.stream("POST", url, content=payload, headers=headers) as resp:
                resp.raise_for_status()
                emitted_text = ""
                buf = ""

                async for chunk in resp.aiter_text():
                    buf += chunk
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        for t in _extract_texts_from_line(line):
                            if t == emitted_text or emitted_text.startswith(t):
                                continue
                            delta = clean_gemini_text(t[len(emitted_text):])
                            emitted_text = t
                            if delta:
                                yield (delta, False)

        yield ("", True)

    async def generate_text(
        self, prompt: str, model_id: int = 1, think_mode: int = 4
    ) -> str:
        """Non-streaming generation."""
        pieces = []
        async for delta, is_done in self.stream_generation(prompt, model_id, think_mode):
            if delta:
                pieces.append(delta)
            if is_done:
                break
        return clean_gemini_text("".join(pieces))
