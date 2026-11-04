# Native-component notice evidence and supplement

Reviewed **2026-11-04 (America/Chicago)** against checkout
`7cc898267d5874724eeb5d4d251d92b4c694533b`, using the supplied
`staging-container-diagnostics.zip` and the existing dependency review.
The checkout was clean at the start. The approved authorship statement and
technical CHIRP comparisons in [chirp-provenance.md](chirp-provenance.md) are
unchanged. No dependency versions or original project license terms changed.

**Collection executed successfully; compliance review is not complete.**
This is inspection of the supplied actual-image evidence, not a local Docker
build or an independent reproduction of the CI execution. Docker is still
unavailable locally. No CI run URL/signature was supplied; archive integrity is
checked against the user's stated checksum, not a claim of independent attestation.

## Actual-image evidence identifiers

| Evidence | Observed identifier/result |
| --- | --- |
| Supplied ZIP SHA-256 | `5843bdb76cc1caf20fc0f9132369cc4e6e62bad55771bf362c496e180de076d4` — matches |
| `licenses/inventory.json` SHA-256 | `517fa9ee3ad8d139ef27288a3e37504cbb4d81fa72b02ab4e2ea7055ca7465e9` |
| `licenses/notices-index.json` SHA-256 | `4fb107ab461b11dd96ad4445083a3f7bd00dbf30982f6b60a1abc24c13ae69ad` |
| Collected UTC | `2026-11-04T18:52:44.438624+00:00` |
| Recorded checkout | `7cc898267d5874724eeb5d4d251d92b4c694533b`; dirty flag false |
| Final image ID | `sha256:bdb65d39b44c3e8843f29ce31e74e7b2eaf812c83b532e2f613c6b4b80bf24bf` |
| Identity binding | Build IID and staging container image ID agree; BuildKit `containerimage.digest` also records that value |
| Runtime | Linux amd64/x86_64; configured user `10001:10001`; both probes UID 10001; CPython 3.13.15 |
| BuildKit Python material | `pkg:docker/python@3.13.15-slim-bookworm?platform=linux%2Famd64`, digest `2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26` |
| BuildKit Dockerfile frontend material | `pkg:docker/docker/dockerfile@1`, digest `4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e` |
| Collection | `complete`; no top-level or per-probe errors; 354 notice-origin records / 155 distinct byte sequences, all stored hashes and sizes checked |
| Selected state at capture | Running, exit code 0, OOMKilled false, empty runtime error; this state alone does not establish smoke-test success |

The reported Python material digest equals the configured multi-platform digest;
this artifact does **not** establish a separate Linux child-manifest digest.
The source commit is the collector's checkout identity with its recorded binding,
not a new embedded-source attestation. The attached archive is local evidence,
not an enduring download or source-delivery service.

Base Python has pip **26.2.1**. `/opt/venv` has **61 installed distributions**:
the 59 locked runtime packages, pip 26.2.1 and Radio Loadout 0.1.0. Both pip vendor
manifests list 18 pins, including certifi **2026.6.17** and setuptools **70.3.0**
for the vendored `pkg_resources` material; these are not standalone setuptools
installations. ensurepip contains `pip-26.2.1-py3-none-any.whl`, SHA-256
`71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e`.
The archive records its vendor notices as well as both installed pip copies.

All **97 Debian binary packages** have a detected copyright path and recorded
source-package/version fields. Examples: glibc `2.36-9+deb12u14`, OpenSSL
`3.0.20-1~deb12u2`, GCC 12 runtime `12.2.0-14+deb12u1`, zlib
`1:1.2.13.dfsg-1`, and tzdata `2026b-0+deb12u1`. CPython's installed
`/usr/local/lib/python3.13/LICENSE.txt` is present (SHA-256
`78b12c3a81360b357002334f0e70ea0e92eebf7a9b358805c03c48484945f3bb`).
Presence is established; full notice sufficiency, resolved linkage, modifications,
historical Python incorporated-component coverage, and GPL/LGPL source-access
arrangements remain to be reviewed. The collection is not a complete file-level SBOM.

Direct certifi's CA bundle hash is
`2ef52ad56b4803e264045c915e55c236cbfa045b84b81efefc218a19eb44bd2b`;
pip/ensurepip vendor copies use
`bbc7e9c01d7551bb8a159b5dedd989b8ee3ce105aff522b68eb1b01bf854cab0`.
These are separate versions/covered-source questions. No MPL preferred-form or
recipient-source-access conclusion is closed by this work.

## Matching binaries and source selection

Downloaded the exact PyPI release wheels and source archives, checked PyPI
SHA-256 values and the existing lock hashes, and compared the wheels' native
members with the hashes captured from `/opt/venv`:

