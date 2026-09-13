"""OpenAI Sentinel Proof-of-Work (PoW) solver.

Reverse-engineered from ChatGPT frontend web runtime (`sentinel-*.js`).
"""
import base64
import json
import random
import time
from typing import Optional


def fnv1a_mix(text: str) -> str:
    """Recreation of OpenAI's S(e) hash function from sentinel runtime.

    Uses FNV-1a basis with 32-bit Murmur3-style bit mixing.
    """
    t = 2166136261
    for char in text:
        t ^= ord(char)
        t = (t * 16777619) & 0xFFFFFFFF

    t ^= (t >> 16)
    t = (t * 2246822507) & 0xFFFFFFFF
    t ^= (t >> 13)
    t = (t * 3266489909) & 0xFFFFFFFF
    t ^= (t >> 16)

    return f"{t:08x}"


def build_sentinel_config(
    user_agent: str,
    build_id: str = "prod-75afbc79cc892d58982f98cde20fbf205800b19a",
    session_id: Optional[str] = None,
) -> list:
    """Build the client configuration array expected by OpenAI Sentinel PoW."""
    now_ms = int(time.time() * 1000)
    return [
        3000,  # screen.width + screen.height (e.g. 1920 + 1080)
        time.strftime("%a %b %d %Y %H:%M:%S GMT+0530 (India Standard Time)"),
        2147483648,  # jsHeapSizeLimit (2GB)
        0,  # placeholder for nonce
        user_agent,
        None,
        build_id,
        "en-US",
        "en-US,en",
        0,  # placeholder for elapsed ms
        "hardwareConcurrency−16",
        None,
        None,
        round(time.perf_counter() * 1000, 1),
        session_id or str(random.random()),
        "",  # acquisition query params
        16,  # hardwareConcurrency
        now_ms,  # timeOrigin
        0, 0, 0, 0, 0, 0, 0,  # feature flags
    ]


def solve_pow(
    seed: str,
    difficulty: str,
    user_agent: str,
    build_id: str = "prod-75afbc79cc892d58982f98cde20fbf205800b19a",
    session_id: Optional[str] = None,
    max_attempts: int = 500000,
) -> str:
    """Solve the Proof-of-Work challenge and return the sentinel proof token.

    Format: `gAAAAAB{base64_payload}~S`
    """
    start_time = time.perf_counter()
    config = build_sentinel_config(user_agent, build_id, session_id)
    diff_len = len(difficulty)

    for nonce in range(max_attempts):
        config[3] = nonce
        config[9] = int((time.perf_counter() - start_time) * 1000)

        raw_json = json.dumps(config, separators=(",", ":"))
        b64 = base64.b64encode(raw_json.encode()).decode()

        combined = seed + b64
        h = fnv1a_mix(combined)[:diff_len]
        if h <= difficulty:
            return f"gAAAAAB{b64}~S"

    raise RuntimeError(f"Failed to solve PoW within {max_attempts} attempts")


def generate_requirements_token_answer(
    user_agent: str,
    build_id: str = "prod-75afbc79cc892d58982f98cde20fbf205800b19a",
) -> str:
    """Generate the initial requirements token (prefixed with gAAAAAC)."""
    config = build_sentinel_config(user_agent, build_id)
    config[3] = 1
    config[9] = 1
    raw_json = json.dumps(config, separators=(",", ":"))
    b64 = base64.b64encode(raw_json.encode()).decode()
    return f"gAAAAAC{b64}"
