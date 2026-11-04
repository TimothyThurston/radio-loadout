# Radio Loadout third-party licensing review

Review date: **2026-11-03 (America/Chicago)**. Reviewed commit:
`abca8d54efe96e91afdc687ba6432a084a026b32` (`Apply PolyForm Strict 1.0.0 licensing`).
The working tree was clean at the start of that baseline review, for which this
report was the only repository change. The production API-documentation follow-up
below records the subsequent 2026-11-04 code change; original artifact hashes and
upstream inventory evidence remain historical. This is an evidence record and a
release checklist,
not completed legal clearance or an opinion that ownership has been established.

## Actual-image evidence and native notice supplement — 2026-11-04

The supplied `staging-container-diagnostics.zip` matches SHA-256
`5843bdb76cc1caf20fc0f9132369cc4e6e62bad55771bf362c496e180de076d4`.
It records successful, error-free collection at checkout
`7cc898267d5874724eeb5d4d251d92b4c694533b` from Linux amd64 image
`sha256:bdb65d39b44c3e8843f29ce31e74e7b2eaf812c83b532e2f613c6b4b80bf24bf`.
Both interpreters report CPython 3.13.15 / UID 10001. Actual evidence includes
61 venv distributions (59 locked runtime packages, pip and the project), base and
ensurepip pip 26.2.1/vendor contents, and 97 Debian binary/source package records.
All 354 notice-origin records passed stored hash/size checks (155 unique texts).
Collection executed successfully; **compliance review is not complete**.

[The native-component evidence record](native-component-notices.md) gives the
inventory/index hashes, base identifiers and limitations. This supplied evidence
supersedes earlier statements that final-image evidence was pending. Docker is
still unavailable locally; the supplied run was not independently reproduced.
The BuildKit material is the configured multi-platform Python digest, without a
separate established Linux child digest. Notice presence does not establish
source access, complete native coverage or redistribution readiness.

Installed uvloop/Pydantic Core binary hashes exactly match the reviewed release
wheels. [Supplemental bundle 1](../src/radio_loadout/third_party_notices/v1/README.md)
now preserves libuv 1.52.1's LICENSE, LICENSE-extra, tree.h BSD and inet.c ISC
texts from uvloop 0.23.0's matching source archive. Exact Pydantic source/crate
evidence supports adding ICU4X Unicode-3.0 (including ICU/IBM), PyO3/ffi 0.30.1
MIT/Apache, and related url/idna-path notices. Source defaults and versioned
binary paths support this scoped supplement, not inclusion of every Cargo.lock
entry. The complete upstream feature/link graph remains unresolved.

The bundle is package data in wheel/source archives and passes through the
existing wheel-based container build. CI now collects its installed bytes and
checks every bundle file plus the reviewed native identities, including after
smoke failures and before cleanup. **Actual-image verification of this newly
added bundle requires the next Linux CI execution**; the supplied ZIP predates
it. Only the identified notice texts are supplemented. Other native coverage,
certifi direct/vendor/bootstrap preferred-form and source access, Debian/CPython
obligations, CHIRP provenance and project permissions remain open. The approved
authorship statement is unchanged. Temporary artifacts are not permanent source
access, and this work is not legal clearance.

Radio Loadout's original material remains under **PolyForm Strict 1.0.0**.
That license does not cover third-party material. Nothing here changes a
component's license, supplies missing permissions, or claims users' channel data
or generated CSV/JSON configurations.

## Production API-documentation follow-up — 2026-11-04

**Addressed for production/staging only:** the public interactive-documentation
delivery finding. This follow-up was made in the working tree based on the same
commit above; no new commit, deployment or publication was made. The pre-existing
untracked review report was preserved and amended only for this finding.

`web/app.py:create_app(docs_enabled=...)` now constructs separate FastAPI instances
from the application endpoint router. `web/production.py:create_app` requests an
instance with `docs_url=None`, `redoc_url=None` and
`swagger_ui_oauth2_redirect_url=None`, then applies the existing trusted-host and
privacy/security boundaries. It does not remove routes from the development
singleton. The `web/app.py:app` development entry point retains all three pages.
The homepage shows **View API** only when that instance has a docs URL.

Production `/docs`, `/redoc` and `/docs/oauth2-redirect` return **404**, including
production security headers and `Cache-Control: no-store`. `/openapi.json`
remains **200 application/json**, under trusted-host controls, with the same
application schema as development. The raw schema does not load browser scripts,
fonts or favicons. The builder and application API endpoints are unchanged.

Evidence for this follow-up:

- `tests/test_api_documentation.py`: 16 passing cases cover production 404s
  (including `/docs/` and `/redoc/`), development 200s, independent instances in
  both creation orders, conditional homepage links, absence of the identified
  CDN/font/favicon references on production pages, raw-schema parity and
  trusted-host enforcement for docs/schema requests.
- Full local Python regression suite: **631 passed** on Windows / Python 3.13.15;
  existing privacy-conscious errors, host/header controls, input-limit tests and
  real-loopback staging workflow smoke tests passed. Two existing dependency
  deprecation warnings remain. Ruff passed.
- JavaScript syntax checks: **15 files passed**; simulated-DOM suite:
  **53 passed**.
- Existing Playwright production-server configuration: **20 passed** in Chromium
  desktop and narrow viewports, including two executions of
  `tests/e2e/production-docs.spec.mjs`. The new test intercepts external requests
  on the production homepage/builder and requires none, verifies the hidden API
  link and documentation-asset references, checks all three 404s and the raw
  JSON schema. Existing builder, import/export and accessibility journeys passed.
- `scripts/package_smoke_probe.py` now checks the same production page/link/asset
  policy, docs/redirect 404s and JSON schema through real HTTP from an installed
  wheel. The local staging smoke driver uses this probe as well. The complete
  `python scripts/smoke_package.py` run **passed**: wheel/source-archive audit,
  exact packaged asset/notice bytes and license metadata, isolated non-editable
  install outside the checkout, `pip check`, production documentation checks,
  compatibility, CSV upload/download round trip and all three oversized-input
  rejections. The fresh Windows install used FastAPI **0.162.0** and Starlette
  **1.10.0**; the local source tests used FastAPI **0.141.1**. Logs are in
  ignored `dist/build.log`, `install.log`, `dependencies.log` and `probe.log`.
  The built source archive was refreshed/audited after recording these results;
  baseline artifact hashes below identify the earlier review, not this rebuild.

No dependency versions, original license text/copyright notices or other
licensing findings were changed. Disabling routes stops production delivery of
the identified documentation pages/assets; FastAPI's upstream documentation code
still exists in the dependency installation, and developer documentation still
uses its browser assets. This does **not** resolve the separate notice obligations
for distributing that dependency or establish provenance/legal clearance.

Docker remains unavailable: the configured Linux image, pinned Linux runtime,
remote CI, Firefox/WebKit and non-Chromium browsers were not verified by this
follow-up. Only this production API-documentation finding is marked addressed;
CHIRP provenance, native bundle notices, certifi source arrangements and final
image/OS review remain open.

## Readiness by delivery method

| Delivery | Evidence-based conclusion | Remaining gate |
| --- | --- | --- |
| Hosted channel builder (`/`, `/builder`) | Lower third-party distribution burden: the inspected templates use local project CSS/JS, and server dependencies are not sent with normal channel exports. No reviewed server license requires publishing the entire application merely to run it as a service. | Resolve the CHIRP provenance question for delivered JavaScript/data tables and project code. Production API-doc delivery was disabled in the 2026-11-04 follow-up. Confirm the actual deployment dependency set. |
| Hosted API documentation | **Addressed in the 2026-11-04 production/staging code:** `/docs`, `/redoc`, and the OAuth redirect return 404; production links and identified browser-asset references are absent. Raw `/openapi.json` remains available. | Development docs remain enabled. The historical browser inventory below still applies to development and to any future decision to re-enable public docs; final container/OS and dependency-redistribution review remain separate. |
| Downloadable project wheel/source archive, without dependencies bundled | The inspected archives contain project files and project notices, not dependency wheels, npm packages, or Python itself. Merely declaring dependencies is not redistribution of their contents. | Resolve CHIRP provenance before treating these artifacts as redistribution-ready. Recheck future artifacts. A wheelhouse, offline installer, or repackaged environment requires a separate dependency notice/source review. |
| Distributed runtime container | **Hold redistribution pending corrective work.** The supplied actual-image inventory confirms server wheels, native code, Python, pip/bootstrap contents, and Debian components. | Verify the new supplemental notice bytes in the next built image, complete native/OS/Python coverage review, and establish applicable source access. Successful inventory collection is established; compliance is not. |
| Distributed build/test image or browser-test environment | Broader scope than the runtime image. Includes additional vendored licenses and downloaded browser components. | Review setuptools' LGPL/MPL material, npm bundle notices, Node, Chromium/FFmpeg and their exact binaries before sharing such an environment. These tools are not automatically part of the project wheel or runtime image. |

These conclusions concern third-party licensing only. They neither authorize
redistribution of Radio Loadout's original material under Strict nor replace a
separate permission agreement when one is needed.

## Scope, method, and reproducibility (2026-11-03 baseline)

Inspected `pyproject.toml`, both `deploy/*.lock` files, `deploy/build-requirements.in`,
`package.json`, `package-lock.json`, `MANIFEST.in`, `.dockerignore`, `Dockerfile`,
`.github/workflows/ci.yml`, packaging/smoke scripts, existing licensing documents,
templates/static assets, and CHIRP-related implementation, fixtures and history.

Downloaded all **59 runtime and four build wheels** specified in the lockfiles,
using pip's `--require-hashes --only-binary=:all: --no-deps`, CPython 3.13 / cp313,
and compatible x86-64 manylinux 2014 / 2.17 / 2.28 platform selectors. Every wheel
passed the lockfile hash check. These are identified, compatible **candidate
artifacts**, not a capture of an installed container. The actual Linux installer
may prefer a different compatible platform wheel; inspect that exact artifact
before release. `--no-deps` downloaded the explicit lock entries rather than
resolving a fresh dependency graph. No downloaded native code was executed.

Read wheel license/copyright/NOTICE entries, vendored notices, npm tarball
notices and bundle license sidecars. Downloaded the exact source archives for
certifi and the 11 runtime packages with native extensions. Inspected setup/Cargo
files and native ELF dynamic dependencies without executing the binaries.
Six representative Rust crate downloads were checked against the exact Cargo.lock
checksums. This does not establish the complete feature-selected native build graph.

All five npm tarballs matched `package-lock.json` SHA-512 integrity values.
Downloaded public upstream evidence and API-doc assets; no project source was
uploaded to a scanner. Temporary evidence was retained locally under
`%LOCALAPPDATA%/Temp/radio-license-review-d6fjqu1f/` (wheels, sources, npm archives,
selected crates, CDN bytes, and JSON evidence records). That temporary cache is
not a release source-availability mechanism and may be deleted by the OS.
The tables below retain artifact names, hashes, internal evidence paths and
public retrieval references so the review can be reproduced without it.

`Get-Command docker` and the conventional Docker Desktop CLI path found no Docker
executable. Docker was not installed. There is no locally built image ID,
Linux-amd64 child-manifest digest, `dpkg-query` output, or final-image notice audit.
The multi-platform base digest is a configured input, not proof of final contents.

