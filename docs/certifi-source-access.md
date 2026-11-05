# Certifi source references for recipients

Prepared 2026-11-05 for the reviewed staging environment. Certifi's covered
material retains its [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/)
terms and existing notices, independently of Radio Loadout's PolyForm Strict
license. The project's terms do not restrict recipients' MPL rights.

| Included material | Upstream source |
| --- | --- |
| Application certifi **2026.10.23** | [Exact source archive](https://files.pythonhosted.org/packages/fd/11/b524cbd9bbdaca58608e4cf4053fd463417549e1959fa8d3aa18319f9555/certifi-2026.10.23.tar.gz) |
| certifi **2026.6.17** in base pip, venv pip and ensurepip | [Exact certifi source](https://files.pythonhosted.org/packages/c9/c7/424b75da314c1045981bd9777432fad05a9e0c69daa4ed7e308bbaffe405/certifi-2026.6.17.tar.gz) and [pip 26.2.1 source](https://files.pythonhosted.org/packages/ae/15/4500e320e6b101ec3b719ae85b697d9940b6cda672bc555bd6016fc60c6f/pip-26.2.1.tar.gz) for its namespace-modified Python wrappers |

These official upstream URLs were checked at review time. The
[evidence review](certifi-source-review.md) lists all four installed locations,
notices, archive hashes, exact release commits and correspondence limits. The
[machine-readable manifest](../scripts/certifi-source-manifest.json) also pins
source snapshots containing certifi's update helpers.

From the checkout or an unpacked Radio Loadout source archive, with Python 3.11+:

```sh
python scripts/retrieve_certifi_sources.py --download-dir generated/certifi-sources
python scripts/retrieve_certifi_sources.py --download-dir generated/certifi-sources --offline
```

This downloads five original source archives, checks their hashes and selected
source/notice bytes, and writes `receipt.json`. It does not extract, install,
execute, publish or update certificate trust. The second command checks a retained
copy without network access. These sources retain their upstream license notices.

**Remaining limitation:** both certifi releases' historical Mozilla input revision
and generator response remain unidentified. Matching the shipped PEM does not
alone establish complete preferred source for modification. No project source
mirror or enduring recipient delivery arrangement has been published. Upstream
links, local downloads and expiring CI diagnostics are not a project retention
commitment. Before redistribution, the owner still needs to select and maintain
source delivery alongside releases or an appropriate stable access arrangement,
including any further required inputs. Supply this guide and the selected access
instructions with any future image distribution. This guide is not a completed compliance
assessment or a grant of additional rights in Radio Loadout.
