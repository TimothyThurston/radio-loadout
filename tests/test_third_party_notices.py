"""Verbatim bundle integrity, distribution inclusion and actual-image byte verification."""

import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def verifier(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("verify_third_party_notices")


def installed_evidence(verifier, directory):
    """Synthetic collector result: never passed off as an actual Docker execution."""
    directory.mkdir()
    payload = verifier.bundle_payload()
    manifest = json.loads(payload["manifest.json"])
    site = "/opt/venv/lib/python3.13/site-packages/"
    distributions = [{"name": "radio-loadout", "version": "0.1.0", "scope": "installed",
                      "origin": site + "radio_loadout-0.1.0.dist-info/METADATA"}]
    distributions.extend({"name": a["distribution"], "version": a["version"], "scope": "installed"}
                         for a in manifest["runtime_artifacts"])
    image = "sha256:" + "a" * 64
    inventory = {"collection_status": "complete", "errors": [], "source_commit": "b" * 40,
                 "image": {"id": image, "os": "linux", "architecture": "amd64", "user": "10001:10001"},
                 "image_binding": {"staging_container": image, "build_iidfile": image},
                 "probes": [{"interpreter": {"executable": "/opt/venv/bin/python"}, "errors": [],
                             "python": {"distributions": distributions, "native_binaries": [
                                 {"path": site + a["native_file"], "sha256": a["native_sha256"]}
                                 for a in manifest["runtime_artifacts"]]}}]}
    index = []
    for name, data in payload.items():
        checksum = hashlib.sha256(data).hexdigest()
        stored = "notices/" + checksum + ".txt"
        (directory / "notices").mkdir(exist_ok=True)
        (directory / stored).write_bytes(data)
        index.append({"origin": site + "radio_loadout/third_party_notices/v1/" + name,
                      "interpreter": "/opt/venv/bin/python", "stored_as": stored,
                      "sha256": checksum, "bytes": len(data), "gzip": False})
    save_evidence(directory, inventory, index)
    return inventory, index


def save_evidence(directory, inventory, index):
    (directory / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    (directory / "notices-index.json").write_text(json.dumps(index), encoding="utf-8")


def test_bundle_maps_source_identities_and_keeps_distinct_libuv_notices(verifier):
    payload = verifier.bundle_payload()
    manifest = json.loads(payload["manifest.json"])
    assert len(payload) == 15
    libuv = manifest["components"][0]
    assert libuv["version"] == "1.52.1" and len(libuv["notice_files"]) == 4
    assert b"2015-present libuv project contributors" in payload["libuv/LICENSE.txt"]
    assert b"Copyright Joyent" in payload["libuv/LICENSE-extra.txt"]
    assert b"Copyright 2002 Niels Provos" in payload["libuv/tree.h-BSD-notice.txt"]
    assert b"2004 by Internet Systems Consortium" in payload["libuv/inet.c-ISC-notice.txt"]
    assert b"International Business Machines" in payload["icu4x/LICENSE.txt"]
    assert "pyo3-ffi" in {c["component"] for c in manifest["components"]}


def test_changed_upstream_notice_fails_before_packaging(verifier, tmp_path):
    shutil.copytree(ROOT / verifier.BUNDLE, tmp_path / verifier.BUNDLE)
    (tmp_path / verifier.BUNDLE / "libuv/LICENSE.txt").write_bytes(b"Substituted parent notice")
    with pytest.raises(verifier.NoticeCheckError, match="bytes changed"):
        verifier.bundle_payload(tmp_path)


def test_archive_payload_includes_all_supplemental_bytes(verifier):
    smoke = importlib.import_module("smoke_package")
    payload = smoke.source_payload(ROOT)
    for name, data in verifier.bundle_payload().items():
        assert payload["radio_loadout/third_party_notices/v1/" + name] == data


def test_collector_retains_installed_ledger_and_exact_notices_only(verifier, tmp_path):
    probe = importlib.import_module("image_inventory_probe")
    site, stdlib = tmp_path / "site", tmp_path / "stdlib"
    stdlib.mkdir()
    bundle = site / "radio_loadout/third_party_notices/v1"
    shutil.copytree(ROOT / verifier.BUNDLE, bundle)
    (bundle / ".env").write_text("PRIVATE")
    (bundle / "unrelated.py").write_text("PRIVATE")
    evidence = probe.Evidence()
    probe.collect_python([site], stdlib, evidence)
    assert not evidence.errors
    found = {Path(n["origin"]).relative_to(bundle).as_posix(): n["sha256"] for n in evidence.notices}
    assert found == {name: hashlib.sha256(data).hexdigest() for name, data in verifier.bundle_payload().items()}


def test_actual_installed_evidence_passes_only_with_every_byte(verifier, tmp_path):
    installed_evidence(verifier, tmp_path / "evidence")
    result = verifier.verify_inventory(tmp_path / "evidence")
    assert result["status"] == "passed" and len(result["verified_files"]) == 15


@pytest.mark.parametrize("failure", ["missing", "changed", "escape", "partial", "identity", "version", "native", "base-only"])
def test_actual_image_verification_rejects_missing_changed_or_mismatched_evidence(verifier, tmp_path, failure):
    directory = tmp_path / "evidence"
    inventory, index = installed_evidence(verifier, directory)
    if failure == "missing":
        index.pop()
    elif failure == "changed":
        (directory / index[0]["stored_as"]).write_bytes(b"Altered installed bytes")
    elif failure == "escape":
        index[0]["stored_as"] = "../private.txt"
    elif failure == "partial":
        inventory["collection_status"] = "partial"
    elif failure == "identity":
        inventory["image_binding"]["staging_container"] = "sha256:" + "c" * 64
    elif failure == "version":
        inventory["probes"][0]["python"]["distributions"][1]["version"] = "future"
    elif failure == "native":
        inventory["probes"][0]["python"]["native_binaries"][0]["sha256"] = "d" * 64
    elif failure == "base-only":
        for row in index:
            row["interpreter"] = "/usr/local/bin/python"
    save_evidence(directory, inventory, index)
    with pytest.raises(verifier.NoticeCheckError):
        verifier.verify_inventory(directory)


def test_ci_checks_actual_evidence_even_after_failures_before_upload_cleanup():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    job = workflow.split("  container:\n", 1)[1].split("  browser:\n", 1)[0]
    collect = job.index("Collect final image packages")
    verify = job.index("Verify supplemental notice bytes")
    assert collect < verify < job.index("Upload container diagnostics") < job.index("Stop the local test container")
    assert "if: ${{ always() }}" in job[verify:job.index("Capture selected container state")]
    assert "--inventory-dir generated/container-diagnostics/licenses" in job
    assert "--output generated/container-diagnostics/supplemental-notices-check.json" in job
    assert "continue-on-error" not in job
