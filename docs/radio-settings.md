# Radio-wide settings and recommendation foundation

Implemented from `757237e931a6588c1b7fc25f9e8069d3f9166843` on 2026-11-06.

## What this is

An optional, separate **manual settings guide and session-only plan** at
`/radio-settings`, linked from the channel builder. Choose the exact documented
model/firmware explicitly. Generic mode has no assumed settings; unknown model
or firmware IDs return 404, never another device's preset.

The first guide is the BF-F8HP PRO V0.53 documented pilot. It does not detect
firmware, read current settings, connect to hardware, write a radio, generate a
CPS payload or add global settings to CHIRP Generic CSV. Configuration remains
documented guidance only; programming/live control remain unsupported.

Opening the guide from the builder uses a separate tab with `noopener`; neither
the builder's selected review target nor its channel draft is transferred.
The guide's model selector reloads the page and starts an empty plan. Its label
warns that loading another guide discards the previous plan.

## Evidence and recommendations are distinct

`radio_settings.py` separates:

- Documented options, menu locators, evidence pages and whether the options are
  an exhaustive list or only a reviewed subset.
- Manufacturer default plus evidence. All seven pilot defaults are **unknown**;
  a recommendation is never inserted into that field or presented as a readback.
- A Radio Loadout recommendation value, revision, rationale, intended scenario
  and limitations/tradeoffs. These are editorial starting suggestions, not
  manufacturer endorsements or objectively optimal/safety-certified settings.
- User-customized plan values and their separate provenance in the frontend.

The source is the manufacturer's
[V3.1 / V53 manual](https://baofengtech.com/wp-content/uploads/2026/01/BTECHmanual_BF-F8HPPRO_2026.pdf),
printed pp. 50–53, reviewed 2026-11-06. The four pages were visually inspected.
The existing profile records the manual SHA-256
`1114e1e55c6e6bc71dddcac1421333d199660377115ca2cc5ffb96e75d100b47`.
Only independently structured factual settings/locators are recorded; the manual
and its tables are not redistributed. No CHIRP/manufacturer driver was copied.

| Setting | Radio Loadout starting suggestion | Explicit qualification |
| --- | --- | --- |
| Squelch | Level 2 | Adjust to local noise; excessive squelch can hide weak signals |
| Power save | Off | Listening-first choice, not a battery-endurance preset |
| VOX | Off | Deliberate PTT operation; this does not disable all transmission |
| Transmit timeout | 60 seconds | May interrupt a long transmission; follow local procedures |
| Roger tone | Off | No extra end-of-transmission audio; local preferences may vary |
| Key beep | On | Audible feedback may help setup or disturb quiet environments |
| Backlight timeout | 20 seconds | Readability/battery compromise; reviewed options are a subset |

These suggestions have not been tested on physical equipment. Users must confirm
the exact firmware and observe their device's behavior before any manual change.
No frequency, channel power, access tone, emergency/alarm or protected region is
modified by the plan. Scan-resume behavior, dual-watch dependencies, VOX gain and
delay, global RF power and additional settings are deliberately deferred rather
than assumed to be fully modeled.

## Plan workflow and isolation

1. The plan starts empty; radio state and factory defaults are unknown.
2. Editing **Your plan** records a user-customized value, not a radio readback.
3. Adjust/deselect proposals and select **Preview selected suggestions**.
4. The preview shows prior plan value/origin and proposed value/origin.
5. **Add reviewed changes to plan** applies only that captured preview locally.
   Editing a proposal, its inclusion or the plan invalidates the preview.
6. Cancelling preserves the plan; clearing only empties this page's plan, not a
   radio. Reloading, leaving or loading another guide discards the session plan.

No settings persistence or settings-file import/export is implemented. There is
no localStorage access, network write or channel integration in the settings
scripts. Version-1 channel backups/drafts remain unchanged and exclude this
plan. Copy needed notes before leaving. Portability requires a deliberate future
versioned loadout format, not an undocumented extension of backup v1.

## Implementation contracts

`GET /radio-profiles/{profile_id}/settings` returns schema version 1, catalog
revision 1, recommendation ID, exact profile/source metadata and the seven
setting definitions. There is no POST settings endpoint. Recommendation
revisions are independent of profile and channel-backup versions.

`RadioSetting.validate()` and `validate_setting_values()` reject unknown settings
and wrong primitive types without coercion, partial changes or nearest-value
substitution. In particular, Python booleans are not integer levels. Null is not
a setting value; missing entries mean unset. The validator is a foundation for
future adapters, not a promise of adapter support.

`settings-plan.js` implements pure typed, non-mutating plan operations, provenance
and captured/stale-preview checks. `radio-settings.js` owns page-only state and
uses `textContent` for rendered differences. Controls start disabled and remain
disabled without JavaScript or after a catalog initialization failure. The page
still displays its guidance without JavaScript. A normal paragraph, visible by
default, explains unavailable editing. Only successful controller initialization
hides it. This also handles a missing controller asset, without relying solely
on `noscript` parsing when a test browser disables script execution.

Python tests cover definition validity, catalog serialization, exact model/firmware
scope, primitive type rejection, HTML/catalog consistency, unchanged channel
exports and production boundaries. JavaScript tests cover plan semantics and a
small simulated controller DOM, including cancellation, invalidation, safe text
rendering and failed edits. Installed-wheel smoke checks include the guide,
catalog and every referenced local asset.

Five settings Playwright journeys run in both desktop and narrow projects (34 total
suite cases), covering editing/preview, cancellation, channel-draft isolation,
reload/clear, accessibility, narrow layout, local-only loading and no-JavaScript
behavior, plus a deliberately blocked controller resource in an isolated context.
The latter asserts exactly that resource failure and no page exceptions; it does
not relax shared normal-page error checks. Hidden preview controls are checked
by DOM identity for disabled state and separately excluded from the accessible
role tree. **Execution is pending in this environment**: the pinned Chromium
download returned a corrupt/truncated archive. Listing cases is not passing
them; run the complete suite on Windows/CI before accepting the UI. Actual radios,
Firefox/WebKit, real phones, manual screen readers and Docker/Linux CI are not
verified by this work.

The container allowlist explicitly declares the settings template and both
scripts. `test_container_assets.py` checks explicit file/ancestor declarations
against all packaged runtime web assets, and detects omitted/new asset rules.
This static declaration guard does not emulate Docker's full pattern matching
or establish actual-image inclusion. Existing Linux container smoke checks load
the settings guide/catalog and all referenced assets; actual Docker execution
is still required.

## Next architecture boundary

Before adding a write adapter, model current-device snapshots separately from
plans and recommendations; verify identity/firmware, original-image backups,
dependent settings, supported field mappings and preservation of unsupported
regions. Never translate a plan directly into a write or infer that matching
menu choices establish binary-format compatibility. A future persistent settings
format needs versioning, migrations and atomic restore tests first.
