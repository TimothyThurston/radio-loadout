# Radio Loadout

> Build your channels once. Load them anywhere.

Radio Loadout is a browser-first radio channel planning and configuration export project. It lets users create organized channel loadouts through a guided web interface and download them as CHIRP-compatible CSV files.

The long-term goal is to provide one radio-independent channel plan that can eventually be exported for CHIRP, DMR codeplug tools, and selected manufacturer programming applications.

## Project status

Radio Loadout is currently in early development, but its analog channel builder is functional.

The current version includes:

- A working browser-based channel builder
- CHIRP Generic CSV downloads
- Analog tone and repeater configuration
- Browser draft saving
- Verified channel presets
- Automated model, exporter, and web tests
- **23 passing automated tests**

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

Both commands should complete successfully before committing changes.

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

- CHIRP CSV import
- Portable JSON loadout import and export
- Server-side user accounts or cloud synchronization
- A production database
- Radio-specific compatibility profiles
- ZIP-code repeater lookup
- Satellite channel presets
- DMR codeplug export
- Manufacturer-specific CPS export
- Direct USB radio programming
- A production-hosted public release

The current CHIRP exporter supports analog channels only.

## Roadmap

### Version 1 — Analog web application

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
- NOAA Weather preset
- Amateur Calling preset
- Automated tests

Remaining Version 1 work:

- Improve user-facing validation and error messages
- Add known-good CHIRP compatibility fixtures
- Verify exported files through repeated CHIRP testing
- Add CHIRP CSV import
- Add portable JSON backup and restoration
- Add initial radio compatibility profiles
- Add broader browser and end-to-end testing
- Update user documentation
- Prepare and deploy the public website

### Version 2 — Data sources and digital radio

Planned Version 2 features include:

- Repeater lookup by ZIP code or location
- Satellite presets
- Emergency and monitoring presets
- Source attribution and last-updated information
- Maintainable frequency-data update pipelines
- Change detection for updated repeater and satellite records
- Initial DMR channel, contact, talkgroup, and zone models
- The first verified DMR codeplug workflow

### Version 3 — Broader radio compatibility

Longer-term work may include:

- Additional DMR ecosystems
- Manufacturer-specific CPS exports
- Radio-specific memory and field validation
- Bank and zone mapping
- Export bundles containing multiple formats
- More extensive radio compatibility testing
- Selected app-based radio workflows
- Research into safe direct-radio programming

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