# Radio Loadout JSON backup format

Backups are UTF-8 JSON documents downloaded as `radio_loadout_backup.json`:

```json
{
  "format": "radio-loadout",
  "version": 1,
  "channels": [
    { "name": "LEGACY EXAMPLE", "receive_frequency_mhz": "146.52" }
  ]
}
```

The optional UTF-8 BOM is accepted. The document must be an object with exactly
`format`, `version`, and `channels`. The format identifier is the string
`radio-loadout`; version is the integer `1`, not the string `"1"`. Other versions
(including 999), unknown document fields, and malformed JSON are rejected.
`channels` must be a non-empty array of channel objects in builder order.

The executable schema is in
[`backup-format.js`](../src/radio_loadout/web/static/backup-format.js). It does not
read the live HTML, construct cards, use network services, or consult the CSV
export validator. Future UI changes must explicitly update the format contract
and its fixtures, rather than changing backup validation implicitly.

## Channel fields and legacy defaults

Version 1 stores form-control snapshots. Every field is a **string** except
`receive_only`, which is a **boolean**. JSON numbers, nulls, arrays, and objects
are not accepted as substitutes. `"false"` is not a boolean. Newly exported
backups contain every builder field through the existing `getCardDraft()`
serializer. Older backups may omit optional fields; only omission applies a
default. An explicitly supplied empty string is retained, not replaced.

| Field | Type / allowed values | Default when omitted |
| --- | --- | --- |
| `name` | Single-line string; empty allowed | Required key |
| `receive_frequency_mhz` | Numeric draft string; empty allowed | Required key |
| `transmit_frequency_mhz` | Numeric draft string; empty allowed | `""` |
| `receive_only` | Boolean | `false` |
| `mode` | `"FM"`, `"NFM"`, `"AM"`, or empty | `"FM"` |
| `power_watts` | Numeric draft string; empty allowed | `"5.0"` |
| `tone_mode` | `"none"`, `"tone"`, `"tsql"`, `"dtcs"`, `"cross"`, or empty | `"none"` |
| `tone_frequency_hz` | Numeric draft string; empty allowed | `"100.0"` |
| `dcs_code` | DCS draft string; empty allowed | `"23"` |
| `dcs_polarity` | `"NN"`, `"NR"`, `"RN"`, `"RR"`, or empty | `"NN"` |
| `transmit_tone_mode` | `"none"`, `"ctcss"`, `"dcs"`, or empty | `"none"` |
| `transmit_ctcss_frequency_hz` | Numeric draft string; empty allowed | `"100.0"` |
| `transmit_dcs_code` | DCS draft string; empty allowed | `"23"` |
| `transmit_dcs_polarity` | `"N"`, `"R"`, or empty | `"N"` |
| `receive_tone_mode` | `"none"`, `"ctcss"`, `"dcs"`, or empty | `"none"` |
| `receive_ctcss_frequency_hz` | Numeric draft string; empty allowed | `"100.0"` |
| `receive_dcs_code` | DCS draft string; empty allowed | `"23"` |
| `receive_dcs_polarity` | `"N"`, `"R"`, or empty | `"N"` |
| `tuning_step_khz` | String for 1, 2.5, 5, 6.25, 9, 10, 12.5, 15, 20, 25, 30, 50, 100, 125, 200; or empty | `"5"` |
| `scan_behavior` | `""` (normal), `"S"` (skip), `"P"` (priority) | `""` |
| `comment` | Single-line string; empty allowed | `""` |

Numeric draft strings contain a finite decimal number, optionally negative and
optionally using scientific notation, or are empty. Hexadecimal, `NaN`, infinity,
and arbitrary nonnumeric text are rejected. The grammar is
`^-?(?:\d+|\d*\.\d+)(?:[eE][+-]?\d+)?$`. Single-line text cannot contain CR or LF;
the current text inputs cannot restore those characters without losing them.
Draft names and comments have no backup-specific length restriction.

DCS draft strings use one to three digits from 0–7. Conventional and nonstandard
codes, including `023`, `001`, `000`, and `777`, are supported. Codes normalize to
their integer-string spelling (`"023"` becomes `"23"`) and are displayed/exported
with three digits. Surrounding DCS whitespace is ignored. Invalid digits,
fractions, signs, and invalid input types are rejected. The same JavaScript
normalizer is used for schema validation and card population.

Equivalent numeric selections can canonicalize: `"5.00"` becomes tuning step
`"5"`, and CTCSS `"100"` can select the existing `"100.0"` option. Numeric meaning
is preserved. CTCSS values with additional precision get an exact custom option;
restoration does not round them to one decimal place. Independent DCS polarities,
the tone preset, inactive tone fields, scan settings, comments, and channel order
are retained. A saved transmit frequency is retained even while receive-only
disables that input; export still treats that channel as receive-only.

## Draft validity versus export readiness

A backup is an editable draft, not a promise that the loadout can be exported.
Blank names/frequencies, missing active tones, empty selections, zero or negative
numeric values, unfinished cross-tone configuration, and CTCSS values that would
fail CHIRP validation can be backed up and restored. Backup validation checks
types, representable values, and structure; it does not apply completed-channel
requirements, HTML min/max/step/maxlength constraints, or CHIRP rounding rules.

**Review Compatibility** and CSV generation continue to apply the existing form,
model, and exporter checks. Generic CHIRP compatibility does not guarantee support
by every physical radio.

## Unknown fields and atomic restoration

Unknown fields in either the document or any channel are rejected with the field
name and, for channel fields, the channel number. This includes prototype-like
keys such as `__proto__`. They are not silently discarded. Keep an unsupported
backup intact and use a version of the application that understands its fields.

Every channel is validated and missing optional fields are filled in memory
before card population starts. Existing card functions build a detached
replacement, then swap it into the builder. Only successful restoration saves
the draft to local storage. Parse/validation failures leave the current cards and
saved draft unchanged and display an explanatory error.

Fixtures under [`tests/fixtures/backups`](../tests/fixtures/backups) include an
existing version-1 export, complete settings, unfinished drafts, missing legacy
optionals, unknown fields, version 999, malformed structures, invalid types, and
intentionally invalid JSON. Behavioral tests cover import/export round trips,
polarity and nonstandard DCS preservation, no partial replacement, and unchanged
autosave on failure. Browser tests use a simulated DOM; they do not exercise
native browser download dialogs or physical radios.
