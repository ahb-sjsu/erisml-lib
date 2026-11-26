#!/usr/bin/env bash
# Install or update the erisml.org page-statistics service on Atlas. Idempotent.
#
#   sudo bash /archive/experiments/erisml-stats/repo/tools/site-stats/install.sh
#
# What it does (each step is skipped when already done):
#   1. system user `goatcounter` (no login shell, no home of its own)
#   2. data directory /archive/experiments/erisml-stats/data (owner goatcounter, mode 700)
#   3. GoatCounter $VERSION to /usr/local/bin/goatcounter, verified against the SHA-256 digest
#      that GitHub publishes for the release asset
#   4. the site stats.atlas-sjsu.duckdns.org in a new SQLite database, with an admin login
#      whose password is generated here and stored only in /home/claude/.secrets (mode 600)
#   5. the systemd unit erisml-goatcounter.service, enabled and started
# It does not touch Caddy: adding the import line and reloading Caddy are separate steps in
# README.md, so that a Caddy problem can be rolled back on its own.
set -euo pipefail

VERSION=v2.7.0
ASSET=goatcounter-${VERSION}-linux-amd64.gz
SHA256=98d221cb9c8ef2bf76d8daa9cca647839f8d8b0bb5bc7400ff9337c5da834511
URL=https://github.com/arp242/goatcounter/releases/download/${VERSION}/${ASSET}
HERE=$(cd "$(dirname "$0")" && pwd)
DATA=/archive/experiments/erisml-stats/data
DB=${DATA}/goatcounter.sqlite3
VHOST=stats.atlas-sjsu.duckdns.org
LOGIN=admin@${VHOST}
SECRETS=/home/claude/.secrets
PASSFILE=${SECRETS}/goatcounter_admin.txt

[ "$(id -u)" = 0 ] || { echo "run with sudo" >&2; exit 1; }

# 1. service user
if ! id goatcounter >/dev/null 2>&1; then
    useradd --system --no-create-home --home-dir "$DATA" --shell /usr/sbin/nologin goatcounter
    echo "created user goatcounter"
fi

# 2. data directory (under an existing /archive subtree, never a new top-level dir)
install -d -o goatcounter -g goatcounter -m 700 "$DATA"

# 3. binary, verified
if ! /usr/local/bin/goatcounter version 2>/dev/null | grep -q "${VERSION#v}"; then
    tmp=$(mktemp -d)
    trap 'rm -rf "${tmp:?}"' EXIT
    curl -fsSL -o "$tmp/$ASSET" "$URL"
    echo "${SHA256}  $tmp/$ASSET" | sha256sum -c -
    gunzip "$tmp/$ASSET"
    install -o root -g root -m 755 "$tmp/${ASSET%.gz}" /usr/local/bin/goatcounter
    echo "installed $(/usr/local/bin/goatcounter version | head -1)"
fi

# 4. site and admin login (only when the database does not exist yet)
if [ ! -e "$DB" ]; then
    install -d -o claude -g claude -m 700 "$SECRETS"
    if [ ! -s "$PASSFILE" ]; then
        umask 077
        # no trailing newline: goatcounter reads "-password -" with io.ReadAll, newline included
        openssl rand -base64 24 | tr -d '\n' > "$PASSFILE"
        chown claude:claude "$PASSFILE"
        chmod 600 "$PASSFILE"
    fi
    # the password goes in on stdin ("-password -"), never on a command line
    ( cd "$DATA" && sudo -u goatcounter /usr/local/bin/goatcounter db create site -createdb \
        -db "sqlite+$DB" -vhost "$VHOST" -user.email "$LOGIN" -password - ) < "$PASSFILE"
    echo "created site $VHOST (login $LOGIN; password in $PASSFILE)"
fi

# 5. service
install -o root -g root -m 644 "$HERE/erisml-goatcounter.service" /etc/systemd/system/erisml-goatcounter.service
systemctl daemon-reload
systemctl enable --now erisml-goatcounter.service
systemctl restart erisml-goatcounter.service
sleep 2
systemctl is-active erisml-goatcounter.service
curl -fsS -o /dev/null -w "local count.js: %{http_code}\n" -H "Host: $VHOST" http://127.0.0.1:8095/count.js
