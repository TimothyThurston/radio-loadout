# Real-browser tests

The Playwright suite is configured to run the same journeys in managed **Chromium, Firefox and
WebKit**, each at 1440 × 1000 and 375 × 812. The narrow layout checks also check
320-pixel width in a separate case with fresh fixture setup. All six projects use desktop-engine contexts. A narrow viewport
does not verify a real phone, touch interaction, Safari or an iPhone; Playwright's
WebKit build is not the Safari application. Manual screen-reader behavior remains
unverified. Automated axe checks complement manual accessibility assessment; they
do not establish full WCAG compliance. See the dated verification record below
for what has actually run.

## Install and run

Use Python 3.11+ and Node.js 24 LTS with npm. From the repository root, install
the project in your virtual environment, then the locked browser dependencies:

```sh
python -m pip install -e ".[dev]"
npm ci
npx playwright install chromium firefox webkit
npm run check:syntax
npm run test:js
npm run test:e2e
```

On Linux machines without browser system libraries, use
`npx playwright install --with-deps chromium firefox webkit` instead. To run only
one engine, install only that engine (for example, `npx playwright install firefox`,
or `npx playwright install --with-deps firefox` on Linux) and select both of its
projects explicitly as below. Each CI job installs only its selected engine and
that engine's system dependencies.
`package-lock.json` locks Playwright, axe, and their transitive dependencies;
Playwright selects its matching browser builds. The Playwright dependency remains
pinned to 1.64.1. No global Playwright installation
or local assistant-runtime path is used by project commands or CI.

Playwright starts Uvicorn automatically on **127.0.0.1:8137** and shuts it down
after the run. Do not start the server yourself. It refuses to reuse an existing
server, including a normal development session. If that dedicated port is busy,
choose another port for this test invocation:

```powershell
$env:RADIO_LOADOUT_E2E_PORT = '8138'
npm run test:e2e
```

On a POSIX shell: `RADIO_LOADOUT_E2E_PORT=8138 npm run test:e2e`.
The server uses the repository's `.venv` Python when present, otherwise `python`.
To use a different installed Python, set `PLAYWRIGHT_PYTHON` to its executable
path. The test server uses the repository's `src` directory, binds only loopback,
and has no reload process.
The test server now uses `radio_loadout.web.serve`, exercising the staging host,
security-header and server settings with an explicit loopback-only test config.

Useful commands:

```sh
npm run test:e2e -- --project=chromium-desktop
npm run test:e2e -- --project=chromium-narrow
npm run test:e2e -- --project=chromium-desktop --project=chromium-narrow
npm run test:e2e -- --project=firefox-desktop --project=firefox-narrow
npm run test:e2e -- --project=webkit-desktop --project=webkit-narrow
npm run test:e2e -- --list
npm run test:e2e:headed
npm run test:e2e -- --grep "real JSON download"
npm run test:e2e:report
```

An unfiltered `npm run test:e2e` runs all six projects: 27 desktop cases and
28 narrow cases per engine, 55 cases per engine and 165 cases total. Project selection limits execution; selecting
one engine does not run the other two engines. Retries remain zero and the worker
count remains two. The headed command still opens a disposable Playwright browser,
never your normal browser profile. No tests use persistent contexts, personal downloads,
saved storage state, authentication, or browser extensions. Each test receives a
fresh non-persistent context and asserts that the builder starts without a draft.
Autosave tests refresh only inside that test's disposable context. Synthetic
fixtures live under `tests/fixtures/backups` and `tests/e2e/fixtures`.

## Coverage and assertions

- Create distinct NFM cross-tone and receive-only AM channels through labeled
  controls; duplicate, move both directions, remove, and check every saved value.
- Download a real JSON backup, read its contents, restore the downloaded file
  through the file input, and compare every field and channel order. This includes
  hidden tone settings, independent DCS polarities, nonstandard codes, and custom
  CTCSS options. Refresh and verify the saved draft.
- Reject invalid backups without changing existing controls or local storage.
- Cancel a lossy CHIRP import without changes, then confirm a captured review even
  after selecting another file. Untrusted fixture text remains text, not HTML.
- Mark compatibility reports outdated after edits; prevent an invalid CTCSS
  boundary draft from reaching the CSV download endpoint, then download and read
  a valid CSV after correction.
- Check horizontal overflow, control bounds, clipping/occlusion and keyboard
  access at desktop and narrow widths. Test visible keyboard focus, labeled
  controls and live error/compatibility feedback.
- Run full-page axe scans on the empty builder, advanced settings, rendered error
  feedback and loss-review states, with no excluded rules or ignored violations.
- Review the separate [radio settings guide](radio-settings.md): start unset,
  customize/deselect proposals, preview before adding changes, cancel/invalidate
  reviews, preserve channel drafts, clear/reload, reject unknown profiles and
  keep controls disabled without JavaScript. Check axe, keyboard access, narrow
  layout and absence of automatic external requests.
- Download/restore a real [v2 full loadout](loadout-format-v2.md), preserving
  channels/profile/typed settings. Verify that v1 remains channel-only, cancelled
  and invalid restores preserve work, legacy clearing requires confirmation, and
  the embedded editor adds no CSV form fields. Run axe and narrow-layout checks
  with that editor expanded. Check channel-only autosave and v1 download feedback,
  the visible profile/settings reminder even after a v2 download request, and
  confirmation/cancellation before clearing a nonempty plan, preserving its preview.
