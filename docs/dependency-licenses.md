# Direct dependency license inventory

Recorded 2026-11-01 from project manifests/lock files and upstream package
metadata. This is an inventory and review checklist, not a license clearance
opinion or a new license for Radio Loadout.

| Direct dependency/tool | Recorded version | Reported license | Scope/source |
| --- | --- | --- | --- |
| FastAPI (`standard` extra) | 0.162.0 in runtime lock | MIT | Runtime; [upstream license](https://github.com/fastapi/fastapi/blob/master/LICENSE), [release metadata](https://pypi.org/pypi/fastapi/0.162.0/json) |
| build | 1.6.1 | MIT | Development/image build; [metadata](https://pypi.org/pypi/build/1.6.1/json) |
| setuptools | 84.2.1 in build lock | MIT | Build backend (`>=77` in project); [metadata](https://pypi.org/pypi/setuptools/84.2.1/json) |
| pytest | 9.1.1 inspected locally | MIT | Development, unpinned in project; [metadata](https://pypi.org/pypi/pytest/9.1.1/json) |
| Ruff | 0.16.8 inspected locally | MIT | Development, unpinned in project; [metadata](https://pypi.org/pypi/ruff/0.16.8/json) |
| `@playwright/test` | 1.64.1 | Apache-2.0 | Browser tests; [license](https://github.com/microsoft/playwright/blob/main/LICENSE), pinned npm lock |
| `@axe-core/playwright` | 4.14.0 | MPL-2.0 | Accessibility tests; [upstream project](https://github.com/dequelabs/axe-core-npm), pinned npm lock |
| uv | 0.13.6 | MIT OR Apache-2.0 | Optional direct lock-generation tool; [metadata](https://pypi.org/pypi/uv/0.13.6/json); not installed into image |

The Python base image includes CPython (PSF licensing and bundled notices) and
Debian packages with multiple licenses. Browser downloads and Node/npm have
their own licenses. These are separate from the direct Python/npm dependency
table and must be included in a full distribution inventory.

Items still needing review:

- Radio Loadout has no selected project license. **Absence of a LICENSE file
  does not grant general reuse, modification or redistribution permission.**
  Do not describe the project/image as licensed for public reuse. The rights
  holder must make that decision; see GitHub's [no-license explanation](https://choosealicense.com/no-permission/).
- Review all transitive dependencies selected by `fastapi[standard]`, including
  CLI, telemetry, native wheels and their bundled components. The Linux runtime
  lock currently resolves 59 distributions; the direct FastAPI MIT license is
  not a substitute for their individual licenses/notices.
- Retain and review copyright/license/NOTICE files when distributing an image.
  MIT and Apache identifiers do not remove notice obligations. Review Apache
  notices and any modifications/distribution involving the MPL-2.0 accessibility
  package; the test package is not part of the runtime image.
- Review CPython, Debian, pip/bootstrap packages, native wheel contents and any
  browser binaries shipped separately. Docker is unavailable locally, so an OS
  package/license inventory and final image inspection have not been performed.
- Recheck the inventory when changing locks or tools. Python dev dependencies
  are not fully locked by `pyproject.toml`; observed local versions are not a
  promise about every future install. Runtime/build locks pin the container's
  dependency inputs but are not a legal or vulnerability audit.

No Radio Loadout license has been chosen and no third-party rights are granted
by this document.
