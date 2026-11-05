"""Read installed package/notice evidence; streamed into a restricted image, never installed."""

import base64
import gzip
import hashlib
import io
import json
import os
import platform
import re
import struct
import subprocess
import sys
import sysconfig
import zipfile
from email.parser import BytesParser
from pathlib import Path

NOTICE_NAME = re.compile(r"(?i)(?:^|[._-])(licen[cs]e|copying|copyright|notice|authors|thirdparty)(?:$|[._-])")
NATIVE_NAME = re.compile(r"\.so(?:\.\d+)*$")
MARKERS = {
    "libuv": (b"uv_version_string", b"uv_loop_init"),
    "ICU/Unicode": (b"icu_normalizer", b"icu_properties", b"Unicode-3.0", b"Unicode-DFS"),
    "PyO3": (b"PyO3", b"pyo3"),
    "LibYAML": (b"yaml_get_version_string",),
    "llhttp/http-parser": (b"llhttp_", b"http_parser_"),
    "upb": (b"upb_",),
    "Cython": (b"__pyx_",),
}
NOTICE_TERMS = {
    "libuv": (b"libuv", b"joyent", b"niels provos"),
    "ICU/Unicode": (b"unicode, inc", b"unicode license", b"international components for unicode", b"icu project"),
    "PyO3": (b"pyo3",),
    "LibYAML": (b"libyaml", b"kirill simonov"),
    "llhttp/http-parser": (b"llhttp", b"http-parser", b"fedor indutny"),
    "upb": (b"upb", b"google inc", b"google llc"),
    "Cython": (b"cython",),
}
MAX_NOTICE = 4 * 1024 * 1024
MAX_NOTICES = 32 * 1024 * 1024
MAX_BINARY = 64 * 1024 * 1024
MAX_ENTRIES = 50000
CERTIFI_WRAPPERS = {"__init__.py", "__main__.py", "core.py", "py.typed"}
MAX_WRAPPER = 64 * 1024


def certifi_wrapper_scope(name: str) -> bool:
    """Only direct files in the application/pip certifi packages; never arbitrary source."""
    return name.rsplit("/", 1)[0] in {"certifi", "pip/_vendor/certifi"}