- Preview/add the [ISS receive-only satellite pack](satellite-presets.md), checking
  explicit confirmation, nominal-frequency roles, TX-disable CSV, v2 round trip,
  duplicate skipping and preservation of profile/settings. Cancel an in-flight
  review and inject a review-service failure without replacing channels or
  autosave. Check keyboard activation, axe and narrow layouts.

The custom-tone duplication regression exposed a real defect: assigning a select
value to a fresh card discarded codes/tones absent from its conventional options.
Duplication now uses the existing draft serialization/card-population functions,
which add the required selectable options before assignment. Both a browser test
and a simulated-DOM regression check preserve those values and polarities.

Tests use accessible locators for interaction, existing `data-field` attributes
only to inspect the complete saved field set, and observable-state assertions.
There are no arbitrary sleeps, forced clicks or automatic retries. Unexpected
page JavaScript exceptions and application-script console errors fail the test.
Normal happy-path journeys use real application APIs, downloads, storage and
card functions. A satellite fault-path test deliberately holds a real review
request to test cancellation, then injects HTTP 503 to test preservation/error
feedback. It does not replace successful review/download tests or relax shared
page-error checks.
One isolated settings test deliberately aborts only the controller-script request
to verify fail-closed UI behavior; it asserts that exact expected resource
failure and no page exceptions, without changing the shared error-checking
fixture for normal journeys.

## Diagnostics and CI

The **Browser journeys** GitHub Actions job has a three-entry engine matrix:
`chromium`, `firefox` and `webkit` on Ubuntu. Each job installs Python, locked npm
dependencies and only its own managed browser and system dependencies, then runs
only `<engine>-desktop` and `<engine>-narrow` (55 cases). This avoids running all
165 cases three times. Matrix fail-fast is disabled so an engine failure does not
cancel diagnostics from the other engines. The existing Python and simulated-DOM
JavaScript jobs remain separate.

An HTML report is written to `playwright-report/`. Failed tests retain a trace,
screenshot, assertion details, and (where relevant) axe/application-error JSON.
Downloaded synthetic backup/CSV files are saved only to `test-results/`, not your
Downloads folder. Videos are disabled. These generated directories and
`node_modules/` are ignored by Git. CI uploads only the two test-output directories
with seven-day retention under distinct `chromium-test-results`,
`firefox-test-results` and `webkit-test-results` artifact names, including after
test failures; it never uploads your profile or personal files.

By default a new local run replaces the previous report/output. To retain each
engine's diagnostics when running separate commands, use a separate output and
HTML report directory for each, for example in PowerShell:

```powershell
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/firefox'
npm run test:e2e -- --project=firefox-desktop --project=firefox-narrow --output=test-results/firefox
Remove-Item Env:PLAYWRIGHT_HTML_OUTPUT_DIR
```

Use the corresponding engine name for Chromium/WebKit. On a POSIX shell, prefix
the test command with `PLAYWRIGHT_HTML_OUTPUT_DIR=playwright-report/firefox`.
These directories stay within the existing ignored diagnostic roots.
Open a separately retained report with, for example,
`npx playwright show-report playwright-report/firefox`.

Inspect a trace locally with `npx playwright show-trace path/to/trace.zip`.
Tests should continue to use synthetic data: traces can include page contents and
test-server request bodies. A successful local Windows run does not verify the
Ubuntu CI runner; the actual Actions run must confirm that environment.

## Verification record

The 2026-11-26 expansion was exercised on Windows 11 Home, version
10.0.26300 (64-bit), Node.js 24.22.1 and Python 3.13.15, starting from commit
`40b1fea22fd21c4dd77a41aa47d71a8a48f11d65` plus the uncommitted browser-coverage
changes. The managed builds launched successfully: Chromium 156.0.8078.4
(Playwright revision 1248), Firefox 157.0 (1555), WebKit 27.2 (2370).
All full-suite runs used two workers, zero retries, the unchanged assertions and
the production entry point's unchanged defaults: concurrency limit 16 and
five-second keep-alive timeout.

| Engine | Desktop / narrow result | Total | Retained local report |
| --- | --- | --- | --- |
| Chromium | 27 passed / 27 passed | 54 passed (2.3 minutes) | `playwright-report/chromium/` |
| Firefox | 22 passed, 5 failed / 19 passed, 8 failed | 41 passed, 13 failed (3.3 minutes) | `playwright-report/firefox/` |
| WebKit | 26 passed, 1 failed / 25 passed, 2 failed | 51 passed, 3 failed (3.5 minutes) | `playwright-report/webkit/` |

The per-engine commands above were run through the installed Playwright CLI with
`PLAYWRIGHT_HTML_OUTPUT_DIR=playwright-report/<engine>` and
`--output=test-results/<engine>`. Discovery separately verified that each CI
command selects exactly 54 cases belonging to its own engine. CI YAML parsing
also checked the engine matrix, selected-browser installation, distinct diagnostic
artifact names and failure upload condition. Other CI jobs and top-level
permissions are unchanged.

### Firefox: parallel-run capacity finding, not a cleared engine

