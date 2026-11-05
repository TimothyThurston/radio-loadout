"""Synthetic installed-wrapper evidence; not a substitute for actual Linux CI collection."""

import copy
import importlib
import json
import stat
import zipfile
from pathlib import Path

import pytest
from test_certifi_sources import image_evidence, save

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("verify_certifi_wrappers"), importlib.import_module("image_inventory_probe")


def wrapper_evidence(tool, directory):
    manifest, inventory, index = image_evidence(tool, directory)
    inventory.update(schema_version=1, image_binding={"build_iidfile": inventory["image"]["id"]})
    inventory["image"].update(os="linux", architecture="amd64", user="10001:10001")
    template = inventory["probes"][0]
    inventory["probes"] = []
    expected = tool.expected_wrappers(manifest)
    for executable in tool.INTERPRETERS:
        probe = copy.deepcopy(template)
        probe["interpreter"] = {"executable": executable, "platform": "linux", "machine": "x86_64", "uid": 10001}
        python = probe["python"]
        prefix = "/opt/venv/" if executable == "/opt/venv/bin/python" else "/usr/local/"
        python["certifi_wrapper_schema_version"] = 1
        python["certifi_wrappers"] = [{"path": p, "bytes": r["bytes"], "sha256": r["sha256"]}
                                      for p, r in expected.items() if "!/" in p or p.startswith(prefix)]
        for wheel in python["bootstrap_wheels"]:
            wheel["certifi_wrappers"] = [r for r in python["certifi_wrappers"] if "!/" in r["path"]]
        inventory["probes"].append(probe)
    save(directory, inventory, index)
    return manifest, inventory, index


def test_four_locations_and_repeated_bootstrap_observations_verify_offline(modules, tmp_path):
    tool, _ = modules
    manifest, _, _ = wrapper_evidence(tool, tmp_path)
    result = tool.verify_inventory(tmp_path, manifest)
    assert result["status"] == "passed"
    assert result["copies_checked"] == 4 and result["unique_files_checked"] == 16
    assert result["observations_checked"] == 20
    assert result["interpreter_counts"] == {"/usr/local/bin/python": 8, "/opt/venv/bin/python": 12}
    assert "Not Mozilla" in result["qualification"]
    direct = next(r for p, r in result["verified_files"].items() if p.endswith("/certifi/core.py") and "/pip/" not in p)
    vendored = next(r for p, r in result["verified_files"].items() if p.endswith("/pip/_vendor/certifi/core.py"))
    assert direct["sha256"] != vendored["sha256"]
    assert vendored["source_archive"] == "pip-26.2.1.tar.gz"


