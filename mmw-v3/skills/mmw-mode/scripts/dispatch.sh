#!/usr/bin/env bash
#
# Start one research session on a ticket: `dispatch.sh research <n>`. `dispatch.sh --help`
# prints the usage line.
#
# The session works in its own worktree, `<main worktree>/.worktrees/research-<n>`, on
# the branch `research/<n>`. A new branch starts at the caller's HEAD; a worktree or
# branch already standing there is reused as it is, so research work in it is kept. The
# session commits and pushes its own work: this script pushes nothing, opens no watch
# and writes nothing on the ticket.
#
# The host, model and reasoning effort come from the `researcher` row of models.json
# under MMW_HOME — the role's hosts.json default when the file has no such row —
# resolved against the catalog of the runner that starts the session (`use_catalog_of`).
# The selected runner is `models.py runner`: MMW_RUNNER, then models.json, then, when its
# runner is auto, the runner this process runs in, then orca. That runner's adapter
# (scripts/runners/<runner>.sh) starts the session with a one-line first prompt naming
# the playbook step and a data file, `prompts/<n>-researcher.md` in this repository's
# state directory (statedir.py), whose paths point into the frozen install named by
# MMW_HOME's `installed-root`: the directory holding `install.sh`, with the skills under
# its `skills/`. stdout is the session id. A start the adapter refuses is refused once:
# no retry, no other host, no other runner.
#
# Every refusal exits 2 and names its next step on stderr.

set -uo pipefail

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
MODELS_JSON="${MMW_HOME:-$HOME/.mmw}/models.json"
RUNNER=""
RUNNER_NAME=""
# `models.py` reads models.json, so it belongs to this skill and travels with it.
MODELS_PY="$SKILL_ROOT/scripts/models.py"

# Grok Build hands its agents CLICOLOR_FORCE=1, and `gh` writes ANSI escapes into
# --json output under it, which no JSON reader can parse.
gh_() {
  env -u CLICOLOR_FORCE -u CLICOLOR gh "$@"
}

refuse() {
  echo "dispatch: $1" >&2
  exit 2
}

runner() {
  bash "$RUNNER" "$@"
}

# Called once at the top of every command that talks to the runner, before any `$(…)`.
# The check cannot live in `runner()`: its callers run it inside `$(…)`, and a `refuse`
# there ends only that subshell — the command then carries on with an empty answer.
require_runner() {
  [ -f "$RUNNER" ] || refuse "no runner adapter for ${RUNNER_NAME:-this runner} at ${RUNNER:-scripts/runners/}; name paseo, orca or herdr in MMW_RUNNER or models.json, or restore that file, then run the command again"
}

# Points `runner` at one adapter. The name comes from `models.py runner`.
use_runner() {
  RUNNER_NAME="$1"
  RUNNER="$SKILL_ROOT/scripts/runners/$1.sh"
  require_runner
}

tonight_runner() {
  local name
  name="$(python3 "$MODELS_PY" runner)" && [ -n "$name" ] \
    || refuse "could not tell the selected runner from MMW_RUNNER, $MODELS_JSON or this process"
  printf '%s\n' "$name"
}

# Which catalog `models.py` resolves a models.json row against: the runner that starts the
# session decides. Paseo is handed Paseo's own provider model ids; a runner that runs the
# host's CLI in a terminal (Orca, Herdr) is handed the CLI's own ids, so its row is
# resolved against the CLI's catalog. Resolving against another runner's catalog either
# fails outright (Paseo's daemon is
# not running) or names a model the CLI does not have.
use_catalog_of() {
  case "$1" in
    paseo) export MMW_CATALOG_MODE=paseo ;;
    *) export MMW_CATALOG_MODE=cli ;;
  esac
}

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh research <n>
USAGE
  exit 2
}

# This repository as `gh` names it, owner/name: the data file is written into this
# repository's state directory. Exit 2, with the reason on stderr, when the tracker cannot say.
repo_slug() {
  local slug
  slug="$(gh_ repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null | tr -d '[:space:]')"
  if [ -z "$slug" ]; then
    echo "dispatch: the tracker could not say which repository this checkout is (gh repo view), so its state directory cannot be found" >&2
    return 2
  fi
  printf '%s\n' "$slug"
}

# ------------------------------------------------------------------ local model configuration