All 13 failed cases stopped at `tests/e2e/builder.fixture.mjs:19`, expecting the
initial single channel card and receiving zero. Every retained failing trace has
HTTP 503 responses for `/builder` or required scripts, including
`/static/builder.js?v=11`. The server repeatedly logged `Exceeded concurrency limit`.
The affected test bodies therefore did not establish their intended behavior:

| File and case start lines | Failed project(s) |
| --- | --- |
| `tests/e2e/journeys.spec.mjs`: 27 (JSON round trip), 46 (invalid backup) | Desktop |
| `tests/e2e/loadout-v2.spec.mjs`: 22 (v2 round trip); 47 (cancelled/invalid restore) | Narrow for 22; desktop and narrow for 47 |
| `tests/e2e/radio-profiles.spec.mjs`: 5 (pilot review/export), 24 (blocking/reset) | Narrow |
| `tests/e2e/radio-settings.spec.mjs`: 35 (cancel/edit/clear), 103 (missing controller); 64 (layout/keyboard), 85 (generic/disabled JS) | Desktop for 35/103; narrow for 64/85 |
| `tests/e2e/satellite-presets.spec.mjs`: 39 (preserved work), 54 (cancellation/service failure) | Narrow |

A bounded diagnostic reran only the two affected desktop `journeys.spec.mjs` cases
on a separate loopback server, with one worker and the same server limits. Both
passed (14.2 seconds). This supports a parallel-runner/server-capacity interaction;
it does not prove all Firefox cases pass serially, establish end-user capacity,
or erase the original failures. The diagnostic command was:

```powershell
$env:RADIO_LOADOUT_E2E_PORT = '8138'
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/firefox-isolated'
npx playwright test tests/e2e/journeys.spec.mjs --project=firefox-desktop --workers=1 --grep='real JSON download|invalid backup keeps existing' --output=test-results/firefox-isolated
Remove-Item Env:PLAYWRIGHT_HTML_OUTPUT_DIR
Remove-Item Env:RADIO_LOADOUT_E2E_PORT
```

Do not count this diagnostic as a full Firefox pass. The configured two-worker
run and its diagnostics remain intact. The next step is to characterize concurrent
browser connections and the intended proxy path, then review the runner/server
capacity arrangement. Application code, server limits, keep-alive settings and
assertions were not changed to suppress the finding.

### WebKit: navigation policy and narrow-layout timeout

The desktop and narrow keyboard journeys at `tests/e2e/accessibility.spec.mjs:74` failed on their
first Tab: the `RL Radio Loadout` link was not focused. A separate, application-free
probe created a native link, button and input and pressed Tab three times. Chromium
and Firefox focused `link`, `button`, `input`; this Windows WebKit focused
`button`, `input`, `BODY`. This reproduces a navigation-policy difference without
Radio Loadout scripts or CSS. It does not establish its cause or behavior on Linux,
macOS Safari or iPhones. No forced focus, injected tab indices, browser-specific
assertion exclusions or keyboard-policy override was added. The next step is to
check this same assertion on the Linux CI build and assess the browser's native
keyboard policy before proposing any application change.

The narrow `visible controls fit the viewport and remain reachable without
clipping` case (`tests/e2e/accessibility.spec.mjs:29`) exhausted the existing
45-second test budget at `control.scrollIntoViewIfNeeded()` (line 39), while
waiting for element stability. Its trace shows the control-by-control check still
running. This is an incomplete geometry check, not a confirmed overflow/clipping
assertion failure or a pass. The timeout, scroll action and geometry assertions
are unchanged. Investigate the trace and Linux run to distinguish runner timing,
element stability and an application layout defect before changing behavior.

No browser was missing or failed to launch on this Windows runner. The Firefox
HTTP failures, WebKit native-link navigation difference and WebKit timeout remain
separate findings. No small application portability fix was established; no
application code was changed. All 162 configured cases were attempted without
skips or automatic retries. These failures are outstanding verification gates,
not accepted exceptions, and the added matrix keeps the assertions that expose them.

The updated Ubuntu CI matrix has not been executed; only its YAML and project
filtering were checked locally. Real Safari/iPhone, touch and manual accessibility
testing remain unverified. Windows CHIRP application verification and unresolved
provenance findings remain separate and pending.

## Follow-up investigation (2026-11-26)

The initial results above are retained, including their failures. This follow-up
used the same checkout, browser builds, server concurrency limit of 16,
five-second keep-alive timeout and existing assertions. No application files,
test files, dependency pins, timeouts or retry settings were changed. The pending
Playwright configuration and CI matrix were preserved without modification.

### Full Firefox run with one worker

```powershell
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/firefox-serial-1'
npx playwright test --project=firefox-desktop --project=firefox-narrow --workers=1 --output=test-results/firefox-serial-1
Remove-Item Env:PLAYWRIGHT_HTML_OUTPUT_DIR
```

All 54 cases ran: **48 passed, 6 failed (5.1 minutes)**. Each viewport had 24
passes and 3 failures. All six failures again stopped at the initial channel-card
assertion in `builder.fixture.mjs:19`; every failure trace contains HTTP 503 for
required scripts, including `builder.js`, with server concurrency warnings.

| Failed case | Project(s) |
| --- | --- |
| `loadout-v2.spec.mjs:22`, full-loadout round trip | Firefox desktop |
| `radio-profiles.spec.mjs:24`, blocking/reset | Firefox desktop and narrow |
| `radio-settings.spec.mjs:103`, missing controller | Firefox desktop |
| `radio-settings.spec.mjs:85`, generic/disabled JavaScript | Firefox narrow |
| `satellite-presets.spec.mjs:39`, preserved work | Firefox narrow |

