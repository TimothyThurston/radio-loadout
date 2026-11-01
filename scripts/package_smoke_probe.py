"""Run only with the wheel's fresh Python, from an external working directory."""

import csv
import hashlib
import importlib
import importlib.metadata
import json
import os
import pkgutil
import socket
import sys
import threading
import time
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import ProxyHandler, Request, build_opener


class AssetReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs) -> None:
        attrs = dict(attrs)
        value = attrs.get("src") if tag == "script" else attrs.get("href") if tag == "link" else None
        if value and not urlsplit(value).netloc and urlsplit(value).path.endswith((".js", ".css")):
            self.urls.add(value)


def verify_imports(repo: Path, manifest: Path) -> Path:
    assert sys.flags.isolated, "The installed probe must run with python -I."
    assert not any(key.upper() == "PYTHONPATH" for key in os.environ)
    assert not Path.cwd().resolve().is_relative_to(repo)
    assert not Path(sys.prefix).resolve().is_relative_to(repo)
    assert all(not Path(entry).resolve().is_relative_to(repo) for entry in sys.path if entry)
    import radio_loadout

    package = Path(radio_loadout.__file__).resolve().parent
    assert package.is_relative_to(Path(sys.prefix).resolve()), package
    installed = importlib.metadata.distribution("radio-loadout")
    assert not json.loads(installed.read_text("direct_url.json") or "{}").get("dir_info", {}).get("editable")
    modules = [radio_loadout.__name__, *(module.name for module in pkgutil.walk_packages(
        radio_loadout.__path__, radio_loadout.__name__ + ".",
    ))]
    for name in modules:
        module = importlib.import_module(name)
        assert Path(module.__file__).resolve().is_relative_to(package), name
    expected = json.loads(manifest.read_text(encoding="utf-8"))
    for name, checksum in expected.items():
        filename = package.parent / name
        assert hashlib.sha256(filename.read_bytes()).hexdigest() == checksum, name
    print(f"PASS: {len(modules)} application imports from {package}; all installed payload hashes match.")
    return package


def verify_http(base: str, package: Path, *, installed_importer: bool = True) -> None:
    if installed_importer:
        from radio_loadout.importers.chirp_csv import import_chirp_csv
    else:
        def import_chirp_csv(text):
            return list(csv.DictReader(StringIO(text)))

    opener = build_opener(ProxyHandler({}))  # Never send synthetic local traffic through a proxy.

    def request(path, data=None, content_type=None):
        headers = {"Content-Type": content_type} if content_type else {}
        with opener.open(Request(urljoin(base, path), data=data, headers=headers), timeout=10) as response:
            assert response.status == 200, (path, response.status)
            return response.read(), response.headers

    assets = set()
    for route in ("/", "/builder"):
        content, headers = request(route)
        assert headers.get_content_type() == "text/html"
        parser = AssetReferences()
        parser.feed(content.decode("utf-8"))
        assert "Radio Loadout" in content.decode("utf-8")
        assets.update(urljoin(route, url) for url in parser.urls)
    assert any(urlsplit(asset).path == "/static/backup-format.js" for asset in assets)
    for asset in sorted(assets):
        content, headers = request(asset)
        filename = package / "web" / urlsplit(asset).path.lstrip("/")
        assert content == filename.read_bytes(), asset
        if filename.suffix == ".css":
            assert headers.get_content_type() == "text/css", asset
        else:
            assert "javascript" in headers.get_content_type(), asset
    limits, _ = request("/static/input-limits.json")
    assert limits == (package / "web/static/input-limits.json").read_bytes()
    assert json.loads(limits)["channels"] >= 100
    print(f"PASS: homepage, builder, all {len(assets)} referenced local JS/CSS assets and input limits.")

    sample, headers = request("/downloads/chirp-sample.csv")
    assert "radio_loadout_sample.csv" in headers["Content-Disposition"]
    assert len(import_chirp_csv(sample.decode("utf-8-sig"))) == 4
    channels = [
        {"name": "PKG SYNTH RPT", "receive_frequency_mhz": 146.94, "transmit_frequency_mhz": 146.34,
         "mode": "NFM", "power_watts": 2.5, "tone_mode": "cross", "transmit_tone_mode": "ctcss",
         "transmit_ctcss_frequency_hz": 151.4, "receive_tone_mode": "dcs", "receive_dcs_code": 777,
         "receive_dcs_polarity": "R", "tuning_step_khz": 6.25, "scan_behavior": "P",
         "comment": "Synthetic packaging smoke test"},
        {"name": "PKG SYNTH RX", "receive_frequency_mhz": 121.5, "receive_only": True,
         "mode": "AM", "power_watts": 1, "tone_mode": "none", "tuning_step_khz": 25,
         "scan_behavior": "S", "comment": "Synthetic receive-only test"},
    ]

    def post_channels(route, values):
        content, headers = request(route, urlencode({"channels_json": json.dumps(values)}).encode("utf-8"),
                                   "application/x-www-form-urlencoded")
        return content, headers

    review, _ = post_channels("/validation/chirp.csv", channels)
    report = json.loads(review)
    assert report["compatible"] is True and report["channel_count"] == 2
    assert not any(issue["severity"] == "error" for issue in report["issues"])
    invalid, _ = post_channels("/validation/chirp.csv", [{**channels[0], "mode": "DMR"}])
    assert json.loads(invalid)["compatible"] is False
    print("PASS: compatibility review accepts supported channels and identifies unsupported DMR.")

    exported, headers = post_channels("/downloads/chirp.csv", channels)
    assert "radio_loadout_custom.csv" in headers["Content-Disposition"]
    rows = list(csv.DictReader(StringIO(exported.decode("utf-8"))))
    assert [row["Name"] for row in rows] == [channel["name"] for channel in channels]
    assert [row["Frequency"] for row in rows] == ["146.940000", "121.500000"]
    assert rows[0]["RxDtcsCode"] == "777" and rows[0]["DtcsPolarity"] == "NR"
    assert rows[1]["Duplex"] == "off"
    boundary = "radio-loadout-synthetic-package-boundary"
    upload = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic.csv"\r\n'
              'Content-Type: text/csv\r\n\r\n').encode() + b"\xef\xbb\xbf" + exported + f"\r\n--{boundary}--\r\n".encode()
    imported, _ = request("/imports/chirp.csv", upload, f"multipart/form-data; boundary={boundary}")
    result = json.loads(imported)
    assert result["import_report"]["requires_confirmation"] is False
    assert [channel["name"] for channel in result["channels"]] == [channel["name"] for channel in channels]
    roundtrip, _ = post_channels("/downloads/chirp.csv", result["channels"])
    assert roundtrip == exported
    assert len(import_chirp_csv(roundtrip.decode("utf-8"))) == 2
    print("PASS: sample CSV download and synthetic custom CSV export -> BOM upload -> identical re-export.")


