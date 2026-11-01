# CHIRP import review and resource limits

## Import APIs

`import_chirp_csv(text)` still returns an ordered `list[Channel]` and raises a
validation error for malformed or unsupported data. Call
`import_chirp_csv_detailed(text)` for a `ChirpImportResult` with the same channels,
source CSV row numbers, and `report()` metadata. Both APIs enforce input bounds.

`POST /imports/chirp.csv` returns `channels` in the existing builder format plus
an `import_report`:

```json
{
  "requires_confirmation": true,
  "loss_count": 1,
  "omitted_messages": 0,
  "messages": [{
    "kind": "loss",
    "row_number": 2,
    "channel_index": 0,
    "channel_name": "LOCAL",
    "field": "Bank",
    "message": "Unsupported column 'Bank' contains data that will be discarded."
  }]
}
```

Row numbers identify logical CSV records (the header is row 1). A quoted record
containing newlines is one record; row numbers need not equal physical text-file
line numbers. Channel indexes are zero-based; the interface displays channel
numbers starting at 1. Channels remain in file order.

Report categories distinguish:

- **Normalization:** equivalent representation, such as an absolute split
  frequency exported as an offset, matched-tone semantics, or an equivalent
  Tone/TSQL/DTCS/Cross spelling. These do not require confirmation.
- **Default:** absent power becomes 5 W in the builder and on export; absent
  mode/tuning step use FM/5 kHz, and absent active DCS polarity uses NN. Missing
  data is reported as a default, not as the loss of a supplied value.
- **Loss:** non-empty unsupported columns are discarded, original Location
  numbers differ from the sequential export locations, source precision changes
  when frequencies become whole Hz or tones/power are exported, or surrounding
  name/comment whitespace is removed. These require confirmation.

Empty or whitespace-only unsupported cells do not produce discard warnings.
Original Locations are not used to sort channels: export assigns 0, 1, 2, etc.
Blank Locations receive a normalization note; numerically equivalent zero padding
is normalization, while a changed Location number is loss. Unsupported non-empty
columns include vendor metadata and unsupported digital-call columns even if
their headers appear in the Generic CSV header.

Frequency and power comparisons use source decimal text and the actual numeric
output precision. For CTCSS and power, the report explains changes on later CSV
export; the imported model/builder retain their available precision. A value
that cannot be exported safely may still be imported as an editable draft and
must then be corrected through compatibility review. No radio-specific limits
or invented mappings (for example, Power `High` to watts, or USB to FM) are used.
Unsupported modes/tones remain errors. The current builder cannot represent
multiline names or comments, so the web import explicitly rejects them instead of
silently joining or stripping lines. The Python CSV APIs still support them.
Existing builder name/comment validation also remains in force, with source-row
context on conversion errors.

## Reviewing and applying imports

The server parses and validates the complete CSV and every builder conversion
before returning channels. The browser renders the report using `textContent`.
Imported names, column names, messages, and filenames are never inserted as HTML.

An import with no meaningful loss is applied immediately, with normalization and
default notes visible. An import with loss remains pending until **Replace
channels with reviewed import** is selected. **Cancel import** leaves cards and
autosave unchanged. Confirmation uses a captured copy of the reviewed result;
changing the selected file does not change what will be applied. Starting another
import supersedes the previous pending result. Stale in-flight responses cannot
apply after cancellation or a newer import.

Card construction continues to use the existing detached rendering functions and
draft serializer. Errors restore original card nodes and the previous saved draft;
storage failures are not reported as successful imports. JSON backup restoration
uses the same application/rollback path. Browser storage must be available for a
successful restore. Native storage and download behavior are not covered by the
simulated-DOM tests.

Reports are bounded. If messages are omitted, the total loss count still requires
confirmation, and the interface tells the user to inspect the original CSV. No
unsupported column cell values are copied into the report; row/column identifiers explain
what would be lost. Keep the original CSV if unsupported metadata is needed.

## Central policy and practical defaults

The single policy file is
[`input-limits.json`](../src/radio_loadout/web/static/input-limits.json), loaded by
[`input_limits.py`](../src/radio_loadout/input_limits.py) and embedded as JSON in
the builder page. Change it at deployment time, restart the application, and
reload the builder. Do not edit limits independently in Python or JavaScript.

| Limit | Default | Enforcement |
| --- | ---: | --- |
| CSV upload bytes | 2,097,152 (2 MiB) | Browser before upload; server while reading actual bytes, before UTF-8 decoding; Python text importer checks UTF-8 byte size |
| JSON backup bytes | 4,194,304 (4 MiB) | Browser before reading a native File, and again before parsing; generated backup files are bounded too |
| Submitted `channels_json` bytes | 4,194,304 (4 MiB) | Browser before review; server before JSON/model construction on review and export |
| CSV data records | 5,000 | Importer, excluding header and including blank records |
| Channels | 2,000 | Importer, submitted review/export JSON, direct exporter, browser imports/backups/review |
| Upload read chunk | 65,536 bytes (64 KiB) | Server reads at most this much, and at most remaining allowance plus one byte |
| Report messages | 1,000 | Additional messages counted, without clearing the confirmation requirement |
| Report text per value | 160 characters | Longer channel names, field names, and messages are explicitly abbreviated with an ellipsis |

The existing deterministic 100-channel workflow remains within these limits.
These are application resource policies, not physical-radio memory limits.
Equality with a limit is permitted; exceeding it is rejected. Server byte/row/
channel policy failures return HTTP 413. Invalid settings or CSV return 422;
malformed multipart forms may be rejected by the framework with 400. Review
still returns a structured compatibility report for ordinary invalid channel data.

Review and export accept the same `channels_json` form field in either multipart
or URL-encoded requests. Their per-request field parser is configured to the
application limit, allowing up to three encoded bytes per decoded UTF-8 byte for
URL encoding. The decoded UTF-8 byte limit is checked afterward. OpenAPI retains
the form-field request schema. No process-global CSV settings are changed.
Python's CSV parser can independently reject a very large individual field using
its existing parser limit; such failures receive a clear CSV validation error.

## Deployment and proxy limits are still required

The application byte limits are not complete HTTP-body or denial-of-service
protection. FastAPI/Starlette parse multipart uploads and may spool files to disk
before an endpoint reads its UploadFile. URL-encoded form parsing, multipart
headers, extra parts, and encoding overhead also consume resources before the
logical field checks run. Backup files are browser-local and have no upload
endpoint; the server is authoritative for requests sent to it, not local files.

Configure a reverse proxy or ASGI ingress to bound total request body size,
concurrent connections/requests, read timeouts, multipart counts/header sizes,
and temporary-upload storage. A total-body ceiling such as 16 MiB accommodates
the current 4 MiB decoded JSON limit with worst-case URL-encoding overhead;
choose a deployment-specific ceiling and test both form encodings. Apply rate
limits and worker/resource quotas where appropriate. No proxy settings or
process-global CSV field limits are changed by this feature.