@pytest.mark.parametrize("case", [
    "missing", "extra", "duplicate", "hash", "size", "bool-size", "negative-size", "nonhash", "body",
    "old-collector", "bool-schema", "partial", "probe-error", "missing-probe", "duplicate-probe", "wrong-probe",
    "wrong-platform", "binding", "no-binding", "source-commit", "wrong-image", "base-only",
    "nested-missing", "nested-conflict", "conflicting-repeat", "wrong-source", "namespace-substitution",
])
def test_wrapper_evidence_rejects_incomplete_changed_or_unbound_records(modules, tmp_path, case):
    tool, _ = modules
    manifest, inventory, index = wrapper_evidence(tool, tmp_path)
    probe = inventory["probes"][0]
    python = probe["python"]
    rows = python["certifi_wrappers"]
    if case == "missing":
        rows.pop()
    elif case == "extra":
        rows.append({**rows[0], "path": "/elsewhere/certifi/core.py"})
    elif case == "duplicate":
        rows.append(dict(rows[0]))
    elif case == "hash":
        rows[0]["sha256"] = "0" * 64
    elif case == "size":
        rows[0]["bytes"] += 1
    elif case == "bool-size":
        rows[0]["bytes"] = True
    elif case == "negative-size":
        rows[0]["bytes"] = -1
    elif case == "nonhash":
        rows[0]["sha256"] = "../unsafe"
    elif case == "body":
        rows[0]["content"] = "must not accept source dumps"
    elif case == "old-collector":
        del python["certifi_wrapper_schema_version"]
    elif case == "bool-schema":
        python["certifi_wrapper_schema_version"] = True
    elif case == "partial":
        inventory["collection_status"] = "partial"
    elif case == "probe-error":
        probe["errors"] = [{"reason": "unreadable wrapper"}]
    elif case == "missing-probe":
        inventory["probes"].pop()
    elif case == "duplicate-probe":
        inventory["probes"].append(copy.deepcopy(probe))
    elif case == "wrong-probe":
        probe["interpreter"]["executable"] = "/unexpected/python"
    elif case == "wrong-platform":
        probe["interpreter"]["uid"] = 0
    elif case == "binding":
        inventory["image_binding"]["staging_container"] = "sha256:" + "c" * 64
    elif case == "no-binding":
        inventory["image_binding"] = {}
    elif case == "source-commit":
        inventory["source_commit"] = "unknown"
    elif case == "wrong-image":
        inventory["image"]["architecture"] = "arm64"
    elif case == "base-only":
        inventory["probes"] = [probe]
    elif case == "nested-missing":
        python["bootstrap_wheels"][0].pop("certifi_wrappers")
    elif case == "nested-conflict":
        python["bootstrap_wheels"][0]["certifi_wrappers"] = []
    elif case == "conflicting-repeat":
        next(r for r in inventory["probes"][1]["python"]["certifi_wrappers"] if "!/" in r["path"])["sha256"] = "c" * 64
    elif case == "wrong-source":
        next(a for a in manifest["source_archives"] if a["filename"] == "pip-26.2.1.tar.gz")["members"]["pip-26.2.1/src/pip/_vendor/certifi/core.py"]["sha256"] = "c" * 64
    else:
        direct = next(a for a in manifest["source_archives"] if a["filename"] == "certifi-2026.10.23.tar.gz")
        core = next(r for r in rows if "/pip/_vendor/certifi/core.py" in r["path"])
        core.update(direct["members"]["certifi-2026.10.23/certifi/core.py"])
    save(tmp_path, inventory, index)
    with pytest.raises(tool.SourceCheckError):
        tool.verify_inventory(tmp_path, manifest)


def test_failure_cli_writes_receipt_and_exits_nonzero_without_trace_or_payload(modules, tmp_path, monkeypatch):
    tool, _ = modules
    manifest, inventory, index = wrapper_evidence(tool, tmp_path / "evidence")
    del inventory["probes"][0]["python"]["certifi_wrapper_schema_version"]
    save(tmp_path / "evidence", inventory, index)
    output = tmp_path / "diagnostics/check.json"
    monkeypatch.setattr("sys.argv", ["verify_certifi_wrappers.py", "--inventory-dir", str(tmp_path / "evidence"), "--output", str(output)])
    monkeypatch.setattr(tool, "MANIFEST", tmp_path / "manifest.json")
    tool.MANIFEST.write_text(json.dumps(manifest))
    with pytest.raises(SystemExit) as outcome:
        tool.main()
    assert outcome.value.code == 1
    result = json.loads(output.read_text())
    assert result["status"] == "failed" and "recollect" in result["reason"]
    assert "traceback" not in output.read_text().lower()


