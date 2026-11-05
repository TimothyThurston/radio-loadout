"""Offline source-evidence packaging, byte preservation and qualified scope."""

import copy
import hashlib
import importlib
import json
import stat
import zipfile
from pathlib import Path

import pytest
from test_certifi_sources import specification, tar_bytes

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tool(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("bundle_certifi_sources")


def sources(directory):
    data = tar_bytes([("certifi-test/core.py", b"synthetic source"),
                      ("certifi-test/LICENSE", b"Synthetic original upstream notice")])
    spec = specification(data)
    notice = b"Synthetic original upstream notice"
    spec["members"]["certifi-test/LICENSE"] = {"bytes": len(notice), "sha256": hashlib.sha256(notice).hexdigest()}
    directory.mkdir()
    (directory / spec["filename"]).write_bytes(data)
    return json.dumps({"schema_version": 1, "source_archives": [spec]}).encode(), data


def test_build_is_offline_reproducible_and_preserves_original_archives_notices(tool, tmp_path, monkeypatch):
    manifest, original = sources(tmp_path / "sources")
    (tmp_path / "sources/.env").write_bytes(b"PRIVATE-DO-NOT-PACKAGE")
    retrieve = tool.retrieve
    def offline_only(*args, **kwargs):
        assert kwargs["offline"] is True
        kwargs["opener"] = lambda *a, **k: pytest.fail("No bundle network access")
        return retrieve(*args, **kwargs)
    monkeypatch.setattr(tool, "retrieve", offline_only)
    first = tool.build_bundle(tmp_path / "sources", tmp_path / "first", manifest)
    second = tool.build_bundle(tmp_path / "sources", tmp_path / "second", manifest)
    assert first == second and first["status"] == "verified"
    a, b = tmp_path / "first" / tool.BUNDLE_NAME, tmp_path / "second" / tool.BUNDLE_NAME
    assert a.read_bytes() == b.read_bytes()
    assert (tmp_path / "first/SHA256SUMS").read_text() == first["sha256"] + "  " + tool.BUNDLE_NAME + "\n"
    with zipfile.ZipFile(a) as z:
        assert z.read("sources/certifi-test.tar.gz") == original
        assert b"Historical Mozilla" in z.read("README.txt")
        assert b"not all Radio Loadout dependencies" in z.read("README.txt")
        assert b"No third-party archive is relicensed" in z.read("README.txt")
        index = json.loads(z.read("bundle-index.json"))
        assert index["source_manifest_encoding"] == "Canonical JSON: sorted keys, UTF-8, LF"
        assert not any(".env" in name for name in z.namelist())
    assert tool.verify_bundle(a, manifest) == first
    assert sorted(p.name for p in (tmp_path / "sources").iterdir()) == [".env", "certifi-test.tar.gz"]


def test_manifest_line_endings_and_key_order_do_not_change_bundle_selection(tool, tmp_path):
    manifest, _ = sources(tmp_path / "sources")
    changed = json.dumps(json.loads(manifest), indent=2, sort_keys=True).replace("\n", "\r\n").encode()
    first = tool.build_bundle(tmp_path / "sources", tmp_path / "first", manifest)
    second = tool.build_bundle(tmp_path / "sources", tmp_path / "second", changed)
    assert first == second
    assert tool.verify_bundle(tmp_path / "first" / tool.BUNDLE_NAME, changed) == first


@pytest.mark.parametrize("case", ["missing", "corrupt", "invalid-tar", "changed-member"])
def test_invalid_input_cannot_create_bundle_or_replace_retained_sources(tool, tmp_path, case):
    manifest, original = sources(tmp_path / "sources")
    path = tmp_path / "sources/certifi-test.tar.gz"
    spec = json.loads(manifest)
    if case == "missing":
        path.unlink()
    elif case == "corrupt":
        path.write_bytes(b"corrupt existing bytes")
    elif case == "invalid-tar":
        path.write_bytes(b"not a tar archive")
        spec["source_archives"][0].update(bytes=path.stat().st_size, sha256=tool.digest(path.read_bytes()))
    else:
        spec["source_archives"][0]["members"]["certifi-test/core.py"]["sha256"] = "0" * 64
    before = path.read_bytes() if path.exists() else None
    with pytest.raises((tool.SourceCheckError, tool.tarfile.TarError)):
        tool.build_bundle(tmp_path / "sources", tmp_path / "out", json.dumps(spec).encode())
    assert not (tmp_path / "out").exists()
    assert (path.read_bytes() if path.exists() else None) == before
    assert original  # Fixture archives are never installed/executed.


def test_existing_output_is_never_overwritten(tool, tmp_path):
    manifest, _ = sources(tmp_path / "sources")
    output = tmp_path / "out"
    output.mkdir()
    sentinel = output / "owner-file.txt"
    sentinel.write_bytes(b"keep")
    with pytest.raises(tool.SourceCheckError, match="already exists"):
        tool.build_bundle(tmp_path / "sources", output, manifest)
    assert list(output.iterdir()) == [sentinel] and sentinel.read_bytes() == b"keep"


@pytest.mark.parametrize("case", ["missing", "extra", "duplicate", "traversal", "modified-source", "modified-guide",
                                  "modified-manifest", "modified-index", "link", "compressed", "oversized"])
def test_bundle_verification_rejects_changed_or_unsafe_contents(tool, tmp_path, monkeypatch, case):
    manifest, _ = sources(tmp_path / "sources")
    tool.build_bundle(tmp_path / "sources", tmp_path / "out", manifest)
    good = tmp_path / "out" / tool.BUNDLE_NAME
    with zipfile.ZipFile(good) as z:
        contents = {name: z.read(name) for name in z.namelist()}
    changed = tmp_path / "changed.zip"
    compression = zipfile.ZIP_DEFLATED if case == "compressed" else zipfile.ZIP_STORED
    with zipfile.ZipFile(changed, "w", compression=compression) as z:
        for name, data in contents.items():
            if case == "missing" and name == "README.txt":
                continue
            mapping = {"modified-source": "sources/certifi-test.tar.gz", "modified-guide": "README.txt",
                       "modified-manifest": "source-manifest.json", "modified-index": "bundle-index.json"}
            if mapping.get(case) == name:
                data = b"changed"
            if case == "link" and name == "README.txt":
                member = zipfile.ZipInfo(name)
                member.create_system = 3
                member.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(member, b"/secret")
            else:
                z.writestr(name, data)
        if case == "extra":
            z.writestr("private.txt", b"not part of reviewed sources")
        elif case == "traversal":
            z.writestr("../outside", b"unsafe")
        elif case == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                z.writestr("README.txt", contents["README.txt"])
    if case == "oversized":
        monkeypatch.setattr(tool, "MAX_BUNDLE", 4)
    with pytest.raises(tool.SourceCheckError):
        tool.verify_bundle(changed, manifest)


def test_untrusted_embedded_manifest_cannot_replace_external_trust_root(tool, tmp_path):
    manifest, _ = sources(tmp_path / "sources")
    altered = json.loads(manifest)
    altered["source_archives"][0]["role"] = "different source selection record"
    tool.build_bundle(tmp_path / "sources", tmp_path / "out", json.dumps(altered).encode())
    with pytest.raises(tool.SourceCheckError):
        tool.verify_bundle(tmp_path / "out" / tool.BUNDLE_NAME, manifest)


@pytest.mark.parametrize("case", ["filename", "duplicate", "version", "empty", "hash", "bool-size", "large-set"])
def test_invalid_manifest_cannot_expand_bundle_scope(tool, tmp_path, case):
    manifest, _ = sources(tmp_path / "sources")
    parsed = json.loads(manifest)
    source = parsed["source_archives"][0]
    if case == "filename":
        source["filename"] = "../outside.tar.gz"
    elif case == "duplicate":
        parsed["source_archives"].append(copy.deepcopy(source))
    elif case == "version":
        parsed["schema_version"] = True
    elif case == "empty":
        parsed["source_archives"] = []
    elif case == "hash":
        source["sha256"] = "unreviewed"
    elif case == "bool-size":
        source["bytes"] = True
    else:
        source["bytes"] = 32 * 1024 * 1024 + 1
    with pytest.raises(tool.SourceCheckError):
        tool.build_bundle(tmp_path / "sources", tmp_path / "out", json.dumps(parsed).encode())
    assert not (tmp_path / "out").exists()


def test_cli_failure_is_nonzero_without_traceback_or_publication(tool, tmp_path, monkeypatch, capsys):
    manifest, _ = sources(tmp_path / "sources")
    monkeypatch.setattr(tool, "MANIFEST", tmp_path / "source-manifest.json")
    tool.MANIFEST.write_bytes(manifest)
    monkeypatch.setattr("sys.argv", ["bundle_certifi_sources.py", "--source-dir", str(tmp_path / "missing"),
                                   "--output-dir", str(tmp_path / "out")])
    with pytest.raises(SystemExit) as outcome:
        tool.main()
    assert outcome.value.code == 1
    message = capsys.readouterr().out
    assert json.loads(message)["status"] == "failed" and "Traceback" not in message
    assert not (tmp_path / "out").exists()


def test_cli_build_and_independent_verification_report_same_checksum(tool, tmp_path, monkeypatch, capsys):
    manifest, _ = sources(tmp_path / "sources")
    monkeypatch.setattr(tool, "MANIFEST", tmp_path / "source-manifest.json")
    tool.MANIFEST.write_bytes(manifest)
    for args in (["--source-dir", str(tmp_path / "sources"), "--output-dir", str(tmp_path / "out")],
                 ["--verify-bundle", str(tmp_path / "out" / tool.BUNDLE_NAME)]):
        monkeypatch.setattr("sys.argv", ["bundle_certifi_sources.py", *args])
        with pytest.raises(SystemExit) as outcome:
            tool.main()
        assert outcome.value.code == 0
        result = json.loads(capsys.readouterr().out)
        assert result["status"] == "verified" and "not complete" in result["scope"]
        assert result["sha256"] in (tmp_path / "out/SHA256SUMS").read_text()