The run failed, so the requested condition for a second full consistency run was
not met; no repeat was run and no engine-specific worker setting was adopted.
One worker reduces simultaneous tests but does not reliably avoid the capacity
failure. The earlier two-case isolated pass is not a substitute for this result.
This confirms a server rejection under this runner, rather than a missing browser
or an established importer/exporter defect. The connection lifecycle/keep-alive
cause and production proxy implications still require investigation. Raising
limits or adding delays/retries was not used as a remedy.

### WebKit keyboard policy: native reproduction and source evidence

The following minimal reproduction is preserved independently of application
markup, scripts and CSS. Run from the repository root with the locked Playwright
installation. Each sequence uses a fresh page; no programmatic focus is injected.

```powershell
@'
import { chromium, firefox, webkit, devices } from '@playwright/test';
for (const [engine, type] of Object.entries({chromium, firefox, webkit})) {
  const browser = await type.launch();
  try {
    const profiles = [['default', {}]];
    if (engine === 'webkit') profiles.push(['Desktop Safari', devices['Desktop Safari']]);
    for (const [profile, options] of profiles) {
      for (const key of engine === 'webkit' ? ['Tab', 'Alt+Tab'] : ['Tab']) {
        const page = await browser.newPage(options);
        await page.setContent('<a id="link" href="#target">Link</a><button id="button">Button</button><input id="input" aria-label="Input">');
        const order = [];
        for (let n = 0; n < 3; n++) {
          await page.keyboard.press(key);
          order.push(await page.evaluate(() => document.activeElement.id || document.activeElement.tagName));
        }
        console.log(JSON.stringify({engine, version: browser.version(), profile, key, order}));
        await page.close();
      }
    }
  } finally { await browser.close(); }
}
'@ | node --input-type=module
```

Observed on this Windows runner:

| Engine / context | Key | Focus order |
| --- | --- | --- |
| Chromium default | Tab | link, button, input |
| Firefox default | Tab | link, button, input |
| WebKit default and Desktop Safari descriptor | Tab | button, input, BODY |
| WebKit default and Desktop Safari descriptor | Alt+Tab | button, input, BODY |

