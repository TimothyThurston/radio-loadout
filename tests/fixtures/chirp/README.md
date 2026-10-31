# CHIRP Generic CSV compatibility fixtures

These are small, synthetic fixtures written independently of Radio Loadout's
exporter. They exercise the analog subset supported by V1; they are not exports
captured from physical radios.

| Fixture | Coverage |
| --- | --- |
| `analog_channels.csv` | Simplex FM, positive and negative offsets, receive-only NFM and AM, absolute split transmit frequency, nonsequential locations |
| `tones.csv` | Transmit CTCSS, TSQL, matched DCS with NN/NR/RN/RR polarity, all eight CHIRP cross-tone combinations |
| `tuning_scan_power.csv` | All 15 supported tuning steps, normal/skip/priority scanning, seven power levels, comments |
| `extra_columns.csv` | Additional CHIRP and vendor columns, Unicode, quoted commas and quotes, multiline comments, file ordering |
| `blank_optional.csv` | Empty optional cells, default FM/5 kHz/normal DCS polarity, empty receive DCS code |
| `utf8_bom_crlf.csv` | Actual UTF-8 BOM and CRLF bytes, Unicode and quoted comments; `.gitattributes` preserves the bytes |
| `missing_headers.csv`, `invalid_frequency.csv`, `unsupported_mode.csv`, `invalid_offset.csv`, `invalid_ctcss.csv`, `invalid_dcs.csv`, `unsupported_tuning_step.csv`, `empty.csv` | Rejected input, including an actual zero-byte file |

`tests/test_chirp_compatibility.py` checks independently specified model values
before round-tripping each valid fixture. The deterministic 100-channel test
combines fixture rows and varies names, frequencies, location numbers, power,
scan behavior, tuning steps, and comments.

Round-trip comparisons concern supported channel semantics, not byte-identical
CSV. File order is preserved; source Location numbers are replaced with sequential
export locations. Unknown columns and inactive tone fields are not model data.
An unspecified power remains `None` on import and becomes 5 W on export, preserving
the exporter's existing default. Cross-mode spellings can canonicalize to Tone,
TSQL, or DTCS when their transmit and receive settings allow it.

CHIRP's Generic CSV header mapping is defined in
[`generic_csv.py`](https://github.com/kk7ds/chirp/blob/master/chirp/drivers/generic_csv.py).
Tone semantics follow `split_tone_encode` in
[`chirp_common.py`](https://github.com/kk7ds/chirp/blob/master/chirp/chirp_common.py):
TSQL uses `cToneFreq` for both directions, matched DTCS uses `DtcsCode` for both,
and Cross uses separate transmit and receive fields.
