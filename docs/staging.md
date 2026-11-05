# Production staging preparation

These files prepare a staging deployment; they do not provision a host, configure
external infrastructure or publish an image. Original project material is covered
by [PolyForm Strict 1.0.0](../LICENSE); see [COPYRIGHT](../COPYRIGHT) for scope. No
database, user accounts, or external service credentials are required by the app.

## Local container build and smoke test

Prerequisites: Docker with Linux-container access and Python 3.11+ for the local
standard-library smoke driver. Build from a reviewed checkout:

```sh
docker build --platform linux/amd64 --tag radio-loadout:staging-candidate .
docker run --detach --name radio-loadout-staging --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m,mode=1777 --cap-drop ALL \
  --security-opt no-new-privileges --memory 512m --cpus 1 --pids-limit 128 \
  --publish 127.0.0.1:8000:8000 radio-loadout:staging-candidate
python scripts/staging_smoke.py --base-url http://127.0.0.1:8000
docker stop --time 40 radio-loadout-staging
docker rm radio-loadout-staging
```

These commands bind only the local computer's loopback port. The smoke driver
accepts only an HTTP loopback URL and uses synthetic channels/files. It waits for
observable health, checks health/headers, homepage, builder, exact packaged asset
bytes, downloads, CSV export/BOM import/re-export, compatibility, and HTTP 413 for
oversized CSV and both submitted-JSON endpoints. It logs results, not payloads.

Readiness retries only startup connection failures: resets, refused/aborted
connections, broken pipes, timeouts, and premature disconnects/incomplete reads.
Retries, per-attempt socket timeouts and pauses use the finite readiness budget
(`--wait-seconds`, default 30). The final connection error is reported on expiry.
HTTP errors (including 400/500), invalid health bodies, assertions and configuration
errors fail immediately. The subsequent workflow checks are not retried or ignored.

CI captures the last 200 container log lines plus only status, exit code,
`OOMKilled` and runtime error before cleanup, even when smoke testing fails.
The `staging-container-diagnostics` artifact is retained for seven days. No full
container inspect, environment dump or Docker log `--details` is used. These logs
are for the synthetic CI test container only. Inspect them for startup crashes,
OOM kills or configuration errors; connection retries are not evidence that the
application started correctly. Collection/upload failures do not turn checks green,
and cleanup still runs after diagnostics.

The same job now collects final-image package and license evidence after smoke
testing with `if: always()`, before diagnostics upload and cleanup. The collector
uses the staging container's immutable image ID (or the build IID if startup
never created the container), then probes separate equally restricted,
network-disabled containers. It inventories base Python, `/opt/venv`, vendored
pip/ensurepip components, Debian binary/source versions, existing notices and
bounded native evidence. Buildx `--load` supplies selected build-image identifiers
where available without publishing an image. Raw build metadata is kept outside
the uploaded diagnostics directory and is not uploaded.

