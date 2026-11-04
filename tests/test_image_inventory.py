"""Inventory identities, failure evidence, bounded reads and restricted container execution."""

import base64
import gzip
import hashlib
import importlib
import json
import struct
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

IMAGE = "sha256:" + "a" * 64
COMMIT = "b" * 40


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("collect_image_inventory"), importlib.import_module("image_inventory_probe")


def make_file(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def elf(soname="libuv.so.1"):
    data = bytearray(512)
    data[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<HHIQQQIHHHHHH", data, 16, 3, 62, 1, 0, 64, 0, 0, 64, 56, 2, 0, 0, 0)
    struct.pack_into("<IIQQQQQQ", data, 64, 1, 0, 0, 0x400000, 0, 512, 512, 4096)
    struct.pack_into("<IIQQQQQQ", data, 120, 2, 0, 176, 0, 0, 64, 64, 8)
    strings = soname.encode() + b"\0"
    for pos, (tag, value) in enumerate([(1, 0), (5, 0x400100), (10, len(strings)), (0, 0)]):
        struct.pack_into("<qQ", data, 176 + pos * 16, tag, value)
    data[256:256 + len(strings)] = strings
    return bytes(data)


def test_python_installed_and_vendored_notices_without_source_or_environment_dump(modules, tmp_path):
    _, probe = modules
    site, stdlib = tmp_path / "site", tmp_path / "stdlib"
    stdlib.mkdir()
    make_file(site, "certifi-1.dist-info/METADATA", b"Name: certifi\nVersion: 1\nLicense-File: LICENSE\n")
    notice = make_file(site, "certifi-1.dist-info/licenses/LICENSE", b"Mozilla covered source notice")
    make_file(site, "certifi/cacert.pem", b"synthetic certificates")
    make_file(site, "pip/_vendor/idna-2.dist-info/METADATA", b"Name: idna\nVersion: 2\n")
    make_file(site, "pip/_vendor/idna/LICENSE.md", b"Copyright synthetic vendor")
    make_file(site, "pip/_vendor/vendor.txt", b"idna==2\ncertifi==1 # bundled\n")
    make_file(site, "pip/_vendor/certifi/cacert.pem", b"synthetic vendor certificates")
    make_file(site, "package/private.py", b"PRIVATE-SOURCE-DO-NOT-COLLECT")
    make_file(site, ".env", b"SECRET-DO-NOT-COLLECT")
    make_file(site, "native/example.so", elf() + b"uv_version_string PyO3 icu_normalizer")
    evidence = probe.Evidence()
    result = probe.collect_python([site], stdlib, evidence)
    assert {(r["name"], r["version"], r["scope"]) for r in result["distributions"]} == {
        ("certifi", "1", "installed"), ("idna", "2", "vendored")}
    certifi = next(r for r in result["distributions"] if r["name"] == "certifi")
    assert certifi["declared_notice_status"] == [{"declared": "LICENSE", "present": True}]
    assert str(notice) in [r["origin"] for r in evidence.notices]
    assert result["vendor_manifests"][0]["pins"] == [{"name": "idna", "version": "2"}, {"name": "certifi", "version": "1"}]
    assert len(result["certificate_bundles"]) == 2
    assert result["native_binaries"][0]["dt_needed"] == ["libuv.so.1"]
    review = probe.review_items(result, evidence)
    uv = next(r for r in review if r["component"] == "libuv")
    assert uv["binary_marker_evidence"] and uv["dynamic_linkage_evidence"]
    assert "uncertain" in uv["inclusion"]
    assert uv["notice_search"] == "no matching collected standalone notice found"
    assert not evidence.errors
    serialized = json.dumps({"python": result, "notices": evidence.notices})
    assert "PRIVATE-SOURCE" not in serialized and "SECRET-DO-NOT-COLLECT" not in serialized


def test_ensurepip_archive_and_nested_vendor_evidence(modules, tmp_path):
    _, probe = modules
    site, stdlib = tmp_path / "site", tmp_path / "stdlib"
    site.mkdir()
    wheel = stdlib / "ensurepip/_bundled/pip-9-py3-none-any.whl"
    wheel.parent.mkdir(parents=True)
    with zipfile.ZipFile(wheel, "w") as z:
        z.writestr("pip-9.dist-info/METADATA", "Name: pip\nVersion: 9\n")
        z.writestr("pip/_vendor/certifi/LICENSE", "MPL notice")
        z.writestr("pip/_vendor/certifi/cacert.pem", "synthetic CA source")
        z.writestr("pip/_vendor/vendor.txt", "certifi==7\n")
        z.writestr("pip/__init__.py", "UNRELATED SOURCE")
    evidence = probe.Evidence()
    result = probe.collect_python([site], stdlib, evidence)
    archive = result["bootstrap_wheels"][0]
    assert archive["distributions"][0]["version"] == "9"
    assert archive["vendor_manifests"][0]["pins"] == [{"name": "certifi", "version": "7"}]
    assert "!/pip/_vendor/certifi/cacert.pem" in result["certificate_bundles"][0]["path"]
    assert len(evidence.notices) == 1


def test_debian_sources_and_exact_gzip_notice_bytes(modules, tmp_path):
    _, probe = modules
    docs, common = tmp_path / "doc", tmp_path / "common"
    notice = gzip.compress(b"Copyright Unicode, Inc.", mtime=0)
    path = make_file(docs, "libexample/copyright.gz", notice)
    make_file(docs, "libexample/unrelated.conf", b"DO NOT COLLECT")
    make_file(common, "GPL-2", b"synthetic license")
    run = lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="libexample:amd64\t1+deb\texample-source\t1\tii \nremoved\t0\tremoved\t0\trc \n")
    evidence = probe.Evidence()
    rows = probe.collect_debian(evidence, docs, common, run)
    assert len(rows) == 1 and rows[0]["source_package"] == "example-source"
    assert rows[0]["source_version"] == "1"
    row = next(r for r in evidence.notices if r["origin"] == str(path))
    assert base64.b64decode(row["content_base64"]) == notice
    assert evidence.notice_hits["ICU/Unicode"] == [str(path)]
    assert all("unrelated" not in r["origin"] for r in evidence.notices)


def test_notice_limits_and_keyword_absence_are_not_clearance(modules, monkeypatch):
    _, probe = modules
    evidence = probe.Evidence()
    evidence.notice("LICENSE", b"provided without warranty of fitness for any particular purpose")
    assert not evidence.notice_hits["ICU/Unicode"]  # 'particular' is not ICU evidence.
    monkeypatch.setattr(probe, "MAX_NOTICE", 4)
    evidence.notice("NOTICE", b"too large")
    assert evidence.errors and len(evidence.notices) == 1


def test_notice_symlinks_cannot_read_outside_roots(modules, tmp_path):
    _, probe = modules
    root = tmp_path / "doc"
    root.mkdir()
    outside = make_file(tmp_path, "secret", b"PRIVATE")
    link = root / "LICENSE"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Host does not allow unprivileged symlinks")
    evidence = probe.Evidence()
    evidence.file_notice(link, [root])
    assert evidence.errors and not evidence.notices


def test_notice_path_outside_roots_is_rejected_without_symlink_privileges(modules, tmp_path):
    _, probe = modules
    outside = make_file(tmp_path, "other/NOTICE", b"PRIVATE")
    evidence = probe.Evidence()
    evidence.file_notice(outside, [tmp_path / "allowed"])
    assert evidence.errors and not evidence.notices


def test_dpkg_failure_remains_visible_and_does_not_invent_package_versions(modules):
    _, probe = modules
    evidence = probe.Evidence()
    result = probe.collect_debian(evidence, runner=lambda *a, **kw: SimpleNamespace(returncode=1))
    assert result == [] and evidence.errors
    result = probe.parse_debian("example\t1\t\t\tii \n")
    assert result[0]["source_package"] is None and result[0]["source_version"] is None


def test_declared_notice_escape_is_missing_not_copied(modules, tmp_path):
    _, probe = modules
    site, stdlib = tmp_path / "site", tmp_path / "stdlib"
    stdlib.mkdir()
    make_file(site, "pkg.dist-info/METADATA", b"Name: pkg\nVersion: 1\nLicense-File: ../../secret\n")
    make_file(tmp_path, "secret", b"PRIVATE")
    evidence = probe.Evidence()
    result = probe.collect_python([site], stdlib, evidence)
    assert result["distributions"][0]["declared_notice_status"][0]["present"] is False
    assert not evidence.notices
    assert any(r["component"] == "pkg" for r in probe.review_items(result, evidence))


@pytest.mark.parametrize("blob", [b"not ELF", elf()[:120]])
def test_elf_parser_reports_unsupported_or_truncated_input(modules, blob):
    with pytest.raises((ValueError, struct.error)):
        modules[1].elf_needed(blob)


def test_build_metadata_projects_only_image_identifiers(modules):
    host, _ = modules
    result = host.build_identifiers({"buildx.build.provenance": {"invocation": {"environment": "SECRET"},
        "materials": [{"uri": "pkg:docker/python@3?platform=linux%2Famd64&token=SECRET", "digest": {"sha256": "c" * 64}},
                      {"uri": "git+https://user:SECRET@example/repo", "digest": {"sha1": COMMIT}}]},
        "containerimage.config.digest": IMAGE, "unrelated": "SECRET"})
    text = json.dumps(result)
    assert "SECRET" not in text and "environment" not in text and "git+" not in text
    assert result["resolved_docker_image_materials"][0]["uri"] == "pkg:docker/python@3?platform=linux%2Famd64"
    assert result["containerimage.config.digest"] == IMAGE
    assert "unavailable" in host.build_identifiers({})["resolution_status"]


def fake_probe(executable, *, errors=None):
    data = b"Copyright synthetic installed component"
    return {"interpreter": {"executable": executable, "platform": "linux", "machine": "x86_64", "uid": 10001},
            "errors": errors or [], "notices": [{"origin": executable + "/LICENSE", "gzip": False,
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "content_base64": base64.b64encode(data).decode()}]}


def fake_docker(calls, fail_first=False):
    def run(args, **kwargs):
        calls.append((args, kwargs))
        if args[0] == "git":
            return b"" if "status" in args else COMMIT.encode()
        if args[:3] == ["docker", "container", "inspect"]:
            return IMAGE.encode()
        if args[:3] == ["docker", "image", "inspect"]:
            return json.dumps({"id": IMAGE, "os": "linux", "architecture": "amd64", "user": "10001:10001"}).encode()
        if args[:2] == ["docker", "run"]:
            executable = args[args.index("--entrypoint") + 1]
            if fail_first and executable == "/usr/local/bin/python":
                raise RuntimeError("PRIVATE failure text")
            return json.dumps(fake_probe(executable)).encode()
        raise AssertionError(args)
    return run


@pytest.mark.parametrize("fail_first", [False, True])
def test_collection_binds_actual_image_and_retains_partial_diagnostics(modules, tmp_path, fail_first):
    host, _ = modules
    calls = []
    result = host.collect(tmp_path, "ignored:tag", "staging", run=fake_docker(calls, fail_first))
    assert result["collection_status"] == ("partial" if fail_first else "complete")
    assert result["source_commit"] == COMMIT
    assert result["image_binding"]["staging_container"] == IMAGE
    index = json.loads((tmp_path / "notices-index.json").read_text())
    assert len(index) == (1 if fail_first else 2)
    assert len(list((tmp_path / "notices").iterdir())) == 1  # Content-addressed deduplication.
    assert "PRIVATE" not in (tmp_path / "inventory.json").read_text()
    for args, kwargs in calls:
        if args[:2] != ["docker", "run"]:
            continue
        assert IMAGE in args and "ignored:tag" not in args
        for flag in ["--read-only", "--cap-drop", "--security-opt", "--memory", "--cpus", "--pids-limit", "--network", "--pull"]:
            assert flag in args
        assert args[args.index("--network") + 1] == "none"
        assert args[args.index("--cap-drop") + 1] == "ALL"
        assert not any(a in args for a in ["--privileged", "--user", "--volume", "--mount", "--env"])
        assert b"import sys" in kwargs["payload"]


def test_stopped_or_uncreated_staging_uses_built_id_only(modules, tmp_path):
    host, _ = modules
    iid = tmp_path / "image-id"
    iid.write_text(IMAGE)
    runner = fake_docker([])
    def run(args, **kwargs):
        if args[:3] == ["docker", "container", "inspect"]:
            raise RuntimeError("no container")
        return runner(args, **kwargs)
    image, binding = host.select_image("tag:unused", "staging", iid, run)
    assert image["id"] == binding["build_iidfile"] == IMAGE
    with pytest.raises(ValueError, match="refusing tag-only"):
        host.select_image("tag:unused", "staging", None, run)


def test_mismatched_identity_stops_before_probing(modules, tmp_path):
    host, _ = modules
    iid = tmp_path / "image-id"
    iid.write_text("sha256:" + "d" * 64)
    calls = []
    result = host.collect(tmp_path / "output", "image", "staging", iid, run=fake_docker(calls))
    assert result["collection_status"] == "failed"
    assert not any(args[:2] == ["docker", "run"] for args, kwargs in calls)
    assert (tmp_path / "output/inventory.json").is_file()


def test_unreadable_probe_evidence_makes_collection_partial(modules, tmp_path):
    host, _ = modules
    runner = fake_docker([])
    def run(args, **kwargs):
        if args[:2] == ["docker", "run"]:
            executable = args[args.index("--entrypoint") + 1]
            return json.dumps(fake_probe(executable, errors=[{"origin": "/licenses/NOTICE", "reason": "unreadable"}])).encode()
        return runner(args, **kwargs)
    result = host.collect(tmp_path, "image", "staging", run=run)
    assert result["collection_status"] == "partial"
    assert len(json.loads((tmp_path / "notices-index.json").read_text())) == 2


def test_invalid_optional_build_metadata_does_not_lose_installed_evidence(modules, tmp_path):
    host, _ = modules
    metadata = tmp_path / "build-metadata.json"
    metadata.write_text("not JSON: PRIVATE")
    result = host.collect(tmp_path / "output", "image", "staging", metadata_file=metadata, run=fake_docker([]))
    assert result["collection_status"] == "partial" and len(result["probes"]) == 2
    assert result["errors"][0]["operation"] == "optional build identifiers"
    assert "PRIVATE" not in json.dumps(result)


def test_timeout_removes_only_unique_inventory_container(modules):
    host, _ = modules
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        if args[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired("docker", 180)
        return b""
    with pytest.raises(subprocess.TimeoutExpired):
        host.run_probe(IMAGE, "/usr/local/bin/python", run=run)
    name = calls[0][calls[0].index("--name") + 1]
    assert name.startswith("radio-loadout-inventory-")
    assert calls[1] == ["docker", "container", "rm", "--force", name]


def test_notice_checksum_mismatch_cannot_write_untrusted_filename(modules, tmp_path):
    host, _ = modules
    result = fake_probe("/opt/venv/bin/python")
    result["notices"][0]["sha256"] = "../escape"
    with pytest.raises(ValueError, match="digest"):
        host.store_notices(result, tmp_path, [])
    assert not (tmp_path.parent / "escape").exists()


def test_ci_always_collects_before_upload_and_cleanup_without_permission_changes():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml").read_text()
    job = workflow.split("  container:\n", 1)[1].split("  browser:\n", 1)[0]
    collection = job.index("Collect final image packages")
    assert collection < job.index("Upload container diagnostics") < job.index("Stop the local test container")
    assert "if: ${{ always() }}" in job[collection:job.index("Capture selected container state")]
    assert "--metadata-file generated/container-build/metadata.json" in job
    assert "path: generated/container-diagnostics/" in job and "retention-days: 7" in job
    assert "--read-only" in job and "--cap-drop ALL" in job and "--security-opt no-new-privileges" in job
    assert "--push" not in job and "continue-on-error" not in job
