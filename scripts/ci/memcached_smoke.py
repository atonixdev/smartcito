from __future__ import annotations

import os
import sys

from pymemcache.client.hash import HashClient


def main() -> int:
    endpoints = []
    for endpoint in os.getenv("MEMCACHED_SERVERS", "memcached:11211").split(","):
        host, _, port = endpoint.strip().partition(":")
        if host and port:
            endpoints.append((host, int(port)))

    if not endpoints:
        raise SystemExit("MEMCACHED_SERVERS did not resolve to any usable endpoints")

    client = HashClient(endpoints, connect_timeout=1.0, timeout=1.0, no_delay=True)
    key = "ci:smoke:memcached"
    value = b"orca-ok"

    client.set(key, value, expire=30)
    fetched = client.get(key)
    if fetched != value:
        raise SystemExit(f"unexpected memcached value: {fetched!r}")
    client.delete(key)
    if client.get(key) is not None:
        raise SystemExit("memcached delete verification failed")
    print("memcached smoke passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())