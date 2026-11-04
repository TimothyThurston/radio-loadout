# CHIRP provenance evidence record

Reviewed **2026-11-04 (America/Chicago)** at Radio Loadout commit
`2052235004e2a7a801f814a560a98f331f72309f`
(`Disable production documentation UIs and record license review`). The working
tree was clean at the start of the original technical review. The dated author
statement below was added afterward, preserving the existing uncommitted
documentation changes. This record and the CHIRP references in
[the dependency review](dependency-license-review.md#chirp-format-compatibility-and-provenance)
are the only repository changes made for this task.

**Finding:** this review did not identify a particular copied expressive
implementation or prose fragment. It did identify exact table matches,
CHIRP-specific defaults, shared functional structure and explicit upstream
references, detailed below. Those observations do not prove copying, independent
authorship, permission, or the absence of other copied material. Provenance
remains unresolved: the author has supplied the recollection below, but exact
component-level creation sources and any applicable permission evidence have
not been established. This record is not legal clearance.

## Scope and evidence limits

The scope covers the CSV importer/exporter, CTCSS/DCS validation and browser
tables, tone conversion, tuning steps, compatibility fixtures and related tests.
The source ledger below identifies supporting model, web, reporting and backup
code where those concerns are implemented. It is not a review of every CHIRP
driver, every upstream revision, radio manual or frequency dataset.

Evidence consists of tracked files, all 45 locally reachable commit messages,
relevant introduction/change patches, and downloaded immutable upstream files.
Git author metadata for the inspected `src`/`tests` history names Timothy
Thurston. This records a commit identity, not a declaration that every line was
written unaided or independently. Timestamps are recorded metadata and do not
prove when a particular source became publicly available or was consulted.

The original technical comparison preceded the dated author-reported statement
below. That statement adds recollection, not independent corroboration. No third
party was contacted. No code was rewritten, attribution removed, license changed or
history rewritten. The current PolyForm Strict license applies only within its
existing project scope; it does not override CHIRP's rights. An attribution link
alone would not resolve obligations for copied GPL-covered material.

## Author-reported statement — 2026-11-04

Source: confirmations supplied by Timothy Thurston in this user/assistant
conversation on 2026-11-04 (America/Chicago). The following records the author's
recollection; it has not been independently verified against original development
chats, notes or source-access records.

> Timothy Thurston directly authored Radio Loadout and used AI assistance during planning and development. Exact contributions to individual historical components have not yet been fully reconstructed.

The author reports:

- He did not personally copy or adapt CHIRP source, or supply CHIRP source code
  to an AI assistant.
- He did not bring external sample files into development or testing.
- He consulted RepeaterBook and other references he no longer remembers to
  check repeater settings, tone values and tuning-step options.
- He used RepeaterBook to check values; RepeaterBook records or tables were not
  copied into the repository.
- Original development chats and notes are unavailable.

These statements establish what the author currently reports, rather than
independently verified historical inputs. They do not assign RepeaterBook or any
other reference to every table or fixture, reconstruct individual AI contributions
or an assistant's inputs, establish permissions, or demonstrate a clean-room
development process. The reported absence of external sample files does not
reconstruct how each fixture row and expected test model was created. The
technical comparisons below remain unchanged and provenance remains unresolved.

## Project source ledger

Locations refer to the reviewed project commit. Short commit IDs below resolve
to full hashes and dated milestones in the next table. A recorded introduction
is the first tracked appearance in this repository, not proof of creation from
scratch. The two explicit CHIRP source-code references committed in the fixture
README are its `generic_csv.py` and `chirp_common.py` links; no particular upstream
revision is recorded there. The author's additional value-checking references
are recorded above without assigning them to individual components. U1–U3 below
are review comparators, not established development sources.

| Project material / current locations | Introduction and material changes | Known references, comparison and unresolved source |
| --- | --- | --- |
| [CSV exporter](../src/radio_loadout/exporters/chirp_csv.py): `CHIRP_HEADERS` 18–39; `_channel_to_row` 59–104; `_tone_fields` 122–180; formatting/polarity helpers 183–239 | Introduced with exporter tests at `58a7443`. `91cfba3` removes one blank line, without a semantic change. `cfa8b8c` adds power fallback/sample generation. `3c53622`/`1fbdb4c` extend polarity/web tone support; `9cbbbbd` adds tuning/scan; `1b7a731` adds shared tone validation; `6214300` adds input-count limit. | C1/C3 compare U1/U3 headers, defaults, serialization and `split_tone_decode`. README source references were added later at `b5c4180`; the exporter's original consulted source is not recorded. |
| [CSV importer](../src/radio_loadout/importers/chirp_csv.py): `import_chirp_csv_detailed` 29–63; `_parse_tones` 229–300; cross parsing 303–367; tone/polarity parsing 370–417; tuning/scan 447–464 | Introduced at `96f7a57` with `test_chirp_csv_import.py`. `b5c4180` corrects matched TSQL/DTCS semantics and optional defaults. `1b7a731` validates inactive CTCSS fields and generic DCS. `6214300` adds bounded input and import reports. | C4/C5 compare U3's driver parser and `split_tone_encode`. The fixture README establishes a reference to those semantics, not which source the original importer author used. |
| [Channel/tone models](../src/radio_loadout/models.py): tuning list 8–24; Tone 60–103; tuning membership 163–170 | Channel introduced `77e5ad8`; analog Tone/DCS digit validation `f64f9a6`; polarity `3c53622`; tuning/scan `9cbbbbd`; generic validator extracted at `1b7a731`. | C2/C5/C6: conventional values, accepted ranges and generic-code behavior have upstream counterparts. Initial source for constraints/list selection is unrecorded. |
| [Shared CTCSS checks](../src/radio_loadout/chirp_csv_validation.py): 4–25; [DCS helpers](../src/radio_loadout/dcs.py): 4–30 | Both files introduced `1b7a731`. DCS digit-checking logic was already in `models.py` at `f64f9a6`, so the new file is not the first appearance of that algorithm. | C5 contrasts U3's `VALIDTONE` and generated code list with project type checks, formatted-value revalidation and digit-string validation. No external URL/revision is attached to the original model checks. |
| [Browser tone tables](../src/radio_loadout/web/static/builder.js): CTCSS 1–8, DCS 10–21; option population 168 onward | CTCSS numeric input first `8a2997c`; 50-option HTML table `3004323` (template lines 166–215 at that commit); 104-option DCS HTML table `c1b5986` (243–346 there). Both move into JS constants at `1fbdb4c`. `0903088` preserves custom options when duplicating cards. | C2: present ordered values equal the earlier HTML values and CHIRP tables. No source citation accompanies the table-introduction commits. Standard radio values alone do not establish transcription from CHIRP. |
| [Browser/model tuning controls](../src/radio_loadout/web/templates/builder.html): 211–229; models 8–24; compatibility tests 96–107 | Introduced across models, template, exporter, web conversion and tests at `9cbbbbd`. The tests' separately spelled list arrives at `b5c4180`. | C2: same 15-element set as U1/U3 `TUNING_STEPS`, but sorted differently. This is a selected support policy, not a claim that every physical radio supports every value. Source for the exact selection is unrecorded. |
| [Browser DCS normalization](../src/radio_loadout/web/static/builder.js): 402–404; [backup format](../src/radio_loadout/web/static/backup-format.js): 32–39 | JS normalization introduced in builder at `1b7a731`; moved to the versioned backup module at `aca38e2`. JS DCS tests introduced `1b7a731`, extended `0903088`. | C5: regex/digit representation and canonicalization differ from CHIRP's Python list enumeration. No evidence identifies any assistant's external input. |
| [Web tone-to-model conversion](../src/radio_loadout/web/app.py): `_build_independent_tone` 261 onward, `_build_channel` 283 onward and `_channel_to_form_data` 412 onward; [compatibility review](../src/radio_loadout/compatibility.py): 77 onward; [import report](../src/radio_loadout/importers/chirp_report.py): `describe_row` 56 onward | Web app begins `3d702c6`/`cb1df06`; tone controls `8a2997c`, `c1b5986`, `1fbdb4c`; compatibility module/tests `19008ee`; validation updates `1b7a731`; reporting module/tests `6214300`. Production app separation at current HEAD changes registration, not CHIRP tone logic. | Scope included shared tone mappings and compatibility explanations. Upstream format behavior is relevant, but these modules' creation process is not declared in Git. |
| [Exporter tests](../tests/test_chirp_csv.py) 22–125; [importer tests](../tests/test_chirp_csv_import.py) 18–125 | Exporter tests `58a7443`, updated `cfa8b8c`; importer tests `96f7a57`. | The original importer round trip starts from project Channel objects and the project exporter. It is a consistency test, not an independent upstream-file or provenance test. The exporter tests reuse `CHIRP_HEADERS`. |
| [CHIRP fixtures and README](../tests/fixtures/chirp/README.md); [compatibility tests](../tests/test_chirp_compatibility.py) 58–150, 239–329 | All 14 CSV fixtures, README, `.gitattributes` and compatibility tests introduced together at `b5c4180`. Their Git blobs are unchanged at reviewed HEAD. | Explicit direct references to upstream header mapping and split-tone semantics. Fixture authorship/generation inputs are not recorded; see fixture analysis below. |
| [CTCSS boundary tests](../tests/test_chirp_ctcss_boundaries.py) 17–21, 152–200; [DCS tests](../tests/test_dcs_compatibility.py) 21–130; [JS DCS tests](../tests/js/test_builder_dcs.mjs) | Introduced `1b7a731`; JS duplication regression extended `0903088`. | Local boundary matrices, generic codes and round trips test intended behavior. Comparisons with U3 tests show common functional cases, without establishing a copied test body. |

### Dated project milestones

Dates below are Git author dates in the recorded local offset; hashes allow
review with `git show HASH -- PATH` and `git log --follow -- PATH`.

| Short ID | Full commit | Recorded author date | Relevant change |
| --- | --- | --- | --- |
| `77e5ad8` | `77e5ad888e4b09f731236096681bc991ba47fdd8` | 2026-09-21 06:54 -05:00 | Channel model |
| `f64f9a6` | `f64f9a6a2d5727229a559adbb88f27da5b2bac85` | 2026-09-21 07:00 -05:00 | Analog Tone and generic DCS digit checks |
| `58a7443` | `58a7443c973907098e9d3d01608d10ac4d173dd2` | 2026-09-21 07:19 -05:00 | Exporter and tests |
| `91cfba3` | `91cfba349c059d792eaca2644c5023dc7cdc9242` | 2026-09-21 07:25 -05:00 | Blank-line formatting change |
| `cfa8b8c` | `cfa8b8ceca8f1a44b5ce49e4498632927399c058` | 2026-09-21 07:49 -05:00 | Sample generator/power fallback |
| `3d702c6` | `3d702c640004183133ef58e6a312daa03de45c38` | 2026-09-21 08:01 -05:00 | Web download endpoint |
| `cb1df06` | `cb1df068137f801dcc49cca4d65eabce7a20160e` | 2026-09-21 08:45 -05:00 | Builder template |
| `b31e33f` | `b31e33ffc706812527e515c0f2145c08531fe6d4` | 2026-09-21 13:27 -05:00 | JS multi-channel builder |
| `8a2997c` | `8a2997c6df707cf150453a6a4ab24730e49411f9` | 2026-09-22 15:20 -05:00 | CTCSS browser controls |
| `3004323` | `300432302b80a9d125a04cfe8c700b3600f482bb` | 2026-09-22 15:31 -05:00 | 50-tone HTML list |
| `c1b5986` | `c1b598667a2614ccc625334d2a7fc31b972229da` | 2026-10-06 11:58 -05:00 | DCS HTML controls/list |
| `3c53622` | `3c53622cc8845e4121959c6c00c393f992cd0de6` | 2026-10-06 12:14 -05:00 | DCS polarity |
| `1fbdb4c` | `1fbdb4c3b1fedd0bb054253cc0a2b344566c3a16` | 2026-10-06 12:34 -05:00 | Cross tones and JS tables |
| `9cbbbbd` | `9cbbbbd53f8fe73a1630f877d7f730414d91cd7f` | 2026-10-06 13:53 -05:00 | Tuning/scan |
| `96f7a57` | `96f7a57dd5edcc0f2afbedbd209fb85804c53131` | 2026-10-31 12:51 -05:00 | CSV importer and tests |
| `b5c4180` | `b5c41808e277c01fdeb44bf9441fd1843a7ba5da` | 2026-10-31 15:00 -05:00 | Fixtures, explicit references and matched-tone fixes |
| `19008ee` | `19008eecfa24fbd109217c1d6434da90bd5bd62a` | 2026-10-31 15:34 -05:00 | Compatibility review |
| `1b7a731` | `1b7a731d3a5006a5395d5b5519354c21686cb839` | 2026-11-01 09:49 -06:00 | Shared validators and boundary/DCS tests |
| `aca38e2` | `aca38e20014362118efb0736c5bc7aa735c3064e` | 2026-11-01 10:20 -06:00 | Backup normalization module |
| `6214300` | `62143007fac00121ba03312ff66af38a61f814ff` | 2026-11-01 11:02 -06:00 | Input limits and import review |
| `0903088` | `0903088b3af009d1b73b44d87ea77b5bc6a02dea` | 2026-11-01 11:26 -06:00 | Browser tests and custom-tone duplication fix |

## Historical upstream comparators

Queried GitHub's CHIRP default-branch commit API with `until` timestamps just
before project milestones, then downloaded raw files at the returned full SHAs.
These date-selected revisions are suitable historical comparators. They are
**not evidence that the project author or an assistant accessed those commits**.
No exact development-time upstream revision is established.

| ID | Query cutoff (UTC) / project milestone | Returned upstream commit / recorded committer date |
| --- | --- | --- |
| U1 | 2026-09-21 12:19:09Z, before exporter introduction; returned snapshot also predates the earlier model commits | [`b28df6b3a6b48cbce107f9b70c3cc7aa490dec5d`](https://github.com/kk7ds/chirp/commit/b28df6b3a6b48cbce107f9b70c3cc7aa490dec5d), 2026-09-19 00:03:32Z |
| U2 | 2026-10-06 16:58:28Z, before DCS browser controls | [`73b407369d5291633f64ccd4341b8b588d95c76b`](https://github.com/kk7ds/chirp/commit/73b407369d5291633f64ccd4341b8b588d95c76b), 2026-10-04 15:36:33Z |
| U3 | 2026-10-31 17:51:20Z, before importer; a second query before validation changes at 2026-11-01 15:49:36Z returned the same SHA | [`0b4076d9b19a2a133d11f31546cff8153b39eb89`](https://github.com/kk7ds/chirp/commit/0b4076d9b19a2a133d11f31546cff8153b39eb89), 2026-10-27 03:26:04Z |

The driver and the two upstream test modules are byte-identical across U1–U3.
`chirp_common.py` differs only in an unrelated `match_model` section; its tables,
CSV serialization and split-tone routines compared here are unchanged. Its
source headers and `generic_csv.py` identify Dan Smith and GPL-3.0-or-later;
upstream COPYING supplies GPLv3. The test modules and data files were not assumed
unencumbered merely because they lack the same file header. Whether a specific
adaptation is a covered derivative requires facts and legal assessment beyond
numeric/token matching.

The dependency review's later snapshot `efbbeade947aa4b0acd2da54cb30c1f5f845c14b`
is retained as prior review evidence; it does not establish what was used in
September or October. Historical hashes and immutable file links are included
at the end of this record.

## Specific comparisons and similarities requiring source clarification

### C1. Headers and formatting: interface matches

Project exporter lines 18–39 (original `58a7443` lines 16–37) have the same 21
ordered names as U1/U3
[`Memory.CSV_FORMAT`, lines 398–405](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/chirp_common.py#L398).
The driver maps the active names in
[`CSVRadio.ATTR_MAP`, lines 67–85](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/drivers/generic_csv.py#L67).
CTCSS decimal precision, zero-padded DCS and tuning-step precision correspond
to `Memory.to_csv` at 474–494. These are interoperability details, not enough to
establish copying of implementation. Exact header matches alone are not treated
as suspicious expressive reuse.

The serialization structure differs: CHIRP serializes Memory attributes;
Radio Loadout derives fields from Channel/Tone objects, assigns sequential
locations and uses `csv.writer` and formatting helpers. This difference does
not exclude adaptation. The first export commit already contains the headers
and full tone conversion; it does not record an intermediate source specification.

### C2. Literal tone and tuning tables: exact selection, source unknown

Current browser CTCSS values are the **same 50 values in the same order** as
U1/U3 `TONES` (31–40). Current browser DCS values are the **same 104 values in the
same order** as `DTCS_CODES` (52–63). Their introduction-time HTML lists also
equal the current JS values. The current model's **15 tuning steps equal the
set** in `TUNING_STEPS` (100–105), but Radio Loadout sorts them; CHIRP retains
a historical order that appends 9, 1 and 2.5 after the earlier entries.

These are specific literal-data similarities worth asking about because no
source citation was recorded when the lists appeared. Conventional radio values
and a support-policy list are distinguishable from copied expressive code.
This review did not obtain a manufacturer/standard reference showing the source
actually used for these exact selections. It neither assumes CHIRP was the only
possible source nor decides copyrightability of a particular selection.

### C3. Export tone classification and defaults: structural comparison

Current `_tone_fields` 128–171, and original `58a7443` 114–142, use the broad case
order: no tones; transmit CTCSS only; equal CTCSS; equal DCS; otherwise Cross.
That is also the order of U1/U3
[`split_tone_decode`, 2024–2045](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/chirp_common.py#L2024).
The exporter initializes inactive tone columns with 88.5, zero-padded code 23 and
the two-direction Tone cross spelling. Those choices correspond to CHIRP's
Memory defaults at 287–299. Defaults are CHIRP conventions rather than universal
radio facts, so their source deserves a direct answer.

This is the strongest identified **implementation-structure candidate**, not an
identified copied code fragment. CHIRP mutates a Memory, returns early from
individual cases and assigns relevant attributes afterward. The project formats
tone columns before classifying them, calls `_matching_tones` and returns a
six-value tuple. The project has no matching distinctive upstream explanatory
comment or complete statement block identified in this comparison. That does
not rule out a translation, paraphrase or adaptation of the algorithm.

### C4. Import tone decoding: documented behavioral alignment

Project importer 259–287 uses the receive CTCSS column in both directions for
matched TSQL and the transmit DCS code in both directions for matched DTCS;
Cross at 303–367 uses separate transmit/receive columns and polarity. Compare
U3 [`split_tone_encode`, 2071–2101](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/chirp_common.py#L2071).
The unusual upstream function names describe conversion relative to CHIRP's
Memory model: Radio Loadout's exporter is closer to upstream **decode**, while
its importer is closer to upstream **encode**.

There is affirmative history of a compatibility correction: before `b5c4180`,
the importer could use different transmit/receive CTCSS values in TSQL and a
separate receive DCS code in matched DTCS. That commit changes those cases,
adds deliberately differing inactive values in `tones.csv` rows 3–4, tests them
at compatibility-test lines 239–257, and adds the explicit upstream references.
This supports intentional alignment with CHIRP semantics at that commit. It does
not identify who consulted which revision or whether expressive material was
transcribed. Row-dictionary helpers, normalization, return values and errors
differ from the upstream driver/Memory routines.

### C5. Validation: common acceptance rules, different mechanisms

U3 `VALIDTONE` at 47–48 checks a float in the open 50–300 interval. Shared project
validation at 4–25 enforces that interval, rejects booleans, accepts integers as
numeric input, and rechecks the formatted one-decimal output. The generic Tone
model retains inclusive bounds, which already existed at `f64f9a6`; the stricter
CSV and rounding checks arrive at `1b7a731`. This is a documented behavioral
change, not a byte-identical validator.

U3's `ALL_DTCS_CODES` at 66–69 enumerates 512 three-octal-digit decimal spellings;
the Memory validity map uses it at 340–341. The project tests digit characters
in a formatted string, with explicit Python type rules and JS regex normalization.
That Python approach is already present at `f64f9a6`, then extracted at `1b7a731`.
The browser's 104-code dropdown is therefore distinct from generic accepted DCS
input. Matching the generic domain does not establish copied enumeration code.

The project also validates populated inactive CTCSS cells, corresponding to the
upstream driver assigning/validating each known header (`generic_csv.py` 175–191).
Project tests intentionally distinguish source acceptance from output rounding;
no equivalent copied test-body fragment was identified in the inspected upstream
tone tests. None of these comparisons proves independent derivation.

### C6. Tests and data construction: behavior is not authorship evidence

U3's `tests/unit/test_chirp_common.py` 321–399 enumerates no tone, CTCSS, matched
DCS and Cross cases. Project compatibility tests 72–94 and DCS tests 71–112
cover the same categories, with different parameters, helpers and assertions.
Exhaustive coverage of a format produces expected overlap; the tests' existence
does not establish their source.

Project 100-channel testing at 282–329 reads three project fixtures, varies
locations via multiplication/modulus, advances frequencies, cycles supported
steps/scan/power, and constructs expected Channels. That demonstrates the inputs
are not generated by calling the exporter under test, but their base data and
expected models were introduced in the same commit. It proves a test dependency
relationship, not independence from CHIRP or another external source.

## Fixture origin evidence

All 14 CSV files, their README and `.gitattributes` first appear together at
`b5c4180`; Git blob comparison found no subsequent changes at the reviewed HEAD.
The README's claims are evidence of what the repository says, not a new
author attestation. In particular, “independent” there is relative to Radio
Loadout's exporter. Neither that adjective nor “synthetic” identifies an external
source, permission or creation process.

The dated author statement reports that external sample files were not brought
into development or testing. This is additional recollection about inputs, not
independent evidence of each fixture's generation process or an assistant's inputs.

| Fixture group | Inspectable origin clues | What is not established |
| --- | --- | --- |
| `analog_channels.csv` (6 records) | Nonsequential locations and labeled simplex/repeater/RX/split examples; row 2 uses the earlier project sample's 2M calling name/frequency, and row 5 uses the earlier NOAA example. `examples/generate_chirp_sample.py` already contains those two example identities at `cfa8b8c`. | These overlaps establish earlier examples in this repository, not that the fixture was generated from them or that those examples themselves had no external source. |
| `tones.csv` (14 records) | Four polarity combinations, eight Cross combinations and inactive-column values deliberately different from active values. Test expected models are spelled out at 72–94. | Whether its layout, case selection or comments were manually written, assistant-generated, or adapted from other fixtures. |
| `tuning_scan_power.csv` (15 records) | One record per selected step, patterned frequencies, repeated scan/power cycles and separate test expectations at 96–107. | Source for exact step/power selections; repetitive construction is compatible with several generation methods. |
| `extra_columns.csv` (3 records); `utf8_bom_crlf.csv` (1) | Unicode, quoting, a multiline comment, ignored columns, deliberate BOM/CRLF bytes. `.gitattributes` preserves the latter's bytes. | Who devised the text/edge cases and whether any sample was transformed from an external file. |
| `blank_optional.csv` (3); `missing_headers.csv`; six invalid/unsupported one-record files; `empty.csv` (zero bytes) | Minimal failure cases and blank defaults, introduced alongside tests; malformed frequencies, octal digits and unsupported mode/step are visible in the files. | Minimal or empty content supplies little authorship evidence. Absence of a long distinctive passage is not an origin declaration. |

No committed script generating the original 14 base fixtures was identified in
the introduction patch or scoped history. The existing sample generator creates
a different four-channel export; the later 100-channel test derives data from
the base fixtures. Neither is evidence of how the original base rows were made.

### Bounded historical fixture comparison

At U3, inspected the two relevant upstream unit-test modules and all four CSV
files found in its test tree: `tests/images/Generic_CSV.csv` and the FT3D,
FTM400 and FTM500 RTCSV samples. Parsed their CSV/TSV string literals and files
as **12 datasets / 2,025 data-record occurrences**, including the quoted-header
variant and a headerless TSV literal, preserving quoted fields, Unicode and
multiline cells. Compared complete parsed records, excluding dataset headers,
against all 14 project CSV files. **No whole project data record matched.**

For example, upstream modern CSV test data at `test_csv.py` 21–29 uses different
named channel rows and comments from project `analog_channels.csv` 2–7. The
common calling-frequency value and inactive tone defaults do not identify copied
fixture prose. Upstream test code is unittest-based and exercises CSVRadio/Memory;
the project uses pytest and its own Channel types.

This comparison cannot detect a copied subset of columns, changed names/comments,
reordered/adapted test logic, different CHIRP revisions or other external samples.
It is not a search of all upstream historical files. A row mismatch is not proof
of independently authored fixtures.

## AI assistance and authorship evidence

This provenance record and the preceding licensing review were prepared with
**Codex assistance in this user/assistant session**. The session also records
assistant work on the production documentation change now in the reviewed HEAD;
that is outside the CHIRP implementation's introduction history.

The inspected 45 commit messages and versions of the principal scoped source
files/fixture README contained no explicit ChatGPT, Codex, Copilot,
AI-assistance or generated-by/coauthor declaration. That bounded negative search
is not evidence that no assistant was used. The dated statement above now records
Timothy Thurston's direct authorship and AI assistance during planning and
development. Exact contributions to the historical CHIRP implementation and
fixtures have not been fully reconstructed. The author reports not supplying
CHIRP source to an assistant; this does not establish what an assistant may
otherwise have consulted. Original development chats and notes are reported
unavailable. No model, prompt, generation date, particular assistant input or
component-specific source is inferred from that recollection.

## Questions for the project author

The statement answers the general authorship/AI-use question and records the
author's reported personal source-handling practices. It also establishes that
the original chats and notes are unavailable. The remaining questions are more
specific; answers may be unrecoverable and should be recorded as unknown where
recollection or other evidence does not support them.

1. What can still be reconstructed about the author's and AI assistants' specific
   contributions to the exporter (`58a7443`), model/tone checks (`f64f9a6`),
   importer (`96f7a57`) and fixtures (`b5c4180`), without the original chats/notes?
2. Which particular RepeaterBook pages or other references were used for checking,
   and can any be tied to the 50 CTCSS, 104 DCS or 15 tuning-step selections?
   The present recollection does not identify a source for each list.
3. What was the creation basis for `_tone_fields`' case order/defaults and the
   importer/cross-tone logic? The author reports no personal CHIRP adaptation,
   but individual assistant contributions and inputs remain unreconstructed.
4. When the fixture README and matched-tone fixes were added at `b5c4180`, what
   source revision or installed CHIRP release was consulted or run? Were the
   inactive-field tests based on source reading, experiments, or other examples?
5. How were each group's original CSV rows and expected test models created?
   The author reports bringing in no external sample files; can manual construction,
   assistant generation, an internal generator or another creation process be
   established for specific fixtures without assuming their origins?
6. If future evidence identifies any copied/adapted expressive material, what
   permission/license evidence applies? No such permission is established by
   the current recollection, the project license or a reference link.

The smallest justified next action is to record any further component-specific
recollection or surviving evidence against these commits, explicitly leaving
unrecoverable details unknown rather than requiring unavailable chats or notes.
Then examine any identified source/fragment for applicable obligations or permission needs.
No speculative code rewrite, license change or blanket attribution is justified
by table equality alone. Whether any identified expressive adaptation is
GPL-covered, and how it interacts with Strict, is a separate legal question;
attribution alone is not assumed to resolve it.

## Reproducibility and evidence identifiers

The comparison downloaded public files only and did not upload project source.
Temporary evidence is under
`%LOCALAPPDATA%/Temp/radio-chirp-provenance-myi6748y/`: immutable snapshots,
GitHub tree metadata, comparison JSON and fixture blob/hash records. This cache
is optional review evidence, not an enduring permission/source-delivery service.
The references and checksums below allow retrieval without it.

Useful read-only history commands:

```sh
git log --follow --format=fuller -- src/radio_loadout/exporters/chirp_csv.py
git show 58a7443:src/radio_loadout/exporters/chirp_csv.py
git show b5c4180 -- tests/fixtures/chirp tests/test_chirp_compatibility.py src/radio_loadout/importers/chirp_csv.py
git show 1b7a731 -- src/radio_loadout/dcs.py src/radio_loadout/chirp_csv_validation.py
git log -S CTCSS_FREQUENCIES -- src/radio_loadout/web/static/builder.js
```

The default-branch API queries used
`https://api.github.com/repos/kk7ds/chirp/commits?until=TIMESTAMP&per_page=1`
with the UTC cutoffs above. Comparison scripts parsed literal table assignments
without importing upstream code. They compared current arrays and their original
HTML options, and inspected relevant source functions manually. A supplementary
diagnostic stripped blank/comment lines and outer whitespace from 11 selected
project Python modules/tests against U3's two modules/two test modules; it found
no equal runs of four such lines. A token comparison of original/current
importer/exporter and the two current shared validators against upstream modules
found its longest match in the 21-header literal; the remaining longest matches
were short generic syntax. These diagnostics do not detect renamed/translated
code reliably and are not plagiarism or legal clearance tests. Application tests
were not rerun for this documentation-only task; functional passing tests would
not prove source provenance.

### Upstream file hashes

All hashes are SHA-256 of downloaded file bytes. U3 links are immutable; files
whose hashes are equal across U1–U3 can also be retrieved at the respective SHAs.

| File / snapshot | SHA-256 |
| --- | --- |
| U1 `chirp/chirp_common.py` | `ac01722d05af258ea499d5d5f107e299eccdd674395b5f3cee6424115d1b435a` |
| [U3 `chirp/chirp_common.py`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/chirp_common.py) (also U2) | `8b0436f8865607e678c29a1b30f6373a066e6a2bc3c2f3ee0ae0e5a780798ea8` |
| [U3 `chirp/drivers/generic_csv.py`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/drivers/generic_csv.py) (also U1/U2) | `a43a8209351897cf0321f02b18267c0e473e3e019f1d7fbb3365ee4abe23ad64` |
| [U3 `tests/unit/test_chirp_common.py`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/tests/unit/test_chirp_common.py) (also U1/U2) | `6f60c015c0885fc758eb5266b27c01f8610bd1d45f5e430c4174bff5e4c083b2` |
| [U3 `tests/unit/test_csv.py`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/tests/unit/test_csv.py) (also U1/U2) | `1abe6c773fdf1cce35e86e05ef79d9a1832c8d85a878ced02cb8ad592029d21c` |
| [U3 `COPYING`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/COPYING) (also U1/U2) | `8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903` |
| [U3 `tests/images/Generic_CSV.csv`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/tests/images/Generic_CSV.csv) | `db21f69af6fd62f8225532346c5c7fa78b85f42789adca1d7a7f612db07bbc20` |
| [U3 `tests/unit/rtcsv_ft3d.csv`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/tests/unit/rtcsv_ft3d.csv) | `9fe8cc53173a95446b5659f14b6bbd1b9d40f88477c61417f64b5c43b655132e` |
| [U3 `tests/unit/rtcsv_ftm400.csv`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/tests/unit/rtcsv_ftm400.csv) | `f47c9b60d7c193492825c8b79a065f1c1f6cb7e593d89d80debc01b3297cdfb7` |
| [U3 `tests/unit/rtcsv_ftm500.csv`](https://raw.githubusercontent.com/kk7ds/chirp/0b4076d9b19a2a133d11f31546cff8153b39eb89/tests/unit/rtcsv_ftm500.csv) | `725d51fc854a288eb25bbeb96d2983fb811c54867176c0322af2f01dda5100bd` |
