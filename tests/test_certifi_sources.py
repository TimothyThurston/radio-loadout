"""Bounded, nonexecuting certifi source retrieval and qualified image correspondence."""

import copy
import hashlib
import importlib
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tool(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("retrieve_certifi_sources")


def tar_bytes(files):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data in files:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return output.getvalue()


def specification(data, member_data=b"synthetic source"):
    return {"filename": "certifi-test.tar.gz", "url": "https://files.pythonhosted.org/pinned/certifi-test.tar.gz",
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "members": {"certifi-test/core.py": {"bytes": len(member_data), "sha256": hashlib.sha256(member_data).hexdigest()}}}


class Response(io.BytesIO):
    def geturl(self):
        return "https://files.pythonhosted.org/pinned/certifi-test.tar.gz"


def test_pinned_retrieval_keeps_archive_without_extracting_or_running(tool, tmp_path):
    data = tar_bytes([("certifi-test/core.py", b"synthetic source")])
    spec = specification(data)
    calls = []
    def opener(url, timeout):
        calls.append((url, timeout))
        return Response(data)
    result = tool.retrieve(tmp_path, {"source_archives": [spec]}, opener=opener)
    assert result[0]["sha256"] == spec["sha256"] and len(calls) == 1
    assert sorted(p.name for p in tmp_path.iterdir()) == [spec["filename"]]
    assert (tmp_path / spec["filename"]).read_bytes() == data
    assert tool.retrieve(tmp_path, {"source_archives": [spec]}, offline=True) == result


def test_corrupt_cache_is_not_overwritten_or_silently_refetched(tool, tmp_path):
    data = tar_bytes([("certifi-test/core.py", b"synthetic source")])
    spec = specification(data)
    path = tmp_path / spec["filename"]
    path.write_bytes(b"corrupt existing archive")
    def forbidden(*args, **kwargs):
        pytest.fail("must not refetch a corrupt cached source")
    with pytest.raises(tool.SourceCheckError, match="checksum"):
        tool.retrieve(tmp_path, {"source_archives": [spec]}, opener=forbidden)
    assert path.read_bytes() == b"corrupt existing archive"


def test_offline_missing_never_accesses_network(tool, tmp_path):
    spec = specification(b"not downloaded")
    with pytest.raises(tool.SourceCheckError, match="Offline"):
        tool.retrieve(tmp_path, {"source_archives": [spec]}, offline=True,
                      opener=lambda *a, **k: pytest.fail("network forbidden"))


def test_bad_download_never_becomes_a_retained_source_archive(tool, tmp_path):
    spec = specification(b"reviewed")
    with pytest.raises(tool.SourceCheckError, match="Downloaded archive checksum"):
        tool.retrieve(tmp_path, {"source_archives": [spec]}, opener=lambda *a, **k: Response(b"changed"))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name", ["../outside.py", "/absolute.py", "C:/drive.py"])
def test_unsafe_archive_members_rejected_without_extraction(tool, tmp_path, name):
    data = tar_bytes([("certifi-test/core.py", b"synthetic source"), (name, b"unsafe")])
    path = tmp_path / "source.tar.gz"
    path.write_bytes(data)
    with pytest.raises(tool.SourceCheckError, match="Unsafe"):
        tool.verify_archive(path, specification(data))


@pytest.mark.parametrize("case", ["duplicate", "missing", "changed"])
def test_missing_duplicate_or_changed_source_member_rejected(tool, tmp_path, case):
    files = [("certifi-test/core.py", b"synthetic source")]
    if case == "duplicate":
        files *= 2
    elif case == "missing":
        files = [("certifi-test/other.py", b"synthetic source")]
    else:
        files = [("certifi-test/core.py", b"modified contents")]
    data = tar_bytes(files)
    path = tmp_path / "source.tar.gz"
    path.write_bytes(data)
    with pytest.raises(tool.SourceCheckError):
        tool.verify_archive(path, specification(data))


@pytest.mark.parametrize("url", ["http://files.pythonhosted.org/x", "https://example.com/x", "https://user:pass@files.pythonhosted.org/x"])
def test_source_download_never_downgrades_or_uses_arbitrary_hosts(tool, url):
    with pytest.raises(tool.SourceCheckError):
        tool.official_url(url)


def image_evidence(tool, path):
    manifest = json.loads(tool.MANIFEST.read_bytes())
    notice = b"synthetic source-form notice"
    for release in manifest["releases"]:
        release["notice_sha256"] = tool.digest(notice)
    releases = {r["version"]: r for r in manifest["releases"]}
    probe = {"errors": [], "python": {"certificate_bundles": [], "vendor_manifests": [],
                                      "bootstrap_wheels": [], "distributions": []}}
    python = probe["python"]
    index = []
    stored = "notices/" + tool.digest(notice) + ".txt"
    (path / "notices").mkdir(parents=True)
    (path / stored).write_bytes(notice)
    for record in manifest["inventory_copies"]:
        python["certificate_bundles"].append({"path": record["bundle_path"], "sha256": releases[record["version"]]["cacert_sha256"]})
        vendor = {"origin": record["version_origin"], "pins": [{"name": "certifi", "version": record["version"]}]}
        if record["kind"] == "application":
            python["distributions"].append({"name": "certifi", "version": record["version"], "origin": record["version_origin"]})
        elif record["kind"] == "ensurepip-bootstrap":
            wheel = next(w for w in manifest["review_reference_wheels"] if w["filename"].startswith("pip-"))
            python["bootstrap_wheels"].append({"path": record["bundle_path"].split("!/")[0],
                                               "sha256": wheel["sha256"], "vendor_manifests": [vendor]})
        else:
            python["vendor_manifests"].append(vendor)
        for origin in record["notice_origins"]:
            index.append({"origin": origin, "stored_as": stored, "sha256": tool.digest(notice),
                          "bytes": len(notice), "gzip": False})
    inventory = {"collection_status": "complete", "errors": [], "source_commit": "a" * 40,
                 "image": {"id": "sha256:" + "b" * 64}, "probes": [probe]}
    save(path, inventory, index)
    return manifest, inventory, index


def save(path, inventory, index):
    (path / "inventory.json").write_text(json.dumps(inventory))
    (path / "notices-index.json").write_text(json.dumps(index))


def test_image_check_identifies_four_copies_without_asserting_wrapper_or_mozilla_provenance(tool, tmp_path):
    manifest, _, _ = image_evidence(tool, tmp_path)
    result = tool.check_inventory(tmp_path, manifest)
    assert result["copies_checked"] == 4
    assert "wrapper files" in result["scope"] and "unverified" in result["scope"]


@pytest.mark.parametrize("case", ["new-location", "pem", "version", "bootstrap", "notice", "escape", "partial"])
def test_image_correspondence_fails_when_reviewed_evidence_changes(tool, tmp_path, case):
    manifest, inventory, index = image_evidence(tool, tmp_path)
    python = inventory["probes"][0]["python"]
    if case == "new-location":
        python["certificate_bundles"].append({"path": "/new/certifi/cacert.pem", "sha256": "c" * 64})
    elif case == "pem":
        python["certificate_bundles"][0]["sha256"] = "c" * 64
    elif case == "version":
        python["vendor_manifests"][0]["pins"][0]["version"] = "unknown"
    elif case == "bootstrap":
        python["bootstrap_wheels"][0]["sha256"] = "c" * 64
    elif case == "notice":
        index.pop()
    elif case == "escape":
        index[0]["stored_as"] = "../outside.txt"
    else:
        inventory["collection_status"] = "partial"
    save(tmp_path, inventory, index)
    with pytest.raises(tool.SourceCheckError):
        tool.check_inventory(tmp_path, manifest)


def test_main_retains_failure_receipt_without_network_or_unverified_claim(tool, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["retrieve_certifi_sources.py", "--offline", "--download-dir", str(tmp_path)])
    with pytest.raises(SystemExit) as outcome:
        tool.main()
    assert outcome.value.code == 1
    receipt = json.loads((tmp_path / "receipt.json").read_bytes())
    assert receipt["status"] == "failed" and "unresolved" in receipt["scope"]


def test_manifest_is_limited_to_exact_certifi_and_pip_source_references(tool, tmp_path):
    manifest = json.loads(tool.MANIFEST.read_bytes())
    assert {r["version"] for r in manifest["releases"]} == {"2026.6.17", "2026.10.23"}
    assert len(manifest["inventory_copies"]) == 4 and len(manifest["source_archives"]) == 5
    for archive in manifest["source_archives"]:
        tool.official_url(archive["url"])
        assert len(archive["sha256"]) == 64 and archive["members"]
        assert "latest" not in archive["url"] and "/master" not in archive["url"]
    changed = copy.deepcopy(manifest)
    changed["source_archives"][0]["filename"] = "../outside.tar.gz"
    with pytest.raises(tool.SourceCheckError, match="filename"):
        tool.retrieve(tmp_path / "cache", changed, offline=True)