This rules out Radio Loadout markup/CSS and the Desktop Safari descriptor as the
source of the observed native-link omission. The pinned Playwright
[WebKit upstream configuration](https://github.com/microsoft/playwright/blob/v1.64.1/browser_patches/webkit/UPSTREAM_CONFIG.sh)
identifies WebKit base revision `56453fdfe0b0ca6258c23e6453b34f70b885d13f`.
At that revision, the official
[TabsToLinks preference](https://github.com/WebKit/WebKit/blob/56453fdfe0b0ca6258c23e6453b34f70b885d13f/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml)
defaults true for GTK/WPE and false otherwise. The
[native event handler](https://github.com/WebKit/WebKit/blob/56453fdfe0b0ca6258c23e6453b34f70b885d13f/Source/WebCore/page/EventHandler.cpp)
uses the client's keyboard-navigation mode and only inverts link tabbing for
Option-Tab on Cocoa. These platform defaults explain the Windows observations;
they are not evidence that application links need extra tab indices. The project
does not configure a keyboard preference or custom launch argument for WebKit.
Linux GTK/WPE is expected to differ based on that source; it has not been run here.

**Proposed equivalent interaction, not implemented:** retain the exact ordered
locators, focus/visible-focus assertions, keyboard activation, value checks and
live-feedback checks. Run the unchanged Tab journey on a WebKit platform with
native link tabbing enabled. For a future Cocoa-hosted check, validate the
documented Option-Tab gesture (`Alt+Tab` in Playwright) for each forward traversal
instead of bypassing links or calling `.focus()`.
[Apple's keyboard guide](https://support.apple.com/en-lamr/guide/safari/cpsh003/mac)
documents this gesture and the Safari preference that swaps Tab behavior; the
[Playwright maintainer response](https://github.com/microsoft/playwright/issues/5609)
also recommends that gesture, in a Mac discussion from 2021. It is not a validated
Windows alternative: the current Windows reproduction explicitly shows it does
not include the link. No keyboard assertion or test interaction was changed.
Real macOS Safari/iPhone verification remains separate.

### WebKit scrolling: isolated failure and cumulative runner cost

The original narrow geometry case was run unchanged in isolation, with one
worker, a separate loopback server and tracing retained:

```powershell
$env:RADIO_LOADOUT_E2E_PORT = '8138'
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/webkit-scroll-isolated'
npx playwright test tests/e2e/accessibility.spec.mjs --project=webkit-narrow --workers=1 --grep='visible controls fit the viewport' --trace=on --output=test-results/webkit-scroll-isolated
Remove-Item Env:PLAYWRIGHT_HTML_OUTPUT_DIR
Remove-Item Env:RADIO_LOADOUT_E2E_PORT
```

**Isolated result: 1 failed (45.8 seconds)** at the existing 45-second test limit,
still in `scrollIntoViewIfNeeded()` at line 39. The original trace reached the
320-pixel viewport after 27.6 seconds at 375 pixels; the isolated trace reached it
after 28.1 seconds. All geometry assertions for 375 pixels completed before that
transition. The isolated run progressed to control index 61 at 320 pixels before
the deadline; the final recorded action lasted about 0.14 seconds before the
timeout. This is cumulative test work, not one control waiting for 45 seconds.
The 320-pixel pass is incomplete; neither a clipping failure nor a geometry pass
is established for the unchecked controls.

A separate application-free timing probe used 24 native buttons, all already
visible at 375 × 812, no CSS or animation, and the same native
`scrollIntoViewIfNeeded()` call once per button. All bounding rectangles were
checked unchanged before/after. The observed costs were:

| Engine | Total for 24 calls | Median per call |
| --- | --- | --- |
| Chromium | 808 ms | 34 ms |
| Firefox | 948 ms | 33 ms |
| Windows WebKit | 2,938 ms | 121 ms |

The pinned Playwright
[WebKit page implementation](https://github.com/microsoft/playwright/blob/v1.64.1/packages/playwright-core/src/server/webkit/wkPage.ts)
requires five stable animation frames on Windows versus one on other WebKit
platforms. Its
[injected stability check](https://github.com/microsoft/playwright/blob/v1.64.1/packages/injected/src/injectedScript.ts)
also discards very short frames for the Windows WebKit workaround. This accounts
for a platform-specific baseline cost even without application motion. Together
with the traces and focused failure, the evidence supports cumulative runner
overhead as a cause of this timeout, rather than demonstrating a moving or covered
application control. It does not prove every layout check would pass with more time.

No force option, CSS/animation override, timeout increase, assertion removal or
test split was applied. Next examine the same unchanged geometry case on Linux
and profile read-only geometry-query overhead before proposing a bounded test-only
optimization. Keep native scrolling, both widths and every geometry assertion.

Reports and traces for this follow-up are separate from the original full suites:
`playwright-report/firefox-serial-1/`, `test-results/firefox-serial-1/`,
`playwright-report/webkit-scroll-isolated/` and `test-results/webkit-scroll-isolated/`.
Full-suite failures and isolated diagnostic results must not be combined into a
passing engine result. Ubuntu CI, Windows CHIRP and provenance gates remain pending.

## Bounded geometry and connection follow-up (2026-11-26)

The earlier combined-test results above remain historical evidence. This change
splits that geometry work; it does not waive the incomplete 320px check or the
keyboard requirement. Original assertion expressions, control selection, native
scrolling, hit testing, bounds, minimum sizes, overflow and button-text clipping
checks are retained in `checkGeometry` in `tests/e2e/accessibility.spec.mjs`.

### Separate geometry cases and fixture scopes

Desktop projects run the separately named 1440px geometry case. Narrow projects
run separately named 375px and 320px cases. Each case receives its own fresh
context/page, verifies the empty starting draft through the shared fixture, then
restores the same synthetic backup. The configured **45-second per-test limit**
is unchanged. There are no forced interactions, retry settings or skipped cases.

The `@geometry-desktop` / `@geometry-narrow` project filters scope only these
geometry cases to their original viewports. They do not filter shared journeys
or keyboard failures. Discovery before/after confirmed every other original case
in every engine/project remains selected. Counts are now 27 desktop + 28 narrow
= **55 per engine, 165 total**. The extra case is the formerly combined narrow
check, not duplicate desktop execution of narrow checks.

Independent commands, each starting its own test server and fresh fixture:

```powershell
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/webkit-375-split'
npx playwright test tests/e2e/accessibility.spec.mjs --project=webkit-narrow --grep='at 375px' --trace=on --output=test-results/webkit-375-split
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/webkit-320-split'
npx playwright test tests/e2e/accessibility.spec.mjs --project=webkit-narrow --grep='at 320px' --trace=on --output=test-results/webkit-320-split
$env:PLAYWRIGHT_HTML_OUTPUT_DIR = 'playwright-report/webkit-split-suite'
npx playwright test --project=webkit-desktop --project=webkit-narrow --output=test-results/webkit-split-suite
Remove-Item Env:PLAYWRIGHT_HTML_OUTPUT_DIR
```

| Run | Result |
| --- | --- |
| Independent 375px case | 1 passed; case 31.1 s, invocation 34.7 s |
| Independent 320px case | 1 passed; case 29.9 s, invocation 33.4 s |
| Complete WebKit suite after split | 53 passed, 2 failed (3.6 min); both failures are unchanged keyboard journeys |
| 375px geometry within complete suite | Passed, 28.0 s |
| 320px geometry within complete suite | Passed, 26.8 s |
| 1440px geometry within complete suite | Passed, 44.4 s |

These independent passes establish completion of all geometry assertions at both
narrow widths on this Windows WebKit build; they are not a keyboard pass or a
substitute for the full suite result. Reports and traces are retained in the
separate report/output directories shown above.
The full suite used the unchanged two-worker configuration and attempted all 55
cases with zero skips/retries. Desktop had 26 passes/1 keyboard failure; narrow
had 27 passes/1 keyboard failure. Both keyboard failures still stop at the first
navigation link (`accessibility.spec.mjs:80`, assertion helper line 70). Geometry
completion does not resolve them. Chromium/Firefox's new 55-case suites were not
rerun in this bounded follow-up; their discovery/coverage mapping was checked.

### Firefox: single normal load versus cross-context accumulation

Temporary instrumentation lives outside application code under the ignored
`generated/browser-bounded-followup/` directory:
`observe_server.py`, `probe_firefox.mjs`, and the result JSON files below. It uses
Uvicorn's existing `server_options`, production factory and automatically selected
`HttpToolsProtocol` (local Uvicorn 0.53.0). A subclass delegates connection and
response-completion callbacks unchanged, reading the server's connection/task
sets. A read-only 50 ms sampler records count changes; warnings record counts at
the rejection point. Application code and response handling are not replaced.

Each experiment starts a new loopback-only server and Firefox browser, then uses
one fresh context for each normal `/builder` navigation. No startup health GET,
navigation retry, mock, artificial inter-context delay or raised limit is used.
The first experiment has one context; the second has six sequential contexts.
A third fresh-server six-context experiment adds whitelisted path attribution
to server warnings. This is an instrumentation refinement, not a retry of a
navigation to obtain success. All keep the concurrency limit 16 and keep-alive 5 s.

Bounds: one navigation per context, at most six contexts per experiment,
20 observed page requests per navigation, 30 s navigation deadline, 60 s server
watchdog and at most 1,200 telemetry events. After the final context closes,
drain observation ends on zero connections/tasks or after seven seconds, allowing
the existing five-second idle timeout to be observed. This observation interval
does not delay or retry a navigation. Logs contain relative times, counts,
phase names, statuses and whitelisted paths only; query strings, full URLs,
request/response bodies, operator data, credentials and exception payloads are
not recorded. No radio/user backup data was supplied.

| Experiment / result file | Peak connections / tasks | Concurrency warnings | Connections/tasks drained after final context close |
| --- | --- | --- | --- |
| `fresh-context.json` (1 load) | 6 / 7 | 0 | Yes, both zero after 4.948 s |
| `sequential-contexts.json` (6 loads) | 19 / 7 | 15 | Yes, both zero after 4.218 s |
| `sequential-contexts-server-paths.json` (6 loads) | 18 / 7 | 10 | Yes, both zero after 3.027 s |

The single fresh load returned 200 for the document and all seven required
JS/CSS assets, initialized one channel card and had no failed requests. Closing
the context left six idle server connections (zero tasks); they later drained.
The Firefox browser process remained open throughout drain observation and was
closed only afterward, so browser-process shutdown did not cause the recorded drain.
Thus a normal fresh-context load alone did **not** produce 503 in this bounded
observation. This is not a general capacity guarantee.

In both sequences, the first two contexts succeeded. Connections persisted after
each context closed: 6 after the first, 12 after the second, then 14–15 after later
contexts; tasks were zero at the load/close checkpoints. Asset rejections began
on the third context. The original sequence rejected the document on contexts
5–6; the path-attributed sequence rejected it on contexts 4–6. At warning time,
connection counts were 16–18 and task counts 0–4. The installed Uvicorn handler
rejects a request if either set reaches the limit; task saturation was not the
trigger observed here. Counts can briefly exceed 16 because accepted TCP
connections are counted before request rejection; the configured limit was not
increased.

Observed failing paths and roles:

| Path(s), with queries omitted | Result / relevance |
| --- | --- |
| `/static/backup-format.js`, `/static/settings-plan.js`, `/static/loadout-format.js`, `/static/radio-settings.js`, `/static/satellite-presets.js`, `/static/builder.js` | HTTP 503 across the experiments; required builder/profile/settings/backup assets, not optional failures |
| `/builder` | HTTP 503 on later contexts; required document |
| `/favicon.ico` | Three rejection warnings in the path-attributed run; optional favicon, not an explanation that excuses required-asset/document failures |

The path-attributed run's ten server warnings map to four required-script
rejections, three document rejections and three favicon rejections. The browser
page response events captured the seven required script/document 503s; the server
path observations additionally identified the three browser-managed favicon
requests. No JS/CSS 503s occurred in the single fresh load. Document 200/one card
alone does not imply successful initialization of all features when scripts fail.

The evidence establishes cross-context idle-connection accumulation on this
direct Windows test server, explaining why one test worker was insufficient.
It does not assign an upstream bug, establish proxy behavior or justify changing
production limits. No Firefox execution setting was changed. A next investigation
can distinguish browser-process/socket-pool lifetime from context lifetime while
preserving the same assertions and limits. No fixed wait was added to make tests
pass. All three observed runs drained to zero after closure.

Local diagnostic invocation, from the repository root with Node/Python available:

```powershell
node generated/browser-bounded-followup/probe_firefox.mjs
node generated/browser-bounded-followup/probe_firefox.mjs server-paths
```

These ignored scripts/results are local diagnostic evidence, not installed product
files or permanent CI artifacts. Their raw response and count records remain
separate from full-suite pass/fail results.

### Keyboard verification need: exact supported Linux setup

The native-link reproduction and every application keyboard assertion above are
unchanged. Windows Alt+Tab is not substituted, and keyboard verification remains
failed/pending on the tested Windows WebKit build.

The exact supported setup selected for the next independent keyboard check is
**Ubuntu 24.04 x86-64**, Node.js 24 LTS, Python 3.13 with this project's development
dependencies, locked Playwright **1.64.1**, and its managed **WebKit 27.2 / revision
2370 GTK build**, with the engine's required system packages installed. The
installed CLI's Linux-target dry run resolves `webkit-ubuntu-24.04.zip`; no Linux
browser or host was installed/provisioned during this Windows investigation.
Ubuntu 24.04 is listed in Playwright's official
[supported systems](https://playwright.dev/docs/intro#system-requirements).
The pinned WebKit `TabsToLinks` source cited above defaults true for GTK/WPE,
which supports running the original native Tab sequence without application
markup changes or injected focus. Actual behavior still requires execution.

On that explicit Linux runner, from this checkout:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
npm ci
npx playwright install --with-deps webkit
PLAYWRIGHT_HTML_OUTPUT_DIR=playwright-report/webkit-linux-keyboard npm run test:e2e -- --project=webkit-desktop --project=webkit-narrow --grep='keyboard tab order, visible focus' --output=test-results/webkit-linux-keyboard
```

That last command runs the **two complete keyboard journeys**, not a replacement
native-link probe: exact focus order, visible focus, keyboard activation, edited
values and live feedback must all pass. Then run the complete WebKit suite on
the same runner; passing the focused journeys alone is not full-engine approval.
The existing pending CI matrix remains on `ubuntu-latest`; identify its actual
runner image before calling it this exact setup. Neither that CI run nor this
explicit Ubuntu check was executed here. This is a separate verification need,
not a passed gate or verification of real Safari/iPhones. Windows CHIRP and
provenance findings remain pending.

## Firefox browser lifecycle follow-up (2026-11-27)

The Firefox projects now use a fresh browser process for each test. The test-scoped
fixture in `tests/e2e/browser.fixture.mjs` launches Firefox through the runner's
`playwright` fixture and closes the process during teardown. Playwright keeps its
built-in `browser` fixture worker-scoped. Its default Firefox browser and context
are initialized as fixture dependencies and remain idle while the test uses the
disposable process. The two settings tests that create a second context use the
same disposable process as the main page. Chromium and WebKit use the built-in
browser and context as before. [Playwright fixture API](https://playwright.dev/docs/test-fixtures#overriding-fixtures)

The local Windows measurement used the temporary observer described above and
six consecutive normal builder loads on one fresh server. Each load used a
new Firefox process and context. After each context closed, the observer still
counted five or six connections. After each process closed, it counted **zero
connections and zero tasks**, before the next process launched. Peak counts were
six connections and seven tasks. The document and every required asset returned
200 on all six loads, each rendered one channel card, and the server emitted zero
concurrency warnings. The path/status and count-only evidence is retained locally
in `generated/browser-bounded-followup/sequential-processes.json`. The launcher
`probe_firefox_processes.mjs` and existing observer live in the same ignored
directory.

The earlier shared-process experiment remains the comparison. Idle connections
survived context closure, accumulated to the Uvicorn connection gate and triggered
503s for required scripts and the builder document. The process change removes
that accumulation in the measured test sequence. Production retains the same
16-connection concurrency limit and five-second keep-alive timeout.

Launching and closing a process in the six-load probe took **1.15–1.89 seconds
per test** combined (median 1.35 s), excluding navigation and assertions. This is
a local overhead measurement. The earlier suite with early failures cannot serve
as a like-for-like runtime baseline.

Both complete Firefox runs used the existing two workers and zero retries.
Each passed **55/55** cases (27 desktop and 28 narrow) in **3.5 minutes**.
Neither run emitted a Uvicorn concurrency warning. Local reports are in
`playwright-report/firefox-process-1/` and `playwright-report/firefox-process-2/`.
To rerun the full Firefox scope:

```sh
npm run test:e2e -- --project=firefox-desktop --project=firefox-narrow
```

An isolated, deliberately failing fixture diagnostic first checked Firefox
process selection, the 375 × 812 viewport, user agent, base URL navigation and
empty draft. It reached the deliberate failure and produced a screenshot,
trace and error context under `test-results/firefox-fixture-diagnostic/`.
That diagnostic is excluded from normal test discovery.

The full Chromium regression passed **55/55** in **2.1 minutes**. The focused
WebKit narrow geometry run passed **2/2** in **26.6 seconds**. The 375px case took
22.9 seconds and the 320px case took 22.3 seconds. The 45-second per-test limit
and all geometry and keyboard assertions were preserved.

The Ubuntu CI matrix and the documented Linux WebKit keyboard check remain
pending. The Windows WebKit keyboard assertions and native-link reproduction
are preserved. This run provides no new Safari/iPhone, Windows CHIRP or
provenance evidence.

## WebKit focus and connection follow-up (2026-11-27)

[CI #23](https://github.com/TimothyThurston/radio-loadout/actions/runs/46040468943)
on Ubuntu 26.04 passed 52/55 WebKit cases. Both keyboard journeys failed at the
ISS repeater checkbox and one builder initialization failed.
[CI #24](https://github.com/TimothyThurston/radio-loadout/actions/runs/46041649869)
ran the pinned Ubuntu 24.04 image (OS 24.04.5), before the fixes below. Chromium and
Firefox each passed 55/55. WebKit 27.2, revision 2370, passed 51/55 including all
three geometry cases. Both keyboard journeys failed the visible-focus assertion
with the ISS repeater checkbox active. The settings and satellite desktop cases
failed during builder initialization. The traces contain HTTP 503 for
`radio-settings.js`, `satellite-presets.js` and `builder.js` in the settings case,
and `satellite-presets.js` and `builder.js` in the satellite case. Uvicorn logged
five concurrency-limit warnings. These CI runs did not measure server connection
and task counts. Their failures remain part of the verification record.
[CI #24 WebKit artifact](https://github.com/TimothyThurston/radio-loadout/actions/runs/46041649869/artifacts/15220032557)

### Native checkbox focus

A focused Windows WebKit 27.2 probe used Tab to reach the real
`Include ISS RPT RX` checkbox on the builder and measured the CSS before and
after the change. The standard whole-page keyboard journeys still use their
original sequence. The probe stops at the checkbox, so it can inspect this
control despite the Windows build's earlier link-tabbing limitation.

| Measured property | Before CSS change | With checkbox outline |
| --- | --- | --- |
| `document.activeElement` is the expected checkbox | true | true |
| Matches `:focus-visible` | true | true |
| Outline style | `none` | `solid` |
| Outline width | `3px` | `3px` |
| Outline color | `rgb(238, 252, 247)` | `rgb(82, 230, 165)` |
| Outline offset | `0px` | `4px` |
| Box shadow | `none` | `none` |

The shared input rule applies `outline: none`. The builder's satellite
checkbox sits outside the settings-guide and form-field outline rules. The
general `input:focus` rule declares a shadow, but WebKit computed `none` for
this native checkbox. The new `input[type="checkbox"]:focus-visible` rule
provides a 3px solid outline in the existing accent color with a 4px offset.
The focused label screenshot visibly shows the mint ring around the checked
native control. The local screenshots are in `test-results/webkit-checkbox-before/`
and `test-results/webkit-checkbox-visual/`.

If either original focus assertion fails, the test attaches individual
focus/CSS values and a viewport PNG before rethrowing the original error.
The capture reads the current keyboard state without moving focus or scrolling.
The existing test and assertion timeouts, order and activation checks are intact.

### WebKit connection measurements

An ignored, test-only probe at
`generated/browser-bounded-followup/probe_webkit_processes.mjs` used the existing
read-only Uvicorn observer on Windows. It ran one normal builder load per context
with the desktop WebKit project options. Each scenario started a separate
loopback server using the production factory, concurrency limit of 16 and
five-second keep-alive. The observer captured connection/task counts at
navigation, response completion and closure, and at any concurrency warning.
It recorded whitelisted paths and response codes, with no bodies, headers,
credentials or operator data. There were no delays between loads.

| Scenario | Loads | Peak connections / tasks | Checkpoint after context close | Checkpoint after process close | Rejections / warnings |
| --- | ---: | --- | --- | --- | --- |
| Fresh server and single context | 1 | 6 / 6 | 5 connections, 0 tasks | 0 / 0 | 0 / 0 |
| Repeat contexts with browser retained | 6 | 6 / 7 | 5 connections, 0 tasks after each close | 0 / 0 after closing the retained browser | 0 / 0 |
| Close browser process between loads | 6 | 6 / 7 | 5 connections, 0 tasks after each close | 0 / 0 before every next launch | 0 / 0 |

Every document and required asset returned 200 and every load produced one
channel card. With WebKit retained, each subsequent load started with five open
connections. The count stayed flat across this Windows sequence. These
measurements establish socket retention and release on process closure. They
do not establish accumulation to the limit or explain the Linux CI rejections.

WebKit now uses the same disposable-process fixture as Firefox to release the
measured idle connections at teardown. Both engines close their test context
and browser in `finally` blocks. The runner's Playwright instance still applies
project options and the artifact hooks. Chromium continues using its built-in
browser and context. The production server settings are unchanged.

### Local Windows verification

Two full WebKit desktop/narrow runs each finished with **53 passed, 2 failed**
in **2.8 minutes** using two workers and zero retries. The two failures were the
existing first-link Tab check in both viewports. They stopped before reaching the
checkbox. All three geometry cases passed in both runs. Neither run had an
initialization failure or a Uvicorn concurrency-limit warning. Both focus
attachments were present in each of the four failure traces, with the expected
link's active-element and focus-visible fields both false.

Local reports are under `playwright-report/webkit-focus-lifecycle-1/` and
`playwright-report/webkit-focus-lifecycle-2/`. Chromium passed **55/55** in
**1.9 minutes** and Firefox passed **55/55** in **3.2 minutes**, each including
both original keyboard journeys and all geometry checks. Their reports are in
`playwright-report/chromium-focus-regression/` and
`playwright-report/firefox-focus-regression/`. Ruff, pytest (968 passed and
three existing skips), 140 JavaScript tests, JavaScript syntax and packaging
smoke passed. The isolated checkbox probe passed
with the measured outline and visible ring above. The complete keyboard journeys
and connection behavior with these changes still need verification on the pinned
Ubuntu 24.04 runner. PR #1 remains at its previously tested commit and both CI
failures remain historical results. Real Safari/iPhone, Windows CHIRP and
provenance verification remain separate and pending.

Implementation references: Playwright's official
[browser installation and scope](https://playwright.dev/docs/browsers),
[multi-browser projects](https://playwright.dev/docs/test-projects),
[web-server configuration](https://playwright.dev/docs/test-webserver),
[CI setup](https://playwright.dev/docs/ci-intro),
[accessibility testing guidance](https://playwright.dev/docs/accessibility-testing),
and the official [artifact upload action](https://github.com/actions/upload-artifact).
