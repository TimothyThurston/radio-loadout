# Windows CHIRP Generic CSV verification

**Status as of November 12, 2026:** Owner-reported round trip recorded. The
case-by-case Windows verification gate remains open. The scope is file
exchange only, not radio, firmware, driver, or programming verification.

## Evidence to date

- On November 6, 2026, the owner reported completing a full
  Radio Loadout → CHIRP → Radio Loadout round trip on Windows using
  **CHIRP-next `20251205`**. The exact Radio Loadout revision, Windows build,
  inputs, outputs, and channel fields checked were not recorded. The report
  establishes a successful workflow at the reported scope, not a pass for
  every case below or support on other CHIRP builds.
- [CI #20](https://github.com/TimothyThurston/radio-loadout/actions/runs/42284384069)
  passed at `189b92eb63def4b4c1d205507e4ee15a71d51d8f`. The
  [CSV fixture tests](../tests/test_chirp_compatibility.py) check expected
  analog channel values and importer/exporter round trips. CI does not open
  CHIRP; this is independent evidence about Radio Loadout, not a CHIRP result.
- No artifacts from the owner's original run are required or requested. Use any
  field-level observations already available and run only the missing cases
  on synthetic data. Do not attach personal loadouts or radio images.

## Bounded tone-conversion contract — 2026-11-26

This prospective verification at `189b92eb63def4b4c1d205507e4ee15a71d51d8f`
does not reconstruct creation sources or establish fixture provenance. References
are the already recorded CHIRP snapshot
[`0b4076d9b19a2a133d11f31546cff8153b39eb89`](https://github.com/kk7ds/chirp/commit/0b4076d9b19a2a133d11f31546cff8153b39eb89),
its [split-tone behavior](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/chirp_common.py#L2012)
and [CSV field parsing](https://github.com/kk7ds/chirp/blob/0b4076d9b19a2a133d11f31546cff8153b39eb89/chirp/drivers/generic_csv.py#L167).
They are comparison references, not known historical development inputs or a
verification of the installed Windows CHIRP build. That application gate remains open.

In this table, `C(x)` means CTCSS Hz, `D(x,p)` a three-octal-digit DCS code with
polarity `p` (`N` normal, `R` reverse), and `—` no tone in that direction.
An arrow in CrossMode describes **tone directions**, not RF transmit enablement.

| Intended TX / RX tones | CSV meaning when imported; active fields | Radio Loadout canonical export for these example values |
| --- | --- | --- |
| — / — | Empty Tone; no active tone values | Empty Tone; inactive cells use the project defaults below |
| C(100.0) / — | Tone; rToneFreq | Tone, rToneFreq=100.0 |
| — / C(110.9) | Cross, `->Tone`; cToneFreq | Same mode/direction, cToneFreq=110.9 |
| D(001,R) / — | Cross, `DTCS->`; DtcsCode, first polarity | Same mode/direction, DtcsCode=001, polarity=RN |
| — / D(777,R) | Cross, `->DTCS`; RxDtcsCode, second polarity | Same mode/direction, RxDtcsCode=777, polarity=NR |
| C(100.0) / C(100.0) | TSQL uses cToneFreq in both directions | TSQL; both CTCSS cells=100.0 |
| C(100.0) / C(110.9) | Cross, `Tone->Tone`; separate CTCSS cells | Cross with those separate values |
| D(023,N) / D(023,R) | DTCS uses DtcsCode in both directions; independent polarities | DTCS; both DCS cells=023, polarity=NR |
| D(001,R) / D(777,N) | Cross, `DTCS->DTCS`; separate codes/polarities | Cross; DtcsCode=001, RxDtcsCode=777, polarity=RN |
| C(100.0) / D(777,R) | Cross, `Tone->DTCS`; rToneFreq and RxDtcsCode | Cross; those active values, polarity=NR |
| D(001,R) / C(110.9) | Cross, `DTCS->Tone`; DtcsCode and cToneFreq | Cross; those active values, polarity=RN |

**Format interpretation versus project policy:** active-column meanings and
polarity directions above are the comparison contract. Choosing a canonical
equivalent Tone/TSQL/DTCS spelling from Cross, sequential locations, one-decimal
CTCSS and placeholder cells is Radio Loadout serialization policy, not proof that
all CHIRP builds/radio drivers preserve those spellings. Equal DCS codes remain
matched even when their polarities differ. Non-DCS directions export polarity N.
RF receive-only channels must keep Duplex=off and no transmit frequency through
import/export, independently of receive-tone filtering.

- **Inactive fields:** their values are not additional Channel tone settings.
  When cToneFreq is populated, TSQL ignores rToneFreq after validation; matched DTCS ignores
  RxDtcsCode after validation. Populated CTCSS cells must be numeric and inside
  the strict CSV interval even when inactive. Every populated DtcsCode and
  RxDtcsCode cell now uses the shared DCS parser regardless of Tone/CrossMode;
  invalid codes are rejected with field/row context. Empty optional cells remain
  allowed; the existing active-field requirements still apply.
- **Project defaults:** no Tone means no tones; omitted/blank polarity is NN;
  blank/omitted Mode/TStep/Skip use FM/5 kHz/normal scan. Missing power is None on
  import and 5 W on export. Inactive exported CTCSS cells are 88.5, DCS cells 023,
  and CrossMode is `Tone->Tone` unless Cross requires another direction. An active
  tone value is required, with the documented TSQL single-column fallback:
  cToneFreq if populated, otherwise rToneFreq. Cross RX DCS needs RxDtcsCode;
  matched DTCS can omit it because DtcsCode supplies both directions. These
  fallbacks/placeholders are not claims of universal radio defaults.
- **Invalid/rounding:** malformed active tones, unsupported modes, missing active
  values and polarity outside NN/NR/RN/RR are errors. Generic DCS uses octal-digit
  spellings 000–777, not just the 104-item menu. The universal Tone model allows
  CTCSS endpoints 50/300, but CSV requires 50 < value < 300, including the emitted
  rounded cell: 50.04 and 299.96 can import but cannot export; 50.06 exports 50.1
  and 299.94 exports 299.9. Do not round an invalid input into acceptance.

Coverage uses public `import_chirp_csv` / `export_chirp_csv` entry points and
existing HTTP tests; expectations are literal values, not results generated by
the other converter. New cases live in
[test_tone_conversion_contract.py](../tests/test_tone_conversion_contract.py).

| Coverage | Existing tests retained; bounded additions |
| --- | --- |
| Mode/direction combinations and complete serialized tone cells | `test_chirp_compatibility.py:test_fixture_import_and_round_trip` supplies explicit model expectations and round trips; new `test_export_tone_cells_from_models` checks all seven tone cells from separately constructed inputs. Existing fixtures are not independent historical provenance evidence. |
| Independent DCS polarity and code domain | `test_dcs_compatibility.py:test_matched_dcs_import_builder_review_and_export`, `test_cross_dcs_codes_and_independent_polarities_survive`, invalid type/text cases; no duplicate polarity matrix added. |
| Import separately, normalization and RF receive-only | Existing importer/fixture tests; new `test_equivalent_cross_spelling_has_literal_import_and_export_expectations` and `test_receive_only_receive_filter_survives_both_directions` specify expected models and CSV cells separately before round-trip checks. |
| Optional versus required fields | Existing matched/inactive-field and blank-default tests; new `test_minimal_csv_import_defaults_are_explicit` and `test_missing_active_values_are_rejected` close minimal-input/missing-active gaps. |
| Inactive values, invalid values, rounding | Existing `test_chirp_ctcss_boundaries.py` covers populated inactive CTCSS, source/output boundaries and explicit rounded cells; `test_import_reporting_limits.py` covers precision-loss notices. New `test_import_rejects_invalid_inactive_dcs_fields` checks the previously uncovered reference-validation case. |

Any contract mismatch is recorded before an application change; failing assertions
are not relaxed into a passing policy. No importer/exporter rewrite or provenance
clearance follows from this verification.

**Mismatch found, then scoped correction authorized (2026-11-26).** Before the
correction, `import_chirp_csv` accepted the following non-octal inactive values:

```csv
Name,Frequency,Tone,DtcsCode
SYNTH,146.520000,,089
```

```csv
Name,Frequency,Tone,rToneFreq,RxDtcsCode
SYNTH,146.520000,Tone,100.0,089
```

The initial verification had **946 passed, 3 skipped, 2 failed**; both new
rejection assertions failed with **DID NOT RAISE ValueError**. The owner then
authorized only validation of all populated DCS cells. A preflight check in
`_parse_tones` now calls the existing shared parser and adds the existing field/
row context; no default substitution, tone-mapping or exporter change is made.
Both original assertions remain intact. Additional focused tests cover both
fields across inactive/active/matched/cross modes, row-3 errors, empty optional
cells and generic 000/001/023/777 values. This correction is not a result observed
in Windows CHIRP and does not resolve historical provenance. Windows CHIRP
application checks remain pending.

## Run the missing checks

1. Keep the radio disconnected. Use a disposable browser profile and a
   temporary folder; don't replace an existing draft or open a radio image.
   Record the date, Windows build, the exact CHIRP build shown in About, and
   the Radio Loadout revision (`git rev-parse HEAD`).
2. In Radio Loadout, select the Generic review target. Import a synthetic
   fixture, review any normalization or loss notice before accepting it, run
   **Review Compatibility**, and **Generate CHIRP CSV**. Use the generated
   file to test Radio Loadout → CHIRP: **File → Open** in CHIRP, review the
   Generic CSV document, and save a separate CSV copy. Close/reopen the copy
   to check what persisted. The [CHIRP CSV guide](https://chirpmyradio.com/projects/chirp/wiki/CSV_HowTo)
   describes opening CSV as a generic document.
3. Import the CHIRP-saved copy in Radio Loadout and check the values against
   the original. To test CHIRP → Radio Loadout independently, open the
   original synthetic fixture in CHIRP (not the Radio Loadout export), save
   a new copy, then import it, generate a fresh CSV, and reopen it in CHIRP.
   If CHIRP rejects a raw fixture, note that before trying the normalized
   Radio Loadout output. A pass in one direction does not imply a pass in the
   other.
4. Record the result for each direction. Keep input/output CSVs separate in
   the temporary folder. Optionally record SHA-256 with
   `Get-FileHash -Algorithm SHA256 -LiteralPath .\case.csv` in PowerShell.
   A concise results summary is enough; no screenshots or files are required.

Start with `analog_channels.csv`, `tones.csv` and
`tuning_scan_power.csv` under [tests/fixtures/chirp](../tests/fixtures/chirp/).
Test only the rows relevant to the case. The fixture list is a starting point,
not a claim that the installed CHIRP build accepts each fixture.

## Case matrix

| ID | Synthetic input | What to compare after saving and reopening |
| --- | --- | --- |
| A1 | `2M CALL`, `PLUS RPT`, `MINUS RPT` in `analog_channels.csv` | RX/TX in MHz: 146.520/146.520, 444.500/449.500, 146.940/146.340. Compare effective TX, not just the offset cell. |
| A2 | `SPLIT` in `analog_channels.csv` | 145.000 RX and 435.000 TX. Radio Loadout normalizes the absolute split to a signed offset; the effective TX must not change. |
| A3 | `NOAA 7`, `AIR RX`, and the generated ISS receive-only pack | NFM, AM and FM respectively. Receive-only must stay off for TX; a silently enabled TX is a failure. |
| T1 | `TX CTCSS`, `TSQL` in `tones.csv` | Encode-only 100.0 Hz versus matched 110.9 Hz. Check active tone fields, not unused defaults. |
| T2 | Matched DCS and cross-tone rows in `tones.csv` | DCS codes, all four polarity combinations, and each active TX/RX tone and direction, including different tones or codes. Equivalent mode spelling can normalize. |
| T3 | Generic DCS example below, tested one row at a time if necessary | Check `023`, `001`, `000`, `777`, and separate TX/RX DCS. Record rejection or substitution in the tested CHIRP build. Do not infer support from Radio Loadout accepting a code. |
| O1 | `tuning_scan_power.csv` and `blank_optional.csv` | Tuning step, normal/skip/priority scan, and numeric power. Formatting such as `5W` versus `5.0W` is equivalent. Unspecified power may be defaulted to 5 W by Radio Loadout. |
| O2 | `extra_columns.csv`, `utf8_bom_crlf.csv`, and the sparse locations in `analog_channels.csv` | Row count, names, file/channel order, Unicode, quotes, commas, and multiline comments. Record any CHIRP sort by Location separately from Radio Loadout's sequential renumbering. Unknown columns are not preserved in Radio Loadout; review the warning. |
| R1 | Cancel an import with loss warnings; import `invalid_dcs.csv` | A cancelled or invalid import must preserve the current browser draft. This is a Radio Loadout recovery check, not CHIRP behavior. |

For T3, save the following as UTF-8 text in the temporary folder. Keep the header
when isolating a row; one rejected row can obscure the results for the others.

```csv
Location,Name,Frequency,Duplex,Offset,Tone,rToneFreq,cToneFreq,DtcsCode,DtcsPolarity,RxDtcsCode,CrossMode,Mode,TStep,Skip,Power,Comment
0,DCS 023,146.520000,,0,DTCS,88.5,88.5,023,NN,023,Tone->Tone,FM,5,,5W,Conventional control case
1,DCS 001,146.530000,,0,DTCS,88.5,88.5,001,NR,001,Tone->Tone,FM,5,,5W,Leading zero code
2,DCS 000,146.540000,,0,DTCS,88.5,88.5,000,RN,000,Tone->Tone,FM,5,,5W,Zero code
3,DCS 777,146.550000,,0,DTCS,88.5,88.5,777,RR,777,Tone->Tone,FM,5,,5W,Upper generic code
4,DCS CROSS,146.560000,,0,Cross,88.5,88.5,777,RN,001,DTCS->DTCS,FM,5,,5W,Separate transmit and receive codes
```

## Record and close the gate

Each row and direction is **pending** until observed. Compare channel semantics,
not byte-identical CSV. Use **pass**, **equivalent normalization**,
**unsupported**, **unexpected change**, or **not run**. A missing row, changed
active tone, wrong effective TX, or lost TX-disable is not a normalization.
An explicitly unsupported edge case can be excluded from the release claim;
an unexplained change on an advertised workflow needs investigation.

```text
Date / Windows build:
CHIRP build / Radio Loadout commit:
Case ID and direction:
Input fixture / output name:
Result:
Difference or error (if any):
```

When the supported analog workflow passes both directions, record the exact
build and verified cases here and narrow README claims to that scope. If an
issue is reproduced, add a targeted regression before changing runtime behavior.
No device support, writes, or successful reception are inferred from this gate.
