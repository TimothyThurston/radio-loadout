# Full-loadout JSON version 2

Implemented from `dc057e79b60b3788fc2866b114820b12e9b616c9` on 2026-11-06.
This is an opt-in portable planning document, not a radio image, device backup,
readback, firmware identity proof or programming payload.

## User workflow

1. Build channels and choose the exact documented **Review target**.
2. Expand **Edit settings plan** below the builder. Edit current plan values or
   preview/apply selected suggestions. Merely editing proposals is not applying
   them; pending proposals/previews are not saved.
3. **Export Full Loadout (v2)** downloads `radio_loadout_full_v2.json`.
4. **Import Backup** accepts v1 or v2. V2 validates all data and asks before
   replacing channels, selected profile and the settings plan together.

**Export Backup** still emits the original channel-only v1 file. Browser autosave
also remains channel-only with its existing key/schema. There is no new settings
autosave key or cross-tab state sharing. Profile/settings disappear on reload
unless restored from a downloaded v2 file. Download before leaving; confirm the
file exists in browser downloads. These files may include private operator notes
and channel plans, so share deliberately.

The standalone `/radio-settings` guide remains independent and session-only.
It does not transfer its plan to the builder; use the builder's embedded editor
for full-loadout save/restore. Settings remain outside the channel export form and
never appear in CHIRP CSV.

## Envelope and field rules

```json
{
  "format": "radio-loadout",
  "version": 2,
  "channels": [{"name": "", "receive_frequency_mhz": ""}],
  "radio_profile": {
    "profile_id": "baofeng-bf-f8hp-pro-v053-us",
    "revision": 1
  },
  "settings_plan": {
    "catalog_revision": 1,
    "recommendation_id": "listening-first-handheld-v1",
    "entries": {
      "squelch": {"value": 3, "origin": "user-customized"},
      "vox": {
        "value": false,
        "origin": "radio-loadout-recommendation",
        "recommendation_revision": 1
      }
    }
  }
}
```

All five top-level fields are required; unknown fields are rejected. Version is
numeric `2`, not string `"2"`. UTF-8 JSON with an optional BOM is accepted.
The same 4 MiB backup limit is checked before file reading and after decoding;
exports are byte-checked before requesting a download. The same 2,000-channel
limit applies before normalization, and at least one draft channel is required.

`channels` uses the **unchanged v1 channel-field contract**: numeric form values
remain strings, receive-only is boolean, unfinished values/hidden controls remain
restorable, and optional legacy omissions receive their historical defaults.
Existing DCS and tuning-step normalization stays unchanged. Import success is
not CSV/radio compatibility approval; run Review Compatibility separately.

Generic documents require **both** `radio_profile` and `settings_plan` to be
`null`. A selected profile requires the exact known ID and numeric revision plus
a settings-plan object. Its `entries` may be empty; no suggestions are injected.
There is no profile/firmware alias, generic fallback, closest-value substitution
or automatic upgrade/downgrade. Unknown model/profile/catalog/recommendation
versions fail before changes. Preserve the original file for future migration.

Settings entry IDs/values come only from the trusted runtime catalog, not from
file-supplied labels/options/manual links. Primitive types are strict (`false`,
`0`, and string `"always_on"` are distinct). Null, unknown settings and extra
entry fields are rejected. Allowed origins:

- `user-customized`: exactly `value` and `origin`.
- `radio-loadout-recommendation`: those two fields plus the exact current
  `recommendation_revision`; the value must also match that recommendation.

Origin is recorded planning metadata, **not authenticated authorship or evidence
that someone applied a value to hardware**. Manufacturer defaults/readback and
hardware-verification claims are not accepted backup fields. Every restored
planned value retains its origin without becoming a manufacturer default.

## Restore integrity and compatibility

Validation completes before replacing any cards or plan. Invalid files and
cancelled confirmations preserve channels/profile/settings and stored channel
draft. During application, channel cards, profile and settings have rollback
snapshots; storage/editor failures roll back the page values and retain the
previous channel draft. The single existing localStorage write is the channel
draft, not a multi-key settings transaction. If the storage service becomes
unavailable, restoration fails rather than claiming it was saved.

Channel/profile/settings edits or a saved-draft change detected while awaiting
file reading cancel that stale import. This is not a cross-tab locking service.
Restoration invalidates compatibility review and pending settings previews; no
previous approval can authorize a new configuration or radio write.

V1 imports retain their historical defaults and channel behavior. If the current
settings plan is nonempty, users must confirm clearing it. CSV import and changing
profiles likewise require confirmation before discarding a nonempty plan.
Clearing the draft explicitly clears channels/profile/settings, not a radio.
The original `backup-format.js` schema and v1 export are unchanged. Older released
clients do not understand v2; use v1 when only channel interoperability is needed.

## Implementation and verification boundaries

`loadout-format.js` validates the portable envelope and reuses the original
channel schema plus `RadioSettingsPlan.restore()` for typed settings and origins.
The builder and standalone guide use the same `settings-editor.html` partial;
the editor exposes validated snapshot/restore operations but performs no storage
or device I/O. Schema/profile/catalog/recommendation revisions are independent.

Fixtures include a complete unfinished v2 plan, generic v2, an unknown profile,
and a catalog snapshot checked against Python's current catalog. JavaScript
tests cover mutations, version rejection, byte/channel bounds, round trips,
cancellation, storage/editor rollback, and edits during asynchronous file reads.
Python tests cover HTML/script ordering, fixture consistency, packaging/context
declarations, channel-form isolation and preserved v1 schema. Four new browser
journeys cover real downloads/restoration, legacy clearing, cancellation, bad
files and embedded-editor accessibility/layout in both viewport projects.

The complete Playwright suite lists **42 cases**. Browser execution and Docker
image verification remain pending here; Chromium download is unavailable in this
environment. Test listing/simulated DOM tests are not browser execution. Run all
checks and the full suite on Windows/CI before accepting the UI. No radio has
been connected, read or written by this work.
