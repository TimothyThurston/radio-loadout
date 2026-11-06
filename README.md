# Radio Loadout

> Build your channels once. Load them anywhere.

Radio Loadout is a browser-first radio channel planning and configuration export project. It lets users create organized channel loadouts through a guided web interface and download them as CHIRP-compatible CSV files.

The long-term goal is to provide one radio-independent channel plan that can eventually be exported for CHIRP, DMR codeplug tools, and selected manufacturer programming applications.

## Project status

Radio Loadout is currently in early development, but its analog channel builder is functional.

The current version includes:

- A working browser-based channel builder
- CHIRP Generic CSV downloads and imports
- Portable Radio Loadout JSON backup and restore
- CHIRP Generic CSV compatibility reviews
- Analog tone and repeater configuration
- Browser draft saving
- Verified channel presets
- Automated model, exporter, and web tests
- Automated tests for model validation, CHIRP import/export, compatibility reviews, and web endpoints

Radio Loadout is not yet considered a production-ready release. Generated files should be reviewed and tested with backups before programming a radio.

## Current features

### Browser channel builder

Users can:

- Add multiple channels
- Edit existing channels
- Remove channels
- Duplicate channels
- Move channels up or down
- Configure simplex channels
- Configure repeater channels
- Create receive-only channels
- Add comments
- Download the complete loadout as one CHIRP CSV file

### Supported analog modes

- FM
- NFM
- AM

The internal model also represents DMR channels, but DMR export is not implemented yet.

### Frequency and transmit settings

Each channel can include:

- Channel name
- Receive frequency
- Transmit frequency
- Repeater offset
- Receive-only status
- Transmit power
- Tuning step
- Scan behavior
- Comment

### Tone support

The builder supports:

- No tone
- Transmit CTCSS tone
- CTCSS tone squelch
- Matched DCS/DTCS
- DCS polarity
- Independent transmit and receive tones
- Advanced cross-tone configurations

The CHIRP exporter maps these settings into the appropriate generic CSV fields.

Generic DCS support accepts integer codes whose three-digit spelling contains
only digits 0–7, including `023`, `001`, `000`, and `777`. Codes are stored as
integers (for example, 23) and exported with leading zeros (`023`). Booleans,
floats, negative values, and digits 8 or 9 are rejected. Conventional codes remain
the default dropdown choices; valid imported or restored codes outside that list
receive a selectable option labeled “generic.” JSON backups preserve these codes
and independent TX/RX polarity settings. Generic acceptance does not guarantee
that a physical radio supports the code; radio-specific restrictions remain separate.

### Scan behavior

Channels can be configured for:

- Normal scanning
- Scan skip
- Priority scan

### Automatic draft saving

The builder automatically saves the current channel loadout in the browser using local storage.

Saved drafts are restored when the builder is reopened. Users can also clear the saved draft and start again.

Draft saving is currently local to the browser and is not synchronized between devices.

### Portable JSON backups

**Export Backup** downloads a version-1 `radio_loadout_backup.json` containing the
complete draft, including unfinished channels and inactive tone controls.
**Import Backup** validates the entire file before replacing cards and autosaving
the restored draft. Missing optional legacy fields receive explicit historical
defaults. Unknown fields, unsupported versions, malformed data, and wrong types
produce clear errors without changing existing cards or the saved draft.

The schema is independent of HTML controls. Draft restoration is separate from
CSV export readiness: unfinished settings can be restored and corrected using
**Review Compatibility**. See the [backup format contract](docs/backup-format.md)
for field types, defaults, allowed values, normalization, and fixture coverage.

### CHIRP CSV import review

CSV imports show defaults and expected normalization separately from information
loss. Unsupported non-empty columns, reassigned Location numbers, and meaningful
precision changes require confirmation before replacing channels. Cancelling or
failing an import leaves current cards and autosave unchanged. Confirmation
applies the captured reviewed data, even if another file is selected afterward.

Central defaults permit 2 MiB CSV files, 4 MiB JSON backups/submitted channel JSON,
5,000 CSV data records, and 2,000 channels. Browser checks match the server policy;
the server reads uploads in bounded chunks and enforces request limits. These
are application limits, not radio capabilities. See [import reporting and input
limits](docs/imports-and-limits.md) for detailed API fields, normalization/loss
rules, exact boundaries, bounded reports, and required deployment/proxy limits.

### Channel presets

#### NOAA Weather

The NOAA Weather preset adds all seven U.S. weather-radio channels:

