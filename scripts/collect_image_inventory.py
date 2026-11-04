"""Collect bounded installed-image evidence into local, short-lived diagnostics."""

import argparse
import base64
import hashlib
import json
import re
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode

ROOT = Path(__file__).resolve().parents[1]
IMAGE_FORMAT = ('{"id":{{json .Id}},"os":{{json .Os}},'
                '"architecture":{{json .Architecture}},"user":{{json .Config.User}},'
                '"repo_digests":{{json .RepoDigests}}}')
DIGEST = re.compile(r"sha256:[0-9a-f]{64}$")


def command(args: list[str], *, payload=None, timeout=30) -> bytes:
    result = subprocess.run(args, input=payload, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            timeout=timeout, check=False)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, args)
    return result.stdout


def build_identifiers(metadata: dict) -> dict:
    """Project only image material identifiers; never retain invocation/environment data."""
    provenance = metadata.get("buildx.build.provenance", {})
    predicate = provenance.get("predicate", provenance)
    materials = predicate.get("materials", []) + predicate.get("buildDefinition", {}).get("resolvedDependencies", [])
    selected = []
    for row in materials:
        uri = row.get("uri", "")
        if not uri.startswith("pkg:docker/"):
            continue
        name, _, query = uri.partition("?")
        if not re.fullmatch(r"pkg:docker/[A-Za-z0-9_./:@%+-]+", name):
            continue
        platform = parse_qs(query).get("platform", [])
        if platform and re.fullmatch(r"[a-z0-9_/.-]+", platform[0]):
            name += "?" + urlencode({"platform": platform[0]})
        digests = {key: value for key, value in row.get("digest", {}).items()
                   if key == "sha256" and re.fullmatch(r"[0-9a-f]{64}", value)}
        if digests:
            selected.append({"uri": name, "digest": digests})
    result = {"resolved_docker_image_materials": selected,
              "qualification": "BuildKit-reported image inputs (including possible frontend); not inferred from package locks."}
    for key in ("containerimage.digest", "containerimage.config.digest"):
        value = metadata.get(key)
        if isinstance(value, str) and DIGEST.fullmatch(value):
            result[key] = value
    if not selected:
        result["resolution_status"] = "unavailable in supplied build metadata"
    return result


def select_image(image: str, container: str | None, iidfile: Path | None, run=command):
    candidates = {}
    if iidfile and iidfile.is_file():
        value = iidfile.read_text().strip()
        if not DIGEST.fullmatch(value):
            raise ValueError("invalid build image ID")
        candidates["build_iidfile"] = value
    if container:
        try:
            value = run(["docker", "container", "inspect", "--format", "{{.Image}}", container]).decode().strip()
        except (RuntimeError, subprocess.CalledProcessError):
            value = None
        if value:
            if not DIGEST.fullmatch(value):
                raise ValueError("invalid container image ID")
            candidates["staging_container"] = value
    if len(set(candidates.values())) > 1:
        raise ValueError("staging container and build image IDs differ")
    if container and not candidates:
        raise ValueError("no staging container or build image ID; refusing tag-only fallback")
    selected = next(iter(candidates.values()), image)
    result = json.loads(run(["docker", "image", "inspect", "--format", IMAGE_FORMAT, selected]))
    if not DIGEST.fullmatch(result["id"]):
        raise ValueError("invalid inspected image ID")
    if candidates and result["id"] != selected:
        raise ValueError("inspected image does not match staging image")
    if (result["os"], result["architecture"], result["user"]) != ("linux", "amd64", "10001:10001"):
        raise ValueError("expected Linux amd64 image with configured non-root user")
    return result, candidates


def run_probe(image_id: str, executable: str, *, system=False, run=command) -> dict:
    name = "radio-loadout-inventory-" + uuid.uuid4().hex
    args = ["docker", "run", "--rm", "--name", name, "--pull", "never", "--platform", "linux/amd64",
            "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m,mode=1777",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--memory", "512m", "--cpus", "1", "--pids-limit", "128", "--network", "none",
            "--no-healthcheck", "--interactive", "--entrypoint", executable,
            image_id, "-I", "-B", "-"]
    if system:
        args.append("--system")
    try:
        result = json.loads(run(args, payload=Path(__file__).with_name("image_inventory_probe.py").read_bytes(), timeout=180))
    except subprocess.TimeoutExpired:
        # Only this collector's unique container is removed; the staging container is untouched.
        run(["docker", "container", "rm", "--force", name])
        raise
    interpreter = result["interpreter"]
    if (interpreter["platform"], interpreter["machine"], interpreter["uid"]) != ("linux", "x86_64", 10001):
        raise ValueError("unexpected probe platform or user")
    if interpreter["executable"] != executable:
        raise ValueError("unexpected interpreter executable")
    return result


