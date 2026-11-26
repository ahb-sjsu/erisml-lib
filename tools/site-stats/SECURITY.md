# erisml.org page statistics: trust boundaries

Written before deployment (2026-11-26), as the design the service is built to.

## What runs where
- **GoatCounter** (open source, v2.7.0, verified against GitHub's published SHA-256) runs on
  Atlas as the unprivileged system user `goatcounter`, under a systemd unit that confines it:
  no new privileges, read-only filesystem except its data directory, no capabilities, CPU and
  memory capped. It listens on `127.0.0.1:8095` only.
- **atlas-caddy** (already running, already public on 80/443) is the only way in from the
  internet. It terminates TLS for `stats.atlas-sjsu.duckdns.org` and proxies to the loopback
  port. Caddy sets `X-Forwarded-For` itself and does not trust one sent by a client.

## Boundaries
1. **Internet -> /count and /count.js (public, unauthenticated).** Any browser that loads an
   erisml.org page sends a page-view hit here. Risk: junk or flooded hits. Mitigations:
   GoatCounter's per-client rate limit (4 hits per second by default, keyed on the forwarded
   client address); the service's CPU and memory caps; hits only add rows to a statistics
   database and cannot reach anything else on Atlas.
2. **Internet -> dashboard and API (authenticated).** Everything except counting needs
   GoatCounter's own login. The admin password is generated on Atlas at install and stored
   only in `/home/claude/.secrets/goatcounter_admin.txt` (mode 600); it is never on a command
   line, in this repository or in a log. Login attempts are rate-limited (20 per minute).
3. **GoatCounter -> the host.** The service account has no shell and no sudo; systemd allows
   writes only to `/archive/experiments/erisml-stats/data`.

## Data kept
GoatCounter sets no cookies and tracks no unique identifiers; it records the page, referrer,
browser, screen size and country, and recognises a repeat visit by a non-identifiable hash.
Caddy keeps no access log for this site (no `log` directive), so visitors' addresses are not
written to disk by the proxy.

## Not defended against
A determined flood from many addresses could fill the statistics with junk; the remedy is
to stop the service (`sudo systemctl stop erisml-goatcounter`), which affects nothing else.
