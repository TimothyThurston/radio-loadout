# Real-browser tests

The Playwright suite uses managed **Chromium** at 1440 × 1000 and 375 × 812.
The narrow layout check also checks 320-pixel width. These are desktop Chromium
viewports: Firefox, WebKit, real mobile devices, touch interaction, and manual
screen-reader behavior remain unverified. Automated axe checks complement manual
accessibility assessment; they do not establish full WCAG compliance.

## Install and run

Use Python 3.11+ and Node.js 24 LTS with npm. From the repository root, install
the project in your virtual environment, then the locked browser dependencies:

```sh
python -m pip install -e ".[dev]"
npm ci
npx playwright install chromium
npm run check:syntax
npm run test:js
npm run test:e2e
```

On Linux machines without browser system libraries, use
`npx playwright install --with-deps chromium` instead. CI uses this command.
`package-lock.json` locks Playwright, axe, and their transitive dependencies;
Playwright selects its matching Chromium build. No global Playwright installation
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

Useful commands:

```sh
npm run test:e2e -- --project=chromium-desktop
npm run test:e2e -- --project=chromium-narrow
npm run test:e2e:headed
npm run test:e2e -- --grep "real JSON download"
npm run test:e2e:report
```

The headed command still opens a disposable Playwright browser, never your
normal browser profile. No tests use persistent contexts, personal downloads,
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

The custom-tone duplication regression exposed a real defect: assigning a select
value to a fresh card discarded codes/tones absent from its conventional options.
Duplication now uses the existing draft serialization/card-population functions,
which add the required selectable options before assignment. Both a browser test
and a simulated-DOM regression check preserve those values and polarities.

Tests use accessible locators for interaction, existing `data-field` attributes
only to inspect the complete saved field set, and observable-state assertions.
There are no arbitrary sleeps, forced clicks or automatic retries. Unexpected
page JavaScript exceptions and application-script console errors fail the test.
Tests do not stub the application APIs, downloads, storage, or card functions.

## Diagnostics and CI

The separate **Browser journeys (Chromium)** GitHub Actions job installs Python,
locked npm dependencies and managed Chromium on Ubuntu. Both viewport projects
must pass. The existing Python and simulated-DOM JavaScript jobs remain separate.

An HTML report is written to `playwright-report/`. Failed tests retain a trace,
screenshot, assertion details, and (where relevant) axe/application-error JSON.
Downloaded synthetic backup/CSV files are saved only to `test-results/`, not your
Downloads folder. Videos are disabled. These generated directories and
`node_modules/` are ignored by Git. CI uploads only the two test-output directories
with seven-day retention; it never uploads your profile or personal files.

Inspect a trace locally with `npx playwright show-trace path/to/trace.zip`.
Tests should continue to use synthetic data: traces can include page contents and
test-server request bodies. A successful local Windows run does not verify the
Ubuntu CI runner; the actual Actions run must confirm that environment.

Implementation references: Playwright's official
[web-server configuration](https://playwright.dev/docs/test-webserver),
[CI setup](https://playwright.dev/docs/ci-intro),
[accessibility testing guidance](https://playwright.dev/docs/accessibility-testing),
and the official [artifact upload action](https://github.com/actions/upload-artifact).
