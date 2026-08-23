#!/usr/bin/env bash
# Mechanical checks on a repository's AGENTS.md / CLAUDE.md files. Judges only what a
# machine can: line count, bridge files, path references, tag balance, the
# subdirectory sentence, leftover AGENTS.override.md. Content quality is the skill's job.
#
#   bash scripts/check.sh [repo-root]     # default: current directory
#
# Prints one line per failure as "<path>: <message>", exits 1 on any failure.

set -euo pipefail

ROOT="${1:-.}"
ROOT="$(CDPATH='' cd -- "$ROOT" && pwd -P)"
ROOT_LIMIT=150
fails=0
fail() { echo "$1"; fails=$((fails + 1)); }

# Directories never scanned: VCS, dependencies, worktrees, host caches.
PRUNE=( -name .git -o -name node_modules -o -name .worktrees -o -name .claude -o -name .codex -o -name .pi -o -name .venv -o -name vendor )

find_files() {  # find_files <name>
  find "$ROOT" \( "${PRUNE[@]}" \) -prune -o -type f -name "$1" -print | LC_ALL=C sort
}

rel() { printf '%s\n' "${1#"$ROOT"/}"; }

# 6. No AGENTS.override.md anywhere.
# (Checks are numbered as in the skill's verify.md, not in file order.)
while IFS= read -r f; do
  [ -n "$f" ] && fail "$(rel "$f"): AGENTS.override.md must be renamed to AGENTS.md"
done < <(find_files AGENTS.override.md)

root_agents="$ROOT/AGENTS.md"
if [ ! -f "$root_agents" ]; then
  fail "AGENTS.md: missing at repository root"
fi

while IFS= read -r agents; do
  [ -n "$agents" ] || continue
  dir="$(dirname "$agents")"
  r="$(rel "$agents")"

  # 1. Root file length.
  if [ "$agents" = "$root_agents" ]; then
    n="$(wc -l < "$agents" | tr -d ' ')"
    [ "$n" -le "$ROOT_LIMIT" ] || fail "$r: $n lines, limit is $ROOT_LIMIT"
    # 5. The subdirectory sentence.
    grep -qiE 'subdirector.*AGENTS\.md|AGENTS\.md.*subdirector' "$agents" \
      || fail "$r: subdirectory sentence missing (tell agents to read a subdirectory's AGENTS.md before working there)"
  fi

  # 2. Bridge: CLAUDE.md beside it, only @imports, one of them @AGENTS.md.
  bridge="$dir/CLAUDE.md"
  br="$(rel "$bridge")"
  if [ ! -f "$bridge" ]; then
    fail "$br: missing (must contain @AGENTS.md)"
  else
    ln=0; has=0
    while IFS= read -r line || [ -n "$line" ]; do
      ln=$((ln + 1))
      [ -z "${line//[[:space:]]/}" ] && continue
      case "$line" in
        @AGENTS.md) has=1 ;;
        @*) ;;
        *) fail "$br: line $ln is not an @import: $line" ;;
      esac
    done < "$bridge"
    [ "$has" -eq 1 ] || fail "$br: no @AGENTS.md line"
  fi

  # 4. <important if="..."> tags balanced.
  opens="$(grep -c '<important ' "$agents" || true)"
  closes="$(grep -c '</important>' "$agents" || true)"
  [ "$opens" -eq "$closes" ] || fail "$r: $opens <important> openers but $closes </important> closers"

  # 3. Backticked tokens that look like repository paths must exist.
  #    A path token: contains a slash, no spaces, no glob/variable characters, not a URL,
  #    not an absolute or home path, not an option. Bare filenames are names, not paths.
  while IFS= read -r tok; do
    [ -n "$tok" ] || continue
    case "$tok" in
      *' '*|*'*'*|*'$'*|*'{'*|*'<'*|*'>'*|*'|'*|*'='*) continue ;;
      http://*|https://*|/*|~*|-*|@*|.|..) continue ;;
    esac
    case "$tok" in */*) ;; *) continue ;; esac
    t="${tok%/}"
    if [ ! -e "$dir/$t" ] && [ ! -e "$ROOT/$t" ]; then
      fail "$r: path \`$tok\` does not exist (relative to its directory or the repository root)"
    fi
  done < <(grep -o '`[^`]*`' "$agents" | sed 's/^`//; s/`$//' | LC_ALL=C sort -u)
done < <(find_files AGENTS.md)

[ "$fails" -eq 0 ] && { echo "ok"; exit 0; }
exit 1
