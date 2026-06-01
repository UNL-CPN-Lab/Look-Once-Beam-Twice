#!/usr/bin/env bash
# strip_macos_shadows.sh — remove macOS shadow/sidecar files from a tree
#
# Cleans up the junk macOS leaves on non-HFS filesystems (exFAT, NTFS,
# FAT32, network mounts):
#   ._*              AppleDouble resource-fork shadows (one per real file)
#   .DS_Store        Finder folder-view metadata
#   .Spotlight-V100/ Spotlight search index
#   .fseventsd/      File-system event log
#   .TemporaryItems/ Finder copy/move staging
#
# .Trashes/ is INTENTIONALLY NOT removed — it's where user-deleted files
# live until macOS empties the trash; deleting it loses recovery.
#
# Defaults to a DRY RUN (counts + total size, nothing deleted). Pass
# --apply to actually delete.
#
# Usage:
#   scripts/strip_macos_shadows.sh <path>            # dry-run
#   scripts/strip_macos_shadows.sh <path> --apply    # delete
#
# Safety:
#   - .git/ is always skipped (deleting AppleDouble there is harmless,
#     but it's noisy; -prune keeps the scan fast and the output clean).
#   - errors on individual files are suppressed (typical on flaky exFAT
#     mounts) but a non-zero exit is returned if anything actually fails.

set -uo pipefail

target="${1:-}"
mode="${2:-}"

if [[ -z "$target" || "$target" == "-h" || "$target" == "--help" ]]; then
  cat <<'EOF'
usage: strip_macos_shadows.sh <path> [--apply]

Counts (and optionally removes) macOS shadow files under <path>.
Default = dry-run. Pass --apply to actually delete.
EOF
  exit 1
fi

if [[ ! -d "$target" ]]; then
  echo "error: '$target' is not a directory" >&2
  exit 2
fi

# Resolve to absolute path for clearer reporting
target_abs="$(cd "$target" && pwd)"

apply=false
if [[ "$mode" == "--apply" ]]; then
  apply=true
elif [[ -n "$mode" ]]; then
  echo "error: unrecognized second argument '$mode' (only --apply is supported)" >&2
  exit 2
fi

echo "scanning $target_abs ..."
echo

# Build the find predicate once. -prune drops .git/ from the walk entirely.
# 2>/dev/null swallows permission errors on protected dirs (e.g. .Trashes/501
# can be readable but its subtrees may not be).
scan_files() {
  find "$target_abs" \
    \( -path '*/.git' -prune \) -o \
    \( -type f \( -name '._*' -o -name '.DS_Store' \) -print \) \
    2>/dev/null
}
scan_dirs() {
  find "$target_abs" \
    \( -path '*/.git' -prune \) -o \
    \( -type d \( -name '.Spotlight-V100' -o -name '.fseventsd' -o -name '.TemporaryItems' \) -print \) \
    2>/dev/null
}

# Count files and bytes. wc on stdin gives us a count without buffering.
# A second pass with stat sums sizes.
file_count=$(scan_files | wc -l)
dir_count=$(scan_dirs | wc -l)

if (( file_count == 0 && dir_count == 0 )); then
  echo "nothing to clean."
  exit 0
fi

# Aggregate bytes (only files; dirs sum via separate du). Tolerates files
# disappearing between scan and stat (race on a live tree).
file_bytes=0
if (( file_count > 0 )); then
  file_bytes=$(scan_files | xargs -d '\n' -r stat -c '%s' 2>/dev/null | awk '{s+=$1} END {print s+0}')
fi

human() {
  numfmt --to=iec --suffix=B --padding=8 "$1" 2>/dev/null || echo "$1 B"
}

echo "would remove:"
printf "  %-30s %8d files   %s\n" "._*  +  .DS_Store" "$file_count" "$(human "$file_bytes")"
if (( dir_count > 0 )); then
  echo "  .Spotlight-V100/  +  .fseventsd/  +  .TemporaryItems/   $dir_count directories"
fi
echo

if ! $apply; then
  echo "dry-run only. re-run with:  $0 $target --apply"
  exit 0
fi

# --- apply ---------------------------------------------------------------
echo "deleting..."
rc=0
scan_files | xargs -d '\n' -r rm -f -- || rc=$?
scan_dirs  | xargs -d '\n' -r rm -rf -- || rc=$?

# Re-count to verify
remaining_files=$(scan_files | wc -l)
remaining_dirs=$(scan_dirs | wc -l)

echo
if (( remaining_files == 0 && remaining_dirs == 0 )); then
  echo "done. tree is clean."
else
  echo "warning: $remaining_files files / $remaining_dirs directories still present after delete pass."
  echo "(possible cause: read-only mount, permission denied, or files re-created mid-pass)"
  rc=$(( rc == 0 ? 3 : rc ))
fi

exit "$rc"
