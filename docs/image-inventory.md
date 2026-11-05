# Collecting evidence from the final staging image

The existing Linux-amd64 container CI job builds the final runtime target and
runs the existing restricted staging container/checks. Before cleanup it also
runs `scripts/collect_image_inventory.py`, even after build, startup or smoke
failures. The collector binds to the staging container's immutable `.Image` ID;
if the staging container was never created, it can use the build's `--iidfile`.
If both exist they must agree. It refuses a tag-only fallback when a staging
container was requested, and rejects a non-Linux/amd64 or differently configured
image user. This collects installed image evidence, not candidate-wheel metadata.

The checksum-verified supplied CI artifact now establishes successful collection
from the image recorded in the [native-component evidence review](native-component-notices.md).
Compliance review remains incomplete. Docker is unavailable locally; unit tests
use synthetic files/Docker responses. The later **CI #11 actual-image byte gate
passed** at commit `ec248268cf25d031b1042f7e7c42b1d2f2bdc9da`; see the
[verified run/artifact evidence](native-component-notices.md#ci-11-gate-verified--2026-11-05).
This verifies the supplement, not broader compliance. The focused
[certifi source follow-up](certifi-source-review.md) uses that inventory.

## Build and local collection on a Docker-capable machine

The CI build uses Buildx's Docker exporter (`--load`), targeting Linux amd64.
It does not push an image. Minimal build metadata is written separately from the
uploaded artifact so only selected identifiers are retained. For example:

```sh
mkdir -p generated/container-build
BUILDX_METADATA_PROVENANCE=min docker buildx build --load --platform linux/amd64 \
  --tag radio-loadout:staging-ci \
  --iidfile generated/container-build/image-id \
  --metadata-file generated/container-build/metadata.json .
```

Start and smoke-test the image with the restrictions in [staging.md](staging.md).
Then, before removing the staging container (it may already have exited):

```sh
python scripts/collect_image_inventory.py --container radio-loadout-staging-ci \
  --image-id-file generated/container-build/image-id \
  --build-metadata generated/container-build/metadata.json
```

The default destination is `generated/container-diagnostics/licenses/`. Use
`--output-dir PATH` with an empty directory for a separate run. Existing nonempty
destinations are rejected to prevent mixing image versions. Without `--container`,
`--image IMAGE` inspects that image first and then probes its immutable ID.
If build material identifiers are unavailable, the report says so rather than
inventing a resolved base digest from the Dockerfile. BuildKit may identify both
base image and Dockerfile frontend image inputs; review their roles explicitly.
The configured multi-platform base digest is not automatically the resolved
Linux-amd64 child manifest or final image ID.

See Docker's [metadata-file reference](https://docs.docker.com/reference/cli/docker/buildx/build/#metadata-file)
and [minimal provenance description](https://docs.docker.com/build/metadata/attestations/slsa-provenance/).
Raw build metadata is not uploaded; its invocation, environment, build parameters
and unrelated source URIs are not copied to the inventory.

## Execution boundary

The collector does not depend on the application remaining healthy. It runs
`/usr/local/bin/python` and `/opt/venv/bin/python` in separate, disposable
containers from the same final image ID. Each inherits the image's UID/GID
10001:10001 and uses a read-only root, the existing bounded noexec/nosuid `/tmp`
tmpfs, all capabilities dropped, no-new-privileges, 512 MiB memory, one CPU and
128 PIDs. Collection also disables networking and healthchecks, publishes no
ports, and mounts no host directory or Docker socket. `--pull never` prevents a
tag resolution from fetching a different image. It never overrides the user to
root or changes the original staging container's restrictions.

The standard-library-only probe is streamed over stdin and run with `-I -B`;
it is not installed or copied into the image. It inspects files/metadata without
importing the target third-party packages, loading the inspected extension
binaries or using `ldd`. Normal interpreter startup still applies. A timeout is bounded to 180
seconds per interpreter and triggers removal of only that collector's uniquely
named container. No tools or dependencies are added to the final image.

## Artifact contents and evidence boundaries

The seven-day `staging-container-diagnostics` artifact includes:

| File | Evidence |
| --- | --- |
| `licenses/inventory.json` | Checkout commit, dirty-tree flag, collection time and collector hashes; projected image ID/OS/architecture/user/repository digests; selected BuildKit image materials/config digest when present; both interpreters' versions, prefixes, machine and UID; installed and nested vendored distribution metadata; vendor manifests/component paths; ensurepip wheel metadata/hashes; Debian binary/source package versions; native file hashes, ELF `DT_NEEDED` and selected marker names; review items, limitations and collection errors. |
| `licenses/notices-index.json` | Original notice paths (including archive-member origins), collecting interpreter, size, SHA-256 and stored file. Identical bytes are deduplicated while origins remain distinct. |
| `licenses/notices/<sha256>.txt` or `.gz` | Exact existing notice bytes, including compressed Debian notices. No replacement notices are generated. |
| `supplemental-notices-check.json` (beside `licenses/`) | Pass/failure for exact installed bundle bytes and the reviewed native artifact identities. This supplements collection; it does not assert complete license coverage. |
| `certifi-wrappers-check.json` (beside `licenses/`) | Offline pass/failure comparing installed certifi wrapper hashes/sizes with pinned source-member hashes, plus the existing PEM/notice/version/bootstrap checks. Older inventories must be recollected. |

The source commit is the checkout HEAD at collection, with a dirty flag; CI
builds and collects in the same checkout. It is not inferred from the package
version or asserted to be an embedded authorship claim in the image. Image
inspection uses a Go-template projection, never full `docker inspect`. Collection
never dumps environment variables, Docker config, Git remote URLs, arbitrary
command stderr, package source modules or raw binary content.

The Python searches cover each interpreter's actual purelib/platlib and the
standard-library tree (site-packages handled separately), including nested
`_vendor` notices/metadata, `vendor.txt` pins and ensurepip's bundled wheel
members. Vendor paths with no usable version metadata remain explicitly unknown;
a vendor manifest is not proof that every declared component is loaded. certifi
CA bundles, including vendored/bootstrap copies, are hashed without copying
their certificate contents into the notice artifact.

The wrapper-enabled probe also adds `python.certifi_wrapper_schema_version: 1`
and `python.certifi_wrappers` (path/size/SHA-256 only). Collection is restricted
to four direct files (`__init__.py`, `__main__.py`, `core.py`, `py.typed`) under
the application and pip-vendored certifi packages, including ensurepip's bundled
archive. Source contents are not retained or executed. Reads are bounded to
64 KiB each; bytecode caches and unrelated package sources are excluded.
Unexpected direct package files, links, duplicate archive members and oversized
wrapper reads remain visible errors rather than being treated as verified.

The new offline `scripts/verify_certifi_wrappers.py` CI step runs with `always()`
after collection, before upload/cleanup. It checks both expected interpreters,
image binding, exact wrapper locations and the source-member hashes already
pinned in `scripts/certifi-source-manifest.json`, using pip's modified wrapper
sources where appropriate. It checks 16 unique files; 20 observations reflect
the shared ensurepip archive seen by both probes, not a fifth installed copy.
**CI #13 passed this actual-image gate** at commit
`0b5261390accc2f6efd5d316f2b3b2e605aa051a`, with 16 unique files / 20
observations. Both the wrapper and supplemental checks were independently
replayed from its checksum-verified artifact. See the
[exact evidence record](certifi-source-review.md#ci-13-installed-wrapper-gate-verified--2026-11-05).
CI #12 contains no wrapper records and correctly fails the new gate; its older
evidence was not substituted for the new collection. Broader review remains open.

The fixed `radio_loadout/third_party_notices/v1/manifest.json` and `README.md`
are also retained along with the bundle's notice-named texts. No other arbitrary
package JSON/Markdown/source files are copied. The subsequent `always()` CI step
runs `scripts/verify_third_party_notices.py --inventory-dir ... --output ...`
against this collected evidence. It compares every installed supplemental file
with the checkout's validated bundle, including its manifest/README, and requires
the reviewed uvloop/Pydantic versions and native-file hashes. Missing/changed
bytes, identity drift or incomplete collection fail the check before artifact
upload and cleanup. It does not install tools or change probe restrictions.

The base-interpreter pass runs `dpkg-query` for installed binary package/version
and source package/version fields. It copies notice-named files under installed
packages' `/usr/share/doc/<package>/` trees, `/usr/share/common-licenses/`, and
Python's standard notice locations. A package's `copyright_present` field
includes `copyright` and `copyright.gz`; false means no such path was found,
not a completed legal determination. Symlink targets must remain inside the
allowed notice roots. Inline source headers and every possible nonstandard legal
filename are not exhaustively collected.

Reads are bounded: 4 MiB per notice/metadata entry, 32 MiB total notice content
per interpreter, 64 MiB per native binary and 50,000 walked file entries per
root. Original gzip bytes are retained; decompressed keyword search is bounded.
Unreadable/oversized evidence and unsupported ELF linkage are recorded as
incomplete collection. Review those errors before treating the inventory as complete.

## Reviewing flagged components

`review_items` records actual binary marker/ELF-linkage observations and keyword
matches in collected notices for libuv, ICU/Unicode, PyO3, LibYAML, llhttp/http-parser,
upb and Cython. A marker hit is a clue, not a complete feature-selected build
graph or an upstream version. A matching notice keyword does not establish its
applicability or completeness. Absence of a marker does not prove absence from
the binary, and absence of a matching standalone notice is a review item rather
than automatic proof of a violation. Notice matches may concern another component.

The inventory also records declared license files that are missing and distributions
with no named standalone notice in their metadata directory. Their package/vendor
notice paths may supply additional evidence elsewhere. It does not automatically
repair the candidate-wheel omissions identified in the dependency review.

Review certifi's actual notices, bundle identities and preferred-form source
availability, including separate pip/ensurepip copies. Debian GPL/LGPL, Python
incorporated libraries, native Rust/C dependencies and other component obligations
still need applicable notices and source-access assessment. These findings do
not require publication of all Radio Loadout source merely because a dependency
has copyleft terms. **Temporary CI artifacts are not a permanent recipient
source-access solution.** Inventory collection alone establishes no compliance
or legal clearance and does not resolve CHIRP provenance.

`collection_status` means only complete/partial/failed **collection**, not licensing
readiness. Missing-notice/source-access review items do not themselves change a
successful collection into a license-compliance failure. Unreadable or malformed
optional build metadata still allows installed-package collection, with the
overall result marked partial. Read/identity/probe errors
do make the collector exit nonzero, retaining partial JSON and notices; CI still
uploads diagnostics and cleans up. If no image was built, failure diagnostics
are retained without claiming any image was inspected.

Local checks:

```sh
ruff check .
python -m pytest tests/test_image_inventory.py
python -m pytest
python scripts/collect_image_inventory.py --help
python scripts/smoke_package.py
```

Local validation on 2026-11-04 (Windows / Python 3.13.15): Ruff passed; the full
suite passed 650 tests with one symlink-creation test skipped because the host
does not grant that privilege (19 inventory cases passed). Separate confinement
tests passed without symlinks. JavaScript syntax, 53 JavaScript tests, 20 Chromium
desktop/narrow browser tests and the isolated wheel/source packaging smoke passed.
The workflow parsed as YAML. These results validate local logic and regressions,
not Docker/Buildx execution. The subsequently supplied ZIP establishes the older
image collection. The subsequent CI #11 evidence establishes the supplemental
payload's actual-image verification; see [the updated record](native-component-notices.md).
