"""Exercise a locally running staging server using only synthetic requests."""

import argparse
import json
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

from package_smoke_probe import verify_http, verify_oversized


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
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + args.wait_seconds
    while True:
        try:
            with opener.open(base + "/healthz", timeout=2) as response:
                assert response.status == 200
            break
        except (URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise RuntimeError("Local staging server did not become healthy.") from None
            time.sleep(0.1)
    verify_staging(base, Path(__file__).resolve().parents[1] / "src/radio_loadout")


if __name__ == "__main__":
    main()
