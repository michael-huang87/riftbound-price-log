#!/usr/bin/env bash
# One-off, on the Mac: copies its price log history (prices.db, from 2026-10-23) to the R2 bucket, merged with any days
# the scheduled job already published there.
#   ./backfill.sh <dir>                 dry run: writes the files to <dir>, uploads nothing
#   ./backfill.sh <dir> <public url>    also uploads them (needs the R2_* variables upload.sh names)
set -euo pipefail
here=$(dirname "$0")
python3 "$here/price-log.py" export "$1" "$HOME/Library/Application Support/riftbound-price-log/prices.db" ${2:+"$2"}
[[ $# -ge 2 ]] || { echo "dry run: wrote $1, uploaded nothing"; exit 0; }
"$here/upload.sh" "$1"
