# erisml.org page statistics

GitHub Pages records no visitor statistics, so erisml.org counts page views with a
self-hosted [GoatCounter](https://github.com/arp242/goatcounter) on Atlas, reachable at
`https://stats.atlas-sjsu.duckdns.org`. Design and trust boundaries: `SECURITY.md`.

## How pages are counted
`docs/assets/js/sitebar.js` (the shared top bar, which every volume page loads through
`series.js`) inserts GoatCounter's `count.js` once per page, only on `erisml.org`, so local
previews are not counted. The few pages without the bar (standalone paper pages, the brand
page) carry the same tag directly.

## Files
- `erisml-goatcounter.service`: the systemd unit (loopback only, confined).
- `stats.caddy`: the site block that atlas-caddy imports.
- `install.sh`: installs or updates the service (idempotent).

## Deploy on Atlas
```
# the repository, sparse, under the stats directory
git clone --depth 1 --filter=blob:none --sparse https://github.com/ahb-sjsu/erisml-lib /archive/experiments/erisml-stats/repo
git -C /archive/experiments/erisml-stats/repo sparse-checkout set tools/site-stats
sudo bash /archive/experiments/erisml-stats/repo/tools/site-stats/install.sh

# Caddy: back up, add one import line, validate, reload gracefully (no restart)
cp /home/claude/Caddyfile /home/claude/Caddyfile.bak-stats
echo 'import /archive/experiments/erisml-stats/repo/tools/site-stats/stats.caddy' >> /home/claude/Caddyfile
sudo caddy validate --config /home/claude/Caddyfile --adapter caddyfile
sudo caddy reload --config /home/claude/Caddyfile --adapter caddyfile
```
Updates: `git -C /archive/experiments/erisml-stats/repo pull`, then rerun `install.sh` and
reload Caddy.

## Roll back
```
sudo systemctl disable --now erisml-goatcounter.service
cp /home/claude/Caddyfile.bak-stats /home/claude/Caddyfile
sudo caddy reload --config /home/claude/Caddyfile --adapter caddyfile
```
The statistics database stays in `/archive/experiments/erisml-stats/data`.

## Reading the statistics
Open `https://stats.atlas-sjsu.duckdns.org` and log in as `admin@stats.atlas-sjsu.duckdns.org`
with the password in `/home/claude/.secrets/goatcounter_admin.txt` on Atlas. The login name
can be changed in the dashboard.