# Prints "host<TAB>resolved-model<TAB>effort" for the agent asked for.
row_for_role() {
  [ -f "$MODELS_PY" ] || refuse "no models.py at $MODELS_PY"
  MMW_MODELS_PY="$MODELS_PY" MMW_AGENT="$1" python3 -c '
import importlib.util, os, sys
path = os.environ["MMW_MODELS_PY"]
spec = importlib.util.spec_from_file_location("mmw_models", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    print(mod.row_tsv(os.environ["MMW_AGENT"]))
except ValueError as exc:
    text = str(exc)
    if text.startswith("no row "):
        sys.exit(0)
    print(text, file=sys.stderr)
    sys.exit(2)
'
}

# ------------------------------------------------------------------ worktrees

# The repository's main worktree: where every ticket's worktree lives, whichever
# checkout — and whichever branch — a command runs from.
main_checkout() {
  git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p'
}

worktrees_root() {
  local root
  root="$(main_checkout)"
  [ -n "$root" ] || return 0
  printf '%s/.worktrees\n' "$root"
}

# A ticket's workspace path that is not a worktree of its own: git reads a plain directory
# there as part of the main worktree, and a worktree deleted by hand stays registered and
# refuses `worktree add`. Registrations whose directory is gone are pruned, an empty
# directory is removed, and a directory holding files is refused, because they may be work.
clear_stray_workspace() {
  local root="$1" dest="$2" top
  git -C "$root" worktree prune >/dev/null 2>&1 || true
  [ -d "$dest" ] || return 0
  top="$(git -C "$dest" rev-parse --show-toplevel 2>/dev/null)" || top=""
  [ "$top" = "$(cd "$dest" && pwd -P)" ] && return 0
  if rmdir "$dest" 2>/dev/null; then
    return 0
  fi
  echo "dispatch: $dest holds files and is not a git worktree; move what is in it elsewhere, then run the command again" >&2
  return 1
}

# Check an existing worktree without changing its branch or files. An absent
# directory needs no check; the caller decides whether and when to create it.
require_worktree_branch() {
  local dest="$1" branch="$2" retry="$3" on
  [ -d "$dest" ] || return 0
  on="$(git -C "$dest" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  [ "$on" = "$branch" ] && return 0
  echo "dispatch: $dest is on ${on:-no branch}, not $branch; it is not this ticket's worktree; move it or rename it, then $retry" >&2
  return 1
}

# Attach the existing branch, or cut a new branch at the caller's chosen ref.
# git creates leading directories; a failure leaves its own error visible.
add_branch_worktree() {
  local root="$1" dest="$2" branch="$3" from="$4" retry="$5"
  local args=(worktree add --quiet)
  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
    args+=("$dest" "$branch")
  else
    args+=(-b "$branch" "$dest" "$from")
  fi
  git -C "$root" "${args[@]}" && return 0
  echo "dispatch: could not create $dest on $branch (new branches start at $from), so no session was started; resolve the git error above, then $retry" >&2
  return 1
}

# ------------------------------------------------------------------ start

# Prints the last line of the adapter's start answer. Exit 0 with a session id,
# 1 when the adapter failed or answered empty. The caller writes its own refusal.
start_session() {
  local host="$1" model="$2" effort="$3" cwd="$4" prompt="$5" title="$6"
  shift 6
  local -a environment=()
  local value
  for value in "$@"; do
    environment+=(--env "$value")
  done
  local session
  if ! session="$(runner start --host "$host" --model "$model" --effort "$effort" \
       --cwd "$cwd" --prompt "$prompt" --skip-approval --title "$title" \
       "${environment[@]+"${environment[@]}"}")" \
     || [ -z "$session" ]; then
    return 1
  fi
  printf '%s\n' "$session" | tail -n 1
}

# Resolve the frozen install before any session or worktree is changed.
installed_prompt_root() {
  python3 - "$SKILL_ROOT/scripts" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from statedir import home
marker = home() / "installed-root"
try:
    value = marker.read_text(encoding="utf-8").strip()
except FileNotFoundError:
    fact = "is missing"
except (OSError, UnicodeError):
    fact = "is unreadable"
else:
    root = Path(value)
    fact = "does not name an absolute install directory" if (
        not value or not root.is_absolute() or not root.is_dir() or "\n" in value or "\r" in value
    ) else ""
if fact:
    sys.stderr.write(f"dispatch: installed-root {marker} {fact}; frozen MMW paths cannot be supplied, so startup or adoption was refused; run bash mmw-v3/install.sh --check\n")
    raise SystemExit(2)
print(root.resolve())
PY
}

# Write role data and return its absolute path; packets supply named JSON fields.
write_prompt_data() {
  local role="$1" number="$2" installed="$3" repository="$4" packet="${5:-}"
  MMW_PROMPT_PACKET="$packet" python3 - "$SKILL_ROOT" "$role" "$number" "$installed" "$repository" <<'PY'
import json
import os
import sys
from pathlib import Path
skill, role, number, installed, repository = sys.argv[1:]
sys.path.insert(0, str(Path(skill) / "scripts"))
import locations
from statedir import state_dir, write_atomic
roles = json.loads((Path(skill) / "roles.json").read_text(encoding="utf-8"))
slug = roles[role]["playbook"]
skills = Path(installed) / "skills"
fields = [["Playbook", skills / locations.MODE_PLAYBOOKS_DIRECTORY / (slug + ".md")],
          ["dispatch.sh", skills / locations.MODE_SCRIPTS / "dispatch.sh"]]
fields.extend(json.loads(os.environ["MMW_PROMPT_PACKET"] or "{}").get("fields", []))
directory = state_dir(repository) / "prompts/"
directory.mkdir(parents=True, exist_ok=True, mode=0o700)
data = (directory / f"{number}-{role}.md").resolve()
write_atomic(data, "".join(f"- {name}: {value}\n" for name, value in fields))
print(data)
PY
}

# Return a single-line entry pointing at an existing data file.
session_prompt() {
  python3 - "$SKILL_ROOT" "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path
skill, role, number, data = sys.argv[1:]
sys.path.insert(0, str(Path(skill) / "scripts"))
import locations
roles = json.loads((Path(skill) / "roles.json").read_text(encoding="utf-8"))
slug = roles[role]["playbook"]
excluded = {row["entry"] for row in roles.values() if row.get("playbook") == slug and row.get("entry")}
step = next(anchor for anchor in locations.PLAYBOOK_ANCHORS[slug] if anchor not in excluded)
prompt = f"Use the mmw-mode skill. Role {role}, ticket #{number}, unattended: mmw-mode {slug}#{step}. Data: {data}."
if "\n" in prompt or "\r" in prompt:
    raise SystemExit("dispatch: an entry path contains a line break; the runner would submit more than one message; use a single-line path")
print(prompt)
PY
}

# Start a research session in its own worktree without opening a watch or writing
# ticket events. Its branch starts at the caller's HEAD and is left for the session
# to commit and push; later calls reuse it without resetting any research work.
research_one() {
  local number="$1"
  use_runner "$(tonight_runner)"
  use_catalog_of "$RUNNER_NAME"

  local row host model effort
  row="$(row_for_role researcher)" || exit 2
  IFS=$'\t' read -r host model effort <<<"$row"

  local root cwd branch prompt session installed repository_slug data
  installed="$(installed_prompt_root)" || exit 2
  repository_slug="$(repo_slug)" || exit 2
  data="$(write_prompt_data researcher "$number" "$installed" "$repository_slug")" \
    || refuse "could not write the researcher data for #$number; the session would have no readable task data; check this repository's state directory and research again"
  prompt="$(session_prompt researcher "$number" "$data")" \
    || refuse "could not build the researcher entry for #$number; the session would have no single-line instruction; check the role registry and research again"
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is no HEAD to start research/$number from; run research $number from a worktree"
  cwd="$(worktrees_root)/research-$number"
  branch="research/$number"
  clear_stray_workspace "$root" "$cwd" || exit 2
  require_worktree_branch "$cwd" "$branch" "research $number again" || exit 2
  if [ ! -d "$cwd" ]; then
    add_branch_worktree "$root" "$cwd" "$branch" HEAD "research $number again" || exit 2
  fi
  if ! session="$(start_session "$host" "$model" "$effort" "$cwd" "$prompt" "#$number researcher $$")"; then
    refuse "$RUNNER_NAME did not start $host as researcher for #$number (its reason is above); nothing was retried. Fix what it names, or change this agent's row in $MODELS_JSON, then research $number again"
  fi
  printf '%s\n' "$session"
}

# ------------------------------------------------------------------ entry

[ -f "$MODELS_JSON" ] || refuse "no models.json at $MODELS_JSON; run install.sh"

case "${1:-}" in
  research)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    research_one "$2"
    ;;
  "" | -h | --help)
    usage
    ;;
  *)
    usage
    ;;
esac
