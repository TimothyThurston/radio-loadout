"""Verify supplemental notice bytes locally or against collected final-image evidence."""

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path("src/radio_loadout/third_party_notices/v1")


class NoticeCheckError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative_name(value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
        raise NoticeCheckError("Unsafe notice path")
    return path


def bundle_payload(root=ROOT):
    """Check upstream notice hashes and return every versioned bundle file, including its ledger."""
    directory = root / BUNDLE
    manifest = json.loads((directory / "manifest.json").read_bytes())
    if (manifest["schema_version"], manifest["bundle_version"]) != (1, 1):
        raise NoticeCheckError("Unsupported notice manifest")
    expected = {"manifest.json", "README.md"}
    for notice in manifest["notice_files"]:
        name = str(relative_name(notice["path"]))
        if name in expected:
            raise NoticeCheckError("Duplicate notice path")
        expected.add(name)
        data = (directory / name).read_bytes()
        if sha256(data) != notice["sha256"] or len(data) != notice["bytes"]:
            raise NoticeCheckError("Upstream notice bytes changed")
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in directory.rglob("*")):
        raise NoticeCheckError("Unexpected or missing bundle file/link")
    for component in manifest["components"]:
        if not component["source_url"].startswith("https://") or not re.fullmatch(r"[0-9a-f]{64}", component["source_sha256"]):
            raise NoticeCheckError("Missing component source identity")
        if not component["notice_files"] or not set(component["notice_files"]) <= expected:
            raise NoticeCheckError("Unmapped component notices")
    return {name: (directory / name).read_bytes() for name in sorted(expected)}


def verify_inventory(directory, root=ROOT):
    """Compare actual venv notice bytes and native identities, never a host mount or candidate image."""
    payload = bundle_payload(root)
    inventory_bytes = (directory / "inventory.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    image = inventory["image"]
    if inventory["collection_status"] != "complete" or inventory["errors"]:
        raise NoticeCheckError("Image evidence collection incomplete")
    if (image["os"], image["architecture"], image["user"]) != ("linux", "amd64", "10001:10001"):
        raise NoticeCheckError("Unexpected image platform/user")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image["id"]):
        raise NoticeCheckError("Invalid actual image identity")
    binding = inventory["image_binding"]
    if not binding or any(value != image["id"] for value in binding.values()):
        raise NoticeCheckError("Image binding missing or inconsistent")
    probes = [p for p in inventory["probes"] if p["interpreter"]["executable"] == "/opt/venv/bin/python"]
    if len(probes) != 1 or probes[0]["errors"]:
        raise NoticeCheckError("Missing complete runtime interpreter evidence")
    probe = probes[0]
    distributions = {p["name"].lower().replace("_", "-"): p for p in probe["python"]["distributions"]
                     if p["scope"] == "installed"}
    site = PurePosixPath(distributions["radio-loadout"]["origin"]).parent.parent
    if not site.is_relative_to("/opt/venv"):
        raise NoticeCheckError("Unexpected runtime installation path")
    manifest = json.loads(payload["manifest.json"])
    natives = {p["path"]: p["sha256"] for p in probe["python"]["native_binaries"]}
    for artifact in manifest["runtime_artifacts"]:
        key = artifact["distribution"].lower().replace("_", "-")
        if distributions[key]["version"] != artifact["version"]:
            raise NoticeCheckError("Native distribution changed; review notice applicability")
        if natives.get(str(site / artifact["native_file"])) != artifact["native_sha256"]:
            raise NoticeCheckError("Native binary changed; review notice applicability")
    prefix = str(site / "radio_loadout/third_party_notices/v1") + "/"
    index = json.loads((directory / "notices-index.json").read_bytes())
    found = {}
    for row in index:
        if row["interpreter"] != "/opt/venv/bin/python" or not row["origin"].startswith(prefix):
            continue
        name = row["origin"][len(prefix):]
        if name in found or name not in payload:
            raise NoticeCheckError("Unexpected/duplicate installed bundle file")
        stored = row["stored_as"]
        # The collector uses content-addressed names; never follow artifact-provided arbitrary paths.
        if not re.fullmatch(r"notices/[0-9a-f]{64}\.txt", stored):
            raise NoticeCheckError("Unsafe stored notice path")
        data = (directory / stored).read_bytes()
        if row["gzip"] or row["bytes"] != len(data) or row["sha256"] != sha256(data) or data != payload[name]:
            raise NoticeCheckError("Installed supplemental notice bytes differ")
        found[name] = row["sha256"]
    if found.keys() != payload.keys():
        raise NoticeCheckError("Supplemental bundle missing from actual image evidence")
    return {"status": "passed", "image_id": image["id"], "source_commit": inventory["source_commit"],
            "inventory_sha256": sha256(inventory_bytes), "bundle_version": manifest["bundle_version"],
            "manifest_sha256": sha256(payload["manifest.json"]), "verified_files": found,
            "qualification": "Exact installed supplemental bytes and reviewed native identities only; not license clearance or complete notice/source coverage."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, help="Actual collector output, not the repository bundle")
    parser.add_argument("--output", type=Path, help="Write a bounded diagnostic result, including on failure")
    args = parser.parse_args()
    try:
        result = verify_inventory(args.inventory_dir) if args.inventory_dir else {
            "status": "passed", "scope": "repository bundle only", "files": len(bundle_payload())}
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"status": "failed", "error_type": type(error).__name__}
        if isinstance(error, NoticeCheckError):
            result["reason"] = str(error)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Supplemental notice verification: {result['status']}.")
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
