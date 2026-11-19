# Shared -k parsing for a suite's run.sh. Source it; it reads the caller's
# arguments and sets `pattern` (empty means the whole suite). Any other argv
# shape prints `usage: $0 [-k <pattern>]` on stderr and exits 2.

pattern=""
if [[ $# -ne 0 ]]; then
  if [[ $# -ne 2 || "$1" != "-k" || -z "$2" ]]; then
    echo "usage: $0 [-k <pattern>]" >&2
    exit 2
  fi
  pattern="$2"
fi
