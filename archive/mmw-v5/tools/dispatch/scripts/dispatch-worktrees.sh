# Origin branches and ticket workspaces. Sourced by dispatch.sh.
default_branch() {
  local root="$1" ref
  ref="$(git -C "$root" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)" \
    && { printf '%s\n' "${ref#origin/}"; return 0; }
  ref="$(git -C "$root" ls-remote --symref origin HEAD 2>/dev/null \
    | awk '$1 == "ref:" { sub("refs/heads/", "", $2); print $2; exit }')"
  [ -n "$ref" ] || return 1
  printf '%s\n' "$ref"
}


branch_sync_counts() {
  local root="$1" branch="$2" base_ref="${3:-}" local_ref="refs/heads/$2" remote_ref="refs/remotes/origin/$2" ahead
  if ! git -C "$root" show-ref --verify --quiet "$local_ref"; then
    if git -C "$root" show-ref --verify --quiet "$remote_ref"; then
      printf '0\t0\tremote-only\n'
      return 0
    fi
    echo "dispatch: branch $branch exists neither locally nor on origin; create the intended branch or correct --into and --project before opening the batch" >&2
    return 2
  fi
  if ! git -C "$root" show-ref --verify --quiet "$remote_ref"; then
    if [ -n "$base_ref" ] && git -C "$root" rev-parse --verify --quiet "$base_ref" >/dev/null; then
      ahead="$(git -C "$root" rev-list --count "$base_ref..$local_ref")"
    else
      ahead="$(git -C "$root" rev-list --count "$local_ref" --not --remotes=origin)"
    fi
    printf '%s\t0\tmissing\n' "$ahead"
    return 0
  fi
  printf '%s\t%s\tpresent\n' \
    "$(git -C "$root" rev-list --count "$remote_ref..$local_ref")" \
    "$(git -C "$root" rev-list --count "$local_ref..$remote_ref")"
}


push_open_branches() {
  local root="$1" rows="$2" branch ahead presence behind output
  while IFS=$'\t' read -r _ _ branch ahead presence behind; do
    [ -n "$branch" ] || continue
    [ "$presence" = remote-only ] && continue
    if [ "$presence" = missing ] || [ "$ahead" -gt 0 ]; then
      output="$(git -C "$root" push origin "refs/heads/$branch:refs/heads/$branch" 2>&1)" \
        || { echo "dispatch: could not fast-forward origin/$branch: $(printf '%s' "$output" | tail -2 | tr '\n' ' ')" >&2; return 2; }
      git -C "$root" fetch -q origin "$branch:refs/remotes/origin/$branch" 2>/dev/null || true
    fi
  done <<<"$rows"
}


sync_base_with_project() {
  local root="$1" into="$2" project="$3" missing out files rc
  fetch_origin "$root" || return 2
  missing="$(git -C "$root" rev-list --count "origin/$into..origin/$project")" \
    || { echo "dispatch: could not compare origin/$into with origin/$project" >&2; return 2; }
  if [ "$missing" -gt 0 ]; then
    if git -C "$root" merge-base --is-ancestor "origin/$into" "origin/$project"; then
      out="$(git -C "$root" push origin "refs/remotes/origin/$project:refs/heads/$into" 2>&1)" \
        || { echo "dispatch: could not fast-forward origin/$into to origin/$project: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2; return 2; }
    else
      prepare_merge_worktree "$root" "$into" || return 2
      if ! git -C "$MERGE_ROOT" merge --no-ff -m "Merge branch '$project' into $into" "origin/$project" >/dev/null 2>&1; then
        files="$(git -C "$MERGE_ROOT" diff --name-only --diff-filter=U | paste -sd, -)"
        git -C "$MERGE_ROOT" merge --abort >/dev/null 2>&1 || true
        git -C "$MERGE_ROOT" reset --hard "origin/$into" >/dev/null
        release_merge_lock
        echo "dispatch: origin/$into lacks $missing commit(s) of origin/$project and merging them conflicts in ${files:-unknown files}; nothing was pushed. Merge origin/$project into $into by hand, push it, then run open again" >&2
        return 2
      fi
      out="$(git -C "$MERGE_ROOT" push origin "HEAD:refs/heads/$into" 2>&1)"; rc=$?
      release_merge_lock
      [ "$rc" -eq 0 ] \
        || { echo "dispatch: could not push the merge of origin/$project into origin/$into: $(printf '%s' "$out" | tail -2 | tr '\n' ' '); run open again" >&2; return 2; }
    fi
    git -C "$root" fetch -q origin 2>/dev/null || true
    echo "dispatch: $into took $missing commit(s) from origin/$project before the night opened" >&2
  fi
  if [ "$(current_branch "$root")" = "$into" ] && ! git -C "$root" merge-base --is-ancestor "origin/$into" HEAD \
     && ! git -C "$root" merge --ff-only --quiet "origin/$into" >/dev/null 2>&1; then
    echo "dispatch: this checkout stays behind origin/$into (git would not fast-forward it); the night runs on origin/$into either way" >&2
  fi
  return 0
}


main_checkout() {
  git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p'
}


worktrees_root() {
  local root
  root="$(main_checkout)"
  [ -n "$root" ] || return 0
  printf '%s/.worktrees\n' "$root"
}


workspace_cwd_for() {
  local root dest
  root="$(worktrees_root)"
  [ -n "$root" ] || return 0
  dest="$root/issue-$1"
  [ -d "$dest" ] && printf '%s\n' "$dest"
}


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


workspace_origin_ready() {
  local number="$1" root="$2" into="$3" dest branch local_left remote_left
  dest="$root/.worktrees/issue-$number"
  branch="issue-$number"
  fetch_origin "$root" || return 1
  require_origin_branch "$root" "$into" || return 1
  clear_stray_workspace "$root" "$dest" || return 1
  if [ -d "$dest" ]; then
    local on
    on="$(git -C "$dest" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    [ "$on" = "$branch" ] || {
      echo "dispatch: $dest is on ${on:-no branch}, not $branch; it is not this ticket's worktree — move it or rename it, then start again" >&2
      return 1
    }
  fi
  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch" \
      && git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
    read -r local_left remote_left <<<"$(git -C "$root" rev-list --left-right --count "$branch...origin/$branch")"
    if [ "$local_left" -gt 0 ] && [ "$remote_left" -gt 0 ]; then
      echo "dispatch: $branch and origin/$branch have diverged: local is $local_left commit(s) ahead and origin is $remote_left commit(s) ahead; reconcile them without force-push, then start again" >&2
      return 1
    fi
  fi
}


