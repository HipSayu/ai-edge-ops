#!/usr/bin/env bash
# Adds broker users without prompting. Run from app/:  bash docs/mosquitto/add-users.sh '<password>' user [user ...]
# An edge node's user name is its node id (the ACL lets it write only under ppe/<node id>/); every user gets the same
# password, so use this for a fleet of fake edges, and mosquitto_passwd by hand (README) for real nodes.
# Reload the broker afterwards:  docker compose restart mosquitto
set -euo pipefail
export MSYS_NO_PATHCONV=1

password="${1:?usage: add-users.sh '<password>' user [user ...]}"
shift
[[ $# -gt 0 ]] || { echo "no user given" >&2; exit 1; }

dir="$PWD/volume/mosquitto"
mkdir -p "$dir"
touch "$dir/passwd"
for user in "$@"; do
  docker run --rm -v "$dir:/work" eclipse-mosquitto:2 mosquitto_passwd -b /work/passwd "$user" "$password"
done
echo "$# user(s) in $dir/passwd; restart the broker to load them"
