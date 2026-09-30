#!/usr/bin/env bash
# RS256 key pair for user access tokens: the Cloud signs with jwt_private.pem, the API gateway verifies with
# jwt_public.pem. Usage: bash infra/scripts/gen-jwt-keys.sh <dir>   (never overwrites an existing key)
set -euo pipefail
DIR=${1:?usage: gen-jwt-keys.sh <dir>}
mkdir -p "$DIR"
if [ -e "$DIR/jwt_private.pem" ]; then
  echo "$DIR/jwt_private.pem exists, keeping it"
else
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$DIR/jwt_private.pem"
fi
openssl pkey -in "$DIR/jwt_private.pem" -pubout -out "$DIR/jwt_public.pem"
chmod 600 "$DIR/jwt_private.pem"; chmod 644 "$DIR/jwt_public.pem"
echo "keys in $DIR"
