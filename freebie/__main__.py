"""CLI Entry point: python -m freebie or `freebie` command."""
import argparse
import asyncio
import os
import sys
import uvicorn

from . import __version__
from .auth import auth_manager
from .client import ChatGPTClient
from .config import CONFIG, find_config, load_config
from .models import MODELS


def run_diagnostics():
    """Run connectivity and authentication diagnostics."""
    print(f"Freebie v{__version__} Diagnostic Check")
    print("=" * 50)

    proxy = CONFIG.get("proxy")
    print(f"[*] Proxy: {proxy or 'Direct connection (no proxy)'}")
    print(f"[*] Impersonation profile: {CONFIG.get('impersonate', 'chrome124')}")

    async def _async_check():
        client = ChatGPTClient(proxy=proxy)
        session = await client.get_session()

        # Step 1: Check Cloudflare bypass & landing page
        print("\n[1/4] Testing Cloudflare bypass and ChatGPT landing page...")
        try:
            proxies = {"http": proxy, "https": proxy} if proxy else None
            r = await session.get("https://chatgpt.com", proxies=proxies, timeout=15)
            if r.status_code == 200:
                print("  [+] PASS: Successfully connected to https://chatgpt.com (HTTP 200)")
            else:
                print(f"  [-] FAIL: Upstream returned HTTP {r.status_code}")
        except Exception as e:
            print(f"  [-] ERROR connecting to chatgpt.com: {e}")
            return

        # Step 2: Test Sentinel Requirements & PoW
        print("\n[2/4] Testing Sentinel requirements and Proof-of-Work engine...")
        try:
            token, proof_token = await client.get_chat_requirements()
            if token:
                print(f"  [+] PASS: Sentinel requirements token obtained (len={len(token)})")
            if proof_token:
                print("  [+] PASS: Proof-of-Work solved successfully")
            else:
                print("  [*] INFO: Proof-of-Work was not required for this request")
        except Exception as e:
            print(f"  [-] ERROR during sentinel requirements: {e}")

        # Step 3: Test Zero-Auth Gemini Flash
        print("\n[3/4] Testing Gemini Flash (Zero-Auth engine)...")
        try:
            from .gemini import GeminiClient
            g_client = GeminiClient(proxy=proxy)
            res = await g_client.generate_text("Say OK")
            if res:
                print(f"  [+] PASS: Gemini Flash zero-auth operational (response: '{res[:20]}')")
            else:
                print("  [-] WARNING: Gemini Flash returned empty response")
        except Exception as e:
            print(f"  [-] ERROR testing Gemini Flash: {e}")

        # Step 4: Test Auth
        print("\n[4/4] Checking ChatGPT upstream credentials...")
        access_tok = auth_manager.refresh_access_token_if_needed(proxy)
        if access_tok:
            print(f"  [+] PASS: Valid ChatGPT access token active (prefix: {access_tok[:15]}...)")
        else:
            print("  [*] INFO: No ChatGPT access token configured.")
            print("            -> Calls will route to zero-auth Gemini Flash (model='auto' or 'gemini-3.6-flash').")
            print("            -> To use ChatGPT models (gpt-4o, o3-mini), provide --session-token or --access-token.")

        print("\n" + "=" * 50)
        print("[*] Diagnostic check completed.")

    asyncio.run(_async_check())


def main():
    parser = argparse.ArgumentParser(description="Freebie - OpenAI-compatible API proxy for ChatGPT & Gemini Web")
    parser.add_argument("--host", type=str, default=None, help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind (default: 8080)")
    parser.add_argument("--config", type=str, default=None, help="Path to config.json")
    parser.add_argument("--proxy", type=str, default=None, help="HTTP/HTTPS proxy (e.g. http://127.0.0.1:7890)")
    parser.add_argument("--cookie-file", type=str, default=None, help="Path to cookie file or auth json")
    parser.add_argument("--access-token", type=str, default=None, help="ChatGPT Bearer access token")
    parser.add_argument("--session-token", type=str, default=None, help="ChatGPT __Secure-next-auth.session-token")
    parser.add_argument("--check", action="store_true", help="Run upstream connectivity diagnostics and exit")
    parser.add_argument("--version", action="version", version=f"freebie {__version__}")
    args = parser.parse_args()

    # Load configuration
    cfg_file = args.config or os.environ.get("FREEBIE_CONFIG") or os.environ.get("FREEGPT_CONFIG") or find_config()
    if cfg_file:
        load_config(cfg_file)

    if args.host:
        CONFIG["host"] = args.host
    if args.port:
        CONFIG["port"] = args.port
    if args.proxy:
        CONFIG["proxy"] = args.proxy
    if args.cookie_file:
        CONFIG["cookie_file"] = args.cookie_file
    if args.access_token:
        CONFIG["access_token"] = args.access_token
    if args.session_token:
        CONFIG["session_token"] = args.session_token

    if args.check:
        run_diagnostics()
        sys.exit(0)

    host = CONFIG["host"]
    port = CONFIG["port"]

    print(f"Freebie v{__version__} - ChatGPT & Gemini Web to OpenAI API")
    print(f"  Listening on: http://{host}:{port}")
    print(f"  Base URL:     http://localhost:{port}/v1")
    print(f"  Models:       {', '.join(MODELS.keys())}")
    print(f"  Proxy:        {CONFIG.get('proxy') or 'direct / env'}")
    print(f"  Auth:         {'Session/Access Token configured' if (CONFIG.get('access_token') or CONFIG.get('session_token') or CONFIG.get('cookie_file')) else 'Anonymous'}")
    print(f"  API Keys:     {'Enabled' if CONFIG.get('api_keys') else 'Open (None required)'}")
    print()

    uvicorn.run(
        "freebie.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
