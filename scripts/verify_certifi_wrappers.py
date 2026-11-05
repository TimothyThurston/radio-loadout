"""Offline comparison of installed certifi wrapper hashes with pinned source members."""

import argparse
import json
import re
from pathlib import Path

from retrieve_certifi_sources import MANIFEST, SourceCheckError, check_inventory, digest

WRAPPERS = ("__init__.py", "__main__.py", "core.py", "py.typed")
INTERPRETERS = ("/usr/local/bin/python", "/opt/venv/bin/python")


def expected_wrappers(manifest):
    """Derive expectations from existing reviewed sources, never from collected hashes."""
    archives = {a["filename"]: a for a in manifest["source_archives"]}
    releases = {r["version"]: r for r in manifest["releases"]}
    expected = {}
    for copy in manifest["inventory_copies"]:
        filename = (releases[copy["version"]]["source_archive"] if copy["kind"] == "application"
                    else "pip-26.2.1.tar.gz")
        archive = archives[filename]
        prefix = (filename.removesuffix(".tar.gz") + "/certifi/" if copy["kind"] == "application"
                  else "pip-26.2.1/src/pip/_vendor/certifi/")
        installed_prefix = copy["bundle_path"].removesuffix("cacert.pem")
        for name in WRAPPERS:
            source_member = prefix + name
            source = archive["members"][source_member]
            path = installed_prefix + name
            if path in expected:
                raise SourceCheckError("Duplicate expected certifi wrapper path")
            expected[path] = {"sha256": source["sha256"], "bytes": source["bytes"],
                              "source_archive": filename, "source_member": source_member}
    return expected


def record_map(rows):
    result = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes"}
                or not isinstance(row["path"], str)
                or not isinstance(row["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
                or type(row["bytes"]) is not int or not 0 <= row["bytes"] <= 65536):
            raise SourceCheckError("Malformed certifi wrapper record")
        if row["path"] in result:
            raise SourceCheckError("Duplicate certifi wrapper record within a probe")
        result[row["path"]] = {"sha256": row["sha256"], "bytes": row["bytes"]}
    return result


def verify_inventory(directory, manifest):
    inventory_bytes = (directory / "inventory.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    image = inventory["image"]
    if (inventory["schema_version"] != 1 or inventory["collection_status"] != "complete"
            or inventory["errors"]):
        raise SourceCheckError("Incomplete/unsupported image inventory")
    if ((image["os"], image["architecture"], image["user"]) != ("linux", "amd64", "10001:10001")
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", image["id"])):
        raise SourceCheckError("Unexpected image identity/platform/user")
    binding = inventory["image_binding"]
    if not binding or set(binding) - {"build_iidfile", "staging_container"} or any(
            value != image["id"] for value in binding.values()):
        raise SourceCheckError("Image binding missing or inconsistent")
    if not re.fullmatch(r"[0-9a-f]{40}", inventory["source_commit"]):
        raise SourceCheckError("Invalid source commit identity")
    # Existing certifi checks retain PEM/notices/version/bootstrap-wheel gates.
    correspondence = check_inventory(directory, manifest)
    expected = expected_wrappers(manifest)
    probes = {}
    observed = 0
    for probe in inventory["probes"]:
        interpreter = probe["interpreter"]
        executable = interpreter["executable"]
        if (executable not in INTERPRETERS or executable in probes or probe["errors"]
                or (interpreter["platform"], interpreter["machine"], interpreter["uid"])
                != ("linux", "x86_64", 10001)):
            raise SourceCheckError("Missing/duplicate/invalid interpreter evidence")
        python = probe["python"]
        if (type(python.get("certifi_wrapper_schema_version")) is not int
                or python["certifi_wrapper_schema_version"] != 1):
            raise SourceCheckError("Wrapper collection absent/unsupported; recollect the actual image")
        rows = record_map(python["certifi_wrappers"])
        site_prefix = ("/opt/venv/" if executable == "/opt/venv/bin/python" else "/usr/local/")
        wanted = {path: {"sha256": r["sha256"], "bytes": r["bytes"]}
                  for path, r in expected.items() if "!/" in path or path.startswith(site_prefix)}
        # Venv sysconfig exposes base stdlib/ensurepip, not base site-packages.
        if rows.keys() != wanted.keys():
            raise SourceCheckError("Missing/unexpected certifi wrapper paths for interpreter")
        if rows != wanted:
            raise SourceCheckError("Installed certifi wrapper differs from pinned source")
        for wheel in python["bootstrap_wheels"]:
            nested = record_map(wheel.get("certifi_wrappers", []))
            wheel_wanted = {p: r for p, r in wanted.items() if p.startswith(wheel["path"] + "!/")}
            if nested != wheel_wanted:
                raise SourceCheckError("Bootstrap wrapper evidence missing or inconsistent")
        probes[executable] = len(rows)
        observed += len(rows)
    if set(probes) != set(INTERPRETERS):
        raise SourceCheckError("Both installed interpreter probes are required")
    return {"status": "passed", "source_commit": inventory["source_commit"],
            "image_id": image["id"], "inventory_sha256": digest(inventory_bytes),
            "copies_checked": correspondence["copies_checked"], "unique_files_checked": len(expected),
            "observations_checked": observed, "interpreter_counts": probes,
            "verified_files": expected,
            "qualification": "Exact installed wrapper/typing-marker hashes against pinned source members, "
                             "plus existing PEM/notice/version/bootstrap checks. Repeated ensurepip observations "
                             "are one archive location. Not Mozilla input provenance, permanent source access "
                             "or legal clearance."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest_bytes = MANIFEST.read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest["schema_version"] != 1:
            raise SourceCheckError("Unsupported source manifest")
        result = verify_inventory(args.inventory_dir, manifest)
        result["manifest_sha256"] = digest(manifest_bytes)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result = {"status": "failed", "error_type": type(error).__name__}
        if isinstance(error, SourceCheckError):
            result["reason"] = str(error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Installed certifi wrapper verification: {result['status']}. No compliance conclusion.")
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