| Channel | Frequency |
| --- | ---: |
| NOAA 1 | 162.400 MHz |
| NOAA 2 | 162.425 MHz |
| NOAA 3 | 162.450 MHz |
| NOAA 4 | 162.475 MHz |
| NOAA 5 | 162.500 MHz |
| NOAA 6 | 162.525 MHz |
| NOAA 7 | 162.550 MHz |

These channels are configured as receive-only NFM channels with a 25 kHz tuning step.

#### Amateur Calling

The Amateur Calling preset adds three national simplex calling frequencies:

| Channel | Frequency |
| --- | ---: |
| 2M CALL | 146.520 MHz |
| 1.25 CALL | 223.500 MHz |
| 70CM CALL | 446.000 MHz |

Preset loading avoids adding another copy of a frequency already present in the builder.

## CHIRP export

Radio Loadout currently exports analog channels using CHIRP’s generic 21-column CSV format.

The exporter supports:

- Channel locations
- Names
- Receive frequencies
- Simplex and repeater operation
- Positive and negative offsets
- Receive-only channels
- FM, NFM, and AM
- CTCSS tones
- DCS/DTCS tones
- DCS polarity
- Cross tones
- Tuning steps
- Scan behavior
- Transmit power
- Comments

Unsupported DMR channels are explicitly rejected instead of producing a file that only appears valid.

### Compatibility review

Select **Review Compatibility** to check the current loadout against the CHIRP
Generic CSV exporter. The report identifies each channel by number and name and
shows informational notes, warnings, and errors. Warnings permit export; errors
must be fixed first. Editing, reordering, adding, removing, or importing channels
marks the report as outdated. Generating CSV also requests a current review, and
the download endpoint enforces compatibility independently of the browser.

Compatible with CHIRP Generic CSV does not guarantee support by every radio.
This review adds no radio-specific frequency ranges, name lengths, or memory
counts. It can warn about default power and precision lost during CSV formatting.
CHIRP CTCSS values must be strictly above 50.0 Hz and below 300.0 Hz. Review and
export also reject values whose one-decimal CSV representation reaches either
boundary. Intermediate values are supported, including values outside the
builder's conventional tone list. Import validates populated source CTCSS cells
against the same open interval; an interior value can be imported yet require
correction before export if one-decimal rounding would reach a boundary.

`POST /validation/chirp.csv` accepts the same `channels_json` form field as
`POST /downloads/chirp.csv`. It returns `target`, `compatible`, `channel_count`,
and `issues`. Each issue contains `severity` (`info`, `warning`, or `error`),
`channel_index` (zero-based, or null for a loadout issue), `channel_name`, `field`,
and `message`. Incompatible submissions return a report with `compatible: false`;
they are rejected with HTTP 422 by the download endpoint. Both endpoints reuse
the existing builder form validation and channel construction.

## How it works

1. Open the Radio Loadout channel builder.
2. Add channels manually or load a preset.
3. Configure frequencies, modes, tones, power, and scan settings.
4. Arrange the channels in the desired memory order.
5. Select **Generate CHIRP CSV**.
6. Download the generated file.
7. Open the file in CHIRP and review it before programming a radio.

Radio Loadout generates programming files. It does not directly communicate with or program a connected radio.

## Technology stack

Radio Loadout currently uses:

- Python 3.11 or newer
- FastAPI
- Pydantic
- Jinja2
- HTML
- CSS
- JavaScript
- Pytest
- Ruff
- GitHub Actions

## Running Radio Loadout locally

### 1. Clone the repository