The existing project distribution audit passed against the checkout before this
report was added, including exact runtime/development payloads, notice bytes and
license metadata. No distributions were rebuilt for this report. The existing
source archive therefore does not contain this newly written review.

### Reviewed artifact identifiers (2026-11-03 baseline)

| Input/artifact | SHA-256 or configured identifier |
| --- | --- |
| `dist/radio_loadout-0.1.0-py3-none-any.whl` | `9734d97a7689eb8dc6ac98bc01d186ab6a672599427083f4c5ae6ff243801d3d` |
| `dist/radio_loadout-0.1.0.tar.gz` | `4a0674f8c61a46eeda1ffa3f340886b092be00a597a748e9cc8063bf48c2f092` |
| `pyproject.toml` | `72590bd792adedeb4ffc936192e48b1ae07d28e55aee49a3ceacca3e27908750` |
| `package-lock.json` | `d9781fd7bcf141c35c4931365a45a43a35e99daf8e93f6241cd98e790663b55b` |
| `deploy/requirements-runtime.lock` | `02ce6be2d31380bb0c33193d72a35bbf6ba81a0eb28eb615304e5c8a6283abfd` |
| `deploy/requirements-build.lock` | `63b5bd64186209f5d708106da94a1051c633b820654e954756f27870dfb87d12` |
| `Dockerfile` | `655aeaf2f3ee367061ef738163952f6e90ecd37c1b79c9abaa5dc9179241a32c` |
| Configured base image | `python:3.13.15-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26` |

## Application and browser-delivered components

The project wheel has only `radio_loadout/` and `radio_loadout-0.1.0.dist-info/`
at its top level. Its license entries are the project's `LICENSE` and `COPYRIGHT`.
The source archive has 122 members and no `node_modules`, dependency wheels,
vendored Python environment or shared libraries. Package-data rules include
local templates, CSS, JS and limits JSON. npm dependencies are test-only;
there is no npm production bundling step. Generated channel CSV/JSON data does
not, merely by being generated, contain the server's dependency code.

**Historical API documentation exception (2026-11-03, before the follow-up):**
`web/app.py` constructed `FastAPI(title=...)`
with default docs enabled. `web/production.py` wrapped it without removing routes.
Requests through the production factory with an allowed localhost Host returned
200 for `/docs`, `/redoc`, `/docs/oauth2-redirect`. That baseline probe used the existing
Windows environment's FastAPI 0.141.1; independently, the locked 0.162.0 wheel's
`fastapi/openapi/docs.py` contains the same default asset URLs and copied redirect.

| Browser component | Observed version/evidence | License/notice finding |
| --- | --- | --- |
| Channel-builder JS/CSS and presets | Tracked `web/static/` and templates; CHIRP-related tables discussed below | Treated as project material only subject to provenance verification, not assumed independently authored from absent attribution. |
| Swagger UI JS | `swagger-ui-dist@5` CDN resolved to 5.34.1; bytes match the 5.34.1 npm tarball | Apache-2.0; package `LICENSE`, `NOTICE` (SmartBear), and `swagger-ui-bundle.js.LICENSE.txt` are present upstream. The sidecar includes MIT/BSD component notices. The app does not provide these notice files itself. |
| Swagger UI CSS | CDN response identified 5.34.0; bytes match both reviewed 5.34.0 and 5.34.1 tarballs | Same Apache project; the floating JS and CSS references are independently resolved. Do not infer a single locked release from `@5`. |
| ReDoc standalone JS | `redoc@2` resolved to 2.5.4; bytes match the npm tarball | MIT (Rebilly); `LICENSE` and `bundles/redoc.standalone.js.LICENSE.txt` exist upstream. Sidecar contains bundled component notices; the app does not serve them as a notice resource. |
| Swagger OAuth redirect | Locked FastAPI `fastapi/openapi/docs.py` says copied from Swagger UI v4.14.0 `dist/oauth2-redirect.html` | That upstream release is Apache-2.0 with a SmartBear NOTICE. The inspected FastAPI wheel has its MIT license but no separate Swagger license/NOTICE entry. Track this as an upstream-origin notice gap requiring confirmation/remediation when delivering the redirect script. |
| ReDoc fonts and docs favicon | Generated HTML loads Google Fonts Montserrat/Roboto and FastAPI's favicon | Not pinned in project locks. Font bytes, variants and favicon rights were not established. No font license conclusion is inferred just from Google hosting. Review actual delivered artifacts if retaining these routes. |

CDN-hosted files are fetched by the visitor from third parties; that differs from
bundling them in the project wheel. Do not silently treat CDN delivery as a
complete compliance solution or count these libraries as server-only. If
self-hosting assets, preserve their full license/NOTICE/sidecar material and
review bundled dependencies, not only the headline license. A minimal alternative
is to disable unneeded public docs and redirect routes before deployment.

## Obligations by license and delivery

The following is an application of the inspected terms to the described delivery,
not a conclusion that all obligations have already been met.

