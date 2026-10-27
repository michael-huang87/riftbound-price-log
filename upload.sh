#!/usr/bin/env bash
# Uploads a price log dir (days/<day>.json and days.json, from price-log.py publish) to the R2 bucket:
# day files first, so the index never names a missing one. Needs R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID and
# R2_SECRET_ACCESS_KEY. A day never changes once written, so its file caches for a year; the index for five minutes.
set -euo pipefail
[[ -f "$1/days.json" ]] || { echo "nothing to upload"; exit 0; }
export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" AWS_DEFAULT_REGION=auto
# aws-cli 2.23+ adds checksums by default that R2's docs say to send only when required.
export AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
s3() { aws s3 cp --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com" --content-type application/json "$@"; }
s3 --recursive "$1/days" "s3://$R2_BUCKET/days" --cache-control "public, max-age=31536000, immutable"
s3 "$1/days.json" "s3://$R2_BUCKET/days.json" --cache-control "public, max-age=300"
