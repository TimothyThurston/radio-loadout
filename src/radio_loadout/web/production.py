"""Opt-in staging boundary: host validation, privacy-conscious errors and headers."""

import logging
import os
import re

from starlette.datastructures import MutableHeaders
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

LOGGER = logging.getLogger("radio_loadout.production")
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def allowed_hosts(value: str) -> list[str]:
    hosts = [host.strip().lower() for host in value.split(",")]
    label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    if not hosts or any(not re.fullmatch(rf"{label}(?:\.{label})*", host) or len(host) > 253 for host in hosts):
        raise ValueError("RADIO_LOADOUT_ALLOWED_HOSTS requires exact DNS names or IPv4 hosts, without ports, URLs or wildcards.")
    return list(dict.fromkeys([*hosts, "127.0.0.1", "localhost"]))


class ProductionBoundary:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False
        complete = False

        async def safe_send(message: Message) -> None:
            nonlocal started, complete
            if message["type"] == "http.response.start":
                started = True
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
                if not scope["path"].startswith("/static/") or message["status"] >= 400:
                    headers["Cache-Control"] = "no-store"
            elif message["type"] == "http.response.body":
                complete = not message.get("more_body", False)
            await send(message)

        try:
            await self.app(scope, receive, safe_send)
        except Exception as error:  # noqa: BLE001 -- Outermost HTTP privacy boundary.
            # Exception messages/tracebacks can contain channel data; never log them here.
            LOGGER.error("Unhandled application error (%s)", type(error).__name__)
            if not started:
                await JSONResponse({"detail": "Internal server error."}, status_code=500)(scope, receive, safe_send)
            elif not complete:
                # A failed stream cannot be replaced with a second response. Do not
                # propagate the original payload-bearing exception to the server logger.
                raise RuntimeError("Application response could not be completed.") from None


def create_app() -> ASGIApp:
    from radio_loadout.web.app import app

    if app.debug:
        raise ValueError("Production requires application debug mode to be disabled.")
    hosts = allowed_hosts(os.environ.get("RADIO_LOADOUT_ALLOWED_HOSTS", "localhost,127.0.0.1"))
    return ProductionBoundary(TrustedHostMiddleware(app, allowed_hosts=hosts, www_redirect=False))
