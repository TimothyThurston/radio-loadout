# Local certifi source-evidence bundles

Prepared 2026-11-05 from checkout
`a65c3fc9abada92ca69a6079058a9dd74dbdbc85`.

The owner selected **release-attached source bundles** on 2026-11-05: keep
reviewed third-party sources beside each applicable future distributed release,
rather than require a separate source-hosting service. This is the chosen
delivery approach, not an already operating recipient-access service. No release
or assets have been published, recipient retrieval has not been tested, and the
remaining source/notice reviews are not closed. The certifi bundle is the first
scoped component, not a complete all-dependency source bundle.

## Selected delivery and maintenance policy — 2026-11-05

For a future release that the owner separately approves for distribution:

1. Associate the reviewed source bundles and checksum files with that exact
   versioned release, and provide the recipient guide/link alongside the
   distributed artifacts. Record the application revision, image/artifact
   identifiers, bundle checksums and source selections. Do not rely on a moving
   latest-source link for older binaries.
2. Retain the original selected archives, notices, manifests and verified bundle
   bytes. Keep the corresponding source assets available with releases that
   remain available; do not silently replace old sources with newer pins or
   remove a source asset while its associated artifact remains distributed.
   Review any withdrawal, migration or replacement before making it.
3. The project maintainer owns the maintenance/retrieval check. Before public
   distribution, verify access from the intended recipient's perspective, not
   only from a signed-in maintainer session. Preserve a recoverable retained
   copy; an expiring CI artifact or temporary local cache is not the source of
   record for release delivery.
4. Release approval must still establish source completeness and any further
   component-specific notice, retention or access requirements. This policy
   deliberately does not invent a universal retention duration, make a legal
   clearance claim, or treat an unavailable historical input as supplied.

**Selected:** the release-attached approach and maintenance workflow.
**Not activated:** a published release/source attachment, public recipient access,
automated uploads, or a new hosting account. Historical Mozilla inputs, full
native/OS/Python coverage and other review findings remain open. No release or
source-access obligation is marked fulfilled solely because this policy was
selected. Activation remains a separate owner-approved release action.

The existing version-1 bundle README remains byte-for-byte unchanged, including
its preparation/approval caveats. Those original bundles are not silently
rewritten to record this later policy choice. Their public release activation
and the remaining source reviews still require separate approval and evidence.

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
key order/line endings. A subsequent user-reported Windows / Python 3.13 run
matched the Linux / Python 3.12 ZIP bytes, as recorded below. This verifies only
the reported runtime pair and selected inputs, not universal reproducibility.
The pinned original archives are not rewritten.
The canonical manifest hash in the bundle index is distinct from the raw
working-tree manifest hash recorded by earlier image evidence.

## Before future release delivery

The selected policy does **not** close the operational recipient-access finding.
Before attaching anything to a public release, the owner still needs to approve
that release and address the remaining scoped reviews and access/retention details.
Record the exact application revision, distributed image/artifact identifiers,
bundle ZIP checksum and source selections for each applicable release. Retain
the selected source archives; do not rebuild an older release's source package
using newer dependency pins or silently replace existing bundle bytes.

Check that eventual recipients can actually retrieve the retained sources using
the supplied instructions. An expiring seven-day CI artifact or a developer's
temporary cache is not that delivery arrangement. The tool creates no
release-upload workflow, hosting account, source mirror or automatic publication.
The maintenance policy above was selected separately; the tool does not activate
it. Full native/OS/Python coverage, historical Mozilla inputs,
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
that original Linux follow-up. The subsequent Windows report below is separate.
No CI run, commit, push, release upload or publication was made by that session.
Dependencies, container restrictions, license and approved authorship wording
are unchanged. The bundle remains local preparation, not an activated recipient
source-access arrangement.

## Reported Windows verification — 2026-11-05

The owner supplied the following Windows Codex verification report. This is
**user-reported evidence**, not an independently executed Windows run or an
inspection of the local JSON report. Its reported ZIP hash/size exactly match
the independently built Linux reference above.

| Evidence | Reported result |
| --- | --- |
| Checkout | `ef0d94d34df51a2a84927a09c0c6732282d853e4` |
| Host | Windows 11, build `10.0.26300` |
| Python | `.venv\Scripts\python.exe`, 3.13.15, 64-bit |
| Initial / final Git status | Clean / clean |
| ZIP A / B size | 2,409,640 bytes each |
| ZIP A / B SHA-256 | `f6c7eaffaddaebb79fd3ee7fbe22471d49aacab84409207d5442e27f6d75accd` |
| Build / independent verification | Two fresh builds, both verified; ZIPs byte-identical; both SHA256SUMS match |
| Source preservation / scope | Five original archives unchanged; embedded archives match retained originals; exactly five archives plus three metadata files; no unrelated/user files |
| Network / project changes | No downloads needed; project files/expected hashes unchanged; no commit, push or publication |

The report records successful `-B` invocations of the existing source retrieval
tool, two offline bundle builds and both `--verify-bundle` checks. Outputs remain
under ignored local directories:

- `generated/source-bundles/windows-2026-11-05-48222499-a/`
- `generated/source-bundles/windows-2026-11-05-48222499-b/`
- `generated/source-bundles/windows-2026-11-05-48222499-record/verification-report.json`

No generated ZIP, individual archive, local JSON report or personal path is
added to Git by this record. The bundles remain local evidence; neither the
Windows report nor Linux reference establishes public access, historical Mozilla
inputs or broader legal clearance.