See [final-image inventory collection](image-inventory.md) for commands, exact
output scope, limits, partial-failure handling and review requirements. The
seven-day artifact is diagnostic evidence, not permanent source access or a
license-compliance determination. The supplied checksum-verified CI artifact
establishes successful collection for the [recorded image](native-component-notices.md);
Docker remains unavailable locally. The new supplemental native notice bundle
travels as package data through the wheel into `/opt/venv`. An additional
`always()` step verifies its exact collected installed bytes and reviewed native
identities before upload/cleanup, even after smoke failures. Its result is
`supplemental-notices-check.json` in the same seven-day diagnostics. Verification
of that payload **passed in CI #11** at exact commit
`ec248268cf25d031b1042f7e7c42b1d2f2bdc9da`; see the
[run and artifact evidence](native-component-notices.md#ci-11-gate-verified--2026-11-05).
Neither collection nor this byte gate completes source-access/compliance review.
The [certifi recipient guide](certifi-source-access.md) identifies the two actual
versions and source retrieval steps, with preferred-input and maintained-access
limitations still open.

The multi-stage Dockerfile uses Python **3.13.15 slim Bookworm**, pinned to an
official-image manifest digest. Python 3.13 remains security-maintained according
to the [official support table](https://devguide.python.org/versions/). Build and
runtime dependencies are pinned with hashes. The builder makes a normal wheel;
the final image receives only a virtual environment containing that wheel and
its runtime dependencies. It runs as UID/GID **10001**, with no editable install,
source checkout, reload mode, tests, Node modules, backups or build tools. The
`.dockerignore` allowlist limits even the build context to reviewed inputs.

The locks target **Linux amd64 / Python 3.13**. Other architectures and actual
container execution require verification; a Windows source/package test does
not establish Linux image compatibility. Pinning inputs does not promise a
byte-identical OCI image across Docker/BuildKit versions. The fixed build epoch
stabilizes wheel timestamps. Refresh the base digest and dependency locks during
security maintenance, review the diff, and rerun all checks; do not retain stale
pins indefinitely. No image vulnerability scan is implied by the smoke tests.

Regenerate locks deliberately using the recorded resolver version:

```sh
python -m pip install uv==0.13.6
uv pip compile deploy/build-requirements.in --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --generate-hashes --no-annotate --no-header --output-file deploy/requirements-build.lock
uv pip compile pyproject.toml --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --generate-hashes --no-annotate --no-header --output-file deploy/requirements-runtime.lock
```

The existing `fastapi[standard]` runtime extra is retained, including its CLI and
transitive dependencies. Hashes/pins control resolution, not license approval or
vulnerability status. Preserve dependency license notices. The image's OS and
binary components still need their own inventory/review.

## Server configuration

The container runs `python -I -B -u -m radio_loadout.web.serve` (isolated imports,
no bytecode writes, unbuffered output). The same module can be
run from an installed wheel for local staging without Docker. The factory
`radio_loadout.web.production:create_app` creates an independent web application
and wraps it with the existing trusted-host and security/error boundaries.

### API documentation in production and development

Production/staging disables Swagger UI (`/docs`), ReDoc (`/redoc`), and the
Swagger OAuth redirect (`/docs/oauth2-redirect`). Requests to those routes return
404 with the production security headers and `Cache-Control: no-store`. The
production homepage hides **View API**. The homepage and builder load no
documentation CDN, Google Fonts, or FastAPI favicon assets.

Raw **`/openapi.json` remains available** as JSON under the same trusted-host
controls and production headers. It describes the existing application endpoints
without loading interactive documentation scripts, fonts, or favicons. This
change does not add authentication or restrict access to that schema.

For development, the existing command
`uvicorn radio_loadout.web.app:app --reload` retains Swagger UI, ReDoc, the OAuth
redirect, raw OpenAPI JSON, and the homepage **View API** link. The shared endpoint
router is registered on independently configured FastAPI instances; creating a
staging instance does not remove routes from or otherwise reconfigure the
development instance. Builder, validation, import/export, input limits, host
controls, error privacy, and the existing security-header policy are preserved.

Regression coverage lives in `tests/test_api_documentation.py` and
`tests/e2e/production-docs.spec.mjs`. The local staging and isolated installed-wheel
smoke checks also verify the production 404s, absent links/assets, and available
JSON schema. The browser test blocks and records external requests while loading
the production homepage and builder, and requires none. See the dated API-doc
follow-up in [the dependency review](dependency-license-review.md) for results
and remaining verification limits; other licensing findings remain open.

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | IP bind address inside the container; publish only to loopback/private ingress. Use `127.0.0.1` for direct local wheel testing. |
| `PORT` | `8000` | Integer 1–65535; update container port mapping/ingress if changed. |
| `RADIO_LOADOUT_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated exact DNS/IPv4 hostnames, without schemes, ports or wildcards. Add the chosen staging hostname. Localhost/127.0.0.1 remain allowed for health. |
| `RADIO_LOADOUT_FORWARDED_ALLOW_IPS` | empty | Forwarded headers disabled. Set only actual proxy IPs/CIDRs; `*` and `/0` are rejected. |
| `RADIO_LOADOUT_CONCURRENCY` | `16` | Per-process Uvicorn concurrency limit; saturation returns 503. Not a rate limit or sizing guarantee. |
| `RADIO_LOADOUT_KEEP_ALIVE` | `5` | Idle keep-alive timeout, seconds; not a request-processing deadline. |
| `RADIO_LOADOUT_SHUTDOWN_TIMEOUT` | `30` | Graceful request-drain timeout, seconds. Give the process a longer termination grace period. |
| `TMPDIR` | `/tmp` in image | Writable, ephemeral multipart-upload storage, bounded separately by tmpfs/platform quota. |

One worker, backlog 128, no reload, no access log, warning-level server logs, and
no Uvicorn `Server` header are explicit settings. Invalid settings fail startup.
Measure memory/CPU, slow clients, keep-alive connections, uploads, and saturation
before raising concurrency or selecting a host size. Multiple replicas are
possible because channel state is not stored on the server.

## Hosting/ingress controls still required

Choose a staging host/domain, restrict staging access using the hosting platform's
existing access controls, and keep the backend off the public network. Host
validation is not authentication. Terminate TLS at a trusted reverse proxy or
platform ingress; redirect HTTP to HTTPS there. Configure certificates, renewal,
TLS policy, and HSTS at that edge only after the actual hostname/TLS setup is
verified. No HSTS or redirect loop is imposed on local HTTP tests.

The proxy must preserve an allowed Host and **replace**, not blindly relay,
client-supplied forwarding headers. Configure forwarded-header trust only for
that proxy's network addresses. Never expose the backend directly while trusting
an arbitrary client network. Uvicorn supports these controls as documented in its
[settings reference](https://uvicorn.dev/settings/).

Application policy remains centralized in `web/static/input-limits.json`:
CSV 2 MiB, submitted `channels_json` 4 MiB, 5,000 CSV records, 2,000 channels,
64 KiB bounded CSV reads. JSON backups are browser-local with a 4 MiB file limit.
The server enforces its policies even when browser checks are bypassed. Report
messages/text are also bounded. See [input-limit details](imports-and-limits.md).

These are logical application bounds, not a maximum total HTTP request body.
Multipart parsing may spool to disk before endpoint reads begin. For the ingress,
configure and test at least:

- A total HTTP-body ceiling, for example **16 MiB**, including form/multipart
  overhead. A 4 MiB decoded JSON field can occupy about 12 MiB when percent-encoded.
  Return a clear 413 at the edge; do not disable application bounds.
- Header/part counts and header sizes, upload/read timeout (for example 30 s),
  proxy connect timeout (5 s), and upstream response timeout (60 s). These are
  starting points to measure, not application-enforced total request deadlines.
- Connection/concurrency/rate limits, CPU/memory/process quotas, and an ephemeral
  upload-storage quota. The local example uses 512 MiB memory and 256 MiB tmpfs;
  tmpfs consumes memory. Aggregate body buffering must fit the actual quota.
- Bounded proxy body buffering/storage as well as backend `/tmp`; cleanup on
  worker/container termination; handling of quota exhaustion and interrupted uploads.

The container/server do not configure a proxy, TLS, rate limiting, a whole-request
deadline, or a total-body middleware. All remain deployment responsibilities.

## Errors, headers and logging

`GET /healthz` returns only `{"status":"ok"}`. It is liveness, not a complete
asset/dependency/readiness audit; run the smoke command before promoting an image.

The staging boundary enforces exact trusted hosts and adds `nosniff`, frame denial,
and `Referrer-Policy: no-referrer` to application responses. Dynamic/HTML/CSV/error
responses use `Cache-Control: no-store`; static caching and download disposition
remain intact. Proxy-generated 413/502/503 responses need their own safe headers.

Useful 4xx validation details remain available to the requesting user. Unhandled
500 errors stay generic, with no traceback or configuration in the response.
The outer HTTP boundary records only the exception class, without its value or
traceback, and prevents the original exception reaching the server error logger.
Debug mode is rejected. CSP is deliberately deferred: the existing API docs load
CDN assets and the builder embeds JSON configuration; an untested blanket policy
could break them. Review a tested CSP when those routes/assets are deliberately
changed; this is not a claim of complete browser hardening.

Do not enable access/body/trace logging for channel workflows. Avoid raw client
IP addresses, full URLs/query strings, filenames, channel names/frequencies,
comments, uploaded bytes, validation inputs or browser storage in telemetry.
Use aggregate status/latency/saturation metrics. Configure proxy/platform logs
with the same exclusions, limited retention and restricted access; their default
logs may contain client IPs and request URLs. Never attach personal backups to
CI diagnostics. App-specific safe logging does not sanitize third-party ingress
or tracing agents; review those integrations before enabling them.

## Rollout, persistence and rollback

Before a future deployment, run Ruff, Python/JavaScript/browser checks, packaging
smoke and the container smoke on the target platform. The CI container job builds
and runs only a local test image; it does not push or deploy. Record the verified
image digest, source revision, lock files and non-secret runtime settings. Decide
hosting, access restriction, domain/TLS, proxy trust, resource quotas, monitoring,
and the [outstanding license reviews](dependency-licenses.md) before publication.

There is **no server database or persistent application volume**. Uploads and
exports are transient. Drafts are stored in the browser's localStorage, scoped
to the browser/profile/origin; backups are user-controlled downloaded files.
Changing the staging origin does not transfer drafts. Ask users to export JSON
backups before changing origins or future draft-schema migrations. Preserve TLS
material and deployment configuration through the platform's own managed storage,
not by writing them into this image.

For a future rollout: retain the previous tested image/config, start the candidate
on a separate private target, run smoke checks, then switch traffic through the
chosen platform only after review. For rollback, switch back to the recorded
previous digest/config, drain the candidate for up to the configured shutdown
timeout, and verify health plus a synthetic workflow. No database rollback is
needed today. Do not clear browser storage as a rollback step. Future backup/draft
schema changes require an explicit compatibility/migration plan.