```bash
git clone https://github.com/TimothyThurston/radio-loadout.git
cd radio-loadout
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install the project

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 4. Start the development server

```bash
uvicorn radio_loadout.web.app:app --reload
```

Open the following address in a browser:

```text
http://127.0.0.1:8000
```

The channel builder is available at:

```text
http://127.0.0.1:8000/builder
```

### Installable distributions

Build and verify the actual wheel and source archive with:

```sh
python scripts/smoke_package.py
```

This builds both formats, audits their contents, installs the wheel in a fresh
temporary environment outside the repository, and checks the installed web app
and CSV workflows from a separate directory without editable/PYTHONPATH access.
Verified artifacts and diagnostic logs are kept in the ignored `dist/` directory.
For build-only use, run `python -m build`. See [packaging and installation](docs/packaging.md)
for wheel installation commands, the included assets, and isolation details.

## Development checks

Staging/container preparation, local smoke commands, production settings, and
rollback steps are documented in [staging deployment](docs/staging.md).
The container uses the installable wheel and a non-root user. No deployment is
performed by these commands or by CI. Review the [dependency license inventory](docs/dependency-licenses.md)
for third-party notice obligations and outstanding reviews. The project license
does not authorize redistribution; additional permissions require a separate agreement.

Use Python 3.11 or newer. Activate your virtual environment and install the project
and development dependencies as described above. CI tests Python 3.11 and 3.13.

Run the Python lint checks (this command does not reformat files):

```bash
ruff check .
```

Run the automated test suite:

```bash
python -m pytest
```

Use Node.js 24 LTS for the same JavaScript runtime major as CI. Verify that
`node --version` works in your terminal, then run the syntax and regression checks.
These simulated-DOM tests use Node's built-in modules; they can run without npm
dependencies. Real-browser tests use the separate Playwright setup below.

```bash
node --check src/radio_loadout/web/static/backup-format.js
node --check src/radio_loadout/web/static/builder.js
node --test tests/js/*.mjs
```

If PowerShell cannot find `node`, use the explicit path to your installed
`node.exe`. PowerShell's call operator (`&`) runs an executable stored in a
variable. Enumerate the test files explicitly to avoid shell wildcard differences:

```powershell
$nodeExecutable = 'C:\path\to\node.exe' # Replace with your actual Node.js 24 executable.
& $nodeExecutable --version
& $nodeExecutable --check src/radio_loadout/web/static/backup-format.js
if ($LASTEXITCODE -ne 0) { throw 'Backup format JavaScript syntax check failed.' }
& $nodeExecutable --check src/radio_loadout/web/static/builder.js
if ($LASTEXITCODE -ne 0) { throw 'Builder JavaScript syntax check failed.' }
$jsTests = @(Get-ChildItem -LiteralPath tests/js -File -Filter '*.mjs' |
    Sort-Object Name | Select-Object -ExpandProperty FullName)
if ($jsTests.Count -eq 0) { throw 'No JavaScript test files found.' }
& $nodeExecutable --test @jsTests
if ($LASTEXITCODE -ne 0) { throw 'JavaScript tests failed.' }
```

All checks should complete successfully before committing changes.

### Real-browser journeys

With Node.js 24 LTS, npm, and the Python development environment installed:

```sh
npm ci
npx playwright install chromium
npm run check:syntax
npm run test:js
npm run test:e2e
```

Playwright automatically starts an isolated loopback test server and uses a fresh,
disposable browser context for every test. It never opens your browser profile or
reads personal drafts. The suite tests real downloads/restores, card editing,
import-loss confirmation, compatibility, autosave, responsive layout, keyboard
focus and automated axe accessibility checks using synthetic data.

Chromium is tested at desktop and narrow viewports; Firefox, WebKit and real
mobile devices remain unverified. Automated checks do not replace manual
screen-reader testing. See [browser testing](docs/browser-tests.md) for system
dependencies, server/port configuration, commands, diagnostics and coverage.

### GitHub Actions CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pushes to `main`
and on pull requests. It uses Ubuntu runners with read-only repository contents
permission and does not persist checkout credentials. A new run cancels an older
run for the same workflow and branch or pull-request ref.

The Python matrix installs `.[dev]`, then runs `ruff check .` and
`python -m pytest` on Python 3.11 and 3.13. The separate JavaScript job installs
Node.js 24 LTS and runs both browser-script syntax checks and every `tests/js/*.mjs` test.
The browser job installs locked npm dependencies and managed Chromium, then runs
the desktop and narrow Playwright projects with accessibility checks. Synthetic
failure traces/screenshots and the HTML report are retained for seven days.
The packaging matrix builds and audits both distribution formats and smoke-tests
the installed wheel from external temporary environments on Python 3.11 and 3.13.
Checks are separate steps under Bash with failure propagation; no check is allowed
to fail silently. Matrix fail-fast is disabled so both Python versions can report
their results. This workflow tests the project; it does not publish or deploy it.

Official action releases checked for this workflow: [Checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1),
[Setup Python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0),
and [Setup Node v7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0).
Node.js 24 is listed as LTS in the [official release schedule](https://nodejs.org/en/about/previous-releases).

The test suite currently covers:

- Channel model validation
- Invalid frequencies
- Receive-only channels
- Analog settings
- CTCSS tones
- DCS/DTCS tones
- DCS polarity
- Cross-tone export
- Repeater offsets
- Tuning steps
- Scan behavior
- CHIRP CSV downloads
- Builder page assets
- Draft-saving assets
- NOAA preset assets
- Amateur Calling preset assets

## Project structure

```text
radio-loadout/
├── examples/
│   └── generate_chirp_sample.py
├── src/
│   └── radio_loadout/
│       ├── exporters/
│       │   └── chirp_csv.py
│       ├── web/
│       │   ├── static/
│       │   │   ├── builder.js
│       │   │   └── styles.css
│       │   ├── templates/
│       │   │   ├── builder.html
│       │   │   └── index.html
│       │   └── app.py
│       └── models.py
├── tests/
│   ├── test_chirp_csv.py
│   ├── test_models.py
│   └── test_web.py
├── pyproject.toml
└── README.md
```

### Important modules

- `models.py` contains the radio-independent channel and tone models.
- `chirp_csv.py` converts supported analog channels into CHIRP Generic CSV rows.
- `app.py` provides the FastAPI routes and validates builder submissions.
- `builder.html` contains the channel-builder interface.
- `builder.js` controls channel cards, presets, validation behavior, draft saving, and form submission.
- `styles.css` contains the website styling.
- `tests/` verifies model, exporter, and web behavior.

## Current limitations

Radio Loadout does not currently provide:

- Server-side user accounts or cloud synchronization
- A production database
- Radio-specific compatibility profiles
- Radio-wide settings editing and direct browser read/write
- ZIP-code repeater lookup
- Satellite channel presets
- DMR codeplug export
- Manufacturer-specific CPS export
- Direct USB radio programming
- A production-hosted public release

The current CHIRP exporter supports analog channels only.

## Roadmap

### Version 1 — Polished analog web application

The first public release will focus on creating a dependable analog channel-planning application.

Completed or substantially implemented:

- Universal analog channel model
- CHIRP Generic CSV export
- Browser-based multi-channel builder
- Repeater and receive-only channels
- CTCSS, DCS, and cross-tone controls
- Power, tuning-step, and scan settings
- Channel duplication and reordering
- Automatic browser draft saving
- CHIRP CSV import
- Portable JSON backup and restore
- CHIRP compatibility report with channel-level warnings and errors
- Optional [manufacturer-documented BF-F8HP PRO V0.53 pilot review](docs/radio-profiles.md), with versioned capability metadata and explicit unknowns; not hardware/programming verification
- Separate [radio settings guide and recommendation-plan foundation](docs/radio-settings.md) for that documented pilot, with seven settings, selective preview and custom-value provenance; session-only/manual guidance, not programming or factory defaults
- NOAA Weather preset
- Amateur Calling preset
- Automated tests

Remaining Version 1 work:

- Verify CHIRP CSV import/export in the real CHIRP application, including regression fixtures and radio-specific limitations
- Implement ZIP-code/location repeater lookup with radius, band filters, selection into loadouts, and approved data-source access
- Implement verified satellite frequency presets, including source attribution and last-checked information; add channel sets for Doppler where practical
- Expand the documented pilot into hardware-verified model/firmware profiles; resolve unknown name/tone/power mappings and add applicable device settings without claiming untested support
- Expand the initial separate **Radio Settings** guide to verified model/firmware behavior and additional documented settings, including display, dual watch and scan dependencies; no direct programming is implemented by the guide
- Verify and expand **Recommended Settings** for each supported exact profile; the initial listening-first suggestion plan is editorial/manual guidance, not a hardware-tested everyday preset
- Preserve selective preview/diff, explanations, tradeoffs and individual adjustments as settings support expands; distinguish planned values from device readback and unknown manufacturer defaults
- Make recommended settings editable and reversible: save the current configuration first, provide a reset-to-previous-settings path, and require separate user confirmation before writing to a connected radio
- Keep per-radio preset data versioned and tested alongside driver/firmware profiles; mark unverified combinations unsupported rather than guessing settings or modifying calibration/service/password regions
- Save and restore model-specific settings with full radio image backups, not just channel CSV or generic loadout JSON
- Prototype and verify direct browser read/edit/write of radio settings for at least one supported radio family using an appropriate browser hardware API; do not claim this capability for untested models
- Before device writes, confirm the exact model/firmware, save the original device image, preserve unsupported fields, validate settings, and read back when supported
- Maintain GitHub Actions CI, browser/end-to-end tests, documentation, and project licensing notices
- Polish the responsive user interface, harden upload and deployment behavior, and deploy the public website

Recommended profiles are model- and firmware-specific starting points, not universal optimal settings. Initial V1 profiles should offer an Everyday / Beginner default. Consider Battery Saver and High-Noise profiles later, only if there is verified value and no unsafe transmit behavior. Preset values must be sourced from manufacturer manuals and tested against each supported radio; the model's currently read settings are the source of truth. Recommended presets should never override repeater access tones, transmit authorization, regional band limits, or emergency configuration without explicit user choice.

A radio settings editor without a compatible device driver cannot apply global settings through generic CHIRP CSV. Direct browser radio programming is a targeted V1 capability for **selected, verified devices**, not a promise to replace every CHIRP driver by V1. Unsupported settings remain read-only or hidden; never write protected calibration/service regions.

### Version 2 — Digital radio

Planned Version 2 features include:

- Initial DMR channel, contact, talkgroup, and zone models
- The first verified DMR codeplug workflow
- More digital device profiles and verified browser programming
- Further repeater/satellite data-source integrations and update automation
- Emergency and monitoring preset expansions

### Version 3 — Broader radio compatibility

Longer-term work may include:

- Additional DMR ecosystems
- Manufacturer-specific CPS exports
- Radio-specific memory and field validation
- Bank and zone mapping
- Export bundles containing multiple formats
- More extensive radio compatibility testing
- Selected app-based radio workflows
- Expand safe browser-based direct-radio programming to additional verified radio families and interfaces

Support will be added one verified format and radio family at a time.

“Universal” describes the project’s direction. It is not a claim that every radio or programming format is already supported.

## Design principles

- **Browser first:** the main application should work through a website.
- **One plan, multiple targets:** users should not rebuild the same channel list for every radio.
- **Validate before export:** invalid or unsupported settings should produce clear errors.
- **Never fake compatibility:** unsupported configurations should be rejected instead of silently producing unreliable files.
- **Modular exporters:** each export format should remain independently testable.
- **Traceable data:** imported frequencies should retain source and update information when possible.
- **User control:** generated files should remain visible and reviewable before radio programming.
- **Incremental verification:** new radios and formats should be added only after repeatable testing.

## Data accuracy

Repeater, satellite, aviation, emergency, and other frequency information can change.

Future imported data should include:

- Original source
- Last-updated date
- Geographic coverage
- Licensing or usage restrictions
- Review status
- Change history where practical

Radio Loadout should distinguish verified source data from user-created channels and preserve user edits when upstream information changes.

## Safety and legal notice

Radio Loadout is a planning and file-generation tool. It does not grant authorization to transmit.

Users are responsible for following:

- Amateur-radio license privileges
- Band plans
- Service restrictions
- Equipment-certification requirements
- Local regulations
- Applicable national regulations

A listed frequency may be legal to monitor but illegal to transmit on without the correct authorization or equipment.

Always review generated files before importing them into programming software or writing them to a radio. During early development, use backups and known-good configurations.

## Contributing

Bug reports and radio/format research are welcome. Before preparing or submitting
code patches, tests, documentation patches, or other changes to project material,
arrange and agree on the necessary permissions with Timothy Thurston. The project
license does not itself authorize modification or redistribution. See
[contributing guidance](CONTRIBUTING.md).

Bug reports should include:

- Target radio
- Programming application and version
- Expected result
- Actual result
- Generated file or a privacy-safe reproduction
- Steps needed to reproduce the problem

Do not submit undocumented proprietary formats or sensitive personal channel data.

## Author

Radio Loadout is developed by Timothy Thurston.

## License

Copyright (c) Timothy Thurston. Radio Loadout's original project material is
**source-available, not open source**, under the
[PolyForm Strict License 1.0.0](LICENSE). See the separate [copyright and scope
notice](COPYRIGHT).

Strict permits its defined noncommercial uses, including the personal uses and
noncommercial organization uses specified in the license. It does not authorize
modification, derivative works, or redistribution. Additional permissions require
a separate agreement with Timothy Thurston. Rights under applicable law,
including fair use, are preserved by the license.

Third-party components are excluded from the project's license and copyright
claim; their licenses and notices remain applicable. See the
[dependency inventory](docs/dependency-licenses.md) for pending reviews.
The [versioned supplemental notices](src/radio_loadout/third_party_notices/v1/README.md)
travel with the wheel, source archive and runtime image as supporting distribution
documentation. Their [evidence and coverage limits](docs/native-component-notices.md)
are separate from the project's license; they do not complete third-party review.

The [local certifi source-bundle tool](docs/source-bundles.md) prepares retained,
checksummed source evidence for possible future release-attached delivery. It
does not publish sources, establish permanent recipient access or close the
remaining preferred-source/native/OS review findings.

No ownership of users' channel data is claimed, and this source-code license is
not imposed on their generated CSV/JSON configurations. Rights or restrictions
in third-party source data continue to apply.
