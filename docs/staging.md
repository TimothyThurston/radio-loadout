# Production staging preparation

These files prepare a staging deployment; they do not provision a host, configure
external infrastructure or publish an image. Original project material is covered
by [PolyForm Strict 1.0.0](../LICENSE); see [COPYRIGHT](../COPYRIGHT) for scope. No
database, user accounts, or external service credentials are required by the app.

## Owner-only Droplet runbook — plan only, 2026-11-12

Safety follow-up reviewed **2026-11-26**; the host steps remain unexecuted.

**No deployment has been performed by preparing this runbook.** The steps below
are for a future, separately approved owner-operated evaluation. They do not
provision a Droplet, buy a plan, install software, publish an image or authorize
public launch. Keep the [release disposition](v1-release-disposition.md) and its
provenance/operator decisions open. [Windows CHIRP verification](chirp-verification.md)
remains pending; neither HTTPS nor a successful smoke test completes that matrix.
Use synthetic channels/files only, a disposable owner browser profile, and no
radio connection. Preserve PolyForm Strict and third-party notices.

### Topology and initial capacity

```text
Owner's approved, signed-in Tailscale device
  -> private HTTPS :443 on the Droplet's exact *.ts.net name (Tailscale Serve)
  -> HTTP 127.0.0.1:8080 (host Nginx)
  -> HTTP 127.0.0.1:8000 (Docker loopback publication -> container :8000)
```

