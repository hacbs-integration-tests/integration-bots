#!/bin/bash
# next-folder.sh — Compute the next oras-artifacts_NN folder name in the current directory
#
# Does NOT create the folder. Prints exactly one line, e.g. "oras-artifacts_03".
# Increments the highest existing oras-artifacts_* number, or starts at 01 if none exist.

set -euo pipefail

last=$(ls -d oras-artifacts_* 2>/dev/null | sort -V | tail -1 || echo "")

if [ -z "$last" ]; then
  printf 'oras-artifacts_%02d\n' 1
else
  num=$(echo "$last" | grep -o '[0-9]*$')
  printf 'oras-artifacts_%02d\n' $(( 10#$num + 1 ))
fi