| Component | Wheel SHA-256 | Installed/native wheel-member SHA-256 | Matching release source SHA-256 |
| --- | --- | --- | --- |
| uvloop 0.23.0 | `e2cba180d6451822763eda8364f342435a873bcfb3849cbd82fdeca248ca65eb` | `aa4cf898c2b8daf5b9d5d4ebef86b611e4f5c83432641251cc2ec80050c9ba65` | `28d160f51ab4da3b187063652e643dea6831072add4adc1e6d62afbe73b6be27` |
| pydantic_core 2.50.2 | `31a1fb3ffbd1195b24490f671d12623dd4c9bfa56d6af0a299fa43b516134f5b` | `b50a4af7e9c722d907c5bcd683b6ce24d12b741289d9fb0cf9ec63ee78d5da68` | `1b0e8dc3932cf4e9ed5727570325cacc716b9409ffc794a221c0ccc72e8eb775` |

The exact filenames, download URLs, source members/ranges, notice hashes and
component applicability are recorded in the versioned
[bundle manifest](../src/radio_loadout/third_party_notices/v1/manifest.json).
The release sources are not asserted to reproduce the published binaries bit
for bit. No upstream build log, linker map or feature-selected compilation
receipt was obtained. A PyPI integrity/provenance endpoint lookup for the exact
Pydantic wheel returned 404 during this review; that does not prove no build
evidence exists elsewhere. Source archives were read without executing their code.

### libuv: confirmed missing component notices, supplemental texts added

The image has only uvloop's `LICENSE-MIT` and `LICENSE-APACHE` under its
dist-info license directory; the collected libuv keyword hits belong to
httptools/mdurl, not a libuv notice. In the byte-matched uvloop binary,
`uv_version_string`, `uv_loop_init`, `uv_inet_ntop`, `uv_inet_pton` and the text
`1.52.1` occur. `DT_NEEDED` has libc, libpthread and librt, with no dynamic libuv.
Together with matching source `setup.py` lines 87, 194–205 (default static
`vendor/libuv/.libs/libuv.a`), this supports bundled libuv **1.52.1**.

In that archive, `vendor/libuv/Makefile.am` line 36 includes `src/inet.c` in common
sources; `src/unix/loop.c` line 23 and `src/uv-common.h` line 37 include tree.h.
Linux-selected source therefore supports retaining these notices:

- `vendor/libuv/LICENSE`: unchanged libuv contributors' MIT text.
- `vendor/libuv/LICENSE-extra`: unchanged Joyent/Node text and component pointer.
- `vendor/libuv/include/uv/tree.h` lines 1–24: complete Niels Provos BSD-2 comment.
- `vendor/libuv/src/inet.c` lines 1–16: complete ISC comment, including both
  Internet Systems Consortium and Internet Software Consortium copyright lines.

The bundle preserves the comment delimiters and bytes, adds no invented notice,
and does not substitute uvloop's own copyright. This addresses the identified
text omission in the prepared supplemental payload. Presence in the next built
runtime image remains a CI gate; it has not been verified by the earlier ZIP.

### Pydantic ICU/Unicode and PyO3: narrower evidence and coverage

The actual Pydantic Core installed license is its parent MIT file, SHA-256
`2afdd30d54b4d62b6f488a6bcc1546e84ec5061f13f4209c03d012348783795a`.
The venv collection has no ICU/Unicode or PyO3 notice hit. The byte-matched binary
contains versioned registry source-path suffixes:

```text
icu_normalizer-1.5.0/src/lib.rs
pyo3-0.30.1/src/pybacked.rs
pyo3-0.30.1/src/internal/state.rs
pyo3-ffi-0.30.1/src/lib.rs
```

These are stronger clues than an unversioned keyword or a lock entry, but do not
describe every emitted instruction/table. No `icu_properties-` or ICU data-crate
name string was found by this bounded search; absence is not exclusion evidence.

The matching source's normal dependencies are PyO3 0.30.1 (features num-bigint,
py-clone, smallvec), url 2.5.8 and idna 1.1.0. Its `src/url.rs` uses Url and idna;
the library is a cdylib/rlib, release fat LTO, one codegen unit, stripped.
`pyproject.toml` selects maturin/PyO3 and only the parent LICENSE. Exact downloaded
crates were checked against that source's Cargo.lock, not latest crate versions:

- url 2.5.8 → idna 1.1.0 → idna_adapter 1.2.0.
- idna's default features include compiled_data; its `src/lib.rs` lines 48–49
  reject builds without that feature. idna_adapter enables ICU normalizer and
  properties compiled_data through its same-named feature.
- icu_normalizer 1.5.0 and icu_properties 1.5.1 default to compiled_data. The
  latter enables icu_locid_transform; source manifests lead to their pinned data,
  provider, collections and locale crates. The nine code/data crates listed in
  the manifest carry **identical** Unicode-3.0 LICENSE bytes, including the
  existing ICU/IBM acknowledgement. That full text is retained once with mappings.