def wrapper_record(origin: str, data: bytes) -> dict:
    return {"path": origin, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def collect_certifi_wrapper(path: Path, root: Path, evidence):
    if not confined(path, [root]) or path.is_symlink() or not path.is_file():
        evidence.error(path, "certifi wrapper link/type rejected")
        return None
    with path.open("rb") as source:
        data = source.read(MAX_WRAPPER + 1)
    if len(data) > MAX_WRAPPER:
        evidence.error(path, "certifi wrapper read limit; collection incomplete")
        return None
    return wrapper_record(str(path), data)


def confined(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve()
    return any(resolved.is_relative_to(root.resolve()) for root in roots)


def elf_needed(data: bytes) -> list[str]:
    """Read ELF64 program/dynamic headers without loading the binary or using ldd."""
    if data[:5] != b"\x7fELF\x02" or data[5:6] not in (b"\x01", b"\x02"):
        raise ValueError("unsupported ELF format")
    endian = "<" if data[5] == 1 else ">"
    header = struct.unpack_from(endian + "HHIQQQIHHHHHH", data, 16)
    offset, size, count = header[4], header[8], header[9]
    if size < 56 or count > 4096:
        raise ValueError("invalid program headers")
    segments = [struct.unpack_from(endian + "IIQQQQQQ", data, offset + i * size)
                for i in range(count)]
    entries = []
    for segment in segments:
        if segment[0] == 2:  # PT_DYNAMIC
            if segment[2] + segment[5] > len(data):
                raise ValueError("truncated dynamic section")
            for pos in range(segment[2], segment[2] + segment[5], 16):
                tag, value = struct.unpack_from(endian + "qQ", data, pos)
                if tag == 0:
                    break
                entries.append((tag, value))
    needed = [value for tag, value in entries if tag == 1]
    if not needed:
        return []
    address = next(value for tag, value in entries if tag == 5)  # DT_STRTAB
    load = next(s for s in segments if s[0] == 1 and s[3] <= address < s[3] + s[5])
    start = load[2] + address - load[3]
    strings_size = next(value for tag, value in entries if tag == 10)  # DT_STRSZ
    strings = data[start:start + strings_size]
    if len(strings) != strings_size:
        raise ValueError("truncated string table")
    result = []
    for index in needed:
        end = strings.index(b"\0", index)
        value = strings[index:end].decode("ascii")
        if not re.fullmatch(r"[A-Za-z0-9_.+-]+", value):
            raise ValueError("unexpected SONAME")
        result.append(value)
    return sorted(set(result))


class Evidence:
    def __init__(self):
        self.notices = []
        self.errors = []
        self.seen = set()
        self.total = 0
        self.notice_hits = {key: [] for key in NOTICE_TERMS}

    def error(self, origin, reason):
        # Exception messages and subprocess stderr are deliberately not recorded.
        self.errors.append({"origin": str(origin), "reason": reason})

    def notice(self, origin: str, data: bytes):
        if origin in self.seen:
            return
        self.seen.add(origin)
        if len(data) > MAX_NOTICE or self.total + len(data) > MAX_NOTICES:
            self.error(origin, "notice size limit; collection incomplete")
            return
        self.total += len(data)
        digest = hashlib.sha256(data).hexdigest()
        compressed = origin.lower().endswith(".gz")
        self.notices.append({"origin": origin, "sha256": digest, "bytes": len(data),
                             "gzip": compressed, "content_base64": base64.b64encode(data).decode("ascii")})
        try:
            if compressed:
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as source:
                    text = source.read(MAX_NOTICE + 1)
                if len(text) > MAX_NOTICE:
                    self.error(origin, "decompressed notice exceeds search limit")
                    return
            else:
                text = data
            lowered = text.lower()
            for component, terms in NOTICE_TERMS.items():
                if any(term in lowered for term in terms):
                    self.notice_hits[component].append(origin)
        except (OSError, EOFError):
            self.error(origin, "gzip notice search failed; original bytes retained")

    def file_notice(self, path: Path, roots: list[Path]):
        try:
            if not confined(path, roots):
                self.error(path, "notice symlink escapes collection roots")
            elif path.stat().st_size > MAX_NOTICE:
                self.error(path, "notice size limit; collection incomplete")
            else:
                self.notice(str(path), path.read_bytes())
        except OSError:
            self.error(path, "notice unreadable")


def distribution(data: bytes, origin: str) -> dict:
    metadata = BytesParser().parsebytes(data)
    return {"name": metadata.get("Name"), "version": metadata.get("Version"),
            "origin": origin, "metadata_sha256": hashlib.sha256(data).hexdigest(),
            "scope": "vendored" if "/_vendor/" in origin.replace("\\", "/") else "installed",
            "license_expression": metadata.get("License-Expression"),
            "license_files_declared": metadata.get_all("License-File", []),
            "license_classifiers": [v for v in metadata.get_all("Classifier", [])
                                    if v.startswith("License ::")]}


def vendor_manifest(data: bytes, origin: str) -> dict:
    pins = []
    for line in data.decode("utf-8", "replace").splitlines():
        match = re.fullmatch(r"\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s;#]+)\s*(?:#.*)?", line)
        if match:
            pins.append({"name": match[1], "version": match[2]})
    return {"origin": origin, "sha256": hashlib.sha256(data).hexdigest(), "pins": pins,
            "qualification": "vendor manifest declarations; not evidence each component is imported"}


def archive_evidence(path: Path, evidence: Evidence) -> dict:
    result = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "distributions": [], "vendor_manifests": [], "certificate_bundles": [],
              "vendor_component_paths": [], "certifi_wrappers": []}
    with zipfile.ZipFile(path) as archive:
        vendor_paths = set()
        wrapper_names = set()
        for member in archive.infolist():
            parts = member.filename.split("/")
            if "_vendor" in parts and len(parts) > parts.index("_vendor") + 1:
                prefix = "/".join(parts[:parts.index("_vendor") + 2])
                if not prefix.endswith("/__pycache__"):
                    vendor_paths.add(prefix)
            if member.is_dir():
                continue
            origin = f"{path}!/{member.filename}"
            name = Path(member.filename).name
            notice = NOTICE_NAME.search(name)
            metadata = name == "METADATA" and ".dist-info/" in member.filename
            vendor = name == "vendor.txt" and "/_vendor/" in member.filename
            certificate = member.filename.endswith("certifi/cacert.pem")
            wrapper_scope = certifi_wrapper_scope(member.filename)
            wrapper = wrapper_scope and name in CERTIFI_WRAPPERS
            if wrapper_scope and name not in CERTIFI_WRAPPERS | {"LICENSE", "cacert.pem"}:
                evidence.error(origin, "unexpected certifi package file; review wrapper scope")
            if wrapper:
                if (member.filename in wrapper_names or member.file_size > MAX_WRAPPER
                        or (member.external_attr >> 16) & 0o170000 not in (0, 0o100000)):
                    evidence.error(origin, "duplicate/oversized/linked certifi archive wrapper")
                    continue
                wrapper_names.add(member.filename)
            if not (notice or metadata or vendor or certificate or wrapper):
                continue
            if member.file_size > MAX_NOTICE:
                evidence.error(origin, "archive member exceeds read limit")
                continue
            with archive.open(member) as source:
                data = source.read((MAX_WRAPPER if wrapper else MAX_NOTICE) + 1)
            if len(data) != member.file_size:
                evidence.error(origin, "archive member size mismatch")
                continue
            if notice:
                evidence.notice(origin, data)
            if metadata:
                result["distributions"].append(distribution(data, origin))
            if vendor:
                result["vendor_manifests"].append(vendor_manifest(data, origin))
            if certificate:
                result["certificate_bundles"].append({"path": origin, "bytes": len(data),
                                                       "sha256": hashlib.sha256(data).hexdigest()})
            if wrapper:
                result["certifi_wrappers"].append(wrapper_record(origin, data))
        result["vendor_component_paths"] = sorted(vendor_paths)
    return result


def walk_files(root: Path, evidence: Evidence, *, skip_sites=False):
    def failed(error):
        evidence.error(error.filename or root, "directory unreadable")
    count = 0
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__" and not (
            skip_sites and d in {"site-packages", "dist-packages"}))
        for name in sorted(files):
            count += 1
            if count > MAX_ENTRIES:
                evidence.error(root, "entry limit; collection incomplete")
                return
            yield Path(directory) / name


