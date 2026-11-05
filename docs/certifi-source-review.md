# Certifi source-access evidence review

Prepared **2026-11-05** for the Linux amd64 staging image reviewed at commit
`ec248268cf25d031b1042f7e7c42b1d2f2bdc9da`. This identifies upstream sources
available at review time. It is not a promise that a project source mirror has
been published or that all preferred-source requirements are resolved.
The shorter [recipient guide](certifi-source-access.md) provides retrieval steps.

## Delivery approach selected and Windows report recorded — 2026-11-05

The owner selected [release-attached source bundles and the maintenance
workflow](source-bundles.md#selected-delivery-and-maintenance-policy--2026-11-05).
The policy retains per-release sources/checksums and calls for verified recipient
access before distribution. It is a selected plan, not a published/operating
source-access arrangement; activation and the remaining release-specific reviews
are still pending. No arbitrary legal retention duration or clearance is claimed.

The owner's [Windows verification report](source-bundles.md#reported-windows-verification--2026-11-05)
records two real five-archive builds on Windows 11 / Python 3.13.15 at commit
`ef0d94d34df51a2a84927a09c0c6732282d853e4`. Each reported ZIP is 2,409,640 bytes,
SHA-256 `f6c7eaffaddaebb79fd3ee7fbe22471d49aacab84409207d5442e27f6d75accd`,
matching the independently built Linux / Python 3.12 reference. Both checksum
files and independent verification checks passed; original archives and clean
Git state were reported unchanged. This is attributed user-reported evidence;
the local JSON report/ZIPs were not independently inspected in this follow-up.
Historical Mozilla inputs, full native/OS coverage, CHIRP provenance and the
operational recipient-access finding remain open. No code or bundled notice
bytes were changed, no release created, and no sources published here.

## Local release-source bundle preparation — 2026-11-05

The [source-bundle tooling](source-bundles.md) prepares an offline, independently
checkable ZIP of the same five pinned original archives. It preserves original
archive/notices bytes and includes a qualified README, canonical manifest and
hash index; a separate SHA256SUMS identifies the entire ZIP. It neither selects
new sources nor changes dependencies, wrapper verification or license terms.
The bundle is deliberately named source **evidence**, not complete preferred
source or completed legal clearance. At preparation time, owner selection of
maintained delivery was pending; the subsequent choice is recorded above.
Historical Mozilla inputs and wider reviews remain unresolved. No release or
source mirror was published; this does not close operational recipient access.

## CI #13 installed-wrapper gate verified — 2026-11-05

Verified [CI run #13](https://github.com/TimothyThurston/radio-loadout/actions/runs/42112616503)
at exact commit `0b5261390accc2f6efd5d316f2b3b2e605aa051a`.
All seven jobs succeeded. The
[Linux-amd64 staging job](https://github.com/TimothyThurston/radio-loadout/actions/runs/42112616503/job/127543815295)
passed smoke, actual-image collection, supplemental-notice verification and
**Verify installed certifi wrapper source hashes** before diagnostics upload
and cleanup. The checkout for this documentation follow-up was initially clean
at that exact commit; no application, collector or verifier code changed here.

Downloaded artifact **13453982693**, `staging-container-diagnostics`. Its ZIP
SHA-256 matches GitHub's reported digest. ZIP paths, duplicate entries and CRCs
were checked; all 369 notice-origin hash/size records (167 distinct stored notice
hashes) passed. Evidence identifiers:

| Evidence | Identifier/result |
| --- | --- |
| Diagnostics ZIP SHA-256 | `f9c9cb03a025971f684cb867a70eca4b7a7a2ada26e2d6f99ab13c818df6f5b6` |
| Actual image ID | `sha256:48877ffaa3cab97ebb3ef0f7ec93a2380962100387e7c8c29c2fc4058bc7006f` |
| `licenses/inventory.json` SHA-256 | `26263f27d0950325ce765f9eeb0368ef628ec6504ac979f3c6869e3ea84276a2` |
| `licenses/notices-index.json` SHA-256 | `f128e2f05d9152b875ab5a82131d169058798d15fc247a1132537417ca43d1f8` |
| `certifi-wrappers-check.json` SHA-256 | `893d023e979aac5224fd056b267daaa1db1266832cb80151179194ef18e0cf69` |
| Source manifest SHA-256 | `d6a4550a3bb7c7ffdcf4e6c740c7777bb16d4fa42725361255b43cb8186cb4e0` |
| `supplemental-notices-check.json` SHA-256 | `6279ac8625fe0afe22c14684e7728ed4e980be67004da4f6b9cf0644bea5cb82` |
| Collection | Complete, no top-level/probe errors; clean checkout; collected `2026-11-05T21:26:37.278453+00:00` |
| Image binding / runtime | Build IID and staging-container image ID agree; Linux amd64; user `10001:10001`; both probes CPython 3.13.15 / UID 10001 |
| Wrapper gate | **Passed**, 16 unique files at four locations, 20 observations |
| Supplemental gate | **Passed**, all 15 bundle files and the reviewed native identities |

Replayed both verifiers using the exact commit's files, and compared the replayed
JSON results with the collected CI results: identical. The wrapper result maps
each installed path, size and SHA-256 to its pinned source archive/member.
The base probe contributes eight observations; the venv probe contributes twelve.
Their shared four ensurepip members are one archive location, not another copy.
Pip's modified `core.py` and `__main__.py` match the pip source, rather than being
substituted with the original certifi namespace. Existing certificate, notice,
version and bootstrap-wheel checks also passed.

**Installed certifi wrapper correspondence is verified for this commit/image.**
This closes the previously pending actual-image wrapper checkpoint, not the
historical Mozilla input, maintained recipient-access, native/OS or CHIRP
provenance findings. No entire-application equivalence or legal clearance is
claimed. The artifact expires on 2026-11-12 and is temporary diagnostic evidence,
not permanent recipient source access. No local Docker build or new remote CI
execution was performed for this evidence review. Recheck future images when
the sources, dependencies, wrappers or collection code change.

## Installed-wrapper collection and gate — 2026-11-05

Follow-up prepared from `47464a9d120311fe89d6100aa72063a6279d83af`.
[CI #12](https://github.com/TimothyThurston/radio-loadout/actions/runs/42109371643)
passed at that commit. Its diagnostics ZIP SHA-256 is
`3c39bb35f39782221f88321966427cdca62f946a9d6cc3226a6decd37b9e0f9e`.
That inventory predates wrapper collection; the new gate correctly rejects it
with an explicit recollection requirement. No wrapper hashes were inferred from
the earlier certificate or whole-wheel hashes.

The probe now records only paths, sizes and SHA-256 for `__init__.py`,
`__main__.py`, `core.py` and `py.typed` in the application, base pip, venv pip
and ensurepip archive locations below. It never imports or executes these files
or uploads their contents. Reads are limited to 64 KiB per wrapper. Links,
oversized reads, duplicate archive wrappers and unexpected direct package files
produce collection errors; missing files fail the subsequent comparison.

`scripts/verify_certifi_wrappers.py` derives expected hashes/sizes directly from
the existing source manifest's selected members. Application expectations use
the certifi 2026.10.23 source; all pip expectations use pip 26.2.1's modified
source, not the original upstream namespace. No dependency or manifest hash is
silently refreshed to make a changed installation pass.

The offline gate requires complete, bound Linux-amd64/non-root image evidence
from both interpreters and retains the existing certificate, notice, version-pin
and bootstrap-wheel checks. It requires 16 unique files at four locations;
20 observations include the same four ensurepip members seen by both probes.
Duplicates within a probe, missing/extra paths, incorrect probe ownership,
source/hash/size drift and conflicting nested bootstrap evidence fail visibly.
An `always()` CI step writes `certifi-wrappers-check.json` before diagnostics
upload and cleanup, including a failure receipt when checks cannot complete.

Local validation for this follow-up used Linux / Python 3.12: Ruff passed,
**728 Python tests passed** (40 new wrapper cases), **53 JavaScript tests** and
**15 JavaScript syntax checks** passed. Pinned source downloads and offline
archive/member checks passed, as did the earlier PEM/notice correspondence check
against the checksum-verified CI #12 artifact. Wheel/source packaging and the
isolated installed-wheel HTTP smoke passed. Docker is unavailable in this
environment; no new image, browser run or remote CI run was executed here.

At preparation time, actual-image verification of these newly collected wrapper
hashes awaited a fresh CI execution. **CI #13 subsequently passed that check**;
the exact run/image, artifact checksums and replay results are recorded above.
Local synthetic tests and rejection of CI #12's older evidence were not used as
substitutes for the actual-image result.
Historical Mozilla inputs, maintained recipient access, native/OS reviews and
CHIRP provenance remain unchanged and unresolved. This is source correspondence
tooling, not a new legal conclusion. The original dated findings below describe
the earlier, narrower inventory.

Certifi's included notice identifies Mozilla-derived certificate material under
[MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/). Those third-party rights remain
separate from Radio Loadout's PolyForm Strict license. Keep the included notices;
the project's terms do not restrict recipients' MPL rights in covered source.

## Versions and installed locations

The actual CI #11 inventory contains **two versions at four distinct locations**:

| Version | Location of `cacert.pem` | Version evidence / matching source |
| --- | --- | --- |
| 2026.10.23 | `/opt/venv/lib/python3.13/site-packages/certifi/cacert.pem` | Application distribution metadata; matching certifi source archive below |
| 2026.6.17 | `/usr/local/lib/python3.13/site-packages/pip/_vendor/certifi/cacert.pem` | Base pip 26.2.1 vendor manifest; certifi source plus pip's modified wrapper source |
| 2026.6.17 | `/opt/venv/lib/python3.13/site-packages/pip/_vendor/certifi/cacert.pem` | Venv pip 26.2.1 vendor manifest; same source references |
| 2026.6.17 | `/usr/local/lib/python3.13/ensurepip/_bundled/pip-26.2.1-py3-none-any.whl!/pip/_vendor/certifi/cacert.pem` | Bootstrap wheel/vendor manifest; `!/` denotes an archive member, not another installed directory |

The two interpreter probes see the **same** ensurepip wheel; those repeated
records are not additional copies. The bootstrap wheel SHA-256 is
`71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e`.
This catalog concerns the reviewed runtime image, not older Windows development
observations or a promise about future dependency resolutions.

Direct certifi's notice is under
`certifi-2026.10.23.dist-info/licenses/LICENSE`. Each pip copy includes
`pip/_vendor/certifi/LICENSE` and its dist-info duplicate under
`pip-26.2.1.dist-info/licenses/src/pip/_vendor/certifi/LICENSE`; the bootstrap
wheel contains both too. All have unchanged SHA-256
`e93716da6b9c0d5a4a1df60fe695b370f0695603d21f6f83f053e42cfc10caf7`.
The full origins and per-file checksums are in the
[source manifest](../scripts/certifi-source-manifest.json).

## Exact source downloads

These are upstream archives, not project-hosted mirrors:

| Source | SHA-256 |
| --- | --- |
| [certifi-2026.10.23.tar.gz](https://files.pythonhosted.org/packages/fd/11/b524cbd9bbdaca58608e4cf4053fd463417549e1959fa8d3aa18319f9555/certifi-2026.10.23.tar.gz) | `a9895e6e2758b371e0545e321a3a8fd1fcfd9829ada8824a936dfb16aaaf36cd` |
| [certifi-2026.6.17.tar.gz](https://files.pythonhosted.org/packages/c9/c7/424b75da314c1045981bd9777432fad05a9e0c69daa4ed7e308bbaffe405/certifi-2026.6.17.tar.gz) | `024c88eeec92ca068db80f02b8b07c9cef7b9fe261d1d535abfd5abd6f6af432` |
| [pip-26.2.1.tar.gz](https://files.pythonhosted.org/packages/ae/15/4500e320e6b101ec3b719ae85b697d9940b6cda672bc555bd6016fc60c6f/pip-26.2.1.tar.gz) — contains namespace-modified certifi Python files | `f6ad667e89a1fe78046c8f13232b247200f5258d7828f3f7883d660878e0813f` |

The pip source is relevant: its `core.py` changes resource references from
`certifi` to `pip._vendor.certifi`, and `__main__.py` changes that import. Supplying
only the original certifi archive would omit those pip modifications. Pip's
wheel and source certifi files were compared byte for byte. The original image
collector checked only installed PEM/notices; the later CI #13 wrapper gate
extends installed correspondence to the four specified source/typing files at
each of the four locations, as recorded above.

The retrieval tool also preserves full upstream certifi release-commit snapshots,
including `Makefile` and `strip-non-ascii`, which the PyPI source archives omit:

| Release commit snapshot | Archive SHA-256 |
| --- | --- |
| [d0ac52f3d93a514224197c7efb66c41b1beae5d1](https://github.com/certifi/python-certifi/tree/d0ac52f3d93a514224197c7efb66c41b1beae5d1), tag `2026.06.17` | `3b193ab1518f5b406371747e5585993ffb24b88de6e37994c927bb29f101b4d4` |
| [b60466c9f2882d9cf088943c650b0faac06c080c](https://github.com/certifi/python-certifi/tree/b60466c9f2882d9cf088943c650b0faac06c080c), tag `2026.10.23` | `c53452dfac043982f6931db924de8d68d17356a5b218a88bd448e3dbaa234420` |

Commit archive URLs and required member hashes are pinned in the manifest. If an
upstream server changes archive bytes, the check fails rather than silently
selecting a different revision. Tag objects were dereferenced through the
upstream GitHub API; their signatures were not independently authenticated.

## Retrieve and check without installing anything

From the checkout or an unpacked project source archive, using Python 3.11+:

```sh
python scripts/retrieve_certifi_sources.py --download-dir generated/certifi-sources
python scripts/retrieve_certifi_sources.py --download-dir generated/certifi-sources --offline
```

The first command retrieves five original source archives over verified HTTPS.
Both commands verify archive SHA-256/size and selected source/notice member hashes
without extraction, installation, execution or trust-store updates. They write
a bounded `receipt.json`. Existing corrupt archives fail without being replaced.
No latest-release fallback is used. Downloads stay local and are not published.
The script and manifest are included in the project's source archive; no new
runtime payload or container dependency is added.

To check an independently retained inventory from this image as well:

```sh
python scripts/retrieve_certifi_sources.py --download-dir generated/certifi-sources \
  --offline --inventory-dir PATH/TO/EXTRACTED/DIAGNOSTICS/licenses
```

This checks all four recorded PEM hashes, version evidence, license bytes and
the bootstrap wheel identity. That retrieval command does not itself check the
wrapper records. For wrapper correspondence, run `scripts/verify_certifi_wrappers.py`
as described in the recipient guide; CI #13's actual-image replay passed.
Neither command reconstructs historical certificate-generation inputs.

## What remains unresolved before redistribution

The PEM source hashes match the actual image: `2026.10.23` uses
`2ef52ad56b4803e264045c915e55c236cbfa045b84b81efefc218a19eb44bd2b`;
`2026.6.17` uses
`bbc7e9c01d7551bb8a159b5dedd989b8ee3ce105aff522b68eb1b01bf854cab0`.
Both upstream release snapshots contain the same PEM/Python/notice bytes as their
sdists. These facts establish identified source correspondence, not that a wheel
is automatically source-less or that generated PEM is necessarily the complete
preferred form for modification.

At both exact upstream commits, `Makefile` obtains `https://mkcert.org/generate/`
and pipes it through `strip-non-ascii`. The LICENSE points to Mozilla's moving
`certdata.txt` `tip` URL. [mkcert.org](https://mkcert.org/) describes daily updates
from Mozilla. Neither source snapshot establishes the actual historical Mozilla
revision, service deployment, trust-selection inputs or response used for these
two releases. The notice's old RCS revision is not a pin for 2026 certificate
inputs. Those facts and whether additional inputs constitute preferred source
remain open; rerunning today's moving endpoint would not prove historical output.

MPL defines source by the preferred modification form (§1.13), requires MPL terms
and license access for covered source (§3.1), source availability/information when
executable forms are conveyed (§3.2), and notice preservation (§3.4). This does not
require disclosure of the entire separate application. See the
[license](https://www.mozilla.org/en-US/MPL/2.0/) and
[Mozilla FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

The project owner has selected release-attached source delivery, as recorded
above. Before future redistribution, implement and maintain that selected
arrangement with accurate recipient instructions and verified access; no public
release/source attachment has been activated by this documentation. Include any
further preferred-form
inputs found necessary. The current upstream URLs are verified references, not
an owner-backed retention commitment. No mirror, release attachment or source
bundle has been published by this work. **Seven-day CI artifacts and this local
cache are not permanent recipient source access.** Broader reviews remain open;
this document is not legal clearance or an additional project permission.

## Original source-retrieval checks executed — 2026-11-05

- Verified the GitHub run, exact commit, staging step conclusions and artifact
  digest; replayed all 15 supplemental-file/native-identity checks using exact
  Git object bytes. All 369 collected notice-origin hashes/sizes passed.
- Retrieved five source archives from official PyPI/GitHub sources using the new
  tool; their archive/member hashes passed. Its offline recheck and optional
  actual-image check passed for all four certifi locations. Sources and receipts
  remain local under ignored `generated/certifi-sources/`.
- Compared both certifi reference wheels' PEM/Python/notice bytes with their
  sdists and exact upstream commits. Compared all pip wheel certifi members with
  the matching pip source, including the two namespace changes. This does not
  extend installed-image evidence to uncollected wrapper-file hashes.
- Ruff passed; **23 focused tests passed**; full Python suite **687 passed,
  1 skipped** (existing Windows unprivileged symlink limitation), with two
  existing dependency deprecation warnings. Tests cover offline/no fallback,
  corrupt sources, unsafe/duplicate/missing members, changed version/PEM/license/
  bootstrap evidence and failure receipts.
- Full packaging smoke passed: exact wheel/source archive audits, manifest/tool/
  guide inclusion in the source archive, isolated installed-wheel payload/import
  checks, pip check and existing production HTTP documentation/workflow/limit
  probes. The final documentation source archive is refreshed/audited afterward.

No new local Docker build, browser/JavaScript run or remote CI execution was
performed for this follow-up. CI #11 is prior evidence for the unchanged runtime
bundle, not a claim that this new retrieval tool already ran in CI. The runtime
package data, dependencies, Docker restrictions, CI configuration, project
license and approved authorship statement were preserved. No publication or
permanent hosting was performed.