def store_notices(probe: dict, output: Path, index: list):
    destination = output / "notices"
    destination.mkdir(exist_ok=True)
    total = 0
    for row in probe.pop("notices"):
        digest = row["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid notice digest")
        data = base64.b64decode(row.pop("content_base64"), validate=True)
        total += len(data)
        if len(data) > 4 * 1024 * 1024 or total > 32 * 1024 * 1024:
            raise ValueError("notice payload exceeds limits")
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("notice checksum mismatch")
        filename = digest + (".gz" if row["gzip"] else ".txt")
        (destination / filename).write_bytes(data)
        index.append({**row, "interpreter": probe["interpreter"]["executable"],
                      "stored_as": "notices/" + filename})


def collect(output: Path, image: str, container=None, iidfile=None, metadata_file=None, run=command) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    inventory = {"schema_version": 1, "collected_at_utc": datetime.now(UTC).isoformat(),
                 "collection_status": "failed", "errors": [], "probes": [],
                 "purpose": "Diagnostic evidence, not license clearance or permanent covered-source access."}
    notices = []
    try:
        inventory["source_commit"] = run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
        inventory["working_tree_dirty"] = bool(run(["git", "-C", str(ROOT), "status", "--porcelain"]))
        inventory["source_binding"] = "Checkout HEAD at collection; CI builds and collects in the same checkout. Not an embedded image authorship claim."
        inventory["collector_sha256"] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(__file__).with_name("image_inventory_probe.py"))}
        inventory["image"], inventory["image_binding"] = select_image(image, container, iidfile, run)
        try:
            inventory["build_identifiers"] = build_identifiers(
                json.loads(metadata_file.read_text()) if metadata_file and metadata_file.is_file() else {})
        except (OSError, ValueError, TypeError, AttributeError) as error:
            inventory["build_identifiers"] = {"resolution_status": "supplied build metadata could not be read/projected"}
            inventory["errors"].append({"operation": "optional build identifiers", "error_type": type(error).__name__})
        config_digest = inventory["build_identifiers"].get("containerimage.config.digest")
        if config_digest and config_digest != inventory["image"]["id"]:
            raise ValueError("build metadata config differs from inspected image")
        for executable, system in (("/usr/local/bin/python", True), ("/opt/venv/bin/python", False)):
            try:
                result = run_probe(inventory["image"]["id"], executable, system=system, run=run)
                store_notices(result, output, notices)
                inventory["probes"].append(result)
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
                inventory["errors"].append({"operation": "probe", "interpreter": executable,
                                            "error_type": type(error).__name__,
                                            "exit_code": getattr(error, "returncode", None)})
        inventory["collection_status"] = "complete" if len(inventory["probes"]) == 2 and not (
            inventory["errors"] or any(p["errors"] for p in inventory["probes"])) else "partial"
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError, subprocess.SubprocessError) as error:
        inventory["errors"].append({"operation": "image/source identity", "error_type": type(error).__name__,
                                    "exit_code": getattr(error, "returncode", None)})
    finally:
        (output / "inventory.json").write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output / "notices-index.json").write_text(json.dumps(notices, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="radio-loadout:staging-ci")
    parser.add_argument("--container", help="Bind to this staging container's image, even if stopped.")
    parser.add_argument("--image-id-file", type=Path)
    parser.add_argument("--build-metadata", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated/container-diagnostics/licenses")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        parser.error("Use an empty output directory to avoid mixing different image inventories.")
    result = collect(args.output_dir, args.image, args.container, args.image_id_file, args.build_metadata)
    print(f"Image inventory collection: {result['collection_status']}. Diagnostic files written.")
    raise SystemExit(0 if result["collection_status"] == "complete" else 1)


if __name__ == "__main__":
    main()
