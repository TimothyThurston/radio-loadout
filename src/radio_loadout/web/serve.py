"""Production server entry point used by the staging container."""

import ipaddress
import os

import uvicorn


def integer_setting(name: str, default: int, maximum: int = 65535) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} must be an integer.") from None
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be from 1 to {maximum}.")
    return value


def server_options() -> dict:
    host = os.environ.get("HOST", "0.0.0.0")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        raise ValueError("HOST must be an IP bind address.") from None
    forwarded = os.environ.get("RADIO_LOADOUT_FORWARDED_ALLOW_IPS", "").strip()
    if forwarded:
        try:
            networks = [ipaddress.ip_network(value.strip(), strict=False) for value in forwarded.split(",")]
            if any(network.prefixlen == 0 for network in networks):
                raise ValueError("Unrestricted proxy networks are not allowed.")
            forwarded = ",".join(str(network) for network in networks)
        except ValueError:
            raise ValueError("RADIO_LOADOUT_FORWARDED_ALLOW_IPS requires explicit proxy IP addresses or CIDRs; wildcard trust is not allowed.") from None
    return {
        "host": host,
        "port": integer_setting("PORT", 8000),
        "factory": True,
        "workers": 1,
        "reload": False,
        "proxy_headers": bool(forwarded),
        "forwarded_allow_ips": forwarded,
        "access_log": False,
        "server_header": False,
        "log_level": "warning",
        "limit_concurrency": integer_setting("RADIO_LOADOUT_CONCURRENCY", 16, 4096),
        "backlog": 128,
        "timeout_keep_alive": integer_setting("RADIO_LOADOUT_KEEP_ALIVE", 5, 300),
        "timeout_graceful_shutdown": integer_setting("RADIO_LOADOUT_SHUTDOWN_TIMEOUT", 30, 300),
    }


def main() -> None:
    uvicorn.run("radio_loadout.web.production:create_app", **server_options())


if __name__ == "__main__":
    main()
