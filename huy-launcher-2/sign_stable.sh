#!/usr/bin/env bash
# Finalize Launcher 2 with a permanent private signing key. Keep it OFF GitHub.
set -euo pipefail
if [[ $# -ne 4 ]]; then
  echo "Usage: sign_stable.sh <apksigner.jar> <intermediate.apk> <private.p12> <output.apk>" >&2
  exit 2
fi
: "${HUY2_KEYSTORE_PASSWORD:?Missing HUY2_KEYSTORE_PASSWORD}"
signer="$1"; input_apk="$2"; keystore="$3"; output_apk="$4"
expected="36758c6fe2a6cee38c81f2b42f868119b29a5f173e8015cb03ab440c467751d0"
java -jar "$signer" sign --ks "$keystore" --ks-type PKCS12 --ks-key-alias huylauncher2 \
  --ks-pass env:HUY2_KEYSTORE_PASSWORD --key-pass env:HUY2_KEYSTORE_PASSWORD \
  --v2-signing-enabled true --out "$output_apk" "$input_apk"
java -jar "$signer" verify --verbose --print-certs "$output_apk"
actual="$(java -jar "$signer" verify --print-certs "$output_apk" | sed -n "s/.*certificate SHA-256 digest: *//p" | head -1 | tr "[:upper:]" "[:lower:]" | tr -d "\r")"
test "$actual" = "$expected" || { echo "Signing certificate mismatch!" >&2; exit 1; }
echo "Verified permanent Huy 2 signing certificate: $actual"
sha256sum "$output_apk"
