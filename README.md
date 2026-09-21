# Radio Loadout

> Build your channels once. Load them anywhere.

Radio Loadout is an open-source, browser-first radio channel planning and configuration export project. Its long-term goal is to let radio users build one clean, validated channel plan and convert it into files that can be imported into CHIRP, DMR codeplug tools, and manufacturer-specific programming software.

The project is currently in early development. The data model and first CHIRP exporter are being built before the full website interface.

## The problem

Radio programming is fragmented. Different radios and programming applications expect different fields, file formats, naming limits, tone settings, and channel structures. A channel list that works in one program often has to be rebuilt manually for another.

Radio Loadout is intended to separate the **channel plan** from the **radio-specific export format**:

1. Create or import a channel plan once.
2. Validate frequencies, names, modes, tones, and transmit settings.
3. Select a radio or programming-software target.
4. Export a compatible file.
5. Import that file into the radio's existing programming software.

The website will generate files locally for the user to download. It is not intended to replace CHIRP, a DMR CPS, or a manufacturer's programming application, and direct USB radio programming is not required for the initial product.

## Current status

Radio Loadout is a work in progress and is not yet a finished end-user application.

### Implemented

- A universal `Channel` model
- FM, NFM, AM, and DMR mode representation
- Channel-name and frequency validation
- Receive-only channel support
- Analog CTCSS, DCS, and cross-tone settings
- Transmit-power settings
- A CHIRP Generic CSV exporter using CHIRP's 21-column format
- Automated tests for the current model and exporter behavior
- Explicit rejection of unsupported DMR-to-CHIRP exports instead of silently producing an invalid file

### Current limitations

- The CHIRP exporter currently supports analog channels only.
- DMR-specific codeplug data and DMR export are not implemented yet.
- Manufacturer-specific CPS formats are not implemented yet.
- The browser interface has not been completed.
- Radio-specific field limits and compatibility rules still need to be added target by target.

## Planned export targets

| Target | Status | Purpose |
| --- | --- | --- |
| CHIRP Generic CSV | In development | Import analog channel plans into CHIRP-supported radios |
| DMR codeplug formats | Planned | Export digital contacts, talkgroups, channels, zones, scan lists, and related settings |
| Manufacturer CPS formats | Planned | Support vendor- and model-specific programming workflows |
| CSV, TSV, JSON, TXT, and XML | Planned | Portable channel-plan exchange, backup, and debugging |
| ZIP export bundles | Planned | Package multiple files or radio-specific outputs together |
| Direct USB programming | Long-term research | May be possible for selected radios, but is outside the initial website scope |

Support will be added one verified format and radio family at a time. “Universal” describes the direction of the project, not a claim that every radio is already supported.

## Channel model

The internal model is designed to hold radio-independent channel information before an exporter converts it into a target format. Depending on the mode and radio, a channel may include:

- Channel name
- Receive frequency
- Transmit frequency or repeater offset
- Operating mode and bandwidth
- Receive-only status
- CTCSS transmit and receive tones
- DCS transmit and receive codes
- Cross-tone configuration
- Transmit-power level
- Scan and skip behavior
- Comments or source metadata
- Digital-mode fields as DMR support is developed

Keeping this information in a common model allows multiple exporters to use the same channel plan while applying their own field names, value mappings, restrictions, and file layouts.

## Planned website workflow

The finished website is intended to provide a guided channel builder rather than requiring users to edit raw files.

1. Start a new loadout or import an existing supported file.
2. Add channels manually or select them from supported data sources.
3. Organize channels into a useful order, banks, or zones when the target supports them.
4. Choose the destination radio, CPS, or export format.
5. Review validation warnings and radio-specific compatibility issues.
6. Download the generated file and import it into the appropriate programming application.

An optional installable Progressive Web App may be explored later for offline use, but the primary product is intended to remain a website rather than a required desktop download.

## Data accuracy and updates

Repeater, satellite, and other frequency data changes over time. The long-term plan is to use maintainable data sources and update pipelines rather than permanently embedding an unchanging master list.

Future data features may include:

- Source and last-updated information
- Scheduled data refreshes
- Change detection for added, modified, or removed records
- Review rules before replacing trusted data
- Clear separation between verified source data and user-created channels
- Local caching so a temporary source outage does not destroy an existing loadout

Generated files should remain reviewable before import. Radio Loadout will not assume that every listed frequency is legal to transmit on with every radio, license, service, or location.

## Project structure

The current Python foundation is organized around two main responsibilities:

- `src/radio_loadout/models.py` defines the shared channel data model and validation rules.
- `src/radio_loadout/exporters/chirp_csv.py` converts supported analog channels into CHIRP Generic CSV rows.
- The test suite verifies valid models, rejected inputs, receive-only behavior, tone handling, and exporter output.

As the project grows, target-specific logic should remain isolated in exporters so that adding one radio or file format does not require rewriting the universal channel model.

## Design principles

- **Browser first:** the main user experience should work from a website.
- **One plan, multiple targets:** users should not rebuild the same channel list for every radio.
- **Validate before export:** bad or unsupported values should produce clear errors.
- **Never fake compatibility:** an exporter should reject unsupported settings rather than create a file that only appears valid.
- **Modular exporters:** each format should be independently testable and maintainable.
- **Traceable data:** imported frequency data should retain its source and update date when possible.
- **User control:** generated files should be visible, editable, and reviewable before programming a radio.

## Roadmap

### Phase 1 — Core foundation

- Complete the universal analog channel model
- Expand validation and edge-case coverage
- Finish and verify CHIRP Generic CSV export
- Add round-trip fixtures using known-good files

### Phase 2 — Website MVP

- Build the channel-plan editor
- Add import, reorder, duplicate, edit, and delete controls
- Add target selection and compatibility warnings
- Generate downloadable CHIRP CSV files entirely through the website
- Add loadout save and restore support

### Phase 3 — Radio profiles

- Add per-radio name lengths, frequency ranges, supported modes, power levels, and memory limits
- Add bank and zone mapping rules
- Create verified compatibility tests for each supported radio family

### Phase 4 — DMR and CPS support

- Expand the model for contacts, talkgroups, color codes, time slots, zones, receive groups, and scan lists
- Add DMR codeplug exporters one ecosystem at a time
- Research documented manufacturer CPS formats and safe conversion methods

### Phase 5 — Maintained data sources

- Add repeater and satellite data integrations where licensing and access terms allow
- Track source provenance and update timestamps
- Detect additions, changes, and removals
- Preserve user edits when upstream data changes

## Safety and legal notice

Radio Loadout is a planning and file-generation tool. It does not grant authorization to transmit. Users are responsible for following applicable licensing rules, band plans, service restrictions, equipment-certification requirements, and local regulations.

Always review generated files before importing them into programming software or writing them to a radio. During early development, test with backups and known-good configurations.

## Contributing

The project is still establishing its core model and exporter architecture. Useful contributions will eventually include:

- Verified sample files from supported programming applications
- Exporter and validation tests
- Radio-specific field-limit research
- Documentation corrections
- Reproducible bug reports that include the target radio, programming software, expected result, and generated result

Please avoid submitting undocumented proprietary formats or sensitive personal channel data.

## Project name

The product name is **Radio Loadout**, matching the `radio-loadout` repository name.
