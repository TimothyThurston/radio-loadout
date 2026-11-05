# Certifi source-access evidence review

Prepared **2026-11-05** for the Linux amd64 staging image reviewed at commit
`ec248268cf25d031b1042f7e7c42b1d2f2bdc9da`. This identifies upstream sources
available at review time. It is not a promise that a project source mirror has
been published or that all preferred-source requirements are resolved.
The shorter [recipient guide](certifi-source-access.md) provides retrieval steps.

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
wheel and source certifi files were compared byte for byte; the existing image
collector checks installed PEM/notices, not every installed Python wrapper file.

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
the bootstrap wheel identity. It does not establish all installed wrapper bytes
or reconstruct historical certificate-generation inputs.

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

Before any future redistribution, the project owner must choose a maintained
recipient-access arrangement: preserve and supply the reviewed sources alongside
the distributed release, or maintain an identified stable mirror/delivery location
and include accurate recipient instructions. Include any further preferred-form
inputs found necessary. The current upstream URLs are verified references, not
an owner-backed retention commitment. No mirror, release attachment or source
bundle has been published by this work. **Seven-day CI artifacts and this local
cache are not permanent recipient source access.** Broader reviews remain open;
this document is not legal clearance or an additional project permission.

## Checks executed — 2026-11-05

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