The only remote application entry is Serve on the tailnet. Neither Nginx nor
Docker may listen on the Droplet's public, VPC or Tailscale address. Do not enable
Funnel, a public load balancer, public DNS pointing to the app, a subnet router,
an exit node, or direct public ports 80/443/8000/8080. Serve's certificate does
not require opening public HTTPS. See the [Serve reference](https://tailscale.com/docs/reference/tailscale-cli/serve).

Start with a **Basic, 1 vCPU, 1 GiB RAM, Linux amd64 Droplet**, using an updated
supported Ubuntu LTS host. Confirm the selected architecture/size in the plan
before any future purchase; [DigitalOcean lists a 1 GiB Basic option](https://www.digitalocean.com/pricing/droplets).
This is a starting point for one owner, not a measured capacity guarantee.
The application limit is 512 MiB including its tmpfs pages; Nginx, Tailscale,
Docker and the OS need the remaining memory. Set Nginx's service `MemoryMax=128M`
and `TasksMax=32` as initial host limits, then measure headroom and failures.

**Building the image on 1 GiB is unverified and may need more memory.** Prefer
building/testing the same Linux amd64 Dockerfile on an adequately sized owner
machine, retaining a `docker save` archive/checksum and loading that exact image
privately over owner SSH. Review the provider/image handoff under the release
disposition; it is not public image publication. Do not build alongside the
running app on this VM. If a build is attempted later, stop on OOM/exit 137 or
memory pressure: build elsewhere or request a separately approved temporary
larger VM/resize. Do not automatically upgrade, add swap containing upload data,
or weaken runtime limits to make a build pass.

### Setup order (future operator actions only)

1. **Record decisions before provisioning.** Name Timothy Thurston as the sole
   operator/audience, record the chosen region/size, recovery method and private
   image-transfer arrangement. Keep the five pending repository changes out of
   any staging/reset/commit operation; use a separate clean checkout of a reviewed
   immutable revision for a future build. This runbook does not select an
   uncommitted working tree as a release.
2. **Close the cloud firewall first.** Attach a DigitalOcean Cloud Firewall to
   the future Droplet with no public inbound application ports, for IPv4 and
   IPv6. If bootstrapping SSH is necessary, allow TCP 22 only from the owner's
   current exact public `/32` or `/128`, with SSH keys, not an all-address rule.
   Keep the bootstrap SSH session open. Before removing that temporary rule,
   verify an actual login through DigitalOcean's out-of-band **Recovery Console**
   and a second, independent working SSH session over Tailscale, as described
   below. The regular Droplet Console is not the recovery path. Permit required
   outbound package/time/DNS and Tailscale
   control/relay traffic; outbound-only relay access is acceptable. Do not open
   public app/proxy ports to improve Tailscale connectivity. Review both cloud
   and host rules: [Cloud Firewalls are separate from the host firewall](https://docs.digitalocean.com/products/networking/firewalls/how-to/configure-rules/).
3. **Prepare the host behind that firewall.** Apply OS updates; install supported
   Docker Engine, Nginx, Python 3 and Tailscale from their official package
   instructions. Use a maintained Docker Engine, at least 28.0.0: older releases
   have a [documented localhost-publication isolation caveat](https://docs.docker.com/engine/network/port-publishing/).
   Use owner key-based OpenSSH and sudo; Docker control is root-equivalent.
   Configure a host firewall with public-interface input denied, loopback
   allowed, established traffic allowed, and only the intended Tailscale
   management/HTTPS traffic permitted on `tailscale0`. Account for Docker's
   forwarding rules; do not rely on UFW alone to protect published ports. Stop
   Nginx after installation and disable its packaged wildcard/default listener
   before starting the loopback configuration below. Do not alter tailscaled's
   required firewall integration blindly or lock out the tested recovery path.
4. **Require approved devices and owner-only rules before enabling Serve.** In
   the dedicated staging tailnet's admin console, enable **Device approval**
   under Device management before enrolling further devices. Review all devices
   already present, including their identity, ownership, approval and sharing
   state; revoke/remove unintended devices rather than assuming the new setting
   rechecks them. Enroll and manually approve only the intended owner clients and
   the Droplet under `tag:radio-loadout-staging`. Do not use pre-approved auth keys
   or automatic approval to bypass this review. Keep auth keys/tokens out
   of shell history, Git and diagnostics. Enable tailnet MagicDNS/HTTPS for the
   node's non-sensitive machine name. Certificate names enter public transparency
   logs even though the site is private; see [Tailscale HTTPS](https://tailscale.com/docs/how-to/set-up-https-certificates).
   Record the actual FQDN; replace every example below with it. Do not share the
   node, grant broad member access or enable a Funnel capability for it.
5. **Load/build and verify the exact image**, still without Serve. Use the
   identity record and restricted container command below, run the existing
   loopback smoke test, and verify inventory/notice/wrapper gates for that exact
   candidate. Do not assign an older CI image's evidence to a newly built one.
6. **Configure bounded Nginx on loopback**, test its configuration and local
   health/limits. Confirm no packaged site or IPv6 wildcard listener remains.
   Configure persistence for the bounded temporary mount before enabling the
   service; verify the container/Nginx/Tailscale restart behavior locally.
7. **Enable only private Serve HTTPS**, then complete every access/limit check
   below, including the negative tests. Keep staging closed if one fails or
   remains unverified. No public launch or artifact release follows automatically.

### Verify recovery and a second SSH path before closing public SSH

Use DigitalOcean's [Recovery Console](https://docs.digitalocean.com/products/droplets/how-to/recovery/recovery-console/):
Droplet **Settings → Recovery console → Launch Console**, not the regular
network-dependent Droplet Console. Verify a real local login, `whoami` and sudo/root
access; seeing a login prompt is insufficient. Retain the local recovery password
in the owner's password manager, never Git or diagnostics. A console password
does not require network SSH passwords: keep effective `PasswordAuthentication no`,
`KbdInteractiveAuthentication no`, `PubkeyAuthentication yes` and
`AuthenticationMethods publickey`. Check `sshd -t` and effective `sshd -T -C ...`
settings for both public and Tailscale source addresses, including Match overrides,
before a reload; do not terminate the working bootstrap session.

If a console credential is unavailable, establish one for the existing local
recovery account while the bootstrap session still works, or use the control
panel's [Reset root password](https://docs.digitalocean.com/support/how-do-i-reset-my-droplets-root-password/)
procedure and complete any required password change **in the Recovery Console**.
Do not enable SSH password/keyboard-interactive login. If reset/login fails, plan
a maintenance outage, safely power down and select **Boot from Recovery ISO**.
Use the [Recovery Console/ISO workflow](https://docs.digitalocean.com/products/droplets/how-to/recovery/recovery-iso/)
to mount the installed disk, reset a local password or repair the owner's
authorized_keys/configuration using the recovery shell/chroot. The ISO has its
own credentials/SSH configuration: keep public ingress closed and use its console,
not rescue-network SSH. Return to **Boot from Hard Drive**, then reverify installed
SSH policy, local recovery login and owner access. Do not overwrite unrelated keys
or waive host-key verification to work around rescue-system keys.

Before withdrawing the temporary public SSH rule, **all three paths must be in
hand**: leave the original bootstrap session open; complete the Recovery Console
login above; and open a second key-only OpenSSH session from an approved owner
device to the Droplet's Tailscale IP/name. Use a new TCP connection (disable SSH
multiplexing with `-o ControlMaster=no -o ControlPath=none`), verify the host key
against the trusted console/bootstrap record, then check `whoami`, the SSH
connection's tailnet addresses and sudo. Remove only the temporary public rule
after these succeed; open another fresh Tailscale session afterward before closing
the bootstrap session. If any prerequisite fails, retain the restricted bootstrap
rule and stop to repair it; do not substitute a successful Droplet Console login.

### Owner-only policy, not merely tailnet membership

Serve is private to the tailnet, not inherently restricted to one user. The
dedicated tailnet must have [device approval enabled](https://tailscale.com/docs/features/access-control/device-management/device-approval),
with its existing Machines list reviewed before Serve is enabled. Pending devices
must remain unable to communicate; an owner login alone is not device approval.
An already-approved unfamiliar device must be revoked/removed. Approval and the
owner-only network grant are separate requirements; keep both and review any
broader ACL/grant that could also allow access.
The following is a minimal policy example for a dedicated staging tailnet; substitute
the owner's actual Tailscale login selector (it need not be an email). In an
existing tailnet, review/merge deliberately without overwriting unrelated policy.
Remove or narrow any other ACL/grant that permits non-owner access to this tag.
Grants are additive: a narrow rule cannot override an existing broad allow. See
[grants syntax](https://tailscale.com/docs/reference/syntax/grants).

```json
{
  "tagOwners": {"tag:radio-loadout-staging": ["OWNER_LOGIN"]},
  "grants": [
    {"src": ["OWNER_LOGIN"], "dst": ["tag:radio-loadout-staging"],
     "ip": ["tcp:443", "tcp:22"]}
  ],
  "tests": [
    {"src": "OWNER_LOGIN", "proto": "tcp",
     "accept": ["tag:radio-loadout-staging:443", "tag:radio-loadout-staging:22"],
     "deny": ["tag:radio-loadout-staging:8000", "tag:radio-loadout-staging:8080"]}
  ]
}
```

TCP 22 is conventional key-based OpenSSH over the tailnet here; Tailscale SSH is
not enabled by this example. `tagOwners` authorizes tag assignment, not app login.
Use untagged owner client devices so their owner identity matches the source.
Protect owner/admin accounts and restrict who can change policy. Add a policy
test using an existing non-owner identity/tag that must be denied ports 22 and
443; never add an allow for that identity just to test it. The policy editor's
[accept/deny tests](https://tailscale.com/docs/reference/syntax/policy-file#tests)
are assertions, not extra access rules. With no available non-owner test device,
record the real-device negative test as unverified; do not claim it passed.

### Image identity and restricted runtime

Future commands below assume Bash on the owner-controlled Linux build host,
from a clean checkout. Do not run them while preparing this documentation.
Use fresh output/name values, never replace an existing record or prune rollback
images. For example, when a build is separately approved:

```sh
set -eu
test -z "$(git status --porcelain)" || { echo 'Use a clean reviewed checkout'; exit 1; }
RELEASE_COMMIT=$(git rev-parse HEAD)
RECORD_DIR=$(mktemp -d "$HOME/radio-loadout-stage-record-XXXXXX")
chmod 700 "$RECORD_DIR"
printf '%s\n' "$RELEASE_COMMIT" > "$RECORD_DIR/commit.txt"
sha256sum Dockerfile deploy/requirements-build.lock deploy/requirements-runtime.lock \
  > "$RECORD_DIR/inputs.sha256"
docker buildx build --load --platform linux/amd64 \
  --iidfile "$RECORD_DIR/image-id" .
IMAGE_ID=$(cat "$RECORD_DIR/image-id")
test "$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE_ID")" = linux/amd64
docker image inspect --format '{{.Id}}' "$IMAGE_ID"
```

If transferring an existing image, bind its source commit and input checksums to
the build record, checksum the saved archive before/after transfer, load it and
verify the expected image ID and `linux/amd64`. A mutable tag is not the identity.
Retain the existing collector's selected base-image identifiers where available;
do not invent a Linux child-manifest digest from the configured multi-platform
digest. Record Docker/OS/Python/Nginx/Tailscale versions, non-secret settings,
policy/configuration hashes, date and smoke/gate results in an owner-private
record. Do not dump environment variables, auth material or full Docker inspect.

On the future Droplet, set `IMAGE_ID` to that verified ID, `STAGING_FQDN` to its
exact lower-case `*.ts.net` name, and a fresh `CONTAINER_NAME`. Then use the
existing hardened runtime, with no source/backup/config bind mounts:

```sh
set -eu
: "${IMAGE_ID:?Set the verified image ID}"
: "${STAGING_FQDN:?Set the actual Tailscale FQDN}"
: "${CONTAINER_NAME:?Choose a fresh container name}"
docker run --detach --name "$CONTAINER_NAME" --restart unless-stopped \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m,mode=1777 \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 512m --memory-swap 512m --cpus 1 --pids-limit 128 \
  --log-driver local --log-opt max-size=5m --log-opt max-file=2 \
  --env RADIO_LOADOUT_ALLOWED_HOSTS="$STAGING_FQDN" \
  --env RADIO_LOADOUT_FORWARDED_ALLOW_IPS= \
  --env RADIO_LOADOUT_CONCURRENCY=8 \
  --publish 127.0.0.1:8000:8000 "$IMAGE_ID"
docker inspect --format '{{.Image}}' "$CONTAINER_NAME"
docker exec "$CONTAINER_NAME" python -I -B -c 'import os,platform; assert os.getuid()==10001; print(platform.python_version())'
python3 scripts/staging_smoke.py --base-url http://127.0.0.1:8000
```

Run the standard-library smoke driver from a matching clean source checkout on
the host; do not install development tools into the image. The UID remains the
Dockerfile's 10001. The empty forwarded-header trust setting is deliberate;
authorization is enforced by Tailscale, not an untrusted forwarded identity/IP.
`--memory-swap 512m` with the same memory limit prevents container swap usage;
verify host support. Monitor with selected state/health, `docker stats --no-stream`,
`free -m` and the OOM flag, not channel payload logs. If host headroom is inadequate,
stop and assess capacity; do not silently raise concurrency or allocate two
512 MiB containers on this 1 GiB host.

### Nginx loopback configuration and limits

Install the following example in the host's Nginx `http` include directory
(for example `/etc/nginx/conf.d/radio-loadout.conf`); replace **all** instances of
`radio-loadout-stage.EXAMPLE.ts.net` with the actual lower-case FQDN. Remove the
packaged default site/listeners while preserving unrelated host configuration.
Use a dedicated host: no other proxy/site may forward to this app.

Before starting Nginx, provision `/run/radio-loadout-nginx` as a **64 MiB tmpfs**,
`nosuid,nodev,noexec`, owned by the actual Nginx worker UID/GID with mode 0700.
Persist it with a reviewed mount unit/fstab entry. **RequiresMountsFor alone is
not a filesystem/cap assertion**: without a dedicated mount definition, an ancestor
filesystem can satisfy the dependency. Keep it and add the explicit startup guard
below. Nginx must fail startup rather than spool to an ordinary directory, another
filesystem or an uncapped/wrong-sized tmpfs. Request streaming and disabled
response buffering avoid ordinary proxy disk copies; the cap also bounds fallback
temporary files.

On the future host only, install this example as
`/usr/local/libexec/radio-loadout-check-upload-mount.py`, root-owned mode 0755 in a
root-owned, non-writable-by-workers directory. It is a **host configuration
example**, not a new project/application file. It checks the service's own
[Linux mount namespace](https://man7.org/linux/man-pages/man5/proc_pid_mountinfo.5.html),
requires one dedicated filesystem at the exact path, explicit fixed size and
actual capacity of 67,108,864 bytes, and rejects ambiguous/shared mounts. No
upload or temporary file is written by the check.

```python
# Host-only example: radio-loadout-check-upload-mount.py
import os
import sys
from pathlib import Path

TARGET = "/run/radio-loadout-nginx"
CAP = 64 * 1024 * 1024


def validate_mount(mountinfo, capacity):
    rows = []
    for line in mountinfo.splitlines():
        left, separator, right = line.partition(" - ")
        fields, filesystem = left.split(), right.split()
        if not separator or len(fields) < 6 or len(filesystem) < 3:
            raise ValueError("malformed mount information")
        rows.append((fields, filesystem))
    matches = [(fields, fs) for fields, fs in rows if fields[4] == TARGET]
    if len(matches) != 1:
        raise ValueError("exact dedicated mount is missing or ambiguous")
    fields, fs = matches[0]
    if fields[3] != "/" or fs[0] != "tmpfs":
        raise ValueError("upload mount must be a tmpfs root")
    if sum(row[2] == fields[2] for row, _ in rows) != 1:
        raise ValueError("upload filesystem is shared with another mount")
    options = fields[5].split(",") + fs[2].split(",")
    if not {"rw", "nosuid", "nodev", "noexec"}.issubset(options) or "ro" in options:
        raise ValueError("required upload mount protections are missing")
    sizes = [option.lower() for option in options if option.startswith("size=")]
    if len(sizes) != 1 or sizes[0] not in {"size=65536k", "size=64m", "size=67108864"}:
        raise ValueError("explicit fixed 64 MiB upload cap is missing or wrong")
    if capacity != CAP:
        raise ValueError("actual upload capacity is not 64 MiB")


def main():
    try:
        path = Path(TARGET)
        if not path.is_dir() or path.resolve(strict=True) != path:
            raise ValueError("upload path is missing or resolves through a symlink")
        mountinfo = Path("/proc/self/mountinfo").read_text(encoding="utf-8")
        stats = os.statvfs(TARGET)
        validate_mount(mountinfo, stats.f_frsize * stats.f_blocks)
    except (OSError, ValueError):
        print("Nginx refused: upload storage is not a dedicated protected 64 MiB tmpfs.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Add a host `nginx.service` drop-in with the following directives; **append** this
pre-start check, retaining the package's existing `ExecStartPre`/`nginx -t` checks
and other service configuration. Do not prefix it with `-`, clear the existing
pre-start list or replace it with a condition that merely skips startup. A failed
[ExecStartPre](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#ExecStartPre=)
must fail the unit before its serving process starts.

```ini
[Unit]
RequiresMountsFor=/run/radio-loadout-nginx

[Service]
ExecStartPre=/usr/bin/python3 -I -B /usr/local/libexec/radio-loadout-check-upload-mount.py
MemoryMax=128M
TasksMax=32
```

Run `systemctl daemon-reload` after installing reviewed host unit changes. Verify
the effective unit retains both the mount dependency and guard; invoke the guard
manually before `nginx -t` or any reload because `ExecStartPre` runs on **start**,
not on reload. All starts must use this service; do not bypass it with a direct
`nginx` invocation. For mount changes stop Nginx and Serve first; never unmount or
remount upload storage beneath a running worker, and never unmount `/run` itself.

**Missing-mount test, maintenance window only:** keep verified recovery and SSH
access, disable Serve and stop Nginx. Retain a copy of this mount's definition;
temporarily withhold only its dedicated mount unit/fstab entry (including any
generated definition), reload systemd and unmount this exact, now-idle path.
Leave the empty ordinary directory present. The guard must exit nonzero. Then
`systemctl start nginx` must fail, with no listener on 8080. Retain
`RequiresMountsFor` and the startup guard during the test. Merely unmounting while
leaving an active definition can let systemd remount it: that is **not** a
missing-mount failure test. Do not use lazy/forced unmounts or suppress a failed
check. Restore the definition, mount it, rerun the guard (exit 0), then clear
the failed state and start Nginx. Recheck loopback health before enabling Serve.

**Controlled reboot check:** with recovery and private SSH verified, test a reboot
and record that the dedicated capped tmpfs exists, the guard exits 0, Nginx is
active and both loopback health checks succeed. Review the unit's startup result
and repeat owner/blocked-access checks. If the mount is not recreated, Nginx must
remain failed/non-serving; repair the mount with Serve off rather than start
Nginx manually. Filesystem/cap failures and this real boot ordering remain host
acceptance tests, not conclusions from example syntax validation.

```nginx
# Inside http {}, not a second nested http block.
map $host $rl_host_ok {
    default 0;
    radio-loadout-stage.EXAMPLE.ts.net 1;
    localhost 1;
    127.0.0.1 1;
}
limit_req_zone $server_name zone=rl_rate:1m rate=10r/s;
limit_conn_zone $server_name zone=rl_connections:1m;

server {
    listen 127.0.0.1:8080 default_server;
    server_name radio-loadout-stage.EXAMPLE.ts.net localhost 127.0.0.1;
    if ($rl_host_ok = 0) { return 400; }
    server_tokens off;
    access_log off;
    error_log /dev/null;

    client_max_body_size 16m;
    client_body_buffer_size 64k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;
    client_header_timeout 15s;
    client_body_timeout 30s;
    keepalive_timeout 5s;
    send_timeout 30s;
    reset_timedout_connection on;
    client_body_temp_path /run/radio-loadout-nginx/body;
    proxy_temp_path /run/radio-loadout-nginx/proxy;
    limit_conn rl_connections 8;
    limit_conn_status 429;
    limit_req zone=rl_rate burst=20 nodelay;
    limit_req_status 429;

    # Apply the same safe headers to proxy errors as to app responses.
    proxy_hide_header X-Content-Type-Options;
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Referrer-Policy;
    proxy_hide_header Cache-Control;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy no-referrer always;
    add_header Cache-Control no-store always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host radio-loadout-stage.EXAMPLE.ts.net;
        proxy_set_header Forwarded "";
        proxy_set_header X-Forwarded-For "";
        proxy_set_header X-Forwarded-Host "";
        proxy_set_header X-Forwarded-Proto "";
        proxy_set_header X-Real-IP "";
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 60s;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_max_temp_file_size 0;
        proxy_next_upstream off;
        proxy_redirect http://radio-loadout-stage.EXAMPLE.ts.net/ https://radio-loadout-stage.EXAMPLE.ts.net/;
    }
}
```

The app still performs host validation and input checks. Nginx rejects unknown
incoming hosts and sends the fixed approved host upstream; client-supplied
forwarding headers are not trusted. The explicit redirect rule preserves HTTPS
for absolute app redirects while forwarding trust stays disabled. This profile
uses no HTTP listener/redirect on port 80. No certificate files enter the image.
See Nginx's [core limits](https://nginx.org/en/docs/http/ngx_http_core_module.html),
[proxy streaming/timeouts](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
[request-rate](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html) and
[active-connection](https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html)
references. The rate/concurrency keys are intentionally **global for this site**:
Serve connects from loopback, not a distinct trusted client IP.

These are starting limits, not a benchmark. App CSV remains 2 MiB, submitted
channel JSON 4 MiB, browser backups 4 MiB, 5,000 CSV records and 2,000 channels.
The larger 16 MiB proxy body cap accommodates form encoding/overhead without
changing app limits. Nginx caps header buffer sizes, not every multipart count;
existing app multipart limits remain in force. Its 30/60-second timeouts are
inactivity intervals, **not a total whole-request deadline**. This owner-only
profile does not claim slow-client/public-service hardening. An abusive or
unexpected long-running client is a stop/review condition, not a reason to
increase limits. No raw access/error/request logging is enabled for this site;
check local config/startup status and synthetic results instead.

Validate with `sudo nginx -t`, then start/reload only after confirming the tmpfs
and service limits. Check `curl --fail http://127.0.0.1:8080/healthz` and
`ss -lntp`: 8000/8080 must be loopback-only, with no `0.0.0.0`, `[::]`, public,
VPC or tailnet listeners on those ports. Review Nginx's effective configuration
locally for residual default sites; do not upload a full config containing secrets.

### Private HTTPS and acceptance checks

Only after policy and both loopback hops pass, a future operator may enable:

```sh
sudo tailscale serve --bg --https=443 http://127.0.0.1:8080
sudo tailscale serve status
```

Serve manages the private HTTPS endpoint/certificate. Verify its exact URL and
target. The read-only `sudo tailscale funnel status` must show no active public
forwarding; see its [status reference](https://tailscale.com/docs/reference/tailscale-cli/funnel).
Never enable Funnel. Background Serve persists
across restarts, so repeat access/listener checks after a controlled reboot.
No public DNS, public port 443 rule, `https+insecure`, public tunnel or command
enabling Funnel is part of setup. Do not serve the checkout, a directory or backup files.

Record date, actual versions/image ID, expected/observed result and pass/fail/
not-run for each check. Use normal certificate validation, not `curl -k`.

| Check | Procedure / required result |
| --- | --- |
| Owner HTTPS | From the owner's signed-in approved client, open the exact Serve URL: `/healthz` is 200 with only `{"status":"ok"}`, `/builder` loads its local assets, synthetic review/export/import works, and no browser TLS warning or unexpected external asset request occurs. Confirm security/no-store headers, docs/ReDoc/OAuth redirect 404, and raw `/openapi.json` 200. Do not infer CHIRP application's behavior from this. |
| Local boundaries | Direct host loopback health works at both 8000 and 8080. Verify the running container's `.Image`, non-root UID, selected health/OOM state, mount/limits and localhost-only Docker publication. Test a non-allowed Host gets 400; it must not be silently routed as the fixed allowed host. |
| Non-owner tailnet | Policy tests must deny non-owner access. From an already available non-owner device, attempt the Serve URL and direct tailnet-IP ports 22/8000/8080: no app/proxy response or login access. The owner also must not reach 8000/8080 remotely. Keep a device test marked not-run if unavailable. |
| Outside tailnet | From a separate network with Tailscale disabled (no exit node, VPN, SSH tunnel or configured HTTP proxy), use bounded connection attempts to the Droplet's public IPv4 and IPv6 at 80/443/8000/8080 and the Serve URL. None may return the application/proxy. DNS failure or routing failure for the private name alone does not test the public IPs. Confirm firewall policy and absence of Funnel as well. Do not open access for the test. |
| App upload limits | Run the existing smoke driver on backend loopback first. Then, from the owner's client in the matching checkout, run the Python snippet below over private HTTPS: each of the three oversized CSV/JSON requests must return 413, showing limits survived both proxies. Also round-trip a small synthetic CSV through the browser. |
| Proxy body ceiling | On the owner's client, create a temporary file of exactly 17 MiB of zero bytes, outside the repo; POST it with a known Content-Length to `/validation/chirp.csv`, for example with `curl --max-time 30 -H 'Expect:' --data-binary @oversized-synthetic.bin -D - -o /dev/null -w '%{http_code}\n' https://ACTUAL_FQDN/validation/chirp.csv` on Linux (use `curl.exe` and `NUL` for the output sink on Windows). Require 413 from the proxy plus safe headers; the app's smaller limits remain unchanged. Never use a personal backup as the body. |
| Recovery / device prerequisites | Before removing public SSH, verify Recovery Console login and a separate new key-only Tailscale SSH connection while the bootstrap session stays open. Record device approval enabled, the already-enrolled device review and the intended clients/node approved; pending/unintended devices must not gain access. |
| Upload mount / reboot | Run the missing-mount negative test above, retaining the guard and RequiresMountsFor: ordinary directory must cause guard nonzero and service-start failure/no 8080 listener. Restore the correct mount for a positive start, then verify the guard, mount cap and boot ordering after reboot. |
| Nginx rate gate | With Serve off and no other test traffic, test loopback 8080 separately: at most 40 synthetic `/healthz` GETs, at most 2 in flight, within a 5-second test budget; stop on the first rejection. Require **429** from Nginx, and healthy backend responses before/after. Two in flight stays below both configured concurrency ceilings, so a 503 is not a rate-limit pass. If 429 is not observed within the bound, record not demonstrated and investigate pacing/configuration, not an unbounded retry. |
| Uvicorn concurrency gate | Bypass Nginx via host loopback 8000 with Serve off. Use the bounded socket probe below to occupy the configured connection budget and require **503 Service Unavailable** on a synthetic health request, then close all probe sockets and verify health recovers. A proxy 429 cannot demonstrate this backend limit. Do not lower/raise limits or combine this with the rate test. |
| Quotas / recovery | Check bounded quota failures do not crash the host; inspect selected memory/OOM state and free/tmpfs capacity. Nginx `limit_req_status` and `limit_conn_status` are explicitly **429** here; Uvicorn concurrency rejection is **503**, which can also pass through Nginx. Do not treat any unrelated 503 as proof of concurrency rejection. Do not perform an unbounded load test on 1 GiB. Repeat owner and negative access tests after restart and rollback; retain failures without weakening checks. |

For the HTTPS app-limit check, run this Python from the owner's matching checkout
(use `.venv\Scripts\python.exe` on Windows or Python 3 on Linux); replace the URL:

```python
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
from package_smoke_probe import verify_oversized
verify_oversized("https://ACTUAL_FQDN", Path("src/radio_loadout"))
```

The standard-library helper disables environment HTTP proxies and generates
synthetic bodies. The full `staging_smoke.py` intentionally accepts only HTTP
loopback URLs; do not weaken that restriction to point it at remote HTTPS.
Pace separate checks to avoid tripping the intentional site-wide rate cap.

For the backend concurrency test, run this host-only synthetic probe while Serve
is off, no other checks are running and the recorded container setting is exactly
`RADIO_LOADOUT_CONCURRENCY=8`. It opens at most eight short-lived idle connections
plus one probe at a time, sends no uploads, and closes everything within a bounded
test. Uvicorn counts open connections as well as tasks; see its
[concurrency behavior](https://uvicorn.dev/server-behavior/#resource-limits).
Nginx's separately configured [rate](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html#limit_req_status)
and [connection](https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html#limit_conn_status)
rejections use the explicitly chosen 429 codes above.

```python
# Host-only example: direct Uvicorn concurrency probe, not an app change.
import http.client
import socket
import time
from contextlib import ExitStack


def probe_backend():
    deadline = time.monotonic() + 5

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError("Synthetic concurrency probe exceeded five seconds")
        return min(1.0, value)

    with ExitStack() as sockets:
        for _ in range(8):
            sockets.enter_context(socket.create_connection(("127.0.0.1", 8000), timeout=remaining()))
        # A few bounded probes allow the event loop to accept the idle sockets.
        for _ in range(3):
            connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=remaining())
            try:
                connection.request("GET", "/healthz", headers={"Connection": "close"})
                response = connection.getresponse()
                if response.status == 503:
                    print("Observed direct-backend 503; all held sockets will close now.")
                    return
                if response.status != 200:
                    raise RuntimeError("Unexpected direct-backend status")
            finally:
                connection.close()
        raise RuntimeError("Backend 503 not demonstrated within the bounded probe")


if __name__ == "__main__":
    probe_backend()
```

Do not count timeouts/connection errors as a 503 pass. After this probe releases
all sockets, require a fresh 200 `{"status":"ok"}` response on loopback 8000 and
8080 before resuming any other checks or Serve. A Docker health probe may briefly
observe saturation; require recovery and no OOM/crash. Backend 503 can occur
before the app's middleware runs, so it need not have app-added headers on direct
8000; proxy-facing failures must still carry the configured safe headers.

### Fail closed and roll back on 1 GiB

Keep the previous verified image ID, source revision, container flags and private
Nginx/Serve/policy configuration record. Do not prune or overwrite them. Export
synthetic browser backups before origin/schema changes; keep the same Serve
hostname to preserve the browser origin. There is no server database to migrate,
and rollback must not clear localStorage.

If any access boundary fails, stop sharing first using the matching configuration:
`sudo tailscale serve --bg --https=443 off`. Keep cloud ingress closed. Do not
temporarily open public ports, relax grants or enable Funnel for troubleshooting.

Use a brief maintenance window rather than two simultaneous 512 MiB app
containers: disable Serve, `docker stop --time 40 CANDIDATE_CONTAINER`, then
restart the retained previous container on 127.0.0.1:8000, or create a fresh one
from the recorded previous **image ID** with the same hardened flags. Restore
only the reviewed matching proxy configuration if it changed, run `nginx -t`
and reload; its upstream stays on loopback. Verify local health, exact identity
and synthetic smoke before re-enabling the same private Serve endpoint, then
repeat owner HTTPS and blocked-access/limit checks. Keep failed candidate state
and bounded, privacy-safe diagnostics for review. If no verified previous image
exists, leave Serve off until a candidate passes; a first staging run has no
imaginary rollback target.

Documentation-local checks on 2026-11-26 parsed the Python/JSON and service-drop-in
examples, checked Bash syntax and local links, and exercised 29 synthetic mount
cases plus eight mocked backend-probe cases, including error cleanup. These do
not verify Linux mounts, systemd/Nginx startup, Recovery Console login, device
approval or real 429/503 responses; those still require the actual host/tailnet.

All host/Nginx/Tailscale commands, the 1 GiB capacity, image transfer/build,
private HTTPS, external negative tests and rollback above remain **unexecuted**
until a separately authorized staging exercise. Adding this runbook does not
close the license/source-access findings or Windows CHIRP verification.

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

The subsequent wrapper-enabled collector and `always()` verifier add
`certifi-wrappers-check.json` to those diagnostics. Only fixed certifi wrapper
paths/sizes/hashes are collected, not source contents. The offline comparison
uses existing pinned certifi/pip source members and preserves the same image,
interpreter and container restrictions. See [the wrapper follow-up](certifi-source-review.md#installed-wrapper-collection-and-gate--2026-11-05).
**CI #13 completed actual-image collection and passed this wrapper gate**, in
addition to the supplemental-notice gate, at commit
`0b5261390accc2f6efd5d316f2b3b2e605aa051a`. The
[evidence record](certifi-source-review.md#ci-13-installed-wrapper-gate-verified--2026-11-05)
includes artifact/image identifiers, checksums and successful independent replays.
Earlier green CI runs were not evidence for previously uncollected wrappers.
Source access and broader review remain separate; no deployment occurred.
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

For the owner-only Droplet profile above, Tailscale Serve terminates private
HTTPS. Keep public HTTP/HTTPS ports closed instead of adding a public redirect
listener; Nginx stays on loopback.

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
Debug mode is rejected. CSP remains deliberately deferred. Production API docs
are disabled; development docs still use CDN assets and the builder embeds JSON
configuration. Review a tested CSP against the actual production pages before
enabling one; this is not a claim of complete browser hardening.

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