| License/material | Hosted service | Distribution of that component |
| --- | --- | --- |
| MIT, ISC, BSD-2/3 | Server-only operation does not by itself require application source publication. | Keep applicable copyright, permissions/conditions and disclaimers. BSD-3 also restricts endorsement. Retain actual upstream notices, including vendored ones; a license identifier table is insufficient. |
| Apache-2.0 | No general network-source publication requirement; browser-delivered code needs separate consideration. | Supply license text, preserve applicable source attributions and upstream NOTICE information; identify modified files when applicable. A separate NOTICE need not be invented for every Apache package that has none. See [Apache section 4](https://www.apache.org/licenses/LICENSE-2.0). |
| MPL-2.0 | Ordinary server-only use has no network disclosure trigger. | Preserve covered-file notices and license access; Source Code Form distributions remain MPL. Executable distributions need the covered source available and recipients told how to obtain it under reasonable terms. Separate-file larger works can retain other licenses. This does not require putting all Radio Loadout code under MPL. See [MPL sections 3.1–3.4](https://www.mozilla.org/en-US/MPL/2.0/) and [Mozilla FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/). |
| LGPL-3.0 vendored build tool | Build-tool use alone is not application relicensing. | If the library/build environment is conveyed, assess LGPL source, license, modification and replacement/relinking requirements for the way it is combined. Its presence in a builder does not prove it is in the final runtime image. |
| PSF/Python historical licenses | No entire-application source requirement from running Python. | Retain the PSF notice/agreement and applicable historical/component licenses; summarize changes to Python if distributing a changed derivative. Python includes additional separately licensed code. See [pinned CPython LICENSE](https://github.com/python/cpython/blob/v3.13.15/LICENSE). |
| Unicode/ICU data and native bundles | Server-only operation has a different delivery boundary from conveying binaries. | Preserve the applicable Unicode and other component notices in software/supporting documentation as the actual terms require. A parent project's MIT identifier does not replace these notices. |
| Debian GPL/LGPL and other OS packages | Mere network operation does not generally invoke GPL source distribution duties; check individual licenses. | Identify exact source-package versions, retain `/usr/share/doc/*/copyright` and referenced license texts, and arrange corresponding-source delivery/access as required for the chosen distribution method. LGPL/GCC runtime exceptions and separate-program aggregation need component-specific treatment, not whole-application copyleft assumptions. |

### certifi: scope and source access

The locked **certifi 2026.10.23** wheel's
`certifi-2026.10.23.dist-info/licenses/LICENSE` describes a Mozilla-derived CA
bundle and includes an MPL-2.0 notice with a license URL. Its `certifi/cacert.pem`
is present as PEM text. The exact source archive was downloaded and checked;
the source and wheel PEM SHA-256 values both equal
`2ef52ad56b4803e264045c915e55c236cbfa045b84b81efefc218a19eb44bd2b`.
This supports correspondence for the reviewed bundle, not proof about a later image.

For server-only hosting, this is not a reason to publish Radio Loadout's source.
For a distributed environment/container, preserve the certifi notice and
license access, keep the matching release source available to recipients, and
document a stable way to obtain it. The wheel already contains Python/PEM text;
do not automatically label it source-less because it is called a wheel. Confirm
the preferred form for modifying the generated Mozilla-derived bundle, including
the matching upstream data/generation inputs if required, before asserting MPL
source obligations are fully satisfied. The upstream moving Mozilla `tip` URL
in LICENSE does not alone identify a reproducible historical input.

The repository has no recipient-facing certifi source-access arrangement.
Record this as a **redistribution readiness gap**, not a finding that MPL requires
the whole application to be disclosed or that a separate online offer is always
needed when complete preferred-form source is already supplied. certifi's own
[documentation](https://certifiio.readthedocs.io/en/latest/) identifies the CA
bundle as MPL licensed. Do not put it under PolyForm Strict or strip it during
image slimming. pip may carry a second vendored certifi copy needing separate review.

### Apache and already-supplied notices

The requests 2.34.2 wheel supplies both `licenses/LICENSE` and `licenses/NOTICE`
under its `.dist-info`; the latter attributes Requests to Kenneth Reitz (2019).
Keep both in a distributed environment. The OpenTelemetry packages,
googleapis-common-protos and python-multipart supply Apache license files;
the inspected wheels have no standalone NOTICE entries. Check source-file
copyright headers as well when copying or modifying code.

Playwright's npm packages supply Microsoft/Puppeteer NOTICE material;
`playwright` and `playwright-core` also carry bundle-specific license sidecars.
`rich-toolkit` includes BSD Click and MIT Textual notices in
`LICENSE-THIRD-PARTY`; Typer carries a separate BSD Click license at
`typer/_click/LICENSE.txt`. markdown-it-py carries both its own and the original
markdown-it license. These are confirmed supplied notices to preserve, not
missing-license findings. They illustrate why checking only `.dist-info/LICENSE`
or the manifest's license string is inadequate.

## Native components: confirmed evidence and remaining gaps

All 11 native-bearing runtime wheels were inspected. Their ELF dynamic
dependencies include glibc/libpthread and, for some Rust wheels, libgcc_s,
libdl/librt and the ELF loader; protobuf also needs libstdc++ and libm. Exact OS
versions are now recorded in the supplied actual-image evidence; linkage and
applicable runtime exception coverage still require review.
ELF DT_NEEDED identifies dynamic dependencies, not all statically linked code.

The table retains historical candidate-wheel/source findings. The
[2026-11-04 native supplement](native-component-notices.md) confirms the actual
uvloop/Pydantic binary matches and records the added texts and narrower inclusion
evidence. It does not mark the entire native inventory addressed.

| Wheel/component | Actual source/binary/notice evidence | Finding and smallest corrective action |
| --- | --- | --- |
| uvloop 0.23.0 / libuv | Source defaults to linking `vendor/libuv/.libs/libuv.a`; bundled header identifies libuv 1.52.1. Wheel has libuv symbols and no dynamic libuv dependency. Source has `vendor/libuv/LICENSE` and `LICENSE-extra`; wheel supplies only uvloop's own MIT/Apache files. | Confirmed bundled-notice omission relative to source. Include libuv's applicable MIT, Joyent/Node, FreeBSD tree.h BSD-2 and ISC inet notices, checking the Linux-selected files. Do not substitute uvloop's copyright for libuv's. |
| pydantic_core 2.50.2 | Wheel supplies only parent MIT LICENSE. Source Cargo.lock has 102 package entries, including ICU 1.5.x, PyO3 0.30.1, idna and Unicode-related crates. Exact icu_normalizer 1.5.0 and icu_properties_data 1.5.0 crates supply Unicode-3.0 notices; PyO3 supplies MIT/Apache notices. | Confirmed wheel notice coverage gap against candidate source dependencies; exact compiled features/linkage still to establish. Generate notices from the feature-selected native build graph, including ICU/Unicode data and applicable PyO3 notices. A parent MIT file is insufficient evidence for all bundled code. |
| fastar 0.12.0 | Native `.so`; wheel only parent MIT. Cargo.lock has 45 entries, including PyO3 0.29.1. | Resolve feature-selected Rust runtime dependencies and retain their notices. No assertion that every build-only crate is shipped. |
| rignore 0.8.1 | Native `.so`; parent MIT only. Cargo.lock has 34 entries, including ignore 0.4.24 and PyO3 0.29.1. Exact ignore crate has `COPYING`, MIT and Unlicense texts. | Review selected crates and license alternatives, then supplement binary notices as needed. |
| watchfiles 1.3.0 | Native `_rust_notify.abi3.so`; parent MIT only. Cargo.lock has 47 entries; notify 8.0.0 is CC0-1.0 in its actual crate, not inferred MIT. PyO3 is 0.29.0. | Review selected Rust dependencies. Do not assign watchfiles' MIT license to notify or Unicode data. |
| unicode-ident 1.0.12 | Matching checksums in pydantic_core and watchfiles source locks; actual crate has MIT/Apache plus Unicode-DFS-2016 texts. | Macro/build usage may not place this crate's tables in the final wheel. Establish reachability before claiming a binary omission; keep notices if applicable. |
| httptools 0.9.0 | Wheel supplies parent MIT, `vendor/http-parser/LICENSE-MIT` (Joyent/Node), and `vendor/llhttp/LICENSE` (Fedor Indutny); two native extensions. | Positive notice-preservation evidence. Keep all three files; confirm source-to-wheel vendor versions if repackaging. |
| PyYAML 6.0.3 / LibYAML | `_yaml.so` contains `yaml_get_version_string`, `libyaml` and `0.2.5`; no dynamic libyaml entry. Source setup links yaml. Wheel has one MIT notice naming Ingy döt Net and Kirill Simonov, also the LibYAML authors. | Strong evidence of embedded LibYAML; parent notice overlaps upstream LibYAML's authors/terms. Do not declare missing attribution solely because no separate LibYAML file exists. Record exact build version and compare [LibYAML 0.2.5 License](https://github.com/yaml/libyaml/blob/0.2.5/License) to the shipped combined notice; confirm sufficiency before distribution. |
| protobuf 7.36.2 / upb | Native `_message.abi3.so` and upb symbols; source upb headers carry Google BSD notices pointing to LICENSE. Wheel carries Google BSD-3 license. | Parent license covers visible upb headers; inspect the full compiled source/dependency set and preserve any additional notices. Native code is not automatically cleared by one header sample. |
| charset-normalizer 3.5.2 | Two native modules; exact source uses Cython generation; parent MIT supplied. | Verify generated-code/runtime provenance and any applicable Cython exception/notice, without assuming the compiler's entire license applies to output. |
| MarkupSafe 3.0.4; websockets 17.4 | Native speedups; their BSD-3 notices are present; source archives inspected. | No additional native notice omission established in this review. This is not an exhaustive compiler/runtime bill of materials. |

For libuv, the exact source archive's `vendor/libuv/include/uv/tree.h` was also
read: it contains Niels Provos' 2002 BSD-2 conditions. `vendor/libuv/src/inet.c`
contains the ISC/Internet Software Consortium notices. `LICENSE-extra` identifies
these components but is not itself a substitute for their full applicable
notice texts. The Pydantic binary also contains `icu_normalizer` and PyO3 markers,
supporting the need to follow up the source-lock evidence; this still does not
identify every selected crate or its precise contribution to the executable.

## Build and test scope

Container build locks pin build 1.6.1, packaging 26.3, pyproject-hooks 1.3.3 and
setuptools 84.2.1. The final stage copies `/opt/venv` into a fresh base; it does
not copy the builder's global build-tool installation. The Dockerfile installs
project/runtime wheels with pip without a notice-stripping step. That suggests
supplied `.dist-info/licenses` survive, but only final image inspection can
confirm it. pip installed by `venv` remains a runtime-image component unless
explicitly removed; it is not covered by the 59-entry runtime lock.

**setuptools is not solely MIT internally.** Its inspected wheel vendors
autocommand 2.2.2 with LGPL-3.0 text. `setuptools/config/NOTICE` identifies
MPL-2.0 validate-pyproject schemas; `_validate_pyproject/NOTICE` identifies more
MPL material and BSD-3 fastjsonschema code. Keep these notices and assess covered
source/replacement obligations if distributing a builder or development image.
Normal use to build Radio Loadout does not place these tools' licenses on the
application output. Their presence alone does not block the runtime wheel.

The Python dev extra, CI Python installs, and isolated packaging smoke installs
are unpinned; they do not promise the runtime-lock versions. The current local
environment has different versions (for example FastAPI 0.141.1 and certifi
2026.7.22). It must not be cited as evidence that those versions exist in the
configured Linux image. Local pytest/Ruff evidence is listed below; development
dependencies and their future resolutions need a fresh inventory if shipped.

All five locked npm packages are test tools. axe-core/MPL applies to its covered
files, not the whole application. Injecting axe into an automated local browser
test is not shipping it to ordinary site visitors. If a bundle/test report or
test environment containing axe is distributed, retain its MPL notices and
covered source access as applicable, plus `LICENSE-3RD-PARTY.txt`. That file
lists MIT and ISC dependencies which must not be relabeled MPL or Strict.

Playwright includes inlined packages not represented as separate lockfile nodes.
Its sidecar notices are identified below. The lockfile does not inventory the
Chromium/FFmpeg binaries downloaded by `playwright install --with-deps chromium`.
Local cache directories include Chromium revision 1248 and FFmpeg revision 1013,
but they are Windows test-cache evidence, not Linux container components. This
review did not inventory those binaries' full versions/notices. Neither browsers
nor Node/npm are copied into the configured runtime image or project archives.
CI-uploaded Playwright HTML reports may themselves embed third-party browser
assets; review their actual exported bytes if distributing them publicly.

## Container OS and Python: actual-image collection, incomplete obligation review

**2026-11-04 collection implementation update:** the existing Linux-amd64 container
CI job now uses a focused [final-image inventory collector](image-inventory.md)
after smoke testing, including failure paths, before artifact upload and cleanup.
It binds collection to the staging container/build image ID, obtains package and
notice evidence through both base and virtual-environment interpreters, includes
pip/ensurepip vendored and bootstrap contents, and queries installed Debian
binary/source versions. It retains existing notices and bounded native marker/
ELF evidence, with selected resolved BuildKit image identifiers where available.
Raw build metadata, environment variables and full Docker inspection are not uploaded.

That implementation initially awaited CI evidence. The subsequently supplied ZIP
now establishes successful collection from the image identified above; see the
[actual-image evidence record](native-component-notices.md). Docker remains
unavailable locally. Missing notices, source access and native inclusion still
need component-specific review; the seven-day artifact is not a permanent
source-access mechanism. Historical candidate-wheel evidence remains identified
as such, with exact actual-image binary matches recorded for uvloop/Pydantic.

| Component family | What is established | Required image evidence |
| --- | --- | --- |
| CPython | Actual probes report 3.13.15; installed stdlib LICENSE.txt collected and hashed; pinned source LICENSE previously inspected. | Review incorporated-component notices, exact build configuration and enabled-component linkage (OpenSSL, SQLite, zlib, libffi, expat and compression). |
| Debian Bookworm | 97 installed package/source-version records; all have a detected copyright path; common license files collected. | Review actual copyright text/exception applicability and corresponding-source arrangements for applicable GPL/LGPL packages. Presence is not sufficiency. See [Debian copyright-file policy](https://www.debian.org/doc/debian-policy/ch-docs.html#copyright-information). |
| glibc, libgcc/libstdc++, loader and other shared libraries | Selected wheels' ELF references establish required SONAMEs, not the installed versions or license exception coverage. | Match every resolved shared object to its OS/source package; inspect LGPL and GCC runtime exceptions and any binary modification requirements. Do not infer that separate application code becomes GPL. |
| OpenSSL, CA certificates, tzdata and base utilities | Actual installed records include OpenSSL 3.0.20-1~deb12u2, ca-certificates 20250419~deb12u1 and tzdata 2026b-0+deb12u1. | Assess collected notice applicability, enabled usage and source access where required. Debian CA bundles and certifi are separate components. |
| pip / ensurepip / vendored bootstrap libraries | Base and venv pip 26.2.1, ensurepip wheel/hash and 18-pin vendor manifests/notices collected. Vendor certifi is 2026.6.17, distinct from direct certifi 2026.10.23. | Review those exact vendored/bootstrap components and their notices/source access; a vendor pin is not proof of every component's runtime use. |

The [official Python image documentation](https://hub.docker.com/_/python) does
not substitute for notices for everything inside an image. A current upstream
Dockerfile may describe a newer Python release; it is not evidence of the pinned
digest's OS versions. Do not advertise the entire container as PolyForm licensed.
Preserving copyright files alone also does not fulfill every GPL/LGPL source duty.

## CHIRP format compatibility and provenance

**2026-11-04 evidence update:** [CHIRP provenance record](chirp-provenance.md)
reviews project commit `2052235004e2a7a801f814a560a98f331f72309f`, introduction/change
patches, and date-selected historical CHIRP revisions predating the scoped work.
It identifies exact 50-tone/104-code table matches, the same tuning-step set,
CHIRP-specific defaults and shared tone-case structure. No particular copied
expressive implementation/prose fragment was identified; this does not prove
that none exists. Its bounded parsed-fixture comparison found no whole data-row
match in the selected upstream datasets. The linked record now includes a
dated **author-reported statement (2026-11-04)**, using Timothy Thurston's exact
authorship wording. He reports direct authorship with AI assistance during
planning/development, no personal copying/adaptation of CHIRP source or supplying
it to an assistant, and no external sample files brought into development/testing.
He recalls consulting RepeaterBook and other now-unremembered references to
check repeater settings, tone values and tuning-step options; he reports that
RepeaterBook records/tables were not copied into the repository. Original
development chats and notes are reported unavailable.

These are author recollections, not independently verified historical inputs.
Exact contributions to individual components, sources for each table, fixture
creation processes, development-time upstream revisions, assistant inputs and
any applicable permissions remain unestablished. The statement does not establish
clean-room development or alter the technical comparison findings. CHIRP
provenance remains **unresolved**; only the production API-documentation finding
above is marked addressed.

The paragraphs below retain the earlier review's comparison evidence and its
limits; the linked record supplies the more detailed historical source ledger,
specific locations/comparisons, fixture evidence and questions for the author.

Inspected exporter/importer, `chirp_csv_validation.py`, `dcs.py`, channel models,
browser CTCSS/DCS arrays, CHIRP fixture CSV files/README and compatibility tests.
The fixture README says the fixtures are synthetic and independently specified
relative to Radio Loadout's exporter; it does not prove that no upstream code,
test data or expressive tables were reused. It explicitly references CHIRP's
`generic_csv.py` header mapping and `chirp_common.py` tone semantics.

For an immutable comparison, downloaded upstream CHIRP commit
`efbbeade947aa4b0acd2da54cb30c1f5f845c14b` and its COPYING plus both referenced
files (hashes below). Both Python files identify Dan Smith and GPL-3.0-or-later;
COPYING is GPLv3. This current upstream snapshot is not necessarily the version
consulted when Radio Loadout was written.

The inspected Radio Loadout logic uses its own Channel/Tone data model and CSV
helpers. CHIRP uses its Memory model, CSV driver and split-tone routines.
There are necessary semantic overlaps: 21-column names/order, Tone/TSQL/DTCS/Cross
spellings, polarity, tone bounds, conventional CTCSS/DCS values and tuning steps.
Implementing a compatible interface or using radio facts is distinguishable from
copying protectable implementation or expressive selections. These observations
are not a legal determination about those particular tables or any code fragment.

History inspected includes exporter introduction
`58a7443c973907098e9d3d01608d10ac4d173dd2`, fixture introduction
`b5c41808e277c01fdeb44bf9441fd1843a7ba5da`, and validation changes
`1b7a731d3a5006a5395d5b5519354c21686cb839`. Those commits record changes but
do not contain a complete external-source ledger or contributor declarations.
No imported CHIRP package or bundled CHIRP source tree was found; **that absence
does not establish independent authorship**. No claim of a clean-room process
is made. The code reading and functional comparisons here are limited, not a
whole-history plagiarism analysis.

The dated author statement supplies a general authorship/source-handling account,
but does not reconstruct sources for individual code components, literal tables
or fixture rows. Record any further component-specific recollection or surviving
evidence and leave unavailable details explicitly unknown. Compare any identified
expressive adaptation against the relevant historical source and assess applicable
permissions. If GPL material was copied in a way that creates a
covered derivative, retaining a credit alone may not resolve incompatibility
with Strict's restrictions. Seek separate permission or another compatible
technical resolution; this report neither applies GPL to all project code nor
recommends changing the project's chosen license. Preserve any third-party rights.

## Confirmed findings, gaps, and prioritized actions

| Priority | Finding/status | Smallest recommended follow-up |
| --- | --- | --- |
| P0 before container redistribution | Successful actual-image collection is established from the checksum-verified ZIP. The [scoped native notice supplement](native-component-notices.md) is prepared; its delivery and other native/source-access findings remain open. | Run the updated Linux CI job to verify installed supplemental bytes, then complete native build-graph/OS/Python review and recipient source arrangements. Temporary diagnostics alone are not clearance or permanent source delivery. |
| P0 before project redistribution | [Historical comparisons and a dated author-reported statement are recorded](chirp-provenance.md). Component-level creation sources and any applicable permissions remain unresolved; no particular copied expressive fragment was identified, which does not exclude copying. | Record any further component-specific recollection or surviving evidence; original chats/notes are reported unavailable, so leave unrecoverable details unknown. Assess any actual adaptation and applicable permissions without assuming clearance from recollection or table/row comparisons. |
| P1 production API-doc delivery — addressed 2026-11-04 | Production/staging docs and OAuth redirect now return 404, production pages hide their links/assets, and development retains docs on independent instances. | Verified locally by regression/browser checks and the installed-wheel smoke probe; raw OpenAPI JSON remains available. Development/dependency redistribution notice questions and the uninspected final image remain separate. |
| P1 before conveying dependency environment | certifi notice/source correspondence partly verified, but recipient source mechanism/preferred bundle source unresolved. | Retain the exact certifi notices, document matching source access and check preferred-form inputs. Include pip's vendored copy if present. Do not demand disclosure of the entire app. |
| P1 for any bundled release | Package audits now verify exact supplemental notice bytes; an always-run actual-image evidence check is implemented for the new bundle. | Inspect the next Linux CI result; this check covers the versioned supplement, not every third-party obligation. Separately test archives if dependencies are ever vendored. |
| P2 documentation | Existing direct inventory is metadata-based and incomplete: e.g. python-dotenv 1.2.4's actual notice is BSD-3; notify is CC0; setuptools has LGPL/MPL components. | Update the older inventory to point to the stronger artifact evidence when documentation changes beyond this report are authorized. |
| P2 if shipping development artifacts | Test/browser/build bundles have extra components and licenses. | Preserve npm sidecars/NOTICE, inventory exported HTML reports and browser binaries, and review setuptools' covered material if the builder itself is distributed. |

During the 2026-11-03 baseline review, no unrelated edits, dependency updates,
application changes, licensing-file changes, CI changes, commits, pushes,
deployments or image publication were performed. The review does not resolve ownership questions by assumption, and
it does not label any delivery as legally cleared.

## Detailed artifact inventories

The following inventory distinguishes **license text actually present** from
unresolved embedded-component coverage. A permissive parent license is not a
claim that every byte in a native or bundled artifact is covered by that license.
Evidence paths are archive-member paths, not paths expected in this repository.

### Locked Python runtime and build wheels

R = server runtime lock (59 entries); B = container build lock (four entries). Runtime here means installed by the configured runtime lock, even when a CLI, cloud or telemetry extra is not exercised by the application. Native packages and bundled code need the separate qualifications above. All actual notice entries in each archive were collected; evidence paths below list the supplied license/NOTICE files. PyPI release artifact links provide retrieval metadata; the conclusion is based on the downloaded files, not those metadata labels.

| ID / scope | Component / version | License text identified | Actual archive notice evidence |
| --- | --- | --- | --- |
| W01 / R | [agent-detector 2.0.0](https://pypi.org/pypi/agent-detector/2.0.0/json) | MIT | `agent_detector-2.0.0.dist-info/licenses/LICENSE` |
| W02 / R | [annotated-doc 0.0.5](https://pypi.org/pypi/annotated-doc/0.0.5/json) | MIT | `annotated_doc-0.0.5.dist-info/licenses/LICENSE` |
| W03 / R | [annotated-types 0.8.0](https://pypi.org/pypi/annotated-types/0.8.0/json) | MIT | `annotated_types-0.8.0.dist-info/licenses/LICENSE` |
| W04 / R | [anyio 4.16.0](https://pypi.org/pypi/anyio/4.16.0/json) | MIT | `anyio-4.16.0.dist-info/licenses/LICENSE` |
| W05 / B | [build 1.6.1](https://pypi.org/pypi/build/1.6.1/json) | MIT | `build-1.6.1.dist-info/licenses/LICENSE` |
| W06 / R | [certifi 2026.10.23](https://pypi.org/pypi/certifi/2026.10.23/json) | MPL-2.0 (Mozilla CA bundle notice) | `certifi-2026.10.23.dist-info/licenses/LICENSE` |
| W07 / R | [charset-normalizer 3.5.2](https://pypi.org/pypi/charset-normalizer/3.5.2/json) (native) | MIT | `charset_normalizer-3.5.2.dist-info/licenses/LICENSE` |
| W08 / R | [click 8.5.0](https://pypi.org/pypi/click/8.5.0/json) | BSD-3-Clause | `click-8.5.0.dist-info/licenses/LICENSE.txt` |
| W09 / R | [detect-installer 0.2.1](https://pypi.org/pypi/detect-installer/0.2.1/json) | 0BSD | `detect_installer-0.2.1.dist-info/licenses/LICENSE` |
| W10 / R | [dnspython 2.9.1](https://pypi.org/pypi/dnspython/2.9.1/json) | ISC, with additional retained historical notices | `dnspython-2.9.1.dist-info/licenses/LICENSE` |
| W11 / R | [email-validator 2.3.0](https://pypi.org/pypi/email-validator/2.3.0/json) | Unlicense | `email_validator-2.3.0.dist-info/licenses/LICENSE` |
| W12 / R | [fastapi 0.162.0](https://pypi.org/pypi/fastapi/0.162.0/json) | MIT | `fastapi-0.162.0.dist-info/licenses/LICENSE` |
| W13 / R | [fastapi-cli 0.0.32](https://pypi.org/pypi/fastapi-cli/0.0.32/json) | MIT | `fastapi_cli-0.0.32.dist-info/licenses/LICENSE` |
| W14 / R | [fastapi-cloud-cli 0.26.0](https://pypi.org/pypi/fastapi-cloud-cli/0.26.0/json) | MIT | `fastapi_cloud_cli-0.26.0.dist-info/licenses/LICENSE` |
| W15 / R | [fastar 0.12.0](https://pypi.org/pypi/fastar/0.12.0/json) (native) | MIT | `fastar-0.12.0.dist-info/licenses/LICENSE` |
| W16 / R | [googleapis-common-protos 1.76.0](https://pypi.org/pypi/googleapis-common-protos/1.76.0/json) | Apache-2.0 | `googleapis_common_protos-1.76.0.dist-info/licenses/LICENSE` |
| W17 / R | [h11 0.16.0](https://pypi.org/pypi/h11/0.16.0/json) | MIT | `h11-0.16.0.dist-info/licenses/LICENSE.txt` |
| W18 / R | [httpcore 1.0.9](https://pypi.org/pypi/httpcore/1.0.9/json) | BSD-3-Clause | `httpcore-1.0.9.dist-info/licenses/LICENSE.md` |
| W19 / R | [httpcore2 2.16.0](https://pypi.org/pypi/httpcore2/2.16.0/json) | BSD-3-Clause | `httpcore2-2.16.0.dist-info/licenses/LICENSE.md` |
| W20 / R | [httptools 0.9.0](https://pypi.org/pypi/httptools/0.9.0/json) (native) | MIT | `httptools-0.9.0.dist-info/licenses/LICENSE`<br>`httptools-0.9.0.dist-info/licenses/vendor/http-parser/LICENSE-MIT`<br>`httptools-0.9.0.dist-info/licenses/vendor/llhttp/LICENSE` |
| W21 / R | [httpx 0.28.1](https://pypi.org/pypi/httpx/0.28.1/json) | BSD-3-Clause | `httpx-0.28.1.dist-info/licenses/LICENSE.md` |
| W22 / R | [httpx2 2.16.0](https://pypi.org/pypi/httpx2/2.16.0/json) | BSD-3-Clause | `httpx2-2.16.0.dist-info/licenses/LICENSE.md` |
| W23 / R | [idna 3.20](https://pypi.org/pypi/idna/3.20/json) | BSD-3-Clause | `idna-3.20.dist-info/licenses/LICENSE.md` |
| W24 / R | [Jinja2 3.1.6](https://pypi.org/pypi/Jinja2/3.1.6/json) | BSD-3-Clause | `jinja2-3.1.6.dist-info/licenses/LICENSE.txt` |
| W25 / R | [markdown-it-py 4.2.0](https://pypi.org/pypi/markdown-it-py/4.2.0/json) | MIT | `markdown_it_py-4.2.0.dist-info/licenses/LICENSE`<br>`markdown_it_py-4.2.0.dist-info/licenses/LICENSE.markdown-it` |
| W26 / R | [MarkupSafe 3.0.4](https://pypi.org/pypi/MarkupSafe/3.0.4/json) (native) | BSD-3-Clause | `markupsafe-3.0.4.dist-info/licenses/LICENSE.txt` |
| W27 / R | [mdurl 0.1.2](https://pypi.org/pypi/mdurl/0.1.2/json) | MIT | `mdurl-0.1.2.dist-info/LICENSE` |
| W28 / R | [opentelemetry-api 1.45.2](https://pypi.org/pypi/opentelemetry-api/1.45.2/json) | Apache-2.0 | `opentelemetry_api-1.45.2.dist-info/licenses/LICENSE` |
| W29 / R | [opentelemetry-exporter-http-transport 0.66b2](https://pypi.org/pypi/opentelemetry-exporter-http-transport/0.66b2/json) | Apache-2.0 | `opentelemetry_exporter_http_transport-0.66b2.dist-info/licenses/LICENSE` |
| W30 / R | [opentelemetry-exporter-otlp-common 0.66b2](https://pypi.org/pypi/opentelemetry-exporter-otlp-common/0.66b2/json) | Apache-2.0 | `opentelemetry_exporter_otlp_common-0.66b2.dist-info/licenses/LICENSE` |
| W31 / R | [opentelemetry-exporter-otlp-proto-common 1.45.2](https://pypi.org/pypi/opentelemetry-exporter-otlp-proto-common/1.45.2/json) | Apache-2.0 | `opentelemetry_exporter_otlp_proto_common-1.45.2.dist-info/licenses/LICENSE` |
| W32 / R | [opentelemetry-exporter-otlp-proto-http 1.45.2](https://pypi.org/pypi/opentelemetry-exporter-otlp-proto-http/1.45.2/json) | Apache-2.0 | `opentelemetry_exporter_otlp_proto_http-1.45.2.dist-info/licenses/LICENSE` |
| W33 / R | [opentelemetry-proto 1.45.2](https://pypi.org/pypi/opentelemetry-proto/1.45.2/json) | Apache-2.0 | `opentelemetry_proto-1.45.2.dist-info/licenses/LICENSE` |
| W34 / R | [opentelemetry-sdk 1.45.2](https://pypi.org/pypi/opentelemetry-sdk/1.45.2/json) | Apache-2.0 | `opentelemetry_sdk-1.45.2.dist-info/licenses/LICENSE` |
| W35 / R | [opentelemetry-semantic-conventions 0.66b2](https://pypi.org/pypi/opentelemetry-semantic-conventions/0.66b2/json) | Apache-2.0 | `opentelemetry_semantic_conventions-0.66b2.dist-info/licenses/LICENSE` |
| W36 / B | [packaging 26.3](https://pypi.org/pypi/packaging/26.3/json) | Apache-2.0 OR BSD-2-Clause | `packaging-26.3.dist-info/licenses/LICENSE`<br>`packaging-26.3.dist-info/licenses/LICENSE.APACHE`<br>`packaging-26.3.dist-info/licenses/LICENSE.BSD` |
| W37 / R | [protobuf 7.36.2](https://pypi.org/pypi/protobuf/7.36.2/json) (native) | BSD-3-Clause | `protobuf-7.36.2.dist-info/LICENSE` |
| W38 / R | [pydantic 2.14.2](https://pypi.org/pypi/pydantic/2.14.2/json) | MIT | `pydantic-2.14.2.dist-info/licenses/LICENSE` |
| W39 / R | [pydantic_core 2.50.2](https://pypi.org/pypi/pydantic_core/2.50.2/json) (native) | MIT | `pydantic_core-2.50.2.dist-info/licenses/LICENSE` |
| W40 / R | [pydantic-extra-types 2.11.1](https://pypi.org/pypi/pydantic-extra-types/2.11.1/json) | MIT | `pydantic_extra_types-2.11.1.dist-info/licenses/LICENSE` |
| W41 / R | [pydantic-settings 2.16.2](https://pypi.org/pypi/pydantic-settings/2.16.2/json) | MIT | `pydantic_settings-2.16.2.dist-info/licenses/LICENSE` |
| W42 / R | [Pygments 2.21.0](https://pypi.org/pypi/Pygments/2.21.0/json) | BSD-2-Clause | `pygments-2.21.0.dist-info/licenses/AUTHORS`<br>`pygments-2.21.0.dist-info/licenses/LICENSE` |
| W43 / B | [pyproject_hooks 1.3.3](https://pypi.org/pypi/pyproject_hooks/1.3.3/json) | MIT | `pyproject_hooks-1.3.3.dist-info/licenses/LICENSE` |
| W44 / R | [python-dotenv 1.2.4](https://pypi.org/pypi/python-dotenv/1.2.4/json) | BSD-3-Clause | `python_dotenv-1.2.4.dist-info/licenses/LICENSE` |
| W45 / R | [python-multipart 0.0.33](https://pypi.org/pypi/python-multipart/0.0.33/json) | Apache-2.0 | `python_multipart-0.0.33.dist-info/licenses/LICENSE.txt` |
| W46 / R | [PyYAML 6.0.3](https://pypi.org/pypi/PyYAML/6.0.3/json) (native) | MIT | `pyyaml-6.0.3.dist-info/licenses/LICENSE` |
| W47 / R | [requests 2.34.2](https://pypi.org/pypi/requests/2.34.2/json) | Apache-2.0 | `requests-2.34.2.dist-info/licenses/LICENSE`<br>`requests-2.34.2.dist-info/licenses/NOTICE` |
| W48 / R | [rich 15.0.0](https://pypi.org/pypi/rich/15.0.0/json) | MIT | `rich-15.0.0.dist-info/licenses/LICENSE` |
| W49 / R | [rich-toolkit 0.20.6](https://pypi.org/pypi/rich-toolkit/0.20.6/json) | MIT | `rich_toolkit-0.20.6.dist-info/licenses/LICENSE`<br>`rich_toolkit-0.20.6.dist-info/licenses/LICENSE-THIRD-PARTY` |
| W50 / R | [rignore 0.8.1](https://pypi.org/pypi/rignore/0.8.1/json) (native) | MIT | `rignore-0.8.1.dist-info/licenses/LICENSE` |
| W51 / R | [sentry-sdk 2.73.0](https://pypi.org/pypi/sentry-sdk/2.73.0/json) | MIT | `sentry_sdk-2.73.0.dist-info/licenses/LICENSE` |
| W52 / B | [setuptools 84.2.1](https://pypi.org/pypi/setuptools/84.2.1/json) | MIT parent; LGPL/MPL and others vendored | `setuptools/config/NOTICE`<br>`setuptools/config/_validate_pyproject/NOTICE`<br>`setuptools-84.2.1.dist-info/licenses/LICENSE`<br>`setuptools/_vendor/ (see inventory below)` |
| W53 / R | [shellingham 1.5.4](https://pypi.org/pypi/shellingham/1.5.4/json) | ISC | `shellingham-1.5.4.dist-info/LICENSE` |
| W54 / R | [starlette 1.10.0](https://pypi.org/pypi/starlette/1.10.0/json) | BSD-3-Clause | `starlette-1.10.0.dist-info/licenses/LICENSE.md` |
| W55 / R | [truststore 0.10.5](https://pypi.org/pypi/truststore/0.10.5/json) | MIT | `truststore-0.10.5.dist-info/licenses/LICENSE` |
| W56 / R | [typer 0.27.3](https://pypi.org/pypi/typer/0.27.3/json) | MIT | `typer-0.27.3.dist-info/licenses/LICENSE`<br>`typer/_click/LICENSE.txt` |
| W57 / R | [typing_extensions 4.16.0](https://pypi.org/pypi/typing_extensions/4.16.0/json) | PSF-2.0 and historical Python terms | `typing_extensions-4.16.0.dist-info/licenses/LICENSE` |
| W58 / R | [typing-inspection 0.4.4](https://pypi.org/pypi/typing-inspection/0.4.4/json) | MIT | `typing_inspection-0.4.4.dist-info/licenses/LICENSE` |
| W59 / R | [urllib3 2.8.0](https://pypi.org/pypi/urllib3/2.8.0/json) | MIT | `urllib3-2.8.0.dist-info/licenses/LICENSE.txt` |
| W60 / R | [uvicorn 0.54.0](https://pypi.org/pypi/uvicorn/0.54.0/json) | BSD-3-Clause | `uvicorn-0.54.0.dist-info/licenses/LICENSE.md` |
| W61 / R | [uvloop 0.23.0](https://pypi.org/pypi/uvloop/0.23.0/json) (native) | MIT and Apache-2.0 texts; see native gap | `uvloop-0.23.0.dist-info/licenses/LICENSE-APACHE`<br>`uvloop-0.23.0.dist-info/licenses/LICENSE-MIT` |
| W62 / R | [watchfiles 1.3.0](https://pypi.org/pypi/watchfiles/1.3.0/json) (native) | MIT | `watchfiles-1.3.0.dist-info/licenses/LICENSE` |
| W63 / R | [websockets 17.4](https://pypi.org/pypi/websockets/17.4/json) (native) | BSD-3-Clause | `websockets-17.4.dist-info/licenses/LICENSE` |

### Python wheel artifact checksums

Hashes identify the exact downloaded candidate wheel and its embedded evidence. Each matched a hash in the reviewed lockfile. Other platforms, ABIs and wheel rebuilds require their own review.

| ID | Filename | SHA-256 |
| --- | --- | --- |
| W01 | `agent_detector-2.0.0-py3-none-any.whl` | `22c6a1c9c23894a12f55aea625f060b8d3330fba774de72d02d5442bb580417f` |
| W02 | `annotated_doc-0.0.5-py3-none-any.whl` | `117bac03a25ede5df5440e855b32d556049ca169ead221505badf432fed4b101` |
| W03 | `annotated_types-0.8.0-py3-none-any.whl` | `f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0` |
| W04 | `anyio-4.16.0-py3-none-any.whl` | `c66ae634e0b8228396b801741beb3294326d4b6102f7bba4041c0dfb58c29026` |
| W05 | `build-1.6.1-py3-none-any.whl` | `ecd351a4be9d35a9eaaba244a7687143c9c7d4aea6ac964e7e7ddab20cbcf4e7` |
| W06 | `certifi-2026.10.23-py3-none-any.whl` | `e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1` |
| W07 | `charset_normalizer-3.5.2-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `7218e8f32b0956cfcd048fd42d9d5779809745ca1d86113ca56f66e7ae1549c4` |
| W08 | `click-8.5.0-py3-none-any.whl` | `255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360` |
| W09 | `detect_installer-0.2.1-py3-none-any.whl` | `87e2ce7d05cb108b178f8e45bb80d3d88c0cb4b397983345c18ad6562e02e620` |
| W10 | `dnspython-2.9.1-py3-none-any.whl` | `7c81caf8de1ed57b8cfc7e0ad4f528a0b8ceace473c7eb946df195dc9def751f` |
| W11 | `email_validator-2.3.0-py3-none-any.whl` | `80f13f623413e6b197ae73bb10bf4eb0908faf509ad8362c5edeb0be7fd450b4` |
| W12 | `fastapi-0.162.0-py3-none-any.whl` | `3785963de305dd09912426cb81f2d230fce98ab3521cdfe97265c8d14983128c` |
| W13 | `fastapi_cli-0.0.32-py3-none-any.whl` | `8dcc286fa32f01bbd3f65dd09cfd5a2540ed5f2230b77db7fd30978d6165f3c4` |
| W14 | `fastapi_cloud_cli-0.26.0-py3-none-any.whl` | `94029f92f3dc4289b376e1213f0d6cc7c30d4f32de7e47b5effc6dc754ab9ce9` |
| W15 | `fastar-0.12.0-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `e2bfad69679111e4567d4bad41fd795071c9335cd94bc0f26e24b7d19e95c9b1` |
| W16 | `googleapis_common_protos-1.76.0-py3-none-any.whl` | `59e13344a9f3651aa201a03e2bee815a3bf43a4baf1f9ff8a9b62a840ce25fac` |
| W17 | `h11-0.16.0-py3-none-any.whl` | `63cf8bbe7522de3bf65932fda1d9c2772064ffb3dae62d55932da54b31cb6c86` |
| W18 | `httpcore-1.0.9-py3-none-any.whl` | `2d400746a40668fc9dec9810239072b40b4484b640a8c38fd654a024c7a1bf55` |
| W19 | `httpcore2-2.16.0-py3-none-any.whl` | `5c4358319f2602d984ad93182c9fee5160f22e9da7babdda870a5e7c4e2dc34f` |
| W20 | `httptools-0.9.0-cp313-cp313-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl` | `088de1738e1af624466a01c35d652dbe6fb825be887c76d68aa850621d81db88` |
| W21 | `httpx-0.28.1-py3-none-any.whl` | `d909fcccc110f8c7faf814ca82a9a4d816bc5a6dbfea25d6591d6985b8ba59ad` |
| W22 | `httpx2-2.16.0-py3-none-any.whl` | `fd2c5d7909e8d86fe92d53020c310ca0e4e431b838c207c5754b9bbf0308d49a` |
| W23 | `idna-3.20-py3-none-any.whl` | `ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c` |
| W24 | `jinja2-3.1.6-py3-none-any.whl` | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` |
| W25 | `markdown_it_py-4.2.0-py3-none-any.whl` | `9f7ebbcd14fe59494226453aed97c1070d83f8d24b6fc3a3bcf9a38092641c4a` |
| W26 | `markupsafe-3.0.4-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `434139499bb20b502ed3baa1f169e618f924a97e7a777fea1a49446d80106cf6` |
| W27 | `mdurl-0.1.2-py3-none-any.whl` | `84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8` |
| W28 | `opentelemetry_api-1.45.2-py3-none-any.whl` | `2cbd737377e710ee740d261c94e93fa0f08e6d037c18f17513cc0a2d94479a34` |
| W29 | `opentelemetry_exporter_http_transport-0.66b2-py3-none-any.whl` | `fd5f5b490c099acda1cd7b909d5e8981436bf18cc8c6098d302d114c271720e9` |
| W30 | `opentelemetry_exporter_otlp_common-0.66b2-py3-none-any.whl` | `ace86efb75489f925f1ef809856ae5f0c7db534e4afdc624530222228b1236a5` |
| W31 | `opentelemetry_exporter_otlp_proto_common-1.45.2-py3-none-any.whl` | `af483b24217028892f017096731b794b196b785025d2e6808874720fd0b05a80` |
| W32 | `opentelemetry_exporter_otlp_proto_http-1.45.2-py3-none-any.whl` | `6e4d025138829d0ee57946930c2ccad6491ad4d92a958e9c7eea69278fe60cfc` |
| W33 | `opentelemetry_proto-1.45.2-py3-none-any.whl` | `03a7ca1b43f89fd5b965d5975902bb2515c0c86e2428b456836e9a6149c6235a` |
| W34 | `opentelemetry_sdk-1.45.2-py3-none-any.whl` | `ff974ea70ee4f1d51e2ec152db37c2b626c7bf82bb3f7d86114fd8704e7199c6` |
| W35 | `opentelemetry_semantic_conventions-0.66b2-py3-none-any.whl` | `4cbe61e5f9275d57ab31708446e7938ef4291ebbe6a7fca6f7a629c5acae87d8` |
| W36 | `packaging-26.3-py3-none-any.whl` | `d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c` |
| W37 | `protobuf-7.36.2-cp310-abi3-manylinux2014_x86_64.whl` | `89f23aa53c24553a2416fd4fd1ec06f74fa42b14b546d8883128813f775bbfd2` |
| W38 | `pydantic-2.14.2-py3-none-any.whl` | `7efbf7507b937931cd32a5755acb00ea1cf5ccb1d4e8067a5850d5069e382118` |
| W39 | `pydantic_core-2.50.2-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `31a1fb3ffbd1195b24490f671d12623dd4c9bfa56d6af0a299fa43b516134f5b` |
| W40 | `pydantic_extra_types-2.11.1-py3-none-any.whl` | `1722ea2bddae5628ace25f2aa685b69978ef533123e5638cfbddb999e0100ec1` |
| W41 | `pydantic_settings-2.16.2-py3-none-any.whl` | `8d523e5c129b097686bde019bd6109bff53f4c8c3f63f1ddf9933ffa42e5ab4f` |
| W42 | `pygments-2.21.0-py3-none-any.whl` | `2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9` |
| W43 | `pyproject_hooks-1.3.3-py3-none-any.whl` | `5fc53fdac9f7bd63fbcdc868fb5f90b4784d78a53a3d3388cd738b807441a20b` |
| W44 | `python_dotenv-1.2.4-py3-none-any.whl` | `42269a8a5b3fd54ffa6f3d84b18abed50064717576b4ecf03dc4a55d8aa04fdc` |
| W45 | `python_multipart-0.0.33-py3-none-any.whl` | `8f16c07b36add9da6b2ee87d3efcaf0a45a6de9c3d0a5dd94e9ccf7675a7bc45` |
| W46 | `pyyaml-6.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `0f29edc409a6392443abf94b9cf89ce99889a1dd5376d94316ae5145dfedd5d6` |
| W47 | `requests-2.34.2-py3-none-any.whl` | `2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0` |
| W48 | `rich-15.0.0-py3-none-any.whl` | `33bd4ef74232fb73fe9279a257718407f169c09b78a87ad3d296f548e27de0bb` |
| W49 | `rich_toolkit-0.20.6-py3-none-any.whl` | `465453ba6f94f99401f59f79fb562827ba5f6b4d4759015d40019f5c67750262` |
| W50 | `rignore-0.8.1-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `2ca91c91a53135889945e77b286215ecd41c8f1090398db97ca3459c5a290eb6` |
| W51 | `sentry_sdk-2.73.0-py3-none-any.whl` | `0bcfa6928ea5adbb89591858b514d27adac27c7a3cccc31b20ed10e0b09eda9e` |
| W52 | `setuptools-84.2.1-py3-none-any.whl` | `ca140b45d5325a9478f880e351484f62fef15f336462e449ca0c03c873d589c2` |
| W53 | `shellingham-1.5.4-py2.py3-none-any.whl` | `7ecfff8f2fd72616f7481040475a65b2bf8af90a56c89140852d1120324e8686` |
| W54 | `starlette-1.10.0-py3-none-any.whl` | `478c0ab3b4ced6e82719849c118fa406f0278a3499c1a898cd15cd31bdc38ce4` |
| W55 | `truststore-0.10.5-py3-none-any.whl` | `9aaaedaefaf06d8b206278cf8b5012bc897f485a874503501e12d776df78951c` |
| W56 | `typer-0.27.3-py3-none-any.whl` | `e50022f28b82a86313e54501317a1db64bf8f8d036ff8cfe5ca7e47675454aff` |
| W57 | `typing_extensions-4.16.0-py3-none-any.whl` | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |
| W58 | `typing_inspection-0.4.4-py3-none-any.whl` | `65b8397ba37ccbce054456aaccddfc91e6e3083c92824df348d96ca832f3f147` |
| W59 | `urllib3-2.8.0-py3-none-any.whl` | `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3` |
| W60 | `uvicorn-0.54.0-py3-none-any.whl` | `505bdb0f318731d45f1f712071fc781a8981f6847a31c902c9f5e652d4f67faf` |
| W61 | `uvloop-0.23.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `e2cba180d6451822763eda8364f342435a873bcfb3849cbd82fdeca248ca65eb` |
| W62 | `watchfiles-1.3.0-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `b5768b49e426fd5b550b012c866db347cdf15c398ef98dc557b6e6b72fa74cd1` |
| W63 | `websockets-17.4-cp313-cp313-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl` | `25eb661d8ba7e2b85ebb4e7a1bb9f6a3280910ed10b84330a7abfb5ed32d2764` |

### Native/certifi source artifacts inspected

Each download was checked against its PyPI release SHA-256. These are upstream source releases, not a reproduction of the wheel build. Source URLs can be recovered by exact filename from the release artifact JSON linked above.

| Source archive | SHA-256 | Evidence focus |
| --- | --- | --- |
| `certifi-2026.10.23.tar.gz` | `a9895e6e2758b371e0545e321a3a8fd1fcfd9829ada8824a936dfb16aaaf36cd` | LICENSE; matching certifi/cacert.pem |
| `charset_normalizer-3.5.2.tar.gz` | `39de2a259fc954455c57274dc94c79d5842774e1247a016aff30bc0efed0f4ef` | LICENSE, setup.py Cython generation |
| `fastar-0.12.0.tar.gz` | `bba71522eae6a7627a5514ffdd4ac9645ef27d82e23931d79fd974bb49c3f2ad` | LICENSE, Cargo.toml/Cargo.lock |
| `httptools-0.9.0.tar.gz` | `d484ebb7e3a3f3597b0f645fbd1b85633674ca808c1f5ba11c2caf7c66f5c8b6` | LICENSE and vendor/http-parser, vendor/llhttp notices |
| `markupsafe-3.0.4.tar.gz` | `2e9ad7dd851bf45fab9f75cbff4cb493fee9979e8d8c7c9c3ee119022518edd6` | LICENSE.txt and source layout |
| `protobuf-7.36.2.tar.gz` | `497d0463ff3316681da6c0b9e8d06cb465d61abce00b613ab42226175644d1bb` | LICENSE, setup.py, upb source header |
| `pydantic_core-2.50.2.tar.gz` | `1b0e8dc3932cf4e9ed5727570325cacc716b9409ffc794a221c0ccc72e8eb775` | LICENSE, Cargo.toml/Cargo.lock; selected crates below |
| `pyyaml-6.0.3.tar.gz` | `d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f` | LICENSE, setup.py libyaml linkage |
| `rignore-0.8.1.tar.gz` | `2b6cf58501e9ff1b6a71c3fd66c8a105311e1f23237626fd4c9c00606bb3d30f` | LICENSE, Cargo.toml/Cargo.lock |
| `uvloop-0.23.0.tar.gz` | `28d160f51ab4da3b187063652e643dea6831072add4adc1e6d62afbe73b6be27` | setup.py; vendor/libuv LICENSE, LICENSE-extra and version.h |
| `watchfiles-1.3.0.tar.gz` | `99aee4a07847c06820765fd7b1b49ceac4f3f711ccb7d104655a33231de1c207` | LICENSE, Cargo.toml/Cargo.lock |
| `websockets-17.4.tar.gz` | `09d3939b70df0c8ad2da145ebd50978bccaee1d565e838b0e7921a34d38571eb` | LICENSE and source layout |

### Selected Rust components: direct artifact evidence

These are samples from exact source locks, not an exhaustive native inventory. A Cargo.lock includes development/build/platform-specific packages; its presence does not prove final binary inclusion. Crate SHA-256 values below matched the corresponding source Cargo.lock checksums.

| Crate / version | License evidence inside actual crate | Source-lock match | SHA-256 |
| --- | --- | --- | --- |
| [icu_normalizer 1.5.0](https://static.crates.io/crates/icu_normalizer/icu_normalizer-1.5.0.crate) | Unicode-3.0; LICENSE | pydantic_core | `19ce3e0da2ec68599d193c93d088142efd7f9c5d6fc9b803774855747dc6a84f` |
| [icu_properties_data 1.5.0](https://static.crates.io/crates/icu_properties_data/icu_properties_data-1.5.0.crate) | Unicode-3.0; LICENSE | pydantic_core | `67a8effbc3dd3e4ba1afa8ad918d5684b8868b3b26500753effea8d2eed19569` |
| [unicode-ident 1.0.12](https://static.crates.io/crates/unicode-ident/unicode-ident-1.0.12.crate) | (MIT OR Apache-2.0) AND Unicode-DFS-2016; LICENSE-MIT/APACHE/UNICODE | pydantic_core, watchfiles | `3354b9ac3fae1ff6755cb6db53683adb661634f67557942dea4facebec0fee4b` |
| [pyo3 0.30.1](https://static.crates.io/crates/pyo3/pyo3-0.30.1.crate) | MIT OR Apache-2.0; LICENSE-MIT/APACHE, including pyo3-runtime copies | pydantic_core | `229ca13b8a15bb0d1487b81ab975bfcd97513416499a8312011b6036e42e0de4` |
| [notify 8.0.0](https://static.crates.io/crates/notify/notify-8.0.0.crate) | CC0-1.0; LICENSE-CC0 | watchfiles | `2fee8403b3d66ac7b26aee6e40a897d85dc5ce26f44da36b8b73e987cc52e943` |
| [ignore 0.4.24](https://static.crates.io/crates/ignore/ignore-0.4.24.crate) | Unlicense OR MIT; COPYING, LICENSE-MIT, UNLICENSE | rignore | `81776e6f9464432afcc28d03e52eb101c93b6f0566f52aef2427663e700f0403` |

### setuptools bundled build components

Actual vendored license files were inspected in W52 (setuptools). The vendor directory, rather than the top-level metadata alone, establishes the additional scope. Versions below are from the internal distribution metadata; license text was checked separately.

| Bundled component | Version | License text | Archive evidence |
| --- | --- | --- | --- |
| autocommand | 2.2.2 | LGPL-3.0 text | `setuptools/_vendor/autocommand-2.2.2.dist-info/LICENSE` |
| backports.tarfile | 1.2.0 | MIT | `setuptools/_vendor/backports.tarfile-1.2.0.dist-info/LICENSE` |
| importlib_metadata | 8.7.1 | Apache-2.0 | `setuptools/_vendor/importlib_metadata-8.7.1.dist-info/licenses/LICENSE` |
| jaraco.text | 4.0.0 | MIT | `setuptools/_vendor/jaraco.text-4.0.0.dist-info/LICENSE` |
| jaraco.context | 6.1.0 | MIT | `setuptools/_vendor/jaraco_context-6.1.0.dist-info/licenses/LICENSE` |
| jaraco.functools | 4.4.0 | MIT | `setuptools/_vendor/jaraco_functools-4.4.0.dist-info/licenses/LICENSE` |
| more-itertools | 10.8.0 | MIT | `setuptools/_vendor/more_itertools-10.8.0.dist-info/licenses/LICENSE` |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | `setuptools/_vendor/packaging-26.3.dist-info/licenses/LICENSE`<br>`setuptools/_vendor/packaging-26.3.dist-info/licenses/LICENSE.APACHE`<br>`setuptools/_vendor/packaging-26.3.dist-info/licenses/LICENSE.BSD` |
| platformdirs | 4.4.0 | MIT | `setuptools/_vendor/platformdirs-4.4.0.dist-info/licenses/LICENSE` |
| tomli | 2.4.0 | MIT | `setuptools/_vendor/tomli-2.4.0.dist-info/licenses/LICENSE` |
| wheel | 0.46.3 | MIT | `setuptools/_vendor/wheel-0.46.3.dist-info/licenses/LICENSE.txt` |
| zipp | 3.23.0 | MIT | `setuptools/_vendor/zipp-3.23.0.dist-info/licenses/LICENSE` |
| validate-pyproject / generated schemas and validators | Upstream version not established from the inspected NOTICE | MPL-2.0 | `setuptools/config/NOTICE`, `setuptools/config/_validate_pyproject/NOTICE` and covered files |
| fastjsonschema copied code | Upstream version not established from the inspected NOTICE | BSD-3-Clause | `setuptools/config/_validate_pyproject/NOTICE`, `fastjsonschema_exceptions.py` |

### Observed Python test/bootstrap tools (not a lock)

These are exact local observations; they are not the final-image inventory. Their license files were inspected in the existing Windows `.venv`. build/packaging/pyproject-hooks/setuptools are listed separately above. Platform markers can add tools such as colorama; future dev installs and Python 3.11 builds can resolve differently.

| Tool/component | Observed version | Actual notice evidence / result |
| --- | --- | --- |
| pytest | 9.1.1 | MIT; `pytest-9.1.1.dist-info/licenses/LICENSE` |
| ruff | 0.16.8 | MIT parent; native Rust dependencies not exhaustively inventoried; `ruff-0.16.8.dist-info/licenses/LICENSE` |
| iniconfig | 2.3.0 | MIT; `iniconfig-2.3.0.dist-info/licenses/LICENSE` |
| pluggy | 1.6.0 | MIT; `pluggy-1.6.0.dist-info/licenses/LICENSE` |
| colorama | 0.4.6 | BSD-3-Clause; `colorama-0.4.6.dist-info/licenses/LICENSE.txt` |
| uv | 0.13.6 | MIT OR Apache-2.0 parent; optional lock-generation tool, native dependencies not exhaustively inventoried; `uv-0.13.6.dist-info/licenses/LICENSE-APACHE`<br>`uv-0.13.6.dist-info/licenses/LICENSE-MIT` |
| pip | 26.2.1 | MIT parent; vendored packages include separate licenses, including certifi/MPL and packaging/Apache-BSD; `pip-26.2.1.dist-info/licenses/AUTHORS.txt`<br>`pip-26.2.1.dist-info/licenses/LICENSE.txt` |

### Locked npm development dependencies

All five package tarballs matched lockfile SHA-512 integrity. SHA-256 below is an additional artifact identifier. These are not production application bundles. Preserve their supplied notices if these packages or environments are conveyed.

| Package / exact version | License and actual notice evidence | Tarball SHA-256 |
| --- | --- | --- |
| [@axe-core/playwright 4.14.0](https://registry.npmjs.org/@axe-core/playwright/-/playwright-4.14.0.tgz) | MPL-2.0; `package/LICENSE` | `0d16690e81a9c80f653920da310010bd530b3e2bffe18d299769113848b40bdf` |
| [@playwright/test 1.64.1](https://registry.npmjs.org/@playwright/test/-/test-1.64.1.tgz) | Apache-2.0; `package/LICENSE`<br>`package/NOTICE` | `9bc8fb4bf5c8f395c1c6b6999e5480607a5aaaead17e9fe6e58181002b4086e3` |
| [axe-core 4.14.0](https://registry.npmjs.org/axe-core/-/axe-core-4.14.0.tgz) | MPL-2.0; `package/LICENSE`<br>`package/LICENSE-3RD-PARTY.txt` | `2277b0a3ef47af9b52497faa3e71598e86e0a0e5e6eb295207a5657ede4709af` |
| [playwright 1.64.1](https://registry.npmjs.org/playwright/-/playwright-1.64.1.tgz) | Apache-2.0; `package/LICENSE`<br>`package/NOTICE`<br>`package/ThirdPartyNotices.txt` | `36ba838d2d55c44fafcff89f919b5d7bc829209318076578ee2bc7cb5687fd57` |
| [playwright-core 1.64.1](https://registry.npmjs.org/playwright-core/-/playwright-core-1.64.1.tgz) | Apache-2.0; `package/LICENSE`<br>`package/NOTICE`<br>`package/ThirdPartyNotices.txt` | `3af03703c967c95037454f2283f709d53ce804a4776d4219d319f5bbcc2a0185` |

axe-core's `LICENSE-3RD-PARTY.txt` includes MIT notices for colorjs.io, core-js-pure, css-selector-parser, doT.js (and jQote2), emoji-regex, es6-iterator, es6-promise, event-emitter, is-promise, lru-queue, typedarray and weakmap-polyfill; ISC notices cover d, es5-ext, es6-symbol, es6-weak-map, ext, memoizee, next-tick, timers-ext and type. Versions for these embedded copies are not all supplied in that notice, so no version is invented.

Playwright-core also includes `lib/webp_codec.wasm` and Emscripten glue. Its `lib/webp_codec.LICENSE` supplies libwebp BSD-3, Google patent-grant and Emscripten MIT material. Exact upstream build revisions are not stated in that notice and were not established; these are test-tool bundles, not Radio Loadout's browser assets.

### npm embedded bundle notice inventory

These sidecars are present in the actual tarballs, beyond the lockfile's five nodes. Lists below reproduce package identities/version facts from each notice header; they are not additional npm resolutions. For redistribution keep the full sidecars, including nested notice blocks, rather than replacing them with this inventory. Complete bundle build provenance and browser binaries remain outside the established inventory.

**playwright: `package/lib/transform/babelBundle.js.LICENSE`**

Notice SHA-256: `2018f402988d0cff56531005b77bce7c2816a34d0c157ecb510043abd41b1ad3` (UTF-8 notice text; source tarball hash above is authoritative).

`@babel/code-frame@7.29.7`, `@babel/compat-data@7.29.7`, `@babel/core@7.29.7`, `@babel/generator@7.29.7`, `@babel/helper-annotate-as-pure@7.29.7`, `@babel/helper-compilation-targets@7.29.7`, `@babel/helper-create-class-features-plugin@7.29.7`, `@babel/helper-globals@7.29.7`, `@babel/helper-member-expression-to-functions@7.29.7`, `@babel/helper-module-imports@7.29.7`, `@babel/helper-module-transforms@7.29.7`, `@babel/helper-optimise-call-expression@7.29.7`, `@babel/helper-plugin-utils@7.29.7`, `@babel/helper-replace-supers@7.29.7`, `@babel/helper-skip-transparent-expression-wrappers@7.29.7`, `@babel/helper-string-parser@7.29.7`, `@babel/helper-validator-identifier@7.29.7`, `@babel/helper-validator-option@7.29.7`, `@babel/helpers@7.29.7`, `@babel/parser@7.29.7`, `@babel/plugin-proposal-decorators@7.29.7`, `@babel/plugin-syntax-async-generators@7.8.4`, `@babel/plugin-syntax-decorators@7.29.7`, `@babel/plugin-syntax-import-attributes@7.29.7`, `@babel/plugin-syntax-json-strings@7.8.3`, `@babel/plugin-syntax-jsx@7.29.7`, `@babel/plugin-syntax-object-rest-spread@7.8.3`, `@babel/plugin-syntax-optional-catch-binding@7.8.3`, `@babel/plugin-syntax-typescript@7.29.7`, `@babel/plugin-transform-class-properties@7.29.7`, `@babel/plugin-transform-class-static-block@7.29.7`, `@babel/plugin-transform-destructuring@7.29.7`, `@babel/plugin-transform-explicit-resource-management@7.29.7`, `@babel/plugin-transform-export-namespace-from@7.29.7`, `@babel/plugin-transform-logical-assignment-operators@7.29.7`, `@babel/plugin-transform-modules-commonjs@7.29.7`, `@babel/plugin-transform-nullish-coalescing-operator@7.29.7`, `@babel/plugin-transform-numeric-separator@7.29.7`, `@babel/plugin-transform-optional-chaining@7.29.7`, `@babel/plugin-transform-private-methods@7.29.7`, `@babel/plugin-transform-react-jsx@7.29.7`, `@babel/plugin-transform-typescript@7.29.7`, `@babel/preset-typescript@7.29.7`, `@babel/template@7.29.7`, `@babel/traverse@7.29.7`, `@babel/types@7.29.7`, `@jridgewell/gen-mapping@0.3.13`, `@jridgewell/remapping@2.3.5`, `@jridgewell/resolve-uri@3.1.2`, `@jridgewell/sourcemap-codec@1.5.5`, `@jridgewell/trace-mapping@0.3.31`, `baseline-browser-mapping@2.11.20`, `browserslist@4.28.8`, `caniuse-lite@1.0.30001810`, `convert-source-map@2.0.0`, `debug@4.4.3`, `electron-to-chromium@1.5.418`, `gensync@1.0.0-beta.2`, `has-flag@4.0.0`, `js-tokens@4.0.0`, `jsesc@3.1.0`, `json5@2.2.3`, `lru-cache@5.1.1`, `ms@2.1.3`, `node-releases@2.0.54`, `picocolors@1.1.1`, `semver@6.3.1`, `supports-color@7.2.0`, `yallist@3.1.1`.

**playwright: `package/lib/transform/esmLoader.js.LICENSE`**

Notice SHA-256: `3cec0c446526a449e4613b0defee0adb585f88f1d7fdba919421226d69be078e` (UTF-8 notice text; source tarball hash above is authoritative).

`balanced-match@4.0.4`, `brace-expansion@5.0.7`, `buffer-from@1.1.2`, `debug@4.4.3`, `has-flag@4.0.0`, `json5@2.2.3`, `mime@4.1.0`, `minimatch@10.2.5`, `ms@2.1.3`, `source-map-support@0.5.21`, `source-map@0.6.1`, `supports-color@7.2.0`.

**playwright: `package/lib/matchers/expect.js.LICENSE`**

Notice SHA-256: `78b2f60563d28cb3f9ea17e4cdc0657681e641e2f72766771d9e2da9ca94c065` (UTF-8 notice text; source tarball hash above is authoritative).

`@babel/code-frame@7.29.7`, `@babel/helper-validator-identifier@7.29.7`, `@jest/diff-sequences@30.4.0`, `@jest/expect-utils@30.4.1`, `@jest/get-type@30.1.0`, `ansi-styles@4.3.0`, `ansi-styles@5.2.0`, `chalk@4.1.2`, `ci-info@4.4.0`, `color-convert@2.0.1`, `color-name@1.1.4`, `escape-string-regexp@2.0.0`, `graceful-fs@4.2.11`, `has-flag@4.0.0`, `jest-diff@30.4.1`, `jest-matcher-utils@30.4.1`, `jest-message-util@30.4.1`, `jest-util@30.4.1`, `js-tokens@4.0.0`, `picocolors@1.1.1`, `picomatch@4.0.4`, `pretty-format@30.4.1`, `react-is@18.3.1`, `react-is@19.2.7`, `slash@3.0.0`, `stack-utils@2.0.6`, `supports-color@7.2.0`.

**playwright-core: `package/lib/serverRegistry.js.LICENSE`**

Notice SHA-256: `3098a6efcbc11752cbdf6075fa65480f5470f78c8d981fab9c0796dc9a41cefe` (UTF-8 notice text; source tarball hash above is authoritative).

`chokidar@4.0.3`, `readdirp@4.1.2`.

**playwright-core: `package/lib/utilsBundle.js.LICENSE`**

Notice SHA-256: `1362b7f413c08083af537384162ab69a323d019fe26e0a2cd78536fafd6b9cbf` (UTF-8 notice text; source tarball hash above is authoritative).

`@hono/node-server@1.19.14`, `@modelcontextprotocol/sdk@1.29.0`, `@sec-ant/readable-stream@0.4.1`, `agent-base@9.0.0`, `ajv-formats@3.0.1`, `ajv@8.20.0`, `ansi-colors@4.1.3`, `ansi-regex@5.0.1`, `balanced-match@4.0.4`, `brace-expansion@5.0.7`, `buffer-crc32@1.0.0`, `buffer-from@1.1.2`, `bundle-name@4.1.0`, `bytes@3.1.2`, `chokidar@4.0.3`, `colors@1.4.0`, `commander@15.0.0`, `content-type@1.0.5`, `cross-spawn@7.0.6`, `debug@4.4.3`, `default-browser-id@5.0.1`, `default-browser@5.5.0`, `define-lazy-prop@3.0.0`, `diff@9.0.0`, `dotenv@17.4.2`, `enquirer@2.4.1`, `eventsource-parser@3.1.0`, `eventsource@3.0.7`, `fast-deep-equal@3.1.3`, `fast-uri@3.1.7`, `get-east-asian-width@1.6.0`, `get-stream@9.0.1`, `graceful-fs@4.2.11`, `has-flag@4.0.0`, `https-proxy-agent@9.1.0`, `ini@7.0.0`, `ip-address@10.7.2`, `is-docker@3.0.0`, `is-in-ssh@1.0.0`, `is-inside-container@1.0.0`, `is-stream@4.0.1`, `is-wsl@3.1.1`, `isexe@2.0.0`, `jpeg-js@0.4.4`, `json-schema-traverse@1.0.0`, `json5@2.2.3`, `mime@4.1.0`, `minimatch@10.2.5`, `ms@2.1.3`, `open@11.0.0`, `path-key@3.1.1`, `pend@1.2.0`, `pkce-challenge@5.0.1`, `pngjs@7.0.0`, `powershell-utils@0.1.0`, `progress@2.0.3`, `proxy-agent-negotiate@1.1.0`, `proxy-from-env@2.1.0`, `readdirp@4.1.2`, `retry@0.13.1`, `run-applescript@7.1.0`, `shebang-command@2.0.0`, `shebang-regex@3.0.0`, `signal-exit@4.1.0`, `smart-buffer@4.2.0`, `socks-proxy-agent@10.1.0`, `socks@2.8.9`, `source-map-support@0.5.21`, `source-map@0.6.1`, `strip-ansi@6.0.1`, `supports-color@7.2.0`, `which@2.0.2`, `ws@8.21.0`, `wsl-utils@0.3.1`, `yaml@2.9.0`, `yauzl@3.4.0`, `yazl@3.3.1`, `zod-to-json-schema@3.25.2`, `zod@4.4.3`.

**playwright-core: `package/lib/webp_codec.LICENSE`**

Notice SHA-256: `995c7ee35aceb7666829b7a501ca89c0864e12b493c1174b155774ab1e03d831` (UTF-8 notice text; source tarball hash above is authoritative).

Native WebP/Emscripten notice; see the discussion above. No upstream component revision is inferred from its filename.

### API-doc browser artifact identifiers

Floating URL observations are point-in-time evidence. The accompanying npm archive license/NOTICE/sidecars were inspected; this is not a full browser bundle source audit. No claim is made that future visits receive these bytes.

| URL / observed version | Asset SHA-256 |
| --- | --- |
| [https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js](https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js); response version `5.34.1` | `36eeb4d5640b9c036b1d0f854499af1cceebbdb260b790a03a18be5e8488fbf5` |
| [https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css](https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css); response version `5.34.0` | `c3cfe8248c4b0b89673600fb829924eafbac6de4bc4b2b06f5f5243483074d0a` |
| [https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js](https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js); response version `2.5.4` | `dcaf76612bc4a3fbcc923a8966dee2f6146a5f32e5ce1b6f02dd60cbbf89500b` |

| Downloaded npm artifact | SHA-256 | Actual notice files inspected |
| --- | --- | --- |
| [swagger-ui-dist 5.34.1](https://registry.npmjs.org/swagger-ui-dist/-/swagger-ui-dist-5.34.1.tgz) | `8e7286de0230e431fc8a5a75490d28117af3d0c306413b6f9e17f7bb55045fb6` | `package/LICENSE`<br>`package/NOTICE`<br>`package/swagger-ui-bundle.js.LICENSE.txt`<br>`package/swagger-ui-es-bundle-core.js.LICENSE.txt`<br>`package/swagger-ui-es-bundle.js.LICENSE.txt`<br>`package/swagger-ui-standalone-preset.js.LICENSE.txt` |
| [swagger-ui-dist 5.34.0](https://registry.npmjs.org/swagger-ui-dist/-/swagger-ui-dist-5.34.0.tgz) | `15cdd55151558cf29ee70fb485332251a9911ebe27414b243ddd10fef9942394` | `package/LICENSE`<br>`package/NOTICE`<br>`package/swagger-ui-bundle.js.LICENSE.txt`<br>`package/swagger-ui-es-bundle-core.js.LICENSE.txt`<br>`package/swagger-ui-es-bundle.js.LICENSE.txt`<br>`package/swagger-ui-standalone-preset.js.LICENSE.txt` |
| [redoc 2.5.4](https://registry.npmjs.org/redoc/-/redoc-2.5.4.tgz) | `44922df4d0eb45c1b066c09ec251e6bd9bd7ded16bc69e87613337b9d911a56e` | `package/LICENSE`<br>`package/bundles/d87bcbdbea8f8f5aa26f.worker.js.LICENSE.txt`<br>`package/bundles/redoc.browser.lib.js.LICENSE.txt`<br>`package/bundles/redoc.lib.js.LICENSE.txt`<br>`package/bundles/redoc.standalone.js.LICENSE.txt` |

Swagger CSS is byte-identical across both downloaded versions despite the CDN header reporting 5.34.0 for CSS and 5.34.1 for JS. That does not pin future responses. The [Swagger UI v4.14.0 LICENSE](https://github.com/swagger-api/swagger-ui/blob/v4.14.0/LICENSE) and [NOTICE](https://github.com/swagger-api/swagger-ui/blob/v4.14.0/NOTICE) are the additional upstream evidence for FastAPI's copied OAuth redirect.

### CHIRP comparison evidence

| Immutable upstream file | SHA-256 |
| --- | --- |
| [COPYING](https://raw.githubusercontent.com/kk7ds/chirp/efbbeade947aa4b0acd2da54cb30c1f5f845c14b/COPYING) | `8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903` |
| [chirp/drivers/generic_csv.py](https://raw.githubusercontent.com/kk7ds/chirp/efbbeade947aa4b0acd2da54cb30c1f5f845c14b/chirp/drivers/generic_csv.py) | `a43a8209351897cf0321f02b18267c0e473e3e019f1d7fbb3365ee4abe23ad64` |
| [chirp/chirp_common.py](https://raw.githubusercontent.com/kk7ds/chirp/efbbeade947aa4b0acd2da54cb30c1f5f845c14b/chirp/chirp_common.py) | `8b0436f8865607e678c29a1b30f6373a066e6a2bc3c2f3ee0ae0e5a780798ea8` |

The upstream attribution and GPL terms belong to CHIRP and remain separate from the project's PolyForm license. A reference link or a functional compatibility test is not a permission grant or proof of independent authorship.
