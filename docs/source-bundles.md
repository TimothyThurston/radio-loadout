# Local certifi source-evidence bundles

Prepared 2026-11-05 from checkout
`a65c3fc9abada92ca69a6079058a9dd74dbdbc85`.

The proposed delivery approach is to keep reviewed third-party sources beside
each future distributed release, rather than require a separate source-hosting
service. **This follow-up prepares local tooling only.** It does not publish a
release, establish an owner-backed retention commitment, settle historical
Mozilla inputs or authorize container redistribution. The certifi bundle is a
first scoped component, not a complete all-dependency source bundle.

## Prepare locally

Use Python 3.11+ from a checkout or unpacked Radio Loadout source distribution.
Obtain the exact pinned source archives using the existing retrieval tool:

```sh
python scripts/retrieve_certifi_sources.py --download-dir generated/certifi-sources
```

Then build **offline**, choosing a new output directory:

```sh
python scripts/bundle_certifi_sources.py --source-dir generated/certifi-sources --output-dir generated/source-bundles/certifi-preflight-v1
```

The builder refuses existing output directories, corrupt/missing source archives,
links, unsafe archive selections and source/member checksum changes. It never
fetches a missing file or falls back to a different release. Source retrieval is
an explicit separate step. No archives are installed, their code is not executed,
and no trust store is changed. Only the selected files are included; unrelated
cache files, environment variables and user configurations are not collected.

The new directory contains:

| File | Contents |
| --- | --- |
| `certifi-source-evidence-v1.zip` | Five unchanged original archives; a qualified README; canonical source manifest; archive path/size/SHA-256 index |
| `SHA256SUMS` | SHA-256 of the entire ZIP, using a stable filename |

The five archives are certifi 2026.6.17 and 2026.10.23 sdists, their two exact
upstream commit snapshots (including update helpers), and pip 26.2.1's sdist
(including namespace-modified wrappers). Their exact source/notices remain in
the original archives. This does not relicense third-party material under
PolyForm Strict, alter project licensing or supply missing source inputs.

## Independently check a retained bundle

From a separately trusted checkout/source distribution:

```sh
python scripts/bundle_certifi_sources.py --verify-bundle generated/source-bundles/certifi-preflight-v1/certifi-source-evidence-v1.zip
```

Verification does not trust a substituted manifest inside the ZIP. It derives
the expected files and checksums from that checkout's pinned manifest, requires
the exact expected metadata and original archive bytes, and rejects missing,
extra, duplicate, linked, encrypted or unexpectedly compressed entries. There is
no filesystem extraction or network access. A failure exits nonzero with a
bounded diagnostic, not a success receipt. SHA-256 identifies bytes; it is not
authentication of an unknown publisher or a legal determination.

Bundle input/output reads are bounded (64 MiB for the ZIP; 32 MiB total selected
source bytes). The earlier retrieval checker also verifies selected tar members
with its existing archive limits. ZIP timestamps, file order and permissions
are fixed; JSON metadata is canonicalized to sorted-key UTF-8/LF. Repeated local
builds produced identical bytes, including a test that changes only manifest
key order/line endings. Actual Windows and cross-Python-version execution still
need verification; this is not an assertion of universal build reproducibility.
The pinned original archives are not rewritten.
The canonical manifest hash in the bundle index is distinct from the raw
working-tree manifest hash recorded by earlier image evidence.

## Before future release delivery

This preparation does **not** close the maintained-recipient-access finding.
Before attaching anything to a public release, the owner still needs to approve
the delivery/retention arrangement and address the remaining scoped reviews.
Record the exact application revision, distributed image/artifact identifiers,
bundle ZIP checksum and source selections for each applicable release. Retain
the selected source archives; do not rebuild an older release's source package
using newer dependency pins or silently replace existing bundle bytes.

Check that eventual recipients can actually retrieve the retained sources using
the supplied instructions. An expiring seven-day CI artifact or a developer's
temporary cache is not that delivery arrangement. No release-upload workflow,
hosting account, source mirror, retention policy or automatic publication is
created by this tool. Full native/OS/Python coverage, historical Mozilla inputs,
CHIRP provenance and other findings remain as recorded in the
[dependency review](dependency-license-review.md).

For the actual-image wrapper correspondence already verified at CI #13, see the
[certifi evidence record](certifi-source-review.md#ci-13-installed-wrapper-gate-verified--2026-11-05).
For the source selection and unresolved preferred-form details, see the
[recipient guide](certifi-source-access.md).

## Local verification — 2026-11-05

On Linux / Python 3.12, built the five retained source archives twice into
separate new directories and verified each ZIP against the trusted checkout
manifest. Both ZIPs were byte-identical: **2,409,640 bytes**, SHA-256
`f6c7eaffaddaebb79fd3ee7fbe22471d49aacab84409207d5442e27f6d75accd`.
The canonical embedded manifest SHA-256 is
`f52b15532ee9ba84734acff3215aeccd6927a766e5d55709b0da2a17f374d5a0`.

Ruff passed; **756 Python tests passed**, including 28 new bundle cases.
The complete wheel/source packaging and isolated installed-app HTTP smoke passed;
final archives are refreshed/audited after documentation updates. No downloaded
archive or generated ZIP is included in the application distributions. New tests
cover offline-only operation, original archive/notice preservation, deterministic
local output/canonicalization, corrupt/missing inputs, external-manifest trust,
unsafe/changed ZIP entries, no overwrite and nonzero CLI failures.

No Windows, Python 3.11/3.13, browser or new Docker execution was performed for
this follow-up. No CI run, commit, push, release upload or publication was made.
Dependencies, container restrictions, license and approved authorship wording
are unchanged. The bundle remains local preparation, not an activated recipient
source-access arrangement.
