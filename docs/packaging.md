# Building and verifying the installable package

Radio Loadout supports Python 3.11+. Its wheel contains the Python application,
both HTML templates, CSS, `builder.js`, `backup-format.js`, and the centralized
`input-limits.json` resource. These files are loaded relative to the installed
package, so serving the application does not require a repository checkout or
the current directory to contain `src/`.

## Build both distributions

From a development environment with the project installed:

```sh
python -m pip install -e ".[dev]"
python -m build
```

This produces `dist/radio_loadout-0.1.0.tar.gz` and
`dist/radio_loadout-0.1.0-py3-none-any.whl` at the current project version.
The default `build` command first creates the source archive, then builds the
wheel from that archive in isolated build environments. This checks that the
source distribution contains the inputs needed to build the wheel.

The source archive also includes Python/JavaScript/browser tests, synthetic
fixtures, docs, npm manifests/lockfile, browser configuration, and smoke scripts.
It includes the Dockerfile, context allowlist and deployment dependency locks.
It intentionally excludes virtual environments, node modules, browser output,
bytecode, Git metadata, personal configuration and generated distributions.
The wheel contains runtime files and distribution metadata, not development tests.

Package discovery is restricted to regular `radio_loadout` packages; implicit
namespace discovery is disabled. Runtime package data uses explicit patterns in
`pyproject.toml`, independently of the development files selected by `MANIFEST.in`.
This prevents documentation/test files from entering the wheel. The two empty,
unreferenced files formerly under `importers/src/radio_loadout/importers` were
accidental duplicates; the smoke audit rejects their reappearance in an archive.

## Install a wheel without the checkout

Create a new virtual environment outside the repository and install the actual
wheel file by absolute path. For example, on PowerShell (adjust the wheel path):

```powershell
python -m venv "$env:TEMP\radio-loadout-install"
& "$env:TEMP\radio-loadout-install\Scripts\python.exe" -m pip install 'C:\path\to\radio_loadout-0.1.0-py3-none-any.whl'
Set-Location $env:TEMP
& "$env:TEMP\radio-loadout-install\Scripts\python.exe" -I -m uvicorn radio_loadout.web.app:app --host 127.0.0.1 --port 8000
```

On POSIX shells, use an external virtual environment's `bin/python` in place of
`Scripts/python.exe`. Open `http://127.0.0.1:8000/` or `/builder`. No editable
install, `PYTHONPATH`, npm runtime, or external template/static directory is needed
to run the installed application. Node/Playwright are development-test tools.

## Automated packaging smoke check

```sh
python scripts/smoke_package.py
```

The driver uses only the standard library plus the `build` development dependency:

1. Build a new sdist and a wheel from it into a fresh temporary artifact directory.
2. Audit both archives. Every runtime file must match the source bytes; required
   assets must exist. Verify source-archive development files/fixtures as well,
   and reject unexpected payloads, caches, nested duplicates and environment files.
3. Create a fresh virtual environment and a separate working directory under the
   system temporary directory, both outside the repository. Remove inherited
   Python path/home settings and install the wheel with isolated pip configuration.
   The system temporary directory must be outside the repository.
4. Run `pip check`, then copy the standalone probe into that external working
   directory and execute it with the fresh environment's `python -I`. Assert
   that imports come from that environment, no repository path appears on
   `sys.path`, and the install is not editable. Check installed file hashes.
5. Start an installed Uvicorn server on an ephemeral loopback port. Through real
   HTTP, verify homepage/builder rendering, every referenced local JS/CSS asset
   including cache-busting URLs, `backup-format.js`, and the limits JSON resource.
6. Verify the sample CSV download, a two-channel synthetic custom CSV export,
   UTF-8 BOM multipart CSV upload, identical re-export, and compatibility reports
   for both supported channels and unsupported DMR. Stop the server afterward.

The installed HTTP probe uses the staging factory and verifies minimal health
plus oversized-input rejection too. Staging smoke and container commands are described
in [staging deployment](staging.md).

No runtime application or test fixture is imported from the checkout by the
probe. It uses no personal files, browser profiles or stored drafts. Installing
dependencies and isolated build requirements needs access to a package index;
build/runtime dependencies are resolved against the declared project requirements,
not a fully pinned Python dependency lock.

The wheel, source archive, `distribution-contents.json` inventory and build/
install/dependency/probe logs are retained in the ignored `dist/` directory.
Temporary environments are removed after the run, including failures. To retain
the artifacts elsewhere, use `python scripts/smoke_package.py --dist-dir PATH`.
The command does not delete existing output directories or publish anything.
Do not use `python -O`/`PYTHONOPTIMIZE`: probe assertions are deliberately enabled.

The separate GitHub Actions packaging job runs this command on Python 3.11 and
3.13 under Ubuntu and retains package artifacts/logs for seven days. The existing
source tests and browser job remain separate. Local Windows verification does not
substitute for running that Ubuntu job remotely.

Configuration references: official
[build usage](https://build.pypa.io/en/stable/),
[setuptools package discovery](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html),
and [package-data configuration](https://setuptools.pypa.io/en/latest/userguide/datafiles.html).
