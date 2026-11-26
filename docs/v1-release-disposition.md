# Hosted analog V1 release disposition

Prepared **2026-11-12 (America/Chicago)** at commit
`189b92eb63def4b4c1d205507e4ee15a71d51d8f` (`Add reviewed receive-only satellite
presets`). This is a documentation-only synthesis of the existing evidence,
not a new component audit, deployment approval or legal clearance. No finding is
closed by this document.

The starting working tree had four unstaged changes: README.md, deletion of the
two stray Git-output files, and the new [Windows CHIRP verification
record](chirp-verification.md). Those changes are preserved, including their
owner-reported evidence and pending case matrix. This disposition is the only
additional file created for this task; nothing is staged.

The [2026-11-26 component review](#chirp-component-decisions--2026-11-26) below
adds implementation/history checks and specific recommendations for H1–H3. It
preserves the original dated evidence, author statement and other open findings;
it does not record an owner approval or a completed provenance determination.

## Proposed release boundary and decision

The proposed hosted analog V1 is the browser channel builder, analog Generic
CHIRP CSV import/review/export, local JSON backup/full-loadout workflows and the
existing explicitly qualified profile/settings and receive-only preset guidance.
It does not establish device programming, firmware detection, live satellite
activity, reception, DMR export or hardware compatibility. CSV/JSON downloads are
user configurations, not distribution of the server's dependency environment.

**Public launch remains on hold for a recorded owner disposition of CHIRP
provenance, actual candidate/deployment verification, and the supported CHIRP
workflow claim.** These are review gates, not a finding that a particular copied
fragment or infringement has been established. The smallest actions are listed
below; reconstructing unavailable chats is not imposed as an impossible gate.

**Hosted staging is conditional, not approved here.** Local/CI synthetic tests
can continue without publishing artifacts. Before exposing a hosted staging
instance, record its operator, audience and image handoff, apply and verify the
existing access/ingress/privacy requirements, and explicitly disposition the
browser-delivered provenance uncertainty for that audience. Host validation alone
does not make a staging site private. The incomplete CHIRP matrix can be worked
through on restricted staging using synthetic files; it must remain labelled
pending. A public URL called “staging” still delivers browser code to visitors.

Server-only native/certifi/OS redistribution gaps are **not automatically hosted
launch blockers**. If deployment conveys an image or environment to a separate
provider/operator, assess that specific transfer before treating it as solely
internal operation. No provider or transfer arrangement was established here.

## Evidence used and limits

The primary records are [CHIRP provenance](chirp-provenance.md), the
[dependency review](dependency-license-review.md), [native notices](native-component-notices.md),
[source bundles](source-bundles.md), and the current [Dockerfile](../Dockerfile).
Supporting records are [staging requirements](staging.md),
[certifi sources](certifi-source-review.md), the [recipient guide](certifi-source-access.md),
and the pending [Windows matrix](chirp-verification.md). Later dated follow-ups
take precedence over earlier “pending image” or “no method selected” paragraphs;
historical evidence identifiers are not reassigned to this checkout.

| Checkpoint | What the existing record establishes | Limit for this disposition |
| --- | --- | --- |
| Actual-image inventory, 2026-11-04 | The supplied checksum-verified ZIP records Linux amd64 image `sha256:bdb65d39b44c3e8843f29ce31e74e7b2eaf812c83b532e2f613c6b4b80bf24bf`, checkout `7cc898267d5874724eeb5d4d251d92b4c694533b`, CPython 3.13.15, 61 venv distributions, base/ensurepip contents and 97 Debian package/source records. | Successful collection is not complete notice/source review or an inventory of every future image. |
| CI #11 supplemental notice gate | At `ec248268cf25d031b1042f7e7c42b1d2f2bdc9da`, image `sha256:9d6dff64087d059146f63083c91fdb596f0432c2b5b914eaccebc44713e79aae`, all 15 supplemental bundle files passed the actual-image byte check. | This gate is already addressed for that image; it does not cover every native dependency. |
| CI #13 certifi wrapper gate | At `0b5261390accc2f6efd5d316f2b3b2e605aa051a`, image `sha256:48877ffaa3cab97ebb3ef0f7ec93a2380962100387e7c8c29c2fc4058bc7006f`, 16 distinct certifi wrapper/typing files at four locations matched pinned sources; the supplement gate also passed. | Correspondence is established for that image, not historical Mozilla inputs or enduring recipient access. |
| Current application checks | The preceding local patch verification at this HEAD reported Ruff pass, 927 pytest passes/3 skips, 137 JavaScript passes and `git diff --check` pass. The pending Windows document records CI #20 success at this HEAD. | Those are prior results, not tests or remote CI revalidated by this docs-only task. CI success is not a field-level CHIRP run, target-host verification or legal conclusion. |
| Windows CHIRP | The pending document records an owner-reported November 6 Windows round trip with CHIRP-next `20251205`. | Exact original inputs/outputs, project revision, Windows build and checked fields were not recorded. Every case/direction in the new matrix remains pending until observed. |

The current Dockerfile pins
`python:3.13.15-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26`.
The builder installs hashed build/runtime locks, builds a wheel, and installs it
without dependencies into `/opt/venv` after the locked runtime install. The final
stage copies that venv into a fresh base and runs the production entry point as
UID/GID `10001:10001`. It does not copy the builder's global build tools or npm
test environment. Base pip/ensurepip and venv pip still exist. The historical
BuildKit material identifies the multi-platform base digest; a distinct resolved
Linux child digest was not established in that evidence. Neither the Dockerfile
nor a green health check alone establishes actual contents or deployment safety.

## Open findings affecting hosted staging or public launch

“Browser” includes scripts, rendered configuration/tables and data actually sent
to visitors. “Server” means installed or executed on the host without those
dependency bytes being sent in ordinary page/CSV/JSON responses. Each row states
which boundary the uncertainty affects rather than treating the whole repository
as one downloadable program.

| ID / affected material and delivery | Existing evidence | Unknown or remaining gate | Smallest action / owner |
| --- | --- | --- | --- |
| H1 — CHIRP-related browser tables/behavior: `web/static/builder.js`, `backup-format.js`, `web/templates/builder.html` under `src/radio_loadout/`. **Browser delivery**, also in project archives. | The provenance record identifies the same ordered 50 CTCSS and 104 DCS values, the same 15-step set with a different order, and interface/functional similarities. Conventional values and CSV names alone are not proof of expressive copying. No particular copied expressive implementation or prose fragment was identified. | Component-specific source selection, assistant inputs and any applicable permissions remain unestablished. This is the part of CHIRP provenance that cannot be deferred merely by keeping Python on the server. | Timothy Thurston: record any further bounded recollection against the ledger and explicitly leave unrecoverable facts unknown; obtain an appropriate assessment/disposition of delivered material before public launch. If an actual expressive adaptation is identified, assess that fragment and permissions. Neither blanket attribution nor speculative rewriting is justified by table equality alone. |
| H2 — CHIRP importer/exporter, tone/model validation and compatibility reports: `importers/chirp_csv.py`, `exporters/chirp_csv.py`, `chirp_csv_validation.py`, `dcs.py`, `models.py`, `compatibility.py` and web conversion code. **Server code**; results go to browser; source is included if archives/images are conveyed. | Historical comparison found CHIRP-specific defaults and a common tone-case order, with different models/helpers/control flow; later matched-tone fixes and upstream references establish intentional semantic alignment. No particular copied expressive fragment was identified. | Exact creation sources and AI contributions are incomplete; the strongest structural candidate is not an identified copied block. Server-only operation changes the distribution boundary, but does not prove ownership or permission for copying. | Owner: disposition together with H1, preserving existing technical observations. Review any subsequently identified fragment specifically; a credit does not by itself resolve covered GPL adaptation under Strict. Do not relabel the entire application GPL or infer independence from absent imports. |
| H3 — CHIRP fixtures/tests: `tests/fixtures/chirp/`, compatibility, tone-boundary and DCS tests. **Development/source archive**, not normal browser assets or final runtime test files. | Fixtures first appear together at `b5c4180`; a bounded upstream comparison found no whole project data-record match. “Synthetic”/“independent” are repository descriptions, with independence relative to the project exporter. The owner reports no external sample files were brought into development/testing. | Each row's generation process, expected-model origin and assistant inputs remain incompletely reconstructed; row mismatch is not independent-authorship proof. | Owner: preserve any available component-specific account; do not request unavailable original chats or invent generators. Primarily an archive/provenance issue, linked to H1/H2's overall source assessment, not evidence that fixtures are sent to visitors. |
| H4 — Supported Windows Generic CSV workflow: importer/exporter, `docs/chirp-verification.md`, README claims. **Hosted functionality and recipient configuration files**; no radio connection. | Owner-reported round trip and extensive automated semantic/round-trip tests support a workflow at their stated scope. They do not test a particular CHIRP application's complete save/reopen behavior. | A1–A3, T1–T3, O1–O2 and R1 matrix results/directions are not recorded as complete. Effective TX, RX-only, active tones/polarity, generic DCS, Unicode/order and persistence need scoped observations. | Maintainer/owner: run only missing synthetic cases in the named Windows CHIRP build, keeping the radio disconnected. Record supported/equivalent/unsupported/changed/not-run cases. Before advertising a verified analog V1 workflow, either complete its relevant cases or explicitly approve a narrower preview claim with remaining limitations. A successful CSV test does not close provenance. |
| H5 — Deployment candidate identity and unchanged delivery boundary: Dockerfile, both `deploy/*.lock`, production entry point/static assets and image gates. **Server plus browser payload**; possible image handoff to a provider. | Historical inventory and two actual-image gates passed. Current code uses independent production/development instances; production docs/ReDoc/OAuth redirect are disabled, raw `/openapi.json` remains available. Local templates reference local application scripts/styles. | No target-host/image identity, actual ingress behavior or current candidate notice/source inventory was independently inspected in this task. Historical gate results must not be assigned to a new image. | Release maintainer: name the exact candidate and operator; use existing CI/smoke/inventory/notice/wrapper checks, retain image/commit/lock identifiers and verify the actual target's pages, assets, docs 404s and raw schema. Review drift rather than reopening already passed historical gates. Determine whether the provider receives a conveyed environment. |
| H6 — Hosting/access/privacy controls in `docs/staging.md`, `web/production.py`, `web/serve.py`, deployment configuration. **Server/edge**, not downloadable-only. | App has trusted hosts, security headers, bounded inputs and privacy-conscious errors/logging. The documented container restrictions remain required; the Dockerfile itself does not enforce all `docker run`/platform restrictions. | Host/domain, staging access restriction, TLS, exact proxy trust, total HTTP-body/part/header limits, timeouts, rate/concurrency/storage/resource quotas, safe ingress/telemetry logs and rollback configuration have not been established here. | Hosting owner: select and verify these existing staging requirements before remote exposure. Keep read-only runtime, bounded tmpfs, dropped capabilities, no-new-privileges and resource limits. Test edge failures and a synthetic workflow without collecting personal loadouts; retain the previous image/config for rollback. Public launch needs the production target verified, not only localhost smoke. |
| H7 — Operator authority and scope: `LICENSE`, `COPYRIGHT`, hosted JS/documentation, separately attributed material. **Browser/server and any later artifact**. | Original material is source-available under PolyForm Strict 1.0.0; its defined noncommercial permissions do not authorize modification or redistribution. Third parties keep their terms. No ownership of users' channel data is claimed and generated CSV/JSON is not subjected to the project source license. | The proposed operator/provider and any separate permission arrangement have not been identified. The author's rights in original material do not establish rights in third-party material. | Timothy Thurston: record who operates the service and any permission arrangement needed for another operator or artifact recipient. Preserve Strict and third-party carve-outs; this review neither grants a license exception nor decides that owner operation is forbidden by his outgoing license. |
| H8 — Scope of optional pilot/settings/satellite claims: `radio_profiles.py`, `radio_settings.py`, `satellite_presets.py`, associated browser assets and guides. **Server-generated browser guidance and configuration data**. | Existing guides qualify the BF-F8HP PRO V0.53 profile as documented review, settings as manual plans/editorial recommendations with unknown manufacturer defaults, and ISS frequencies as source-dated nominal receive-only references with unknown live status. | Hardware/firmware behavior, profile unknowns, reception, Doppler and station activity remain unverified. This disposition does not independently recheck source pages or resolve their historical creation provenance. | Product owner: retain those limitations in the launch scope; no extra hardware or live-status claim. These unknowns do not require hardware tests to launch a correctly described planning tool, but block claims of verified device programming, live activity or comprehensive radio compatibility. |

The approved author-reported wording remains exactly:

> Timothy Thurston directly authored Radio Loadout and used AI assistance during planning and development. Exact contributions to individual historical components have not yet been fully reconstructed.

The November 4 statement also reports no personal CHIRP copying/adaptation or
CHIRP source supplied to an assistant, no external sample files introduced,
RepeaterBook and now-unremembered references used to check values rather than
copy records/tables, and unavailable development chats/notes. These are author
recollections, not independent evidence for every table/fixture, an assistant's
sources, permissions or clean-room development. H1–H3 remain open.

## CHIRP component decisions — 2026-11-26

Reviewed the current implementation, tables, fixtures and relevant introduction/
change patches at the same HEAD, `189b92eb63def4b4c1d205507e4ee15a71d51d8f`.
This is the actionable component breakdown of H1–H3, using the existing
[provenance ledger and comparisons C1–C6](chirp-provenance.md). File/function
locations below refer to this project revision. Recommendations are proposed
maintainer decisions, not fabricated author declarations, new permissions or
instructions to change code now. **No particular copied expressive code or prose
fragment was identified by this bounded follow-up.** That is not proof that none
exists; specific creation inputs and applicable permissions remain unresolved.

### What was rechecked

- Git object IDs are unchanged since the provenance review's `2052235` for eight
  scoped files: `exporters/chirp_csv.py`, `importers/chirp_csv.py`, `models.py`,
  `chirp_csv_validation.py`, `dcs.py`, `compatibility.py`, `importers/chirp_report.py`
  and `web/static/backup-format.js`, all under `src/radio_loadout/`.
- In the changed `web/app.py`, AST comparison confirms `_validate_independent_tone`,
  `ChannelFormData`, `_build_independent_tone`, `_build_channel` and
  `_channel_to_form_data` are unchanged. Current profile/route additions do not
  reconstruct the historical tone code's creation. Six selected browser functions
  also have unchanged text after line-ending normalization: `populateToneOptions`,
  `normalizeDcsCode`, `applyDraftToCard`, `getCardDraft`, `updateToneFields` and
  `channelDataFromCard`. These are change checks, not authorship tests.
- Re-read the original exporter at `58a7443`, tone/model checks at `f64f9a6`,
  matched-tone correction at `b5c4180`, validator extraction at `1b7a731`, and
  relevant table/tuning/backup/reporting history (`3004323`, `c1b5986`, `1fbdb4c`,
  `9cbbbbd`, `aca38e2`, `19008ee`, `6214300`). The first HTML lists contain 50
  CTCSS and 104 DCS options; their appearance and later move are observable, not
  evidence of which outside source was consulted.
- All 14 `tests/fixtures/chirp/*.csv` Git blobs still equal their first tracked
  versions at `b5c4180`. Read the current fixture expectations, edge cases,
  original exporter/importer tests and sample generator. This does not independently
  establish a fixture's original generation process.
- Retrieved the existing U3 comparator, CHIRP commit
  [`0b4076d9b19a2a133d11f31546cff8153b39eb89`](https://github.com/kk7ds/chirp/commit/0b4076d9b19a2a133d11f31546cff8153b39eb89).
  `chirp_common.py`, `drivers/generic_csv.py`, both scoped upstream unit-test
  modules and `COPYING` all match the SHA-256 values already recorded in
  [the provenance record](chirp-provenance.md#upstream-file-hashes). Parsed literal
  comparisons reconfirm the two ordered tone/code matches and the same tuning
  set in a different order. No upstream code was imported/executed. This revision
  is still a review comparator, not an established development source.

### Implementation and table dispositions

“Retain with rationale” means the observed technical overlap does not justify a
code rewrite on its own; retain the documented uncertainty and proposed reasoning
for the owner's disposition. It does not certify historical independence or
copyrightability of an entire selection. “Additional review” identifies the
particular material to assess; permission is needed only where the facts and
applicable rights require it, not assumed from every match. The approved author
statement above remains the source of the author's recollection, and unavailable
chats/notes are not requested again.

| Component / exact files and symbols | Delivery and established evidence | Still unknown / factual or functional versus expressive distinction | Smallest next action |
| --- | --- | --- | --- |
| C-P1 — CSV vocabulary, serialization and frequency/duplex/power helpers. [Exporter](../src/radio_loadout/exporters/chirp_csv.py): `CHIRP_HEADERS` 18–39, `export_chirp_csv` 45–56, `_channel_to_row` 59–104, `_duplex_fields` 107–119, `_format_frequency` 225–226, `_format_tuning_step` 229–230, `_format_power` 233–239. [Importer](../src/radio_loadout/importers/chirp_csv.py): `REQUIRED_HEADERS` 21, `import_chirp_csv_detailed` 29–63, `_row_to_channel` 100–146, `_parse_frequency_mhz`, `_parse_transmit_frequency` 175–207, `_parse_power`, `_parse_tuning_step`, `_parse_scan_behavior`. | **Server execution**; CSV/data results reach users, implementation is not sent as browser JS. Included if Python sources/images are conveyed. First exporter `58a7443`, importer `96f7a57`; the 21 ordered headers match the recorded interface. Project uses its Channel model, `csv.writer`, assigned sequential locations and separate helpers. | The source actually used for the first implementation is unrecorded. Required names, mode/duplex tokens and semantic TX/offset conversion are interface requirements; a particular implementation/layout is not dictated by them. Decimal/zero-padding compatibility does not prove copying of the surrounding code. Project 5 W fallback is its policy, not a universal radio fact or all-defaults equivalence. | **Retain with documented rationale.** Record the supported CSV contract and project normalization/default choices as the reason for these overlaps; preserve references and tests. No scoped expressive fragment has been identified here to replace. Keep C-P6/C-P7's tone implementation review separate rather than treating header equality as a blocker by itself. |
| C-P2 — Convenience tone/code tables. [Builder JS](../src/radio_loadout/web/static/builder.js): `CTCSS_FREQUENCIES` 1–8, `DCS_CODES` 10–21, `populateToneOptions` 180–217; `applyDraftToCard` handles imported custom options. Original HTML lists at `3004323`/`c1b5986`, moved at `1fbdb4c`. | **Delivered to and executed in the browser**, including when a user never opens tone controls; also in project archives/image assets. Exact 50/104 ordered matches to the historical comparator are confirmed. Custom CTCSS/generic DCS acceptance is wider than the dropdowns. | These are conventional numeric values, but the actual reference and selection process for these exact lists/order remain unknown. Full list/order is a convenience/support choice, not necessary to every CSV parser or every radio. RepeaterBook recollection does not identify the source of these lists. Table equality alone neither proves expressive copying nor establishes independence. | **Propose retention with a specific selection rationale**, with the owner's dated decision and prospective checks against identified radio/reference evidence; do not present new references as historical sources. Assess any remaining concern about the selection specifically. If the owner elects exclusion, propose custom-value entry with import/duplicate/default behavior preserved; merely hiding controls leaves the arrays in delivered JS and is not exclusion. No such UI change is authorized here. |
| C-P3 — Tuning-step support policy. [Models](../src/radio_loadout/models.py): `TUNING_STEPS_KHZ` 8–24, `Channel.__post_init__` membership check; [builder template](../src/radio_loadout/web/templates/builder.html): `data-field="tuning_step_khz"` select; [backup validator](../src/radio_loadout/web/static/backup-format.js): `steps` 4 and `validateField`; compatibility test `STEPS` 97. | **Browser table/validator plus server membership validation**; test copy is test-only. Introduced across model/template/exporter at `9cbbbbd`; backup copy at `aca38e2`. Current 15 values equal the comparator's set, ordered differently. | Numeric steps are radio/format facts; choosing exactly these supported values is policy, not proof every physical radio accepts them. Historical reference for the selection and later copies is unrecorded. Separately spelling the same list in tests is not independent source evidence. | **Retain with documented rationale:** label it the selected Generic CSV support set, preserve radio-specific warnings and add a prospective source/selection basis for each value when documenting that policy. Do not reorder/delete values solely to make a similarity test stop matching; any supported-set change must account for existing v1/v2 backups and tests. |
| C-P4 — CTCSS numeric and output validation. [Models](../src/radio_loadout/models.py): `Tone.__post_init__`; [shared CSV validator](../src/radio_loadout/chirp_csv_validation.py): `validate_chirp_ctcss` 4–12, `format_chirp_ctcss` 15–25; importer `_parse_ctcss_tone` 370–383; exporter `_format_ctcss` 183–187. | **Server execution**, validation messages/results delivered as data. Model checks originate at `f64f9a6`; CSV open interval and formatted-output recheck at `1b7a731`. Generic model bounds are inclusive, CSV bounds exclusive; output rounding is checked separately. | Accepted numeric domain and precision are functional compatibility requirements. The project's bool/int handling and output revalidation differ from the comparator's float predicate. Who supplied the historical rule/input remains unknown; matching a short inequality is not itself an identified expressive block. | **Retain with documented rationale.** State the model/CSV distinction and required boundary/rounding behavior, preserving boundary tests. No identified expressive validator fragment currently supports a replacement task. Keep any assertion of physical-radio tone support separate. |
| C-P5 — Generic DCS representation, polarity and normalization. [DCS helpers](../src/radio_loadout/dcs.py): `validate_dcs_code` 4–11, `parse_dcs_code` 14–25, `format_dcs_code` 28–30; `Tone.__post_init__`; importer `_parse_dcs_tone` 386–394 and `_parse_dcs_polarities` 397–417; exporter `_dcs_polarity` 212–222. Browser: `backup-format.js:normalizeDcsCode` 32–39, `validateField`, and `builder.js:normalizeDcsCode` 414–416 / `applyDraftToCard`. | **Server helpers and delivered browser normalization**. Digit-check approach exists at `f64f9a6`, extracted at `1b7a731`; JS normalization later moves to `aca38e2`. Three octal-digit spellings are accepted generically, including codes beyond the 104-item menu; Python integer spelling and JS regex differ from the comparator's enumeration. | Numeric domain, leading-zero display and TX/RX polarity are representation/behavior facts. Validation implementation, errors and test arrangement are potentially expressive, but no particular copied fragment was identified. Assistant inputs and original creation basis are incomplete. | **Retain with documented rationale:** preserve typed validation, canonical draft spelling and three-digit CSV output, explicitly distinguishing generic acceptance from conventional dropdowns/hardware support. Keep regression cases for `000`, `001`, `023`, `777` and independent polarities. Do not generate a different spelling merely to avoid matching standard notation. |
| C-P6 — Export tone classification and inactive defaults. [Exporter](../src/radio_loadout/exporters/chirp_csv.py): `_tone_fields` 122–180, `_matching_tones` 190–199, `_chirp_tone_name` 202–209, with `_channel_to_row` as caller. Original implementation is already present at `58a7443`. | **Server code used on every export**, including no-tone channels; emitted cells reach users. The provenance record's C3 identifies the same broad case order and CHIRP-specific inactive defaults, while project return values/helpers and assignment structure differ. The corresponding upstream routine is [historical `split_tone_decode`](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/chirp_common.py#L2012). | Tone equivalence and CSV mode names are functional requirements. This particular classification structure/default initialization is the strongest recorded implementation-structure candidate. It is not an identified copied statement block; the initial author/assistant inputs remain unreconstructed. Similar behavior and different syntax do not decide whether an adaptation occurred. | **Obtain targeted additional review first**, limited to this function family, its first patch and comparator C3. Ask whether an actual expressive adaptation is identifiable and what rights/permission issue follows, rather than request unavailable chats. If a material issue is established or the owner chooses a new implementation, prepare the bounded replacement plan below; retain evidence/history and do not assume a rewrite cures provenance. |
| C-P7 — Import matched/cross-tone semantics and defaults. [Importer](../src/radio_loadout/importers/chirp_csv.py): `_parse_tones` 229–300, `_parse_cross_tones` 303–339, `_parse_cross_tone` 342–367 and parsing helpers above. Fixtures README and compatibility tests 240–269 explain matched tone behavior. | **Server execution**; parsed fields and loss/normalization results reach the browser. `96f7a57` introduces importer/tests; `b5c4180` changes matched fields and adds upstream references plus deliberately different inactive values. This positively establishes an interoperability correction, not a particular source-transcription process. | Which exact revision/experiment/assistant input informed that change is unknown. Active-column behavior is necessary for that compatibility choice; row helpers, splitting/dispatch structure and prose could be expressive, but no particular copied body/comment has been identified. The current fallback accepting a single CTCSS column is a project behavior that needs its own stated test scope. | **Include in C-P6's targeted review** the small matched/cross-tone family and `b5c4180` patch; retain format-required semantics unless a concrete issue justifies a change. Additional permission is an option if a covered adaptation is actually established; an attribution URL alone is not that permission. Removing import alone would not remove the export candidate. |
| C-P8 — Browser/server tone-model glue and later reuse. [Web app](../src/radio_loadout/web/app.py): `_validate_independent_tone` 69–83, `ChannelFormData` 86–199, `_build_independent_tone` 266–285, `_build_channel` 288–362, `_channel_to_form_data` 457–492. [Builder](../src/radio_loadout/web/static/builder.js): `updateToneFields` at 299, `getCardDraft` at 346, `applyDraftToCard` at 418, `channelDataFromCard` at 793. | **Python executes server-side; JS is delivered to the browser; API responses contain values, not Python implementations.** These selected functions are unchanged from the earlier reviewed versions. Quick modes map into independent Channel/Tone data; imported tones use independent controls. Later `profile_compatibility.py:check_channel_compatibility` invokes the same generic checker; `loadout-format.js:createValidator` invokes `RadioLoadoutBackup.validate`. | A separate data model and absence of CHIRP imports do not prove independent authorship. The original browser/web contribution inputs remain incomplete; reuse in a new profile or backup does not create new provenance for the reused logic. No distinct copied fragment in this glue was identified. | **Retain with documented mapping rationale**, while carrying C-P2–C-P7 uncertainties through to callers. No new whole-builder rewrite is justified. If the scope is narrowed later, inspect these callers and delivered bundles as well; removing one endpoint or hiding a control is not proof the material is excluded. New profile/settings/satellite source claims are not re-audited by this CHIRP review. |
| C-P9 — Compatibility/import-loss descriptions and error prose. [Compatibility](../src/radio_loadout/compatibility.py): `CompatibilityReport.to_dict`, `validation_report` 60–74, `check_chirp_compatibility` 77–146; [import report](../src/radio_loadout/importers/chirp_report.py): `SUPPORTED_COLUMNS`, `ChirpImportResult.add`, `report`, `describe_row` 56–107; builder `renderCompatibilityReport` / `renderChirpImportReport` display results. | **Server implementation; human-readable result prose reaches the browser**. Introduced at `19008ee` / `6214300`, unchanged since the original provenance review. They describe project validation, defaulting, omitted columns, renumbering and normalization, including project-specific loss confirmation. | Prose can be expressive even where behavior is factual. Historical creation inputs are not declared at component level. Neither the prior bounded comparison nor this inspection identifies a distinctive copied explanation/error body; tests of safe rendering do not establish its authorship. | **Retain with project-behavior rationale**; no specific prose replacement is justified now. If a particular external passage is subsequently identified, compare that exact wording/context and obtain review/permission or propose replacing that passage. Do not add blanket upstream attribution as a purported cure. |

### Fixtures and tests: separate from deployed implementation

All paths in the next table are under `tests/fixtures/chirp/` unless stated.
They are **test/development material**, included by the source-archive manifest
but excluded from the normal runtime wheel/container test payload and ordinary
browser delivery. Do not substitute that packaging fact for an authorship claim.
The previous 12-dataset/2,025-record upstream comparison remains bounded historical
evidence; it was not rerun as a claim about all CHIRP history. Unchanged Git blobs
let the earlier comparison continue to identify the same project inputs.

| Component / exact paths and consumers | What evidence establishes | What remains unknown | Smallest next action |
| --- | --- | --- | --- |
| C-P10a — `analog_channels.csv` (6 rows); `tests/test_chirp_compatibility.py:ANALOG_CHANNELS`, `_channel`, `test_fixture_import_and_round_trip`; `examples/generate_chirp_sample.py:main`; `web/app.py:_sample_channels`. | Earlier project samples contain the calling/weather example identities; fixture names/comments and sparse locations are visible. The generator makes a different four-channel export, not these six original fixture rows. `_sample_channels` supplies a real application download, so **that separate function/output is server/public sample data**, not a served copy of the test file. | Prior existence of project examples does not establish the base fixture's construction or the examples' entire outside-source history. Familiar frequencies/names alone are not expressive-copy evidence. | **Retain tests with the bounded origin rationale** and explicitly separate sample behavior from fixture provenance. If stronger fixture-source evidence is unavailable, record it as unknown. No deletion/re-generation of the original fixture is justified solely to erase a gap. |
| C-P10b — `tones.csv` (14 rows); `TONE_CASES`, `TONE_CHANNELS`, `test_tsql_uses_receive_ctcss_for_both_directions`, `test_matched_dcs_ignores_cross_mode_receive_code` in `tests/test_chirp_compatibility.py`. | Added with the matched-tone correction and references at `b5c4180`; cases spell out inactive-field differences, polarity and cross combinations. These are deliberate semantic tests, not upstream-issued verification receipts. | Functional cases overlap naturally; original parameter/prose/row-generation inputs and assistant contributions are not reconstructed. No copied test/row fragment is identified by existing evidence. | **Retain as test-only evidence**, and use these exact cases when specifying/reviewing C-P6/C-P7. If new tests are needed, record a contemporaneous source/behavior basis for them; do not call future records proof of old authorship. |
| C-P10c — `tuning_scan_power.csv` (15 rows); compatibility-test `STEPS`, `POWERS`, `STEP_CHANNELS`. | Patterned rows exercise all selected steps, scan cycling and power values; expectations were introduced in the same commit. | Exact selection sources and method of generating the original rows are unrecorded. Patterned/synthetic construction does not prove independent creation. | **Retain with the selected-policy rationale** from C-P3. No runtime exclusion follows from this test-only uncertainty. Review any source-archive publication separately under H3. |
| C-P10d — `extra_columns.csv` (3 rows), `utf8_bom_crlf.csv` (1 row), `blank_optional.csv` (3 rows); `EXPECTED_FIXTURES`, `test_fixture_contains_real_utf8_bom_and_crlf_bytes`, `test_blank_optional_defaults_match_omitted_columns` and round-trip tests. | Repository bytes contain intentional Unicode, quoting/multiline cells, BOM/CRLF, omitted fields and default cases. `.gitattributes` protects the byte-specific fixture. | Who devised each text/edge case or any transformed starting input remains unestablished; the owner reports no external samples were brought in. Neither format tricks nor that recollection independently reconstruct origins. | **Retain tests with these evidence limits.** If a specific copied passage/sample is later identified, address only that material with review or a documented new test input. Do not replace all fixtures to claim a clean-room past. |
| C-P10e — `missing_headers.csv`, `invalid_frequency.csv`, `unsupported_mode.csv`, `invalid_offset.csv`, `invalid_ctcss.csv`, `invalid_dcs.csv`, `unsupported_tuning_step.csv` (one data row each), `empty.csv` (zero bytes); `test_invalid_fixtures_are_rejected`, `test_empty_and_header_only_csv_are_rejected`. | Minimal rejection cases and actual empty file; introduced with the fixture set, unchanged. | Very small/empty content supplies little creation evidence. A simple invalid numeric value does not identify copying, while lack of attribution does not prove independence. | **Retain with rejection-spec rationale.** No particular expressive fragment justifies replacement or an upstream permission request for these values alone; do not use them as evidence that the more complex fixture set is independently authored. |
| C-P11 — Test bodies: `tests/test_chirp_csv.py:_read_rows` and six export cases; `tests/test_chirp_csv_import.py:test_chirp_csv_round_trip` and rejection cases; `tests/test_chirp_compatibility.py:test_100_channel_round_trip_preserves_every_supported_field` 282–329; `tests/test_chirp_ctcss_boundaries.py` boundary/inactive-field/rounding cases; `tests/test_dcs_compatibility.py` generic-code, matched/cross/polarity cases; `tests/js/test_builder_dcs.mjs` import/backup/duplication cases. | Relevant introductions are `58a7443`, `96f7a57`, `b5c4180`, `1b7a731`, with JS regression at `0903088`. The 100-channel generator derives from base project fixtures; original round trips reuse the project exporter. Existing upstream comparison reports common functional categories, not an identified copied test body. | Passing tests, repeated expected constants and a different test framework do not reconstruct authorship or supply an independent CHIRP acceptance oracle. Newer test success does not cure legacy fixture questions. | **Retain test-only checks with this rationale.** For any scoped implementation work, add a dated behavioral case matrix with its actual sources/observations and separately specified expected outcomes. Do not generate expected outputs solely from the implementation under replacement. Windows application checks stay pending and are not provenance proof. |

No runtime exclusion is recommended merely because the test inputs' creation
records are incomplete. Holding a source-archive release is a separate option
from removing useful local regression checks. The approved author's account is
retained as recollection, not silently promoted to independently verified origin.

### Bounded alternatives if targeted review requires implementation work

The first proposed replacement boundary, **if justified and separately
authorized**, is C-P6's `_tone_fields` family and, only if needed, C-P7's matched/
cross-tone parser. First record a behavior-only table for no tone, TX-only CTCSS,
matched CTCSS/DCS, unequal and one-sided cross cases, independent polarities and
inactive-column defaults. Identify each observed compatibility source and every
project choice; do not copy explanatory text into that specification. Preserve
the Channel/Tone public contracts, error/input limits, existing backups, RX-only
behavior and CSV results unless a separately reviewed defect requires a change.
Use expected outcomes specified independently of the proposed new implementation
and retain the legacy comparison/history in the provenance record.

A new structure, renamed variables, generated test data or an AI rewrite would
not establish independent historical authorship, remove previously conveyed
material or automatically resolve applicable rights. Everyone has now seen the
comparison; this is not a clean-room claim. Record the real new development inputs
and assess the proposed result and any identified predecessor material before
calling a specific issue addressed. Permission/review remains an alternative to
replacement where applicable; no third party is contacted by this task.

If the owner instead chooses **exclusion from the initial release**, specify a
real product boundary. Hiding Cross controls leaves the shared classifier running
on ordinary exports; hiding dropdowns still sends their JS arrays; disabling
CSV import leaves export and the tables. A JSON-only/custom-value planning preview
would require a separately reviewed route/asset change excluding the relevant
implementation/data from delivery, not a CSS hide or an assertion that all
provenance is resolved. That materially narrows the analog V1 proposition and is
not the recommended first step without a concrete reason from the targeted review.

### Top three decisions / implementation preparations

1. **Disposition the constants and simple compatibility rules (C-P1–C-P5).**
   Decide whether to retain them on the documented factual/interface/support-policy
   rationale. Add prospective reference/selection evidence for the 50/104/15 lists
   without inventing their historical source; commission selection-specific
   review only where a concrete concern remains. Do not rewrite to reduce a
   similarity score.
2. **Review the specific tone conversion family (C-P6/C-P7).** Use the original
   exporter and matched-tone patch plus the pinned comparison to assess whether
   any expressive adaptation is actually identifiable. Decide between reasoned
   retention, applicable permission, or the bounded replacement proposal above.
   Do not expand this into an unaimed rewrite of the whole builder.
3. **Prepare an explicit behavioral oracle and fixture-use decision (C-P10/C-P11).**
   Keep the legacy test provenance limitations and source-archive gate visible;
   document sources/inputs for new cases and use the existing Windows matrix for
   still-missing application observations. Do not make completion of unavailable
   historical chats a prerequisite or mark those Windows checks complete here.

For this follow-up only the existing disposition is edited. No application code,
table, fixture, source-license text, attribution or authorship statement is
changed. `git diff --check`, link/symbol checks and preservation checks validate
the documentation update; application tests were not rerun. The upstream
downloads remain optional temporary comparison evidence, with the immutable
links/hashes in the existing provenance record as the reproducible identifiers.
No code, source bundle or image is published or deployed and no radio is used.

## Open component findings primarily affecting conveyed environments

These components are installed server-side, not ordinary browser dependencies.
Their distribution obligations become relevant when the component/environment is
conveyed; they are not automatically prerequisites to publishing a dependency-free
project wheel or operating a service. Browser code is a separate boundary as
shown above. This distinction follows the existing dependency review; for MPL,
see the [official FAQ on use/distribution](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)
and [sections 3.1–3.4](https://www.mozilla.org/en-US/MPL/2.0/). It does not imply
that all Radio Loadout source must be published.

| ID / components and delivery | Established evidence | Still unknown / smallest action and owner |
| --- | --- | --- |
| D1 — certifi 2026.10.23 at `/opt/venv/lib/python3.13/site-packages/certifi/`; certifi 2026.6.17 in base `/usr/local/lib/python3.13/site-packages/pip/_vendor/certifi/`, venv `/opt/venv/lib/python3.13/site-packages/pip/_vendor/certifi/`, and `/usr/local/lib/python3.13/ensurepip/_bundled/pip-26.2.1-py3-none-any.whl!/pip/_vendor/certifi/`. **Server-installed; image/environment distribution**. | Exact certifi/pip archives, notices, shipped PEM hashes and modified wrappers are pinned; CI #13 establishes wrapper correspondence. The five-archive source-evidence ZIP reproduced at 2,409,640 bytes, SHA-256 `f6c7eaffaddaebb79fd3ee7fbe22471d49aacab84409207d5442e27f6d75accd`, in the recorded Linux and reported Windows runs. | Historical Mozilla/NSS input revision and generator/service response remain unidentified; matching output does not prove complete preferred source. Maintainer: assess the preferred modification form and preserve covered notices/rights for all four copies. Keep missing historical inputs explicit; do not replace pins or infer completeness from a wheel's name or successful hash check. |
| D2 — Source delivery policy/tooling: `docs/source-bundles.md`, recipient guide, pinned retrieval/checking and offline bundle scripts. **Future recipient source artifacts**, not browser/runtime assets. | Owner selected release-attached sources and maintenance checks; the local bundle preserves five original archives and qualified metadata. Retrieval and verification tools exist. | Publication/retention/access are not activated; intended recipients have not tested access. Owner: separately approve a specific release, source selection/completeness and maintained access/retention; maintainer then verifies recipient retrieval. Seven-day diagnostics and local caches are not permanent access. Publishing the evidence ZIP alone does not supply unknown inputs or all dependency sources. |
| D3 — uvloop 0.23.0 / libuv 1.52.1; Pydantic Core 2.50.2 / ICU4X, Unicode, PyO3/ffi 0.30.1 and url/idna path. `third_party_notices/v1/` and native wheels. **Server/native image contents**; supplement also in project archives. | Matching installed uvloop/Pydantic binaries and matching sources support the scoped supplement: libuv LICENSE, LICENSE-extra, tree.h BSD and inet.c ISC, plus Unicode/ICU/PyO3/URL-path texts. All 15 bundle bytes passed actual-image verification. | The identified notice supplement is delivered; full selected native graph, exact feature overrides/toolchain contributions and applicability beyond it remain open. Native-review owner: obtain build-specific evidence or an upstream notice ledger and assess remaining applicable texts. Do not count every Cargo.lock entry as emitted binary code or mistake lack of a marker for absence. |
| D4 — fastar 0.12.0, rignore 0.8.1, watchfiles 1.3.0; selected PyO3 versions, ignore 0.4.24, notify 8.0.0 and potentially unicode-ident 1.0.12. **Server-installed native wheels**, even if a CLI/reload path is unused. | Reviewed locks/source archives and parent notices identify candidate dependencies, with separately inspected MIT/Unlicense, CC0 and Unicode-related texts. These are not complete selected-runtime graphs. | Native-review owner: establish selected compiled components and preserve their applicable notices before environment redistribution. Lock entries can include macros/build/platform-only material; neither parent MIT nor “unused at runtime” proves binary notice coverage. Server installation alone does not send them to visitors. |
| D5 — Other native boundaries: PyYAML 6.0.3/LibYAML 0.2.5, protobuf 7.36.2/upb, charset-normalizer 3.5.2/Cython; httptools 0.9.0/http-parser/llhttp, MarkupSafe 3.0.4, websockets 17.4. **Server wheels / conveyed environment**. | LibYAML markers/static linkage and overlapping authors' MIT notice are recorded; upb visible headers correspond to the supplied Google BSD text. httptools retains vendor notices; MarkupSafe/websockets supply BSD notices. No extra omission was established for the latter two. | Native-review owner: confirm LibYAML build/version and notice equivalence, full protobuf compiled dependency coverage and charset-normalizer generated/runtime provenance; verify vendor versions if repackaging httptools. Do not invent a missing LibYAML notice merely because it is combined, or apply a compiler's full license to all generated output by assumption. |
| D6 — CPython 3.13.15, Debian Bookworm's recorded 97 packages; glibc/loader, libgcc/libstdc++, OpenSSL, SQLite, zlib, libffi, expat/compression, CA certificates and tzdata. **Server/base image**, not project wheel dependencies packaged into the wheel. | Actual Python and Debian package/source versions, copyright paths, common license texts and selected ELF dependencies were collected. CPython LICENSE was inspected. | OS/Python-review owner: map resolved libraries to exact source packages, enabled/incorporated components and applicable notices, LGPL/GCC exceptions and corresponding-source arrangements. Full notice sufficiency, build modifications/configuration and source access remain open. Debian CA sources are separate from certifi. Presence of a copyright file is not completion of every source duty; separate-program aggregation is not whole-application GPL by default. |
| D7 — Base/venv pip 26.2.1, ensurepip wheel and the remaining vendored bootstrap packages. **Server/base/venv components, image distribution**. | Inventory covers both interpreters, bootstrap wheel/hash and 18-pin vendor manifests/notices; certifi received the focused correspondence review. They are additional to the 59-package runtime lock. | Dependency-review owner: review exact vendor/bootstrap notices, source access and applicability beyond certifi. Pins and the certifi wrapper gate do not establish arbitrary installed-file equivalence or completeness for every vendor component. Do not omit bootstrap content because pip is an installer. |
| D8 — FastAPI's copied Swagger OAuth redirect, development Swagger/ReDoc/font/favicon assets; Requests and other Apache/vendor notices. **Redirect/browser assets only on development or if re-enabled; FastAPI code/other licenses remain server-installed**. | Production delivery finding is addressed: docs/redirect 404, hidden links, local page assets; raw schema remains. Requests supplies LICENSE/NOTICE; other reviewed packages retain Apache or nested vendor texts. FastAPI's copied redirect notice question remains in the installed dependency. | Maintainer: keep production docs disabled and preserve supplied notices. Before conveying that dependency or re-enabling docs, resolve applicable Swagger/sidecar/NOTICE and font/favicon evidence; source copying still matters even with a disabled route. Do not invent NOTICE where none exists. The [Apache redistribution conditions](https://www.apache.org/licenses/LICENSE-2.0) apply to the relevant work, not automatically all project material. |
| D9 — setuptools 84.2.1/autocommand LGPL-3.0, validate-pyproject MPL/BSD material, other build tools; five npm tools and embedded sidecars, Node, Chromium/FFmpeg and exported Playwright HTML reports. **Build/test or development-artifact delivery only**, excluded from ordinary hosted assets and the configured final stage. | Existing wheel/tarball inspections identify actual license/NOTICE sidecars and tool versions, including axe-core/MPL and bundled WebP/Emscripten notices. Docker stages separate global builder tools; npm does not build a production bundle. | Build/test-release owner: inventory exact exported reports/browser binaries/environment and retain applicable notices/sources/replacement terms before sharing them. Complete browser/native tool coverage is not established. No requirement to distribute such tools with V1 is introduced; their copyleft does not relicense application build output. |
| D10 — Older direct-license inventory and historical evidence wording: `docs/dependency-licenses.md`, baseline portions of the dependency/native reviews and staging guidance. **Documentation**, source archives if published. | Detailed artifact review supersedes metadata-only summaries; later dated entries close specific gates. Examples include BSD python-dotenv, CC0 notify and setuptools' extra licenses. | Documentation owner: reconcile summaries when separately authorized, preserving dated evidence. Earlier “image pending”/docs-CDN descriptions do not negate later scoped results. This is follow-up documentation work, not a newly discovered browser component or a reason to rerun a completed historical gate. |

## Separate release decisions

| Proposed action | Current disposition |
| --- | --- |
| Restricted hosted evaluation | Conditional on H1/H2 owner disposition for the intended audience and H5–H7 deployment/operator controls. H4 can remain an explicitly pending test objective. No remote staging deployment is approved or performed here. |
| Public hosted analog V1 | Hold pending the hosted gates above. No server-only source-access issue is silently converted into a requirement to publish the entire app. Conversely, “server-only” does not excuse delivery of unreviewed browser tables/code. |
| Publish project wheel/source archive without dependency binaries | Separate approval. Preserve project/supplemental notices and re-audit exact artifacts. H1–H3 and original-material permissions remain relevant; a source archive includes fixtures/tests and documentation. Declared dependencies are not bundled dependency contents. A wheelhouse/offline installer has a larger D1–D8 boundary. |
| Publish certifi source-evidence ZIP | Separate owner publication decision under the selected policy. Keep its qualified scope and original upstream notices; establish recipient retrieval/maintenance. It is neither a complete all-component source bundle nor proof that historical preferred inputs are present. This document does not authorize an upload. |
| Publish/distribute runtime container | Hold for D1–D8 and candidate-specific evidence, including any provider transfer requiring this treatment. Scoped supplement/wrapper gates already passed historically; remaining native, bootstrap, OS/Python and source-access obligations are not closed. |
| Publish builder/test environment or reports with embedded third-party assets | Separate review/approval, including D9's wider inventory. Not part of hosted V1 merely because CI uses those tools. |

PolyForm Strict 1.0.0, the separate project copyright notice, third-party rights
and the approved authorship wording remain unchanged. A launch decision cannot
grant missing third-party permissions. Neither users' channel data nor their
generated configurations acquire the project source-code license through this
review; rights in any independently supplied third-party data still need their
own basis.

## Smallest next actions and verification of this review

1. Timothy Thurston: record the bounded H1–H3 provenance disposition, any remaining
   available recollection and whether specialist review is needed for a specific
   concern; do not fabricate unavailable history or clean-room facts.
2. Hosting owner: choose the operator, restricted audience and candidate/target,
   decide whether any image handoff is a separate conveyance, and verify H5–H7
   against the existing staging checklist before remote exposure.
3. Maintainer/owner: complete the missing synthetic Windows cases for the
   advertised analog workflow or approve explicitly narrower preview claims.
   Leave all unobserved matrix cases pending; no radio connection is required.
4. Keep artifact publication separate. Resolve the applicable D rows and obtain
   a release-specific decision before distributing an environment or activating
   release-attached source delivery. Do not upload temporary diagnostics as a
   substitute for maintained recipient access.

This docs-only task runs `git diff --check` and checks preservation of the four
pre-existing changes and the unstaged index. It does not rerun application tests,
build artifacts/images, inspect a live host, execute CHIRP, revalidate remote CI,
publish sources, connect to a radio or deploy. Source-access findings and Windows
CHIRP cases remain open; this is not legal clearance.
