"""Exercise a locally running staging server using only synthetic requests."""

import argparse
import json
import math
import time
from http.client import IncompleteRead, RemoteDisconnected
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

from package_smoke_probe import verify_http, verify_oversized

TRANSIENT_CONNECTION_ERRORS = (
    ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError,
    BrokenPipeError, TimeoutError, RemoteDisconnected, IncompleteRead,
)


def wait_for_health(base: str, wait_seconds: float) -> None:
    if not math.isfinite(wait_seconds) or wait_seconds <= 0:
        raise ValueError("Readiness wait must be a finite, positive number of seconds.")
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + wait_seconds
    last_error = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            detail = (f"{type(last_error).__name__}: {last_error}" if last_error is not None
                      else "No connection attempt completed before the readiness deadline.")
            raise RuntimeError(
                f"Local staging server did not become healthy within {wait_seconds:g}s. "
                f"Final connection error: {detail}"
            ) from last_error
        try:
            with opener.open(base + "/healthz", timeout=min(2.0, remaining)) as response:
                assert response.status == 200
                assert json.load(response) == {"status": "ok"}
            if time.monotonic() >= deadline:
                raise TimeoutError("Health response arrived after the readiness deadline.")
            return
        except HTTPError:
            raise  # HTTP errors are URLError subclasses, but are not startup retries.
        except URLError as error:
            if not isinstance(error.reason, TRANSIENT_CONNECTION_ERRORS):
                raise  # DNS/configuration/permission failures remain visible immediately.
            last_error = error
        except TRANSIENT_CONNECTION_ERRORS as error:
            last_error = error
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.1, remaining))


def verify_staging(base: str, package: Path) -> None:
    opener = build_opener(ProxyHandler({}))
    for path in ("/healthz", "/", "/builder", "/static/builder.js", "/downloads/chirp-sample.csv"):
        with opener.open(base + path, timeout=10) as response:
            assert response.status == 200
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert response.headers["Referrer-Policy"] == "no-referrer"
            if path == "/healthz":
                assert json.load(response) == {"status": "ok"}
            if not path.startswith("/static/"):
                assert response.headers["Cache-Control"] == "no-store"
    verify_http(base, package, installed_importer=False)
    verify_oversized(base, package)
    print("PASS: staging health, safe headers, synthetic workflows and all three oversized-input rejections.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--wait-seconds", type=float, default=30)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.scheme != "http" or parsed.path not in {"", "/"} or parsed.query or parsed.username:
        parser.error("This local smoke command requires an HTTP loopback URL without credentials, paths or queries.")
    base = args.base_url.rstrip("/")
    wait_for_health(base, args.wait_seconds)
    verify_staging(base, Path(__file__).resolve().parents[1] / "src/radio_loadout")


if __name__ == "__main__":
    main()
