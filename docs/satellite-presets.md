# Receive-only satellite monitoring presets

Implemented from `56ffca5c7c4d09597109a8f180e4e15c7f3271a2` on 2026-11-06.
This first milestone is one small **ISS voice monitoring pack**, not a worldwide
satellite directory, transmit plan, orbital tracker or radio programming driver.

## Frequency evidence and deliberate limits

Pack `iss-voice-rx`, revision 1, records the following nominal Earth receive
frequencies and FM mode. Frequency references were checked on **2026-11-06**:

| Channel | Nominal receive frequency | Role |
| --- | --- | --- |
| ISS RPT RX | 437.800000 MHz FM | ISS FM repeater downlink; not a promise of crew voice activity |
| ISS CREW RX | 145.800000 MHz FM | Crew/school-contact downlink; intermittent rather than a continuous beacon |

Primary references:

- [ARISS — Contact the ISS](https://www.ariss.org/contact-the-iss.html),
  selected voice-downlink and repeater-downlink entries.
- [AMSAT — Amateur Radio on the ISS](https://www.amsat.org/amateur-radio-on-the-iss/),
  selected crew-contact and FM voice-repeater receive-frequency rows.
- [ARISS station-status page](https://www.ariss.org/current-status-of-iss-stations.html),
  linked for independent user checking, not polled or treated as live telemetry.
  Its reviewed snapshot listed a November 4, 2026 status date and planned radio
  shutdown/restart times. A schedule is not proof that the radios restarted.

Only these two agreed voice references are included. Packet/APRS and SSTV
frequency/mode choices are deliberately excluded: differently maintained pages
and changes of operating configuration must not be merged into one assumed
current setup. No activation tone, uplink frequency or transmit setting is added.
The implementation is independently structured from these factual references;
no third-party driver, page, image, bulk database or frequency table is bundled.
No ARISS/AMSAT endorsement or permission agreement is claimed.

`frequency_sources_checked_on` is a **reference-review date**, not an RF reception
test, verified pass, or on-air timestamp. `operational_status` is explicitly
`unknown-not-live-checked`; `hardware_verified` is false. Review sources again
when updating a pack and increment its revision for meaningful changes.

The preset uses application defaults for 5 kHz tuning step, normal scan and
5 W stored power (unused while receive-only). Those values are not satellite-
specific requirements. No tones or receive tone filters are enabled. Both
nominal frequencies may need manual receive tuning for Doppler; no correction
sequence, pass prediction, azimuth/elevation or automatic channel switching is
provided. Reception also depends on the pass, antenna, equipment and local
conditions. Silence is not proof of an app/radio fault or of station failure.

## Preview, review and explicit addition

1. Select one or both monitoring channels in the builder.
2. Choose **Preview ISS receive-only pack**. No cards or saved data change.
3. The app reviews proposed additions through the existing same-origin generic/
   selected-profile validation route. The selected exact profile is bound to
   that request; unknown/mismatched targets do not fall back silently.
4. Review nominal RX frequencies, transmit disable, duplicate count, resulting
   total count and warnings. A documented-profile result is not hardware proof.
5. Choose **Add reviewed receive-only channels**, or cancel. Cancellation is
   available while the compatibility request is in flight as well as afterward.

The review concerns **new channels only**. It does not certify unfinished or
invalid existing channels. Total count is checked against the central 2,000
limit and the selected documented profile's aggregate capacity. Free memory
slots/zones on an actual radio are unknown. Existing CSV review/export still
rechecks the full channel list and selected profile before producing a file.

An existing channel is skipped only when its whole-Hz nominal receive frequency,
FM mode, explicit receive-only flag and no-tone configuration match. An existing
transmit-enabled, differently modulated or tone-filtered channel is preserved;
the app adds a separate safe monitoring entry rather than rewriting it. Only a
single **entirely pristine default placeholder** is replaced. Customized blank
cards are preserved too. Users can edit/delete channels after addition; manually
clearing receive-only can enable transmit, so keep these monitoring entries RX-only.

Preview data is captured/frozen. Channel/profile edits invalidate it. Settings
plan changes, stale saved draft changes and obsolete/cancelled responses cannot
authorize an addition. New cards are prepared off-page; storage/card failures
restore the original card identities/values and channel draft rather than
claiming success. The app does not change the selected profile or settings plan.

## Exports, provenance and persistence

`MonitoringChannel.to_channel()` always produces FM with TX frequency `None`.
Builder controls use `receive_only: true` and a blank transmit field; review
submission converts that absence to JSON null. Generic CSV exports `Duplex=off`,
zero offset, and no tone. Confirm transmit disable in the destination software
and on the actual radio: a generic file is not a verified device write.

Added channels and compact reference comments survive ordinary channel autosave,
v1 backups, v2 full-loadout files and CSV round trips. The fixed backup schemas
are unchanged: **structured pack/source/status metadata is not embedded** in
v1 or v2 files. The editable comment records pack ID/revision, source URL and
check date; editing/removing it loses that reference. It is not authenticated
provenance. Download v2 separately to preserve selected profile/settings values,
which remain excluded from channel autosave. No station-status cache is created.

## Implementation and verification

`satellite_presets.py` contains immutable definitions and a read-only
`GET /presets/satellites` catalog (schema version 1). The builder embeds the same
catalog in escaped JSON. `satellite-presets.js` performs non-mutating selection,
receive-only validation, pristine-placeholder checks, deduplication and count
planning. The builder owns compatibility requests and guarded additions. All
report text uses `textContent`; source links are operator-maintained references
rendered by the server, not imported HTML or automatically loaded resources.

Tests cover exact nominal values, evidence labels, invalid definitions, API/
embedded/fixture consistency, generic/profile checks, CSV RX-disable round trips,
selection, duplicate policy, count bounds, stale/cancelled requests, profile/
settings preservation, failure rollback and literal rendering of untrusted
review text. Packaging smoke loads the catalog and referenced assets; the new
script/template have explicit container declarations. Dependencies, licensing,
device boundaries, input limits and v1/v2 contracts are unchanged.

The committed JSON fixture is decoded explicitly as UTF-8, with a regression
that emulates CP1252 as the default when no encoding is supplied. Reference
links use bounded inline-block targets so wrapped labels have a continuous
clickable rectangle. The focused browser journey checks each link's geometry
and center hit at the existing viewport widths, including 320px; the general
reachability/clipping assertions are unchanged. These follow-up browser checks
still require execution on Windows/CI before the layout fix is confirmed.

Four new browser journeys run in both desktop and narrow Chromium projects,
bringing the suite to **50 cases**. They cover real preview/add/cancel, selective
addition, preservation, CSV and v2 files, API failure injection, keyboard
activation, axe and narrow layouts. **Browser execution remains pending here**:
the pinned Chromium download returned a corrupt/truncated archive. Listing
cases and simulated DOM tests are not browser execution. Run the whole suite
on Windows/CI before accepting the UI. Docker/Linux CI and actual RF/radio
behavior also remain unverified by this work. No radio is connected or written.

Future packs require their own source/operating review, data revisions, safe
defaults and tests. The present UI intentionally exposes one pack; adding a
second pack requires explicit UI selection wiring, not just appending data.