fetch_origin() {
  local root="$1" out
  if ! git -C "$root" remote get-url origin >/dev/null 2>&1; then
    echo "dispatch: this repository has no origin remote" >&2
    return 1
  fi
  if ! out="$(git -C "$root" fetch --prune origin 2>&1)"; then
    echo "dispatch: git fetch origin failed: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
    return 1
  fi
}


current_branch() {
  local branch
  branch="$(git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  case "$branch" in HEAD | "") return 1 ;; esac
  printf '%s\n' "$branch"
}


require_origin_branch() {
  local root="$1" branch="$2"
  git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch" && return 0
  echo "dispatch: origin/$branch does not exist; push the base branch to origin before continuing" >&2
  return 1
}


push_ticket_branch() {
  local number="$1" cwd="$2" out
  if ! out="$(git -C "$cwd" push --set-upstream origin "issue-$number" 2>&1)"; then
    echo "dispatch: git push origin issue-$number was rejected: $(printf '%s' "$out" | tr '\n' ' '); nothing was force-pushed" >&2
    return 1
  fi
  echo "dispatch: pushed issue-$number to origin" >&2
}


give_claim_back() {
  local number="$1" login
  login="$(gh_ api user --jq .login 2>/dev/null | tr -d '[:space:]')"
  [ -n "$login" ] || return 1
  printf '%s' "$(gh_ issue view "$number" --json assignees 2>/dev/null)" \
    | MMW_LOGIN="$login" python3 -c '
import json, os, sys
login = os.environ["MMW_LOGIN"]
try:
    rows = (json.load(sys.stdin) or {}).get("assignees") or []
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if login in [a.get("login") for a in rows if isinstance(a, dict)] else 1)
' || return 1
  gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1 || return 2
  return 0
}


ensure_workspace() {
  local number="$1" root="$2" into="$3" dest branch remote local_left remote_left created=0
  dest="$root/.worktrees/issue-$number"
  branch="issue-$number"
  fetch_origin "$root" || return 1
  require_origin_branch "$root" "$into" || return 1
  clear_stray_workspace "$root" "$dest" || return 1
  if [ -d "$dest" ]; then
    local on
    on="$(git -C "$dest" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    [ "$on" = "$branch" ] \
      || { echo "dispatch: $dest is on ${on:-no branch}, not $branch; it is not this ticket's worktree — move it or rename it, then start again" >&2; return 1; }
  fi
  remote=0
  git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch" && remote=1

  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch" && [ "$remote" = 1 ]; then
    read -r local_left remote_left <<<"$(git -C "$root" rev-list --left-right --count "$branch...origin/$branch")"
    if [ "$local_left" -gt 0 ] && [ "$remote_left" -gt 0 ]; then
      echo "dispatch: $branch and origin/$branch have diverged: local is $local_left commit(s) ahead and origin is $remote_left commit(s) ahead; reconcile them without force-push, then start again" >&2
      return 1
    fi
    if [ "$remote_left" -gt 0 ]; then
      if [ -d "$dest" ]; then
        git -C "$dest" merge --ff-only --quiet "origin/$branch" \
          || { echo "dispatch: could not fast-forward $branch to origin/$branch" >&2; return 1; }
      else
        git -C "$root" branch --force "$branch" "origin/$branch" >/dev/null \
          || { echo "dispatch: could not fast-forward $branch to origin/$branch" >&2; return 1; }
      fi
    fi
  fi

  if [ -d "$dest" ]; then
    if [ "$remote" = 0 ]; then
      push_ticket_branch "$number" "$dest" || return 1
    fi
    printf '%s\t%s\t0\n' "$dest" "$dest"
    return 0
  fi
  mkdir -p "$root/.worktrees"
  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$root" worktree add --quiet "$dest" "$branch" \
      || { echo "dispatch: could not create a worktree for $branch" >&2; return 1; }
    created=1
  elif [ "$remote" = 1 ]; then
    git -C "$root" worktree add --quiet -b "$branch" "$dest" "origin/$branch" \
      || { echo "dispatch: could not create a worktree for $branch from origin/$branch" >&2; return 1; }
    created=1
  else
    git -C "$root" worktree add --quiet -b "$branch" "$dest" "origin/$into" \
      || { echo "dispatch: could not create a worktree for $branch from origin/$into" >&2; return 1; }
    created=1
  fi
  if [ "$remote" = 0 ]; then
    push_ticket_branch "$number" "$dest" || return 1
  fi
  printf '%s\t%s\t%s\n' "$dest" "$dest" "$created"
}


