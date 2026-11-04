# Supplemental third-party notices — bundle 1

Recorded 2026-11-04 for Radio Loadout's Linux amd64 staging environment.
These texts belong to their respective third-party copyright holders and retain
their upstream terms. Radio Loadout's PolyForm Strict license does not apply to
them. The bundle supplements existing installed notices; it does not replace or
remove any package's license files.

`manifest.json` identifies each component/version, exact source archive URL and
SHA-256, applicable notice files, extraction locations and evidence limits. The
reviewed uvloop/Pydantic Core wheel members match the installed-image binary
hashes recorded there. Files under `libuv/` preserve libuv's own LICENSE and
LICENSE-extra and the complete original tree.h BSD and inet.c ISC comment blocks.
They are separate from uvloop's own MIT/Apache notices.

`icu4x/LICENSE.txt` is byte-identical across the listed ICU code/data crates and
includes the original ICU/IBM acknowledgement. The listed source defaults enable
compiled data through idna. A complete upstream feature-selected build/link map
was not obtained; the manifest distinguishes source-chain evidence from exact
versioned paths observed in the binary. `pyo3/` preserves both upstream license
alternatives, also identical in pyo3-ffi and the PyO3 runtime copies. `url/`,
`idna/` and `idna_adapter/` preserve notices for the related source dependency path.
No assertion is made that every Cargo.lock dependency is included in the binary.

The installed bundle is at `radio_loadout/third_party_notices/v1/` inside the
project package. It travels with the wheel/source archive and through the wheel
into the runtime image; dependencies themselves are not bundled in the project
wheel. It is supporting distribution documentation, not browser-delivered code.
The archive audit checks exact bytes, and CI separately checks the final image's
collected installed files against every bundle file and the reviewed native hashes.

This is a limited notice supplement, not a complete bill of materials, legal
clearance or a permission to redistribute Radio Loadout. Other native notices,
binary inclusion, CHIRP provenance and certifi/OS/Python source-access questions
remain open. Public source URLs and temporary diagnostic artifacts do not by
themselves provide an enduring recipient source-access arrangement.
