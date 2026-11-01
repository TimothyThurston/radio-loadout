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

## Development checks

Run the formatter and lint checks:

```bash
ruff check .
```

Run the automated test suite:

```bash
pytest
```

Run the JavaScript regression tests with Node.js:

```bash
node --check src/radio_loadout/web/static/builder.js
node --test tests/js/*.mjs
```

All checks should complete successfully before committing changes.

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
- NOAA Weather preset
- Amateur Calling preset
- Automated tests

Remaining Version 1 work:

- Verify CHIRP CSV import/export in the real CHIRP application, including regression fixtures and radio-specific limitations
- Implement ZIP-code/location repeater lookup with radius, band filters, selection into loadouts, and approved data-source access
- Implement verified satellite frequency presets, including source attribution and last-checked information; add channel sets for Doppler where practical
- Implement initial radio-specific compatibility profiles (exact model/firmware, supported modes, memory/name limits, and device settings)
- Add a **Radio Settings** tab for selected models: squelch, backlight and display options, battery saver, VOX, dual watch, scan behavior, timeout, beeps, and other settings only where supported by each radio
- Add a **Recommended Settings** beginner-friendly preset for each verified radio model/firmware profile: populate a conservative, documented everyday-use baseline without changing channel memories or transmitting frequencies
- Show a clear preview/diff before applying a recommended preset; explain every proposed setting in plain language, highlight trade-offs and any unsupported fields, and allow individual changes to be deselected or adjusted
- Make recommended settings editable and reversible: save the current configuration first, provide a reset-to-previous-settings path, and require separate user confirmation before writing to a connected radio
- Keep per-radio preset data versioned and tested alongside driver/firmware profiles; mark unverified combinations unsupported rather than guessing settings or modifying calibration/service/password regions
- Save and restore model-specific settings with full radio image backups, not just channel CSV or generic loadout JSON
- Prototype and verify direct browser read/edit/write of radio settings for at least one supported radio family using an appropriate browser hardware API; do not claim this capability for untested models
- Before device writes, confirm the exact model/firmware, save the original device image, preserve unsupported fields, validate settings, and read back when supported
- Add GitHub Actions CI, browser/end-to-end tests, updated documentation, and a selected project license
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

Useful contributions may include:

- Verified sample files
- Exporter tests
- Validation tests
- Radio-specific field-limit research
- Documentation corrections
- Reproducible bug reports
- Authorized and appropriately licensed data-source integrations

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

A project license has not yet been selected.
