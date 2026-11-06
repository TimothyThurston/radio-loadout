"""Build/audit both distributions, then test only the installed wheel outside the repo."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

from verify_third_party_notices import bundle_payload

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ASSETS = {
    "radio_loadout/web/static/backup-format.js",
    "radio_loadout/web/static/builder.js",
    "radio_loadout/web/static/loadout-format.js",
    "radio_loadout/web/static/settings-plan.js",
    "radio_loadout/web/static/radio-settings.js",
    "radio_loadout/web/static/styles.css",
    "radio_loadout/web/static/input-limits.json",
    "radio_loadout/web/templates/index.html",
    "radio_loadout/web/templates/builder.html",
    "radio_loadout/web/templates/radio-settings.html",
    "radio_loadout/web/templates/settings-editor.html",
}
FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
                   ".ruff_cache", "test-results", "playwright-report", "build", "dist"}


def source_payload(root: Path) -> dict[str, bytes]:
    """Python packages and explicitly supported runtime resource types."""
    payload = {}
    package = root / "src/radio_loadout"
    for filename in package.rglob("*"):
        if not filename.is_file():
            continue
        relative = filename.relative_to(root / "src").as_posix()
        if filename.suffix == ".py":
            parents = filename.relative_to(package).parts[:-1]
            if not all((package.joinpath(*parents[:index]) / "__init__.py").is_file()
                       for index in range(len(parents) + 1)):
                continue
        elif not (
            relative.startswith("radio_loadout/web/static/") and filename.suffix in {".js", ".css", ".json"}
            or relative.startswith("radio_loadout/web/templates/") and filename.suffix == ".html"
        ):
            continue
        payload[relative] = filename.read_bytes()
    payload.update({"radio_loadout/third_party_notices/v1/" + name: data
                    for name, data in bundle_payload(root).items()})
    missing = REQUIRED_ASSETS - payload.keys()
    if missing:
        raise RuntimeError(f"Required source assets are missing: {sorted(missing)}")
    return payload


def check_member(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise RuntimeError(f"Unsafe archive member: {name}")
    if FORBIDDEN_PARTS.intersection(path.parts) or path.suffix in {".pyc", ".pyo"}:
        raise RuntimeError(f"Accidental generated file in distribution: {name}")
    if any(part == ".env" or part.startswith(".env.") for part in path.parts):
        raise RuntimeError(f"Environment file in distribution: {name}")
    if "/importers/src/" in name:
        raise RuntimeError(f"Accidental nested importer in distribution: {name}")


def audit_distributions(wheel: Path, sdist: Path, root: Path = ROOT) -> dict:
    expected = source_payload(root)
    with zipfile.ZipFile(wheel) as archive:
        wheel_files = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    with tarfile.open(sdist, "r:gz") as archive:
        source_files = {}
        roots = set()
        for member in archive.getmembers():
            check_member(member.name)
            roots.add(PurePosixPath(member.name).parts[0])
            if member.isdir():
                continue
            if not member.isfile():
                raise RuntimeError(f"Unexpected source archive link/device: {member.name}")
            source_files[str(PurePosixPath(*PurePosixPath(member.name).parts[1:]))] = archive.extractfile(member).read()
        if len(roots) != 1:
            raise RuntimeError("Source distribution must have one root directory.")
    for name in wheel_files:
        check_member(name)
    package_files = {name: data for name, data in wheel_files.items() if name.startswith("radio_loadout/")}
    if package_files != expected:
        missing, extra = expected.keys() - package_files.keys(), package_files.keys() - expected.keys()
        changed = {name for name in expected.keys() & package_files.keys() if expected[name] != package_files[name]}
        raise RuntimeError(f"Wheel payload mismatch: missing={sorted(missing)}, extra={sorted(extra)}, changed={sorted(changed)}")
    metadata_roots = {PurePosixPath(name).parts[0] for name in wheel_files if ".dist-info/" in name}
    if len(metadata_roots) != 1 or any(
        name not in expected and PurePosixPath(name).parts[0] not in metadata_roots for name in wheel_files
    ):
        raise RuntimeError("Unexpected top-level wheel files or metadata directories.")
    metadata_root = next(iter(metadata_roots))
    for name in ("LICENSE", "COPYRIGHT"):
        original = (root / name).read_bytes()
        if wheel_files.get(f"{metadata_root}/licenses/{name}") != original:
            raise RuntimeError(f"Wheel omits/changes license notice: {name}")
        if source_files.get(name) != original:
            raise RuntimeError(f"Source distribution omits/changes license notice: {name}")
    for label, data in (("wheel", wheel_files[f"{metadata_root}/METADATA"]),
                        ("sdist", source_files["PKG-INFO"])):
        metadata = BytesParser().parsebytes(data)
        if metadata["License-Expression"] != "LicenseRef-PolyForm-Strict-1.0.0":
            raise RuntimeError(f"Incorrect {label} license expression")
        if set(metadata.get_all("License-File", [])) != {"LICENSE", "COPYRIGHT"}:
            raise RuntimeError(f"Incorrect {label} license file metadata")
    for name, data in expected.items():
        if source_files.get(f"src/{name}") != data:
            raise RuntimeError(f"Source distribution omits/changes runtime file: {name}")
    # A usable source archive must also contain the test fixtures and smoke tooling.
    development_files = {"README.md", "pyproject.toml", "MANIFEST.in", "package.json",
                         "package-lock.json", "playwright.config.mjs", "Dockerfile", ".dockerignore",
                         "LICENSE", "COPYRIGHT", "CONTRIBUTING.md", ".gitattributes",
                         "scripts/certifi-source-manifest.json"}
    for directory, extensions in (("tests", {".py", ".mjs", ".csv", ".json", ".md"}),
                                  ("docs", {".md"}), ("scripts", {".py", ".mjs"}),
                                  ("deploy", {".in", ".lock"})):
        development_files.update(
            filename.relative_to(root).as_posix() for filename in (root / directory).rglob("*")
            if filename.is_file() and (filename.suffix in extensions or filename.name == ".gitattributes")
        )
    for name in development_files:
        if source_files.get(name) != (root / name).read_bytes():
            raise RuntimeError(f"Source distribution omits/changes development file: {name}")
    expected_source = {f"src/{name}" for name in expected} | development_files | {"PKG-INFO", "setup.cfg"}
    unexpected = {name for name in source_files if name not in expected_source
                  and not name.startswith("src/radio_loadout.egg-info/")}
    if unexpected:
        raise RuntimeError(f"Unexpected source distribution files: {sorted(unexpected)}")
    return {wheel.name: sorted(wheel_files), sdist.name: sorted(source_files)}


def run(command: list[str], cwd: Path, env: dict, log: Path) -> None:
    print(f"Running: {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8",
                            errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    log.write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        print(result.stdout, flush=True)
        raise subprocess.CalledProcessError(result.returncode, command)
    if log.name == "probe.log":
        print(result.stdout, end="", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "dist", help="Keep verified artifacts and logs here (default: dist/).")
    args = parser.parse_args()
    destination = args.dist_dir.resolve()
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("PYTHON") and key.upper() != "VIRTUAL_ENV"}
    with tempfile.TemporaryDirectory(prefix="radio-loadout-package-") as directory:
        scratch = Path(directory).resolve()
        if scratch.is_relative_to(ROOT):
            raise RuntimeError("The system temporary directory must be outside the repository.")
        work = scratch / "working"
        work.mkdir()
        artifacts = scratch / "artifacts"
        artifacts.mkdir()
        print(f"External temporary environment/workspace: {scratch}", flush=True)
        try:
            # Default build creates an sdist, then builds the wheel from that sdist.
            run([sys.executable, "-I", "-m", "build", "--outdir", str(artifacts), str(ROOT)],
                work, env, artifacts / "build.log")
            wheels, sdists = list(artifacts.glob("*.whl")), list(artifacts.glob("*.tar.gz"))
            if len(wheels) != 1 or len(sdists) != 1:
                raise RuntimeError("Expected exactly one new wheel and one source distribution.")
            inventory = audit_distributions(wheels[0], sdists[0])
            (artifacts / "distribution-contents.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
            manifest = work / "expected-package.json"
            manifest.write_text(json.dumps({name: hashlib.sha256(data).hexdigest()
                                            for name, data in source_payload(ROOT).items()}), encoding="utf-8")
            venv_path = scratch / "venv"
            venv.EnvBuilder(with_pip=True, system_site_packages=False).create(venv_path)
            python = str(venv_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
            run([python, "-I", "-m", "pip", "--isolated", "install", str(wheels[0])],
                work, env, artifacts / "install.log")
            run([python, "-I", "-m", "pip", "--isolated", "check"], work, env, artifacts / "dependencies.log")
            probe = work / "package_smoke_probe.py"
            shutil.copyfile(ROOT / "scripts/package_smoke_probe.py", probe)
            run([python, "-I", str(probe), str(ROOT), str(manifest)], work, env, artifacts / "probe.log")
            print("Packaging smoke check passed (wheel + sdist, isolated installed app).", flush=True)
        finally:
            destination.mkdir(parents=True, exist_ok=True)
            for artifact in artifacts.iterdir():
                if artifact.is_file():
                    shutil.copyfile(artifact, destination / artifact.name)
            print(f"Artifacts and diagnostic logs: {destination}", flush=True)


if __name__ == "__main__":
    main()
