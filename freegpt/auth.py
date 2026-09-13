"""Authentication and session management for FreeGPT."""
import json
import os
import time
from typing import Dict, Optional, Tuple
from curl_cffi import requests

from .config import CONFIG


class AuthManager:
    """Manages ChatGPT authentication, session tokens, and access token caching."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._cached_cookies: Dict[str, str] = {}

    def get_configured_access_token(self) -> Optional[str]:
        """Return explicitly configured access token, if any."""
        return CONFIG.get("access_token")

    def load_cookie_data(self) -> Tuple[Optional[str], Optional[str]]:
        """Load session token or cookie string from file or config."""
        cookie_file = CONFIG.get("cookie_file")
        session_token = CONFIG.get("session_token")
        if session_token:
            return session_token, None

        if not cookie_file or not os.path.exists(cookie_file):
            return None, None

        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content.startswith("{"):
                data = json.loads(content)
                return (
                    data.get("session_token")
                    or data.get("__Secure-next-auth.session-token"),
                    data.get("access_token"),
                )
            # Cookie line format: key=value; key2=value2
            pairs = dict(p.split("=", 1) for p in content.split("; ") if "=" in p)
            return pairs.get("__Secure-next-auth.session-token"), None
        except Exception:
            return None, None

    def refresh_access_token_if_needed(self, proxy: Optional[str] = None) -> Optional[str]:
        """Fetch fresh accessToken from ChatGPT session if session token is provided."""
        # 1. Use manual access_token if provided
        manual_token = self.get_configured_access_token()
        if manual_token:
            return manual_token

        # 2. Check if cached token is still valid (with 60s buffer)
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        # 3. Try to refresh via session token
        session_token, file_access_token = self.load_cookie_data()
        if file_access_token:
            self._access_token = file_access_token
            self._token_expires_at = time.time() + 3600
            return self._access_token

        if not session_token:
            return None

        try:
            session = requests.Session(impersonate=CONFIG.get("impersonate", "chrome124"))
            cookies = {"__Secure-next-auth.session-token": session_token}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": "https://chatgpt.com/",
            }
            proxies = {"http": proxy, "https": proxy} if proxy else None
            r = session.get(
                "https://chatgpt.com/api/auth/session",
                headers=headers,
                cookies=cookies,
                proxies=proxies,
                timeout=CONFIG["request_timeout_sec"],
            )
            if r.status_code == 200:
                data = r.json()
                token = data.get("accessToken")
                if token:
                    self._access_token = token
                    # Default expiry: 2 hours from now
                    self._token_expires_at = time.time() + 7200
                    return token
        except Exception:
            pass

        return None


auth_manager = AuthManager()