def verify_oversized(base: str, package: Path) -> None:
    opener = build_opener(ProxyHandler({}))
    limits = json.loads((package / "web/static/input-limits.json").read_text())
    boundary = "synthetic-staging-limit-check"
    upload = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="oversized.csv"\r\n'
              'Content-Type: text/csv\r\n\r\n').encode() + b"x" * (limits["csv_upload_bytes"] + 1) + f"\r\n--{boundary}--\r\n".encode()
    requests = [("/imports/chirp.csv", upload, f"multipart/form-data; boundary={boundary}")]
    for path in ("/validation/chirp.csv", "/downloads/chirp.csv"):
        requests.append((path, urlencode({"channels_json": " " * (limits["channels_json_bytes"] + 1)}).encode(),
                         "application/x-www-form-urlencoded"))
    for path, content, content_type in requests:
        try:
            opener.open(Request(base + path, data=content, headers={"Content-Type": content_type}), timeout=15).close()
        except HTTPError as response:
            assert response.code == 413, (path, response.code)
            assert response.headers["Cache-Control"] == "no-store"
            assert isinstance(json.load(response)["detail"], str)
            response.close()
        else:
            raise AssertionError(f"Oversized request accepted: {path}")
    print("PASS: all three oversized-input rejections.")


def main() -> None:
    package = verify_imports(Path(sys.argv[1]).resolve(), Path(sys.argv[2]))
    import uvicorn

    from radio_loadout.web.production import create_app

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(create_app(), log_level="warning", access_log=False, lifespan="off"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 15
            while not server.started:
                if not thread.is_alive() or time.monotonic() >= deadline:
                    raise RuntimeError("Installed test server failed to start.")
                threading.Event().wait(0.05)
            verify_http(f"http://127.0.0.1:{port}", package)
            # The same installed staging boundary also serves the liveness probe.
            with build_opener(ProxyHandler({})).open(f"http://127.0.0.1:{port}/healthz", timeout=5) as response:
                assert json.load(response) == {"status": "ok"}
            verify_oversized(f"http://127.0.0.1:{port}", package)
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive(), "Installed test server did not stop."


if __name__ == "__main__":
    main()
