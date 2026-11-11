#!/usr/bin/env bash
# Makes the broker's TLS certificates in volume/mosquitto/certs: a private CA (ca.crt, ca.key) and a server
# certificate signed by it (server.crt, server.key). Run from app/:  bash docs/mosquitto/make-certs.sh [extra-host ...]
#
# Clients check the broker's host name against the certificate, so list every name they use to reach it. The names
# mosquitto (inside docker compose), localhost and 127.0.0.1 are always included; pass others as arguments, e.g. the
# public name or IP of the server the edge nodes connect to:  bash docs/mosquitto/make-certs.sh mqtt.example.com 203.0.113.7
#
# Give ca.crt to every client (cloud, edge nodes); keep ca.key and server.key private.
set -euo pipefail
export MSYS_NO_PATHCONV=1  # Git Bash on Windows would rewrite the "/CN=..." subjects as paths

OUT="volume/mosquitto/certs"
DAYS_CA=3650
DAYS_SERVER=825
mkdir -p "$OUT"
cd "$OUT"

san="DNS:mosquitto,DNS:localhost,IP:127.0.0.1"
for host in "$@"; do
  if [[ "$host" =~ ^[0-9.]+$ ]]; then san+=",IP:$host"; else san+=",DNS:$host"; fi
done

if [[ ! -f ca.key ]]; then
  openssl genrsa -out ca.key 4096
  openssl req -x509 -new -key ca.key -sha256 -days "$DAYS_CA" -subj "/CN=PPE Vision MQTT CA" -out ca.crt
fi

openssl genrsa -out server.key 2048
openssl req -new -key server.key -subj "/CN=mosquitto" -out server.csr
printf "subjectAltName=%s\nextendedKeyUsage=serverAuth\n" "$san" > server.ext  # a file: openssl on Windows cannot read <(...)
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days "$DAYS_SERVER" -sha256 \
  -extfile server.ext -out server.crt
rm -f server.csr server.ext ca.srl

chmod 600 ca.key server.key 2>/dev/null || true
# The broker runs as an unprivileged user and must be able to read its key.
chmod 644 server.key ca.crt server.crt 2>/dev/null || true
echo "Certificates in $OUT (server certificate valid for: $san)"
