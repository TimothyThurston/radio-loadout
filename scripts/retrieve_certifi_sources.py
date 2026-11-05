"""Retrieve/check pinned certifi sources locally; never install, extract, publish or update trust."""

import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("certifi-source-manifest.json")
MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_MEMBERS = 20000


class SourceCheckError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def official_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"files.pythonhosted.org", "codeload.github.com"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port):
        raise SourceCheckError("Source URL outside the pinned official archive hosts")


def verify_archive(path, specification):
    if path.is_symlink() or path.stat().st_size > MAX_ARCHIVE:
        raise SourceCheckError("Archive link/size rejected")
    data = path.read_bytes()
    if len(data) != specification["bytes"] or digest(data) != specification["sha256"]:
        raise SourceCheckError("Archive checksum/size mismatch; no fallback to another release")
    wanted = specification["members"]
    checked, names, expanded = {}, set(), 0
    with tarfile.open(path, "r:gz") as archive:
        for count, member in enumerate(archive, 1):
            name = member.name
            parts = PurePosixPath(name)
            expanded += member.size
            if (count > MAX_MEMBERS or expanded > MAX_EXPANDED or parts.is_absolute()
                    or ".." in parts.parts or "\\" in name or ":" in name or name in names):
                raise SourceCheckError("Unsafe/duplicate/oversized archive member listing")
            names.add(name)
            if name not in wanted:
                continue
            expected = wanted[name]
            if not member.isfile() or member.size != expected["bytes"] or member.size > MAX_ARCHIVE:
                raise SourceCheckError("Expected source member type/size mismatch")
            contents = archive.extractfile(member).read(MAX_ARCHIVE + 1)
            if digest(contents) != expected["sha256"]:
                raise SourceCheckError("Source member checksum mismatch")
            checked[name] = expected
    if checked.keys() != wanted.keys():
        raise SourceCheckError("Expected source members missing")
    return {"filename": path.name, "sha256": digest(data), "bytes": len(data), "members": checked}


