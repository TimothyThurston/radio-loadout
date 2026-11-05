"""Build/check a local certifi source-evidence ZIP; never download, publish or install."""

import argparse
import io
import json
import re
import tarfile
import tempfile
import zipfile
from pathlib import Path

from retrieve_certifi_sources import MANIFEST, ROOT, SourceCheckError, digest, retrieve

MAX_BUNDLE = 64 * 1024 * 1024
BUNDLE_NAME = "certifi-source-evidence-v1.zip"
README = b"""CERTIFI SOURCE EVIDENCE - LOCAL PREPARATION, NOT RELEASE CLEARANCE

This bundle retains the original source archives selected by the accompanying
source-manifest.json, with their original licenses/notices inside each archive.
The source set covers the reviewed certifi releases, exact upstream snapshots
and pip's namespace-modified wrappers. It is not all Radio Loadout dependencies.
No third-party archive is relicensed under Radio Loadout's PolyForm Strict terms.

bundle-index.json lists archive paths, sizes and SHA-256 values. SHA256SUMS beside
this ZIP identifies the complete ZIP bytes; hashes identify bytes, not legal
clearance or an authenticated publisher. Validate the index against a separately
trusted Radio Loadout source manifest, not a replacement manifest from an
untrusted bundle. The project's verifier does this automatically.

From a trusted Radio Loadout checkout/unpacked source distribution:
  python scripts/bundle_certifi_sources.py --verify-bundle PATH/TO/THIS.zip

For a separate check of retained archives and selected source members, place
the verified archives in a local directory and run from that trusted checkout:
  python scripts/retrieve_certifi_sources.py --download-dir PATH/TO/sources --offline
These tools never install/execute the archived sources or update certificate trust.

LIMITATIONS: Historical Mozilla inputs and generator responses remain unresolved.
This source set does not claim complete preferred-form source, native/OS coverage,
redistribution readiness, permanent recipient access or legal clearance. Local
creation does not publish a release or establish a retention commitment. Owner
approval of delivery/retention and the remaining reviews are needed before this
is treated as a release source-access arrangement. Keep these limitations with
the bundle; do not substitute expiring CI artifacts for maintained source access.
"""


def payload_spec(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise SourceCheckError("Unsupported source manifest")
    # Working-tree CRLF conversion must not create a different source selection/bundle.
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sources = {}
    for row in manifest["source_archives"]:
        name = row["filename"]
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.tar\.gz", name)
                or name in sources or type(row["bytes"]) is not int
                or not 0 <= row["bytes"] <= 32 * 1024 * 1024
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
            raise SourceCheckError("Invalid/duplicate source archive specification")
        sources[name] = row
    if not sources or len(sources) > 20 or sum(r["bytes"] for r in sources.values()) > MAX_BUNDLE // 2:
        raise SourceCheckError("Source bundle set exceeds its bounded scope")
    index = {"schema_version": 1, "scope": "Certifi source evidence only; remaining preferred-source/access questions open.",
             "source_manifest_sha256": digest(manifest_bytes),
             "source_manifest_encoding": "Canonical JSON: sorted keys, UTF-8, LF",
             "archives": [{"path": "sources/" + name, "bytes": sources[name]["bytes"],
                           "sha256": sources[name]["sha256"]} for name in sorted(sources)]}
    metadata = {"README.txt": README, "source-manifest.json": manifest_bytes,
                "bundle-index.json": (json.dumps(index, indent=2, sort_keys=True) + "\n").encode()}
    return manifest, sources, metadata


def verify_bundle(path, manifest_bytes):
    """Check against the separately trusted manifest; no extraction or archived-code execution."""
    _, sources, metadata = payload_spec(manifest_bytes)
    if path.is_symlink():
        raise SourceCheckError("Bundle path must not be a link")
    with path.open("rb") as stream:
        data = stream.read(MAX_BUNDLE + 1)
    if len(data) > MAX_BUNDLE:
        raise SourceCheckError("Bundle exceeds read limit")
    expected = set(metadata) | {"sources/" + name for name in sources}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        names = [r.filename for r in entries]
        if len(names) != len(set(names)) or set(names) != expected:
            raise SourceCheckError("Missing/extra/duplicate bundle entries")
        for member in entries:
            mode = (member.external_attr >> 16) & 0o170000
            if (member.is_dir() or mode not in (0, 0o100000) or member.flag_bits & 1
                    or member.compress_type != zipfile.ZIP_STORED):
                raise SourceCheckError("Unsupported linked/encrypted/compressed bundle entry")
            name = member.filename
            reference = metadata.get(name)
            spec = sources[name.removeprefix("sources/")] if reference is None else None
            size = len(reference) if reference is not None else spec["bytes"]
            checksum = digest(reference) if reference is not None else spec["sha256"]
            if member.file_size != size:
                raise SourceCheckError("Bundle entry size mismatch")
            with archive.open(member) as stream:
                content = stream.read(size + 1)
            if len(content) != size or digest(content) != checksum:
                raise SourceCheckError("Bundle entry checksum mismatch")
    return {"status": "verified", "sha256": digest(data), "bytes": len(data),
            "source_archives": len(sources), "source_manifest_sha256": digest(metadata["source-manifest.json"]),
            "scope": "Retained source-evidence bytes only; not complete preferred source or permanent access."}


def build_bundle(source_dir, output_dir, manifest_bytes):
    manifest, sources, metadata = payload_spec(manifest_bytes)
    if output_dir.exists() or output_dir.is_symlink():
        raise SourceCheckError("Output directory already exists; choose a new directory")
    # Always offline. The existing retrieval tool must first obtain/pin sources separately.
    retrieve(source_dir, manifest, offline=True)
    with tempfile.TemporaryDirectory(prefix="radio-loadout-certifi-bundle-") as temporary:
        candidate = Path(temporary) / BUNDLE_NAME
        with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
            for name in sorted(set(metadata) | {"sources/" + n for n in sources}):
                if name in metadata:
                    data = metadata[name]
                else:
                    spec = sources[name.removeprefix("sources/")]
                    path = source_dir / spec["filename"]
                    if path.is_symlink():
                        raise SourceCheckError("Source archive path is a link")
                    with path.open("rb") as stream:
                        data = stream.read(spec["bytes"] + 1)
                    if len(data) != spec["bytes"] or digest(data) != spec["sha256"]:
                        raise SourceCheckError("Source changed after offline verification")
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        result = verify_bundle(candidate, manifest_bytes)
        # A new destination only, after the complete candidate passes. Never overwrite a release.
        output_dir.mkdir(parents=True, exist_ok=False)
        with (output_dir / BUNDLE_NAME).open("xb") as target:
            target.write(candidate.read_bytes())
        with (output_dir / "SHA256SUMS").open("x", encoding="ascii", newline="\n") as target:
            target.write(result["sha256"] + "  " + BUNDLE_NAME + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output-dir", type=Path, help="New local directory for the ZIP and SHA256SUMS")
    mode.add_argument("--verify-bundle", type=Path, help="Offline check against the checkout's trusted source manifest")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "generated/certifi-sources")
    args = parser.parse_args()
    try:
        manifest_bytes = MANIFEST.read_bytes()
        result = (verify_bundle(args.verify_bundle, manifest_bytes) if args.verify_bundle
                  else build_bundle(args.source_dir, args.output_dir, manifest_bytes))
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError,
            zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        result = {"status": "failed", "error_type": type(error).__name__}
        if isinstance(error, SourceCheckError):
            result["reason"] = str(error)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "verified" else 1)


if __name__ == "__main__":
    main()
