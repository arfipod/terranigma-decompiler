#!/usr/bin/env bash
set -euo pipefail

# Fail if commercial ROMs, generated decompilation output, extracted game data,
# saves, or compiled game images are tracked by Git.
forbidden_files='\.(sfc|smc|fig|swc|gba|srm|sav|state)$'
forbidden_dirs='(^|/)(roms?|generated|extracted|work|dumps?)/'

bad="$(git ls-files | grep -E -i "${forbidden_files}|${forbidden_dirs}" || true)"
if [[ -n "${bad}" ]]; then
  echo "ERROR: repository policy violation. These tracked paths are forbidden:" >&2
  echo "${bad}" >&2
  exit 1
fi

echo "Repository hygiene check passed."