- PyO3 0.30.1 and pyo3-ffi 0.30.1 have identical MIT and Apache-2.0 texts; PyO3's
  `pyo3-runtime` copies match too. Both alternatives are preserved; there is no
  invented Apache NOTICE. Related url/idna/idna_adapter MIT/Apache texts are
  retained from their exact crates.

This supports supplementing the observed ICU normalizer/PyO3 notice gap and
covering the stated source-default ICU data path. It is **not** a declaration
that all 102 Cargo.lock entries, every ICU crate/table, unicode-ident's macro
tables, or build-only crates are in the final binary. Exact upstream feature
overrides, toolchain/runtime contributions, dead stripping and the remaining
Rust crate notices still need build-specific evidence. No Cargo toolchain was
available locally; none was installed, and no wheel was rebuilt as proof of
the publisher's original build.

## Delivery and verification

[Bundle 1](../src/radio_loadout/third_party_notices/v1/README.md) is package data,
with 13 verbatim notice texts plus its manifest and README. It is included in
wheel/source archives and, through the unchanged wheel-based Dockerfile, at
`/opt/venv/lib/python3.13/site-packages/radio_loadout/third_party_notices/v1/`.
The explicit Docker-context allowlist admits only this bundle's JSON/Markdown/
text inputs. Existing dependency and project notices remain intact; the original
PolyForm license and COPYRIGHT are unchanged. The project wheel does not start
bundling dependency binaries. Normal hosted builder pages do not serve this data.

`scripts/smoke_package.py` validates upstream notice hashes and exact bundle
payload bytes in wheel and source archive, then the isolated installed-wheel
probe checks the installed hashes. The final-image collector additionally retains
the installed bundle manifest/README and notices. Immediately afterward, an
`always()` CI step runs:

```sh
python scripts/verify_third_party_notices.py \
  --inventory-dir generated/container-diagnostics/licenses \
  --output generated/container-diagnostics/supplemental-notices-check.json
```

It requires complete actual-image collection, consistent build/container IDs,
the runtime interpreter, exact component versions/native hashes and every
installed bundle byte. Missing/altered files, changed native applicability or
partial evidence fail visibly. It consumes the installed image evidence, not a
host bind-mount substitute. The check also runs after smoke failures and before
seven-day upload/cleanup; collection restrictions and runtime checks are retained.
No tools or dependencies are installed in the final image.

The earlier ZIP necessarily predates this new bundle. **The next Linux-amd64 CI
execution must establish the new payload's actual-image presence.** Local
synthetic-evidence tests and packaging checks cannot substitute for that gate.
Artifacts are temporary diagnostics, not permanent covered-source access.

Local validation on 2026-11-04, Windows / Python 3.13.15:

- Ruff passed; full Python regression: **664 passed, 1 skipped** (the existing
  unprivileged symlink-creation test is unsupported on this Windows host), with
  two existing dependency deprecation warnings. All 14 new notice tests passed.
- The notice tests cover missing/altered installed bytes, unsafe stored paths,
  partial evidence, mismatched image IDs, version/native hash drift and
  base-interpreter-only evidence; they also exercise actual filesystem collection
  of the synthetic installed bundle and failure-path CI ordering.
- JavaScript syntax checks passed for 15 files; **53 JavaScript tests** and
  **20 Chromium desktop/narrow browser tests** passed, including production docs,
  trusted application workflows and accessibility journeys.
- Complete packaging smoke passed: exact wheel/source payload and notice hashes,
  unchanged project license metadata/bytes, isolated non-editable installed wheel,
  pip check and production HTTP workflow/input-limit checks. The final source
  archive is rebuilt/audited after these documentation updates.

No Linux image build was performed locally. The collected pre-supplement image
is evidence for the identified gaps, not evidence that the new payload is already
installed. No GitHub CI execution was triggered from this session.

## Remaining actions and readiness

1. Execute the updated existing CI job and inspect its notice-check result and
   bound image identity. This verifies delivery of the prepared supplement only.
2. Obtain build-specific Rust/native graph evidence or an upstream notice ledger
   for Pydantic and the other flagged Rust wheels (fastar, rignore, watchfiles).
   Assess remaining applicable texts rather than importing every lock entry as
   purported runtime code.
3. Complete Debian/CPython incorporated-component, source-access and runtime
   exception review using the actual inventory, including separate certifi
   direct/vendor/bootstrap versions. No recipient source arrangements were added.

Hosting conclusions remain as in the dependency review; this supplement concerns
conveyed native environments. Container redistribution remains on hold pending
notice delivery verification and the other open reviews. CHIRP provenance is
unchanged. This work grants no additional project permission and is not legal
clearance.