def retrieve(directory, manifest, *, offline=False, opener=urlopen):
    """Keep original archives unchanged; inspect members without extracting or running them."""
    directory.mkdir(parents=True, exist_ok=True)
    results = []
    for specification in manifest["source_archives"]:
        name = specification["filename"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.tar\.gz", name):
            raise SourceCheckError("Unsafe source archive filename")
        official_url(specification["url"])
        path = directory / name
        if path.is_symlink():
            raise SourceCheckError("Source archive path is a link")
        if not path.exists():
            if offline:
                raise SourceCheckError("Offline source archive missing")
            with opener(specification["url"], timeout=30) as response:
                official_url(response.geturl())
                data = response.read(MAX_ARCHIVE + 1)
            if len(data) > MAX_ARCHIVE or len(data) != specification["bytes"] or digest(data) != specification["sha256"]:
                raise SourceCheckError("Downloaded archive checksum/size mismatch")
            # Only a fully verified archive is given its final name. No extraction/install occurs.
            with tempfile.TemporaryDirectory(prefix=".certifi-source-", dir=directory) as temporary:
                candidate = Path(temporary) / name
                candidate.write_bytes(data)
                verify_archive(candidate, specification)
                candidate.replace(path)
        results.append(verify_archive(path, specification))
    return results


def check_inventory(directory, manifest):
    """Check only recorded certifi PEM/notices/pins; the collector did not hash installed wrappers."""
    inventory_bytes = (directory / "inventory.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    if inventory["collection_status"] != "complete" or inventory["errors"] or any(p["errors"] for p in inventory["probes"]):
        raise SourceCheckError("Installed evidence collection incomplete")
    bundles, vendors, distributions, bootstraps = {}, {}, {}, {}
    for probe in inventory["probes"]:
        python = probe["python"]
        for row in python["certificate_bundles"]:
            if row["path"] in bundles and bundles[row["path"]] != row["sha256"]:
                raise SourceCheckError("Conflicting installed PEM evidence")
            bundles[row["path"]] = row["sha256"]
        vendor_rows = list(python["vendor_manifests"])
        for wheel in python["bootstrap_wheels"]:
            vendor_rows.extend(wheel["vendor_manifests"])
            bootstraps[wheel["path"]] = wheel["sha256"]
        for row in vendor_rows:
            pins = [pin["version"] for pin in row["pins"] if pin["name"].lower() == "certifi"]
            if len(pins) != 1 or (row["origin"] in vendors and vendors[row["origin"]] != pins[0]):
                raise SourceCheckError("Missing/conflicting certifi vendor version")
            vendors[row["origin"]] = pins[0]
        for row in python["distributions"]:
            distributions[row["origin"]] = row
            if row["name"].lower() == "pip" and row["version"] != "26.2.1":
                raise SourceCheckError("Pip changed; review modified certifi source correspondence")
    expected_paths = {row["bundle_path"] for row in manifest["inventory_copies"]}
    if bundles.keys() != expected_paths:
        raise SourceCheckError("Installed certifi locations changed; review source inventory")
    releases = {row["version"]: row for row in manifest["releases"]}
    index = json.loads((directory / "notices-index.json").read_bytes())
    notices = {}
    for row in index:
        notices.setdefault(row["origin"], []).append(row)
    for copy in manifest["inventory_copies"]:
        release = releases[copy["version"]]
        if bundles[copy["bundle_path"]] != release["cacert_sha256"]:
            raise SourceCheckError("Installed certifi PEM differs from reviewed source")
        if copy["kind"] == "application":
            row = distributions[copy["version_origin"]]
            if row["name"].lower() != "certifi" or row["version"] != copy["version"]:
                raise SourceCheckError("Application certifi version mismatch")
        elif vendors.get(copy["version_origin"]) != copy["version"]:
            raise SourceCheckError("Vendored certifi version mismatch")
        if copy["kind"] == "ensurepip-bootstrap":
            path = copy["bundle_path"].split("!/", 1)[0]
            pip_wheel = next(w for w in manifest["review_reference_wheels"] if w["filename"].startswith("pip-"))
            if bootstraps.get(path) != pip_wheel["sha256"]:
                raise SourceCheckError("Bootstrap pip wheel changed")
        for origin in copy["notice_origins"]:
            if origin not in notices:
                raise SourceCheckError("Recorded certifi notice missing")
            for row in notices[origin]:
                if not re.fullmatch(r"notices/[0-9a-f]{64}\.txt", row["stored_as"]):
                    raise SourceCheckError("Unsafe stored certifi notice path")
                contents = (directory / row["stored_as"]).read_bytes()
                if (row["gzip"] or row["sha256"] != digest(contents) or row["bytes"] != len(contents)
                        or digest(contents) != release["notice_sha256"]):
                    raise SourceCheckError("Installed certifi notice differs from reviewed source")
    return {"source_commit": inventory["source_commit"], "image_id": inventory["image"]["id"],
            "inventory_sha256": digest(inventory_bytes), "copies_checked": len(expected_paths),
            "scope": "Recorded PEM, license bytes, version pins and bootstrap wheel only; installed wrapper files and Mozilla preferred-source inputs remain unverified."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-dir", type=Path, default=ROOT / "generated/certifi-sources")
    parser.add_argument("--offline", action="store_true", help="Check existing archives without network access")
    parser.add_argument("--inventory-dir", type=Path, help="Optionally check actual collector evidence for the four known copies")
    args = parser.parse_args()
    args.download_dir.mkdir(parents=True, exist_ok=True)
    result = {"status": "failed", "scope": "Source retrieval/correspondence only; preferred form and permanent recipient access unresolved."}
    try:
        data = MANIFEST.read_bytes()
        manifest = json.loads(data)
        if manifest["schema_version"] != 1:
            raise SourceCheckError("Unsupported source manifest")
        result["manifest_sha256"] = digest(data)
        result["archives"] = retrieve(args.download_dir, manifest, offline=args.offline)
        if args.inventory_dir:
            result["installed_correspondence"] = check_inventory(args.inventory_dir, manifest)
        result["status"] = "verified"
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, SourceCheckError):
            result["reason"] = str(error)
    (args.download_dir / "receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Certifi source retrieval/check: {result['status']}; receipt.json written. No compliance conclusion.")
    raise SystemExit(0 if result["status"] == "verified" else 1)


if __name__ == "__main__":
    main()