def make_wrapper(root, relative, data=b"raise AssertionError('DO NOT EXECUTE OR UPLOAD THIS SOURCE')"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_filesystem_collection_hashes_only_fixed_wrapper_scope_without_execution(modules, tmp_path):
    _, probe = modules
    site, stdlib = tmp_path / "site", tmp_path / "stdlib"
    stdlib.mkdir()
    for package in ("certifi", "pip/_vendor/certifi"):
        for name in probe.CERTIFI_WRAPPERS:
            make_wrapper(site, package + "/" + name)
    make_wrapper(site, "other/certifi/core.py", b"PRIVATE UNRELATED SOURCE")
    make_wrapper(site, "certifi/__pycache__/core.cpython-313.pyc", b"IGNORE BYTECODE")
    evidence = probe.Evidence()
    result = probe.collect_python([site], stdlib, evidence)
    assert len(result["certifi_wrappers"]) == 8 and not evidence.errors
    assert not evidence.notices
    assert "DO NOT EXECUTE" not in json.dumps(result) and "PRIVATE" not in json.dumps(result)
    assert not any("__pycache__" in r["path"] for r in result["certifi_wrappers"])


@pytest.mark.parametrize("case", ["oversized", "unexpected", "escaped-link", "internal-link"])
def test_filesystem_collection_reports_bad_wrapper_evidence_without_contents(modules, tmp_path, monkeypatch, case):
    _, probe = modules
    site, stdlib = tmp_path / "site", tmp_path / "stdlib"
    stdlib.mkdir()
    path = make_wrapper(site, "certifi/core.py", b"PRIVATE")
    if case == "oversized":
        monkeypatch.setattr(probe, "MAX_WRAPPER", 4)
    elif case == "unexpected":
        make_wrapper(site, "certifi/unreviewed.py", b"PRIVATE EXTRA")
    else:
        path.unlink()
        target = make_wrapper(tmp_path if case == "escaped-link" else site, "target.py", b"PRIVATE")
        try:
            path.symlink_to(target)
        except OSError:
            pytest.skip("Host does not allow unprivileged symlinks")
    evidence = probe.Evidence()
    result = probe.collect_python([site], stdlib, evidence)
    assert evidence.errors
    assert "PRIVATE" not in json.dumps({"result": result, "errors": evidence.errors})
    if case != "unexpected":
        assert not result["certifi_wrappers"]


@pytest.mark.parametrize("case", ["valid", "oversized", "duplicate", "link", "unexpected"])
def test_bootstrap_collection_hashes_selected_members_and_rejects_bad_evidence(modules, tmp_path, monkeypatch, case):
    _, probe = modules
    wheel = tmp_path / "pip-test.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name in sorted(probe.CERTIFI_WRAPPERS):
            archive.writestr("pip/_vendor/certifi/" + name, b"PRIVATE SOURCE")
        archive.writestr("pip/private.py", b"UNRELATED PRIVATE SOURCE")
        if case == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr("pip/_vendor/certifi/core.py", b"changed")
        elif case == "link":
            info = zipfile.ZipInfo("certifi/core.py")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "/secret")
        elif case == "unexpected":
            archive.writestr("pip/_vendor/certifi/new.py", b"PRIVATE")
    if case == "oversized":
        monkeypatch.setattr(probe, "MAX_WRAPPER", 4)
    evidence = probe.Evidence()
    result = probe.archive_evidence(wheel, evidence)
    assert bool(evidence.errors) == (case != "valid")
    assert "PRIVATE" not in json.dumps(result) and not evidence.notices
    if case == "valid":
        assert len(result["certifi_wrappers"]) == 4
        assert all("!/pip/_vendor/certifi/" in r["path"] for r in result["certifi_wrappers"])


def test_ci_verifies_actual_collected_wrappers_before_upload_cleanup_even_after_failure():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    job = workflow.split("  container:\n", 1)[1].split("  browser:\n", 1)[0]
    check = job.index("Verify installed certifi wrapper source hashes")
    assert job.index("Collect final image packages") < check < job.index("Upload container diagnostics") < job.index("Stop the local test container")
    step = job[check:job.index("Capture selected container state")]
    assert "if: ${{ always() }}" in step and "continue-on-error" not in job
    assert "verify_certifi_wrappers.py" in step and "certifi-wrappers-check.json" in step
    assert "docker" not in step and "pip install" not in step  # Offline comparison of collected JSON.
