# Radio capability profiles: first documented pilot

Implemented 2026-11-06 from checkout
`58e0371832f2745bc74fe0d4ba9640b228fb5eb2`.

This is optional **document-based channel review**, not verified physical-radio
compatibility, programming, live control, firmware detection or global-settings
configuration. Generic CHIRP CSV remains the default. No connected device was
read, modified or written during development.

## Architecture and API

`radio_profiles.py` defines frozen `RadioCapabilityProfile`, `RadioBand` and
`ProfileSource` objects and an explicit ID registry. Schema version 1 and a
per-profile revision are exposed separately from the channel model. Keep factual
limits, source locators/checksums, firmware/region scope and unknown values
separate. No manufacturer driver or CHIRP implementation was copied.

`GET /radio-profiles` returns the catalog, support states and evidence metadata.
The pilot independently reports configuration as documented-review-only,
programming unsupported and live control unsupported, with hardware verification
and firmware detection false. Do not interpret profile selection as a device
identity check. There are no aliases for BF-F8HP (non-Pro), UV-5R or other firmware.

`profile_compatibility.py` layers known profile constraints over the existing
generic checker and preserves generic report/CSV behavior when no profile is
selected. `compatible` still means no blocking errors in the checked scope; an
always-visible pilot warning and unknown-field warnings prevent this from being
presented as complete radio compatibility. Neither checker mutates channels.

The existing review and download POST routes accept optional `radio_profile_id`
beside `channels_json`. Unknown IDs return 422, not generic fallback. Downloads
repeat the checks server-side. Both transport fields must be singular strings;
the ID is limited to 80 characters. Unexpected fields/files are rejected. The
multipart parser permits at most two fields / zero files, retaining the existing
per-part bound. All existing JSON/channel/upload limits and production boundaries
remain in place; this is not a total HTTP-body limit.

## BF-F8HP PRO V0.53 pilot, revision 1

ID: `baofeng-bf-f8hp-pro-v053-us`. Firmware scope: manufacturer's manual print
V3.1 (V53 Firmware), US documentation. The user's actual firmware and hardware
revision are unknown; do not upgrade firmware or claim support to match this ID.

| Reviewed item | Pilot behavior |
| --- | --- |
| Memory total | Blocks above 1,000; records 10 zones / 100 per zone, but assigns no zones or free slots |
| Receive scope | AM airband plus documented VHF/1.25m/350–390/UHF ranges; the exact 137 MHz boundary remains warned |
| Transmit scope | Checks the V0.53 manual's FM/NFM ranges separately from receive ranges; AM requires receive-only |
| Power ceilings | Uses the vendor's band ceilings, not a guessed H/M/L-to-watts mapping; receive-only power is not treated as a transmit setting |
| Names | Numeric length/character set unknown: no guessed 12-character rule, truncation or character substitution |
| Tones | General tone modes described; individual custom values, independent combinations and polarity behavior not hardware verified; generic validation remains enforced |
| Tuning steps | Quick list and VFO table differ, so unlisted generic steps warn rather than asserting an exhaustive memory limit |
| AM spacing | No synthetic 8.33 kHz setting or new generic mode/backup value; spacing/bandwidth limitations are explicit |
| Other gaps | Priority-scan mapping, exact frequency raster, broadcast-FM memory mapping, reserved slots, banks, radio-wide settings and firmware variants remain unverified |

The profile's transmit coverage is a manufacturer capability description, not
operating authorization or a regulatory band-plan validator. The conditional
219–222 MHz area has an additional warning. Independent authorization review is
still the operator's responsibility. Selecting Generic explicitly removes this
optional device review; it does not claim a radio can accept the resulting CSV.

### Primary-source evidence

Reviewed on 2026-11-06:

- [Manufacturer manual V3.1 / V53](https://baofengtech.com/wp-content/uploads/2026/01/BTECHmanual_BF-F8HPPRO_2026.pdf),
  printed pp. 9, 45–46, 49, 64–66 and 78. PDF SHA-256:
  `1114e1e55c6e6bc71dddcac1421333d199660377115ca2cc5ffb96e75d100b47`.
  Technical-spec and version pages were visually inspected. The PDF is not
  redistributed in this repository or package; the profile records factual
  limits and locators, not the manual's text/tables.
- [Manufacturer product page](https://baofengtech.com/product/bf-f8hp-pro/),
  technical specifications for the power ceilings only. The page is mutable;
  its current marketing band summary is not substituted for the versioned manual.
- The older manual and product summary differ from the V53 frequency scope.
  Do not combine them into a supposedly universal model/firmware profile.

## Builder state and backups

The optional selector is session-only and defaults/resets to Generic on page
initialization, successful CSV/JSON import, or successful draft clearing.
Failed imports preserve the selection as well as existing channel/storage data.
Switching the target invalidates review and any in-flight authorization. A target
or channel edit during CSV retrieval suppresses that stale download.

Version-1 backups and local drafts remain **channel-only**, with unchanged schema
and validation. No profile ID is silently appended to that fixed format. A
portable profile selection needs a deliberate future backup-schema revision;
choose the target again after restore. Original CSV exports remain generic and
contain no embedded model, firmware, zones or radio-wide settings.

## Verification boundaries

Python tests cover documented edges, capacity, power ceilings, uncertainty,
non-mutation, exact generic parity, invalid definitions, catalog/transport and
review/download enforcement. JavaScript tests cover profile-bound requests,
safe text rendering, mismatched responses and stale review/download races.
The installed-wheel smoke exercises the catalog, selected review, unchanged CSV
bytes and direct-download rejection. Existing import/backup tests remain intact.

Two new browser journeys cover selection, export, reset, backup schema and error
blocking on desktop/narrow Chromium projects; keyboard expectations include the
new selector. **Browser execution remains unverified here:** the pinned Chromium
download returned an invalid/truncated archive, and no browser executable is
installed. Test listing/syntax checks are not execution. Run the full 24-case
Chromium suite on Windows/CI before accepting the UI change. Firefox/WebKit,
real mobile devices, manual screen-reader testing, Docker CI and actual radio
hardware remain unverified. No programming support is implemented by this work.