def collect_python(roots: list[Path], stdlib: Path, evidence: Evidence) -> dict:
    result = {"distributions": [], "vendor_manifests": [], "bootstrap_wheels": [],
              "native_binaries": [], "certificate_bundles": [], "vendor_roots": [],
              "certifi_wrapper_schema_version": 1, "certifi_wrappers": []}
    for root in sorted(set(roots + [stdlib])):
        for path in walk_files(root, evidence, skip_sites=(root == stdlib)):
            wrapper_scope = certifi_wrapper_scope(path.relative_to(root).as_posix())
            if not confined(path, [root]):
                if NOTICE_NAME.search(path.name) or wrapper_scope:
                    evidence.error(path, "symlink escapes Python collection root")
                continue
            try:
                if wrapper_scope and path.name in CERTIFI_WRAPPERS:
                    record = collect_certifi_wrapper(path, root, evidence)
                    if record is not None:
                        result["certifi_wrappers"].append(record)
                    continue
                if wrapper_scope and path.name not in {"LICENSE", "cacert.pem"}:
                    evidence.error(path, "unexpected certifi package file; review wrapper scope")
                # Fixed package-data scope: retain the supplemental ledger/README as well as
                # license-named texts so CI can compare every installed bundle byte.
                bundle = root / "radio_loadout/third_party_notices/v1"
                supplemental = (path.is_relative_to(bundle) and
                                path.relative_to(bundle).as_posix() in {"manifest.json", "README.md"})
                if NOTICE_NAME.search(path.name) or supplemental:
                    evidence.file_notice(path, [root])
                elif path.name in {"METADATA", "PKG-INFO"} and path.parent.name.endswith((".dist-info", ".egg-info")):
                    if path.stat().st_size > MAX_NOTICE:
                        evidence.error(path, "metadata size limit")
                        continue
                    item = distribution(path.read_bytes(), str(path))
                    item["notice_files_found"] = sorted(str(p) for p in path.parent.rglob("*")
                                                         if p.is_file() and NOTICE_NAME.search(p.name))
                    item["declared_notice_status"] = []
                    for name in item["license_files_declared"]:
                        candidates = [path.parent / "licenses" / name, path.parent / name]
                        found = [p for p in candidates if confined(p, [path.parent]) and p.is_file()]
                        item["declared_notice_status"].append({"declared": name, "present": bool(found)})
                        for candidate in found:
                            evidence.file_notice(candidate, [path.parent])
                    result["distributions"].append(item)
                elif path.name == "vendor.txt" and "_vendor" in path.parts:
                    if path.stat().st_size <= MAX_NOTICE:
                        result["vendor_manifests"].append(vendor_manifest(path.read_bytes(), str(path)))
                elif path.suffix == ".whl" and path.parent.name == "_bundled" and path.parent.parent.name == "ensurepip":
                    archive = archive_evidence(path, evidence)
                    result["bootstrap_wheels"].append(archive)
                    result["certificate_bundles"].extend(archive["certificate_bundles"])
                    result["certifi_wrappers"].extend(archive["certifi_wrappers"])
                elif path.name == "cacert.pem" and path.parent.name == "certifi":
                    result["certificate_bundles"].append({"path": str(path), "bytes": path.stat().st_size,
                                                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                elif NATIVE_NAME.search(path.name):
                    if path.stat().st_size > MAX_BINARY:
                        evidence.error(path, "binary size limit; markers/linkage uninspected")
                        continue
                    data = path.read_bytes()
                    item = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                            "markers": {key: [s.decode("ascii") for s in values if s in data]
                                        for key, values in MARKERS.items() if any(s in data for s in values)}}
                    try:
                        item["dt_needed"] = elf_needed(data)
                    except (ValueError, StopIteration, struct.error):
                        item["linkage_status"] = "ELF linkage could not be parsed"
                        evidence.error(path, "ELF linkage could not be parsed")
                    result["native_binaries"].append(item)
            except (OSError, ValueError, zipfile.BadZipFile):
                evidence.error(path, "Python evidence read failed")
        for vendor in sorted(root.glob("*/_vendor")):
            if confined(vendor, [root]) and vendor.is_dir():
                result["vendor_roots"].append({"path": str(vendor),
                    "version_manifest_present": (vendor / "vendor.txt").is_file(),
                    "components_found": [{"path": str(p), "version": None,
                        "version_evidence": "See any matching distribution metadata/vendor manifest; directory names alone establish no version."}
                        for p in sorted(vendor.iterdir()) if p.name != "__pycache__" and (
                            p.is_dir() or p.suffix == ".py")],
                    "qualification": "Versions absent from metadata/manifests remain unknown; notices do not establish a complete component graph."})
    return result


def parse_debian(text: str) -> list[dict]:
    result = []
    for line in text.splitlines():
        fields = line.split("\t")
        if len(fields) != 5:
            raise ValueError("unexpected dpkg record")
        name, version, source, source_version, status = fields
        if status.startswith("ii"):
            if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?", name):
                raise ValueError("invalid package name")
            result.append({"package": name, "version": version,
                           "source_package": source or None, "source_version": source_version or None})
    return result


def collect_debian(evidence: Evidence, doc_root=Path("/usr/share/doc"),
                   common=Path("/usr/share/common-licenses"), runner=subprocess.run) -> list[dict]:
    result = runner(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\t${db:Status-Abbrev}\n"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=30, check=False)
    if result.returncode:
        evidence.error("dpkg-query", "package query failed")
        return []
    packages = parse_debian(result.stdout)
    if not packages:
        evidence.error("dpkg-query", "no installed Debian packages returned")
    for item in packages:
        directory = doc_root / item["package"].split(":")[0]
        item["copyright_present"] = any((directory / name).is_file()
                                        for name in ("copyright", "copyright.gz"))
        if directory.is_dir() and confined(directory, [doc_root]):
            for path in walk_files(directory, evidence):
                if NOTICE_NAME.search(path.name):
                    evidence.file_notice(path, [doc_root, common])
    if common.is_dir():
        for path in walk_files(common, evidence):
            evidence.file_notice(path, [common])
    return packages


def review_items(python: dict, evidence: Evidence) -> list[dict]:
    result = []
    for key in MARKERS:
        binaries = [{"path": row["path"], "markers": row["markers"][key]}
                    for row in python["native_binaries"] if key in row["markers"]]
        notices = sorted(set(evidence.notice_hits[key]))
        prefixes = {"libuv": ("libuv",), "ICU/Unicode": ("libicu",), "LibYAML": ("libyaml",)}.get(key, ())
        linkage = [{"path": row["path"], "dt_needed": [s for s in row.get("dt_needed", []) if s.startswith(prefixes)]}
                   for row in python["native_binaries"] if prefixes and any(
                       s.startswith(prefixes) for s in row.get("dt_needed", []))]
        result.append({"component": key, "binary_marker_evidence": binaries,
                       "dynamic_linkage_evidence": linkage,
                       "notice_keyword_evidence": notices,
                       "notice_search": "matches found; coverage unverified" if notices else "no matching collected standalone notice found",
                       "inclusion": "uncertain: markers are clues, not a feature-selected binary build graph"})
    result.append({"component": "certifi (including pip/ensurepip vendor copies)",
                   "certificate_bundle_evidence": python["certificate_bundles"],
                   "source_access": "Unresolved: establish preferred-form covered source and recipient access; this artifact is temporary."})
    for row in python["distributions"]:
        if not row["notice_files_found"] or any(not f["present"] for f in row["declared_notice_status"]):
            result.append({"component": row["name"], "metadata_origin": row["origin"],
                           "notice_search": "No named standalone notice in metadata directory, or declared file missing; review package/vendor notices before concluding an omission."})
    return result


def probe(system: bool) -> dict:
    evidence = Evidence()
    roots = sorted({Path(sysconfig.get_path(key)) for key in ("purelib", "platlib")})
    stdlib = Path(sysconfig.get_path("stdlib"))
    python = collect_python(roots, stdlib, evidence)
    packages = []
    if system:
        try:
            packages = collect_debian(evidence)
        except (OSError, ValueError, subprocess.SubprocessError):
            evidence.error("dpkg-query", "system inventory failed")
        extra = Path("/usr/local/share/doc")
        if extra.is_dir():
            for path in walk_files(extra, evidence):
                if NOTICE_NAME.search(path.name):
                    evidence.file_notice(path, [extra])
        for path in (Path("/usr/local/LICENSE"), Path("/usr/local/LICENSE.txt")):
            if path.is_file():
                evidence.file_notice(path, [Path("/usr/local")])
    return {"schema_version": 1, "interpreter": {"executable": sys.executable,
            "version": platform.python_version(), "implementation": platform.python_implementation(),
            "prefix": sys.prefix, "base_prefix": sys.base_prefix, "platform": sys.platform,
            "machine": platform.machine(), "uid": os.getuid()}, "python": python,
            "debian_packages": packages, "notices": evidence.notices, "errors": evidence.errors,
            "review_items": review_items(python, evidence),
            "limitations": ["Standalone notices only; inline source headers are not exhaustively collected.",
                            "Missing keyword matches do not establish absent rights or absent binary inclusion.",
                            "Debian/Python/native covered-source and redistribution obligations still require review."]}


if __name__ == "__main__":
    print(json.dumps(probe("--system" in sys.argv), sort_keys=True))
