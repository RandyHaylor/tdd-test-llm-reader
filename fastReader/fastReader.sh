#!/bin/bash
# fastReader wrapper.
# Location assumption: this script lives INSIDE the fastReader/ folder
# (i.e. alongside cli.py, scanner.py, etc.). It sets PYTHONPATH to the
# parent of that folder so `python3 -m fastReader.<cmd>` resolves.
#
# Optional `json` subcommand: if the sibling quick-json-reader skill is
# installed (i.e. <skills-parent>/quick-json-reader/quick-json-reader
# exists and is executable), `fastReader json <args...>` pass-through
# launches that binary. Override the probed path with FAST_READER_JSON_BIN.

set -e

# Use the invocation path as-is; do NOT call readlink -f here. The whole point
# of a symlinked install (e.g. ~/.claude/skills/fastReader -> dev-checkout)
# is that the wrapper should see itself living at the symlink path so that
# PYTHONPATH and the sibling-skill json probe resolve relative to the
# invoker's skills root, not the dev checkout's parent.
FAST_READER_WRAPPER_SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"                     # .../fastReader (preserves symlinks)
FAST_READER_SKILL_PARENT_DIR="$(dirname "$FAST_READER_WRAPPER_SCRIPT_DIR")"         # parent that contains fastReader

FAST_READER_DEFAULT_JSON_BIN_PATH="$FAST_READER_SKILL_PARENT_DIR/quick-json-reader/quick-json-reader"
FAST_READER_JSON_BIN_PATH="${FAST_READER_JSON_BIN:-$FAST_READER_DEFAULT_JSON_BIN_PATH}"

is_quick_json_reader_binary_available() {
  [ -x "$FAST_READER_JSON_BIN_PATH" ]
}

print_fast_reader_wrapper_help_text() {
  cat <<USAGE
usage: fastReader <subcommand> [args...]
subcommands: load | toc | get | search
examples:
  fastReader load big_doc.md
  fastReader toc <hash> --sections --show-line-range-count
  fastReader get <hash> --section 3
  fastReader search error --manifests <hash>
Add --help / --help-examples / --help-use-cases to any subcommand
for argparse flags, copy-paste recipes, or trigger->command mapping.

Optional module:
USAGE
  if is_quick_json_reader_binary_available; then
    cat <<JSON_ON
  json  (detected: $FAST_READER_JSON_BIN_PATH)
        Pass-through to the quick-json-reader binary for JSON-specific
        extraction/filtering. Example: fastReader json file.json --search-vals error
JSON_ON
  else
    cat <<JSON_OFF
  json  (NOT INSTALLED)
        fastReader already efficiently parses and displays bracketed and
        tagged text. For much more versatile JSON-specific integration —
        schema inference, value search, field exclusion — install the
        quick-json-reader skill alongside this one. When the binary is
        detected at <skills-parent>/quick-json-reader/quick-json-reader
        (or the FAST_READER_JSON_BIN env var), the json module becomes
        available automatically. No reinstall of fastReader required.
JSON_OFF
  fi
}

if [ "$#" -lt 1 ]; then
  print_fast_reader_wrapper_help_text
  exit 0
fi

FAST_READER_SUBCOMMAND_NAME="$1"
shift

case "$FAST_READER_SUBCOMMAND_NAME" in
  load|toc|get|search)
    PYTHONPATH="$FAST_READER_SKILL_PARENT_DIR" exec python3 -m "fastReader.$FAST_READER_SUBCOMMAND_NAME" "$@"
    ;;
  json)
    if is_quick_json_reader_binary_available; then
      exec "$FAST_READER_JSON_BIN_PATH" "$@"
    else
      echo "fastReader: the 'json' module requires the quick-json-reader skill." >&2
      echo "Expected binary at: $FAST_READER_JSON_BIN_PATH" >&2
      echo "Install the quick-json-reader skill alongside fastReader, or set" >&2
      echo "FAST_READER_JSON_BIN to an absolute path to the binary." >&2
      exit 3
    fi
    ;;
  -h|--help)
    print_fast_reader_wrapper_help_text
    exit 0
    ;;
  *)
    echo "fastReader: unknown subcommand '$FAST_READER_SUBCOMMAND_NAME'" >&2
    if is_quick_json_reader_binary_available; then
      echo "valid: load, toc, get, search, json" >&2
    else
      echo "valid: load, toc, get, search  (install quick-json-reader skill to enable 'json')" >&2
    fi
    exit 2
    ;;
esac