worktree_environment() {
  local tree="$1"
  shift
  [ -e "$tree/scripts/env" ] || return 0
  python3 - "$VERIFY" "$tree" "$@" <<'PYENV'
import importlib.util
import sys
from pathlib import Path

script, tree, *steps = sys.argv[1:]
spec = importlib.util.spec_from_file_location("mmw_verify_environment", script)
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(Path(script).resolve().parent))
spec.loader.exec_module(module)
for step in steps:
    if module.run_worktree_environment(Path(tree), step):
        raise SystemExit(2)
PYENV
}


remove_worktree() {
  local root="$1" dest="$2"
  [ -n "$dest" ] || return 0
  [ -z "$(git -C "$dest" status --porcelain 2>/dev/null)" ] || { echo "dispatch: keeping dirty worktree $dest" >&2; return 1; }
  worktree_environment "$dest" down || true
  git -C "$root" worktree remove --force "$dest" >/dev/null 2>&1 && return 0
  [ -d "$dest" ] || return 0
  echo "dispatch: could not remove the worktree at $dest" >&2
  return 1
}


keep_unfinished_work() {
  local number="$1" cwd="$2" left_by="$3" out
  [ -n "$cwd" ] && [ -d "$cwd" ] || return 0
  [ -n "$(git -C "$cwd" status --porcelain --untracked-files=no 2>/dev/null)" ] || return 0
  if ! out="$(git -C "$cwd" commit --all --no-verify --quiet \
        -m "wip(#$number): uncommitted work of $left_by" 2>&1)"; then
    echo "dispatch: $cwd holds uncommitted work of $left_by, and it could not be committed on issue-$number: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
    return 1
  fi
  echo "dispatch: committed the uncommitted work of $left_by on issue-$number" >&2
}


stop_ticket_agents() {
  local number="$1" live_only="${2:-0}" listed name ident state failed=0
  if [ "$#" -ge 3 ]; then
    listed="$3"
  else
    listed="$(sessions_on_ticket "$number")" || return 1
  fi
  while IFS=$'\t' read -r name ident; do
    [ -n "$ident" ] || continue
    use_runner "$name"
    if [ "$live_only" = 1 ]; then
      state="$(runner liveness "$ident")" || state=unknown
      [ "$state" = stopped ] && continue
    fi
    if ! runner stop "$ident"; then
      echo "dispatch: could not stop $ident on #$number; it is still open on $name" >&2
      failed=1
    fi
  done <<<"$listed"
  return "$failed"
}


archive_ticket_agents() {
  stop_ticket_agents "$1"
}


stop_live_ticket_agents() {
  stop_ticket_agents "$1" 1
}


latest_returned_sessions() {
  ticket_events "$1" fold | python3 -c '
import json, sys
state = json.load(sys.stdin)
if (state.get("last") or {}).get("event") != "ticket.returned":
    raise SystemExit(0)
for row in state.get("sessions") or []:
    print("{}\t{}".format(row.get("runner") or "", row.get("session") or ""))
'
}


stop_returned_ticket_agents() {
  local spec="$1" batch number listed failed=0
  batch="$(python3 "$STATUS" --worker-grades "$spec")" || return 1
  for number in $(printf '%s\n' "$batch" | awk '$1 == "BATCH" { print $2 }'); do
    listed="$(latest_returned_sessions "$number")" \
      || { echo "dispatch: could not read #$number after ticket.returned" >&2; failed=1; continue; }
    [ -z "$listed" ] || stop_ticket_agents "$number" 1 "$listed" || failed=1
  done
  return "$failed"
}


archive_workspace() {
  local number="$1" cwd root
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || true
  cwd="$(workspace_cwd_for "$number")"
  if ! archive_ticket_agents "$number"; then
    echo "dispatch: #$number keeps its workspace because its sessions could not all be stopped. Resolve the runner or tracker failure, then retry cleanup" >&2
    return 1
  fi
  [ -n "$cwd" ] || return 0
  [ -n "$root" ] || root="$(dirname "$(dirname "$cwd")")"
  remove_worktree "$root" "$cwd"
}
