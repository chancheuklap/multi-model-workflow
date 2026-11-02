# Git workspaces, integration and landing. Sourced by dispatch.sh.
MERGE_TRIES=3
MERGE_LOCK=""
MERGE_LOCK_PID=""
MERGE_LOCK_READY=""
MERGE_ROOT=""
FILED_MERGE_WORKTREES=""
MERGE_CHECKS_FAILED="[]"
MERGE_CHECKS_DETAIL=""
REPO_URL=""

integrated_ticket_numbers() {
  git -C "$1" log --reverse --first-parent --format='%s' "$2" 2>/dev/null \
    | sed -n "s/^Merge branch 'issue-\([0-9][0-9]*\)'$/\1/p" \
    | awk '!seen[$0]++'
}


integrated_since_start() {
  local number="$1" root base into rc
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is no base branch to read history on"
  base="$(newest_worker_field "$number" base)"
  rc=$?
  case "$rc" in
    0) ;;
    3) refuse "#$number's events carry no worker.started.base, so there is no starting point to read history from" ;;
    *) exit 2 ;;
  esac
  into="$(ticket_into "$number")" || refuse "#$number has no worker.started with a base branch"
  fetch_origin "$root" || exit 2
  require_origin_branch "$root" "$into" || exit 2
  integrated_ticket_numbers "$root" "$base..origin/$into"
}


integrate_conflict_report() {
  local root="$1" number="$2" into="$3" tickets="$4" ticket title
  {
    echo "CONFLICT merging origin/$into into issue-$number"
    echo
    echo "  incoming tickets:"
    if [ -z "$tickets" ]; then
      echo "    none represented by Merge branch 'issue-<n>' commits"
    else
      while IFS= read -r ticket; do
        [ -n "$ticket" ] || continue
        title="$(ticket_title "$ticket")"
        echo "    #$ticket  $title"
      done <<<"$tickets"
    fi
    echo
    echo "  conflicted files:"
    git -C "$root" diff --name-only --diff-filter=U | sed 's/^/    /'
    echo
    echo "  Hand this integration to the Coordinator through dispatch's"
    echo "  blocked-merge route and wait without editing this worktree."
    echo "  The Coordinator resolves and commits the merge; after its"
    echo "  continuation, run dispatch.sh integrate $number again."
  } >&2
}


integrate_ticket() {
  local number="$1" root branch into base tickets out
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is no issue-$number to integrate"
  branch="$(current_branch "$root")" || branch=""
  [ "$branch" = "issue-$number" ] \
    || refuse "integrate $number runs from branch issue-$number, not ${branch:-a detached HEAD}"
  [ -z "$(git -C "$root" status --porcelain --untracked-files=no)" ] \
    || refuse "issue-$number has uncommitted tracked changes; commit them before integrating the base branch"

  into="$(ticket_into "$number")" \
    || refuse "#$number has no worker.started with a base branch; start it first"

  fetch_origin "$root" || exit 2
  require_origin_branch "$root" "$into" || exit 2
  if git -C "$root" merge-base --is-ancestor "origin/$into" HEAD; then
    echo "issue-$number is already current with origin/$into"
    return 0
  fi
  base="$(git -C "$root" merge-base HEAD "origin/$into" 2>/dev/null)"
  [ -n "$base" ] \
    || refuse "issue-$number and origin/$into share no commit, so they cannot be integrated"
  tickets="$(integrated_ticket_numbers "$root" "$base..origin/$into")"

  if out="$(git -C "$root" merge --no-ff -m "Merge $into into issue-$number" "origin/$into" 2>&1)"; then
    if [ -n "$tickets" ]; then
      printf 'integrated origin/%s into issue-%s; incoming tickets:' "$into" "$number"
      while IFS= read -r ticket; do
        [ -n "$ticket" ] && printf ' #%s' "$ticket"
      done <<<"$tickets"
      printf '\n'
    else
      echo "integrated origin/$into into issue-$number; incoming tickets: none"
    fi
    return 0
  fi
  if git -C "$root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    integrate_conflict_report "$root" "$number" "$into" "$tickets"
    return 3
  fi
  echo "dispatch: git merge origin/$into into issue-$number failed: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
  return 2
}


ticket_branch() { printf 'issue-%s\n' "$1"; }

ticket_title() {
  gh_ issue view "$1" --json title -q .title 2>/dev/null | head -n 1
}


merge_slug() { printf '%s\n' "${1//\//-}"; }

release_merge_lock() {
  if [ -n "$MERGE_LOCK_PID" ]; then
    kill "$MERGE_LOCK_PID" 2>/dev/null || true
    wait "$MERGE_LOCK_PID" 2>/dev/null || true
  fi
  [ -z "$MERGE_LOCK_READY" ] || rm -f "$MERGE_LOCK_READY"
  MERGE_LOCK=""
  MERGE_LOCK_PID=""
  MERGE_LOCK_READY=""
}


acquire_merge_lock() {
  local into="$1" slug state answer i
  slug="$(merge_slug "$into")"
  state="$(repository_state_dir)" || return 2
  MERGE_LOCK="$state/merge-$slug.lock"
  MERGE_LOCK_READY="$(mktemp)"
  python3 - "$STATEDIR" "$MERGE_LOCK" "$into" "$$" <<'PY' >"$MERGE_LOCK_READY" 2>&1 &
import importlib.util, os, sys, time
from pathlib import Path

script, lock, into, parent = sys.argv[1:]
spec = importlib.util.spec_from_file_location("mmw_statedir", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    with mod.locked(Path(lock), wait=6.0, purpose=f"landing into origin/{into}"):
        print("LOCKED", flush=True)
        while os.getppid() == int(parent):
            time.sleep(0.1)
except mod.LockHeld as exc:
    print(f"dispatch: another merge into {into} still holds {exc}", flush=True)
    raise SystemExit(2)
PY
  MERGE_LOCK_PID=$!
  for ((i = 1; i <= 70; i++)); do
    [ -s "$MERGE_LOCK_READY" ] && break
    kill -0 "$MERGE_LOCK_PID" 2>/dev/null || break
    sleep 0.1
  done
  answer="$(cat "$MERGE_LOCK_READY")"
  case "$answer" in
    LOCKED) trap release_merge_lock EXIT; return 0 ;;
    "") echo "dispatch: the merge lock helper for origin/$into did not answer" >&2 ;;
    *) printf '%s\n' "$answer" >&2 ;;
  esac
  release_merge_lock
  return 2
}


repository_state_dir() {
  local repo
  repo="$(repo_slug)" || return 2
  python3 - "$STATEDIR" "$repo" <<'PY'
import importlib.util, sys
from pathlib import Path

script, repo = sys.argv[1:]
spec = importlib.util.spec_from_file_location("mmw_statedir", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.state_dir(repo))
PY
}


prepare_merge_worktree() {
  local root="$1" into="$2" main slug dest
  main="$(main_checkout)"
  [ -n "$main" ] \
    || { echo "dispatch: could not resolve the main worktree from $root" >&2; return 2; }
  slug="$(merge_slug "$into")"
  dest="$main/.worktrees/merge-$slug"
  acquire_merge_lock "$into" || return 2

  fetch_origin "$root" || { release_merge_lock; return 2; }
  require_origin_branch "$root" "$into" || { release_merge_lock; return 2; }
  mkdir -p "$(dirname "$dest")"
  clear_stray_workspace "$root" "$dest" || { release_merge_lock; return 2; }
  if [ ! -e "$dest" ]; then
    git -C "$root" worktree add --detach "$dest" "origin/$into" >/dev/null \
      || { echo "dispatch: could not create the merge worktree $dest" >&2; release_merge_lock; return 2; }
  fi
  git -C "$dest" merge --abort >/dev/null 2>&1 || true
  git -C "$dest" reset --hard "origin/$into" >/dev/null \
    || { echo "dispatch: could not reset $dest to origin/$into" >&2; release_merge_lock; return 2; }
  worktree_environment "$dest" setup up || {
    worktree_environment "$dest" down || true
    release_merge_lock
    return 4
  }
  file_merge_worktree "$dest"
  MERGE_ROOT="$dest"
}


file_merge_worktree() {
  local dest="$1" name adapter err
  case " $FILED_MERGE_WORKTREES " in *" $dest "*) return 0 ;; esac
  FILED_MERGE_WORKTREES="$FILED_MERGE_WORKTREES $dest"
  name="$(python3 "$MODELS_PY" runner 2>/dev/null)" && [ -n "$name" ] || return 0
  adapter="$SKILL_ROOT/scripts/runners/$name.sh"
  [ -f "$adapter" ] || return 0
  err="$(bash "$adapter" attach --cwd "$dest" --under-caller 2>&1 >/dev/null)" \
    || echo "dispatch: $name did not file the merge worktree $dest under this session's worktree ($(printf '%s' "$err" | tr '\n' ' ' | sed 's/ *$//')); the landing goes on" >&2
  return 0
}


ticket_passed_commit() {
  local number="$1" commit rc
  commit="$(newest_field "$number" commit ticket.passed)"
  rc=$?
  case "$rc" in
    0)
      [[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "dispatch: #$number passed commit is not a full commit SHA: $commit" >&2; return 2; }
      printf '%s\n' "$commit" ;;
    2) echo "dispatch: could not read #$number's events, so its passed commit is unknown" >&2; return 2 ;;
    3) echo "dispatch: #$number carries no active ticket.passed event" >&2; return 2 ;;
    4) echo "dispatch: #$number's ticket.passed event carries no commit" >&2; return 2 ;;
    *) echo "dispatch: could not resolve #$number's passed commit" >&2; return 2 ;;
  esac
}


landed_tip_ticket() {
  local root="$1" into="$2" tip subject number merge prefix="Merge branch 'issue-"
  tip="$(git -C "$root" rev-parse "origin/$into" 2>/dev/null)" || return 1
  subject="$(git -C "$root" show -s --format=%s "$tip" 2>/dev/null)" || return 1
  case "$subject" in "$prefix"*"'") ;; *) return 1 ;; esac
  number="${subject#"$prefix"}"
  number="${number%"'"}"
  case "$number" in *[!0-9]* | "") return 1 ;; esac
  merge="$(newest_field "$number" merge ticket.landed 2>/dev/null)" || return 1
  [ "$merge" = "$tip" ] || return 1
  printf '%s\n' "$number"
}


run_merge_checks() {
  local root="$1" base_ref="$2" worktree="${3:-}" ticket="${4:-}" out status
  MERGE_CHECKS_FAILED="[]"
  MERGE_CHECKS_DETAIL=""
  out="$(python3 - "$VERIFY" "$root" "$base_ref" "$worktree" "$ticket" <<'PY'
import importlib.util, json, sys
from pathlib import Path

script, root, base_ref, worktree, ticket = sys.argv[1:6]
sys.path.insert(0, str(Path(script).resolve().parent))
spec = importlib.util.spec_from_file_location("mmw_verify_ticket", script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
result = mod.run_repository_check(Path(root), base_ref, worktree or None, ticket or None)
if result["status"] == "pass" and not result["proof"]:
    result["status"] = "cannot-run"
    result["detail"] = "scripts/check changed the checkout or ran on an uncommitted tree; no commit names the checked output"
print(result["status"])
print(json.dumps(result["failed"], separators=(",", ":")))
print(result["detail"])
PY
)" || { MERGE_CHECKS_DETAIL="$VERIFY could not run $root/scripts/check (the reason is above)"; return 2; }
  status="$(printf '%s\n' "$out" | sed -n 1p)"
  MERGE_CHECKS_FAILED="$(printf '%s\n' "$out" | sed -n 2p)"
  MERGE_CHECKS_DETAIL="$(printf '%s\n' "$out" | sed -n '3,$p')"
  case "$status" in
    pass) return 0 ;;
    red) return 1 ;;
    missing) return 3 ;;
    *) return 2 ;;
  esac
}


repository_proof() {
  local issue="$1" commit="$2" base="$3" tier="${4:-default}"
  python3 - "$VERIFY" "$issue" "$commit" "$base" "$tier" <<'PY'
import importlib.util, sys
from pathlib import Path

script, issue, commit, base, tier = sys.argv[1:6]
sys.path.insert(0, str(Path(script).resolve().parent))
spec = importlib.util.spec_from_file_location("mmw_verify_ticket", script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
proof = mod.covering_proof(mod.fetch_comments(int(issue)), commit, base)
if not proof or (tier == "all" and proof["tier"] != "all"):
    sys.exit(1)
print(proof["tier"], proof["commit"], proof["base"])
for step in proof["steps"]:
    if step.startswith("e2e-"):
        print(f"PASS {step} (reused spec.checked on {commit[:12]})")
PY
}


repository_check_missing() {
  python3 - "$VERIFY" "$1" <<'PY'
import importlib.util, sys
from pathlib import Path

script, root = sys.argv[1:3]
sys.path.insert(0, str(Path(script).resolve().parent))
spec = importlib.util.spec_from_file_location("mmw_verify_ticket", script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
print(mod.repository_check_missing(Path(root)) or "")
PY
}


bounce_goes_to_triage() {
  local number="$1" spec="$2" opened bounced rc
  [ -n "$spec" ] || return 0
  opened="$(newest_field "$spec" at spec.opened spec.suspended spec.closed)"; rc=$?
  case "$rc" in
    0) ;;
    3) return 0 ;;
    *) return 2 ;;
  esac
  bounced="$(newest_field "$number" at ticket.bounced)"; rc=$?
  case "$rc" in
    0) [ "$bounced" '<' "$opened" ] && return 1 || return 0 ;;
    3) return 1 ;;
    *) return 2 ;;
  esac
}


bounce_ticket() {
  local root="$1" number="$2" spec="$3" into="$4" base="$5" reason="$6" detail="$7"
  local started siblings="" text retry=0 rc
  local add_label=needs-triage remove_label=ready-for-agent outcome="labelled needs-triage"
  local fields=() prose_dir="" summary="" rest="" commands_json=""
  bounce_goes_to_triage "$number" "$spec"; rc=$?
  case "$rc" in
    0) ;;
    1) retry=1 ;;
    *) echo "dispatch: could not read whether #$number already bounced since the latest spec.opened on #$spec" >&2; return 2 ;;
  esac
  started="$(newest_worker_field "$number" base 2>/dev/null)" || started=""
  if [ -n "$started" ] && git -C "$root" cat-file -e "$started^{commit}" 2>/dev/null; then
    siblings="$(integrated_ticket_numbers "$root" "$started..origin/$into" | awk -v n="$number" '$0 != n')"
  fi
  if [ "$retry" -eq 1 ]; then
    add_label=ready-for-agent
    remove_label=needs-triage
    outcome="returned to ready-for-agent"
    text="Tried to merge issue-$number into origin/$into at $base and returned it to the agent queue for its one retry this night."
  else
    text="Tried to merge issue-$number into origin/$into at $base and handed it to triage."
  fi
  if [ -n "$siblings" ]; then
    text="$text Tickets landed after this ticket started: $(printf '#%s ' $siblings | sed 's/ $//')."
  else
    text="$text No sibling landing after this ticket started was found."
  fi
  if [ "$reason" = conflict ]; then
    text="$text Conflicted files: $(MMW_LIST="$detail" python3 -c 'import json, os; print(", ".join(json.loads(os.environ["MMW_LIST"])))')."
    fields=(--json-field "files=$detail")
  else
    prose_dir="$(mktemp -d)"
    if ! MMW_COMMANDS="$detail" MMW_PREFIX_LEN="${#text}" python3 - "$VERIFY" "$prose_dir" <<'PY'
import importlib.util, json, os, sys
from pathlib import Path

script, dest = sys.argv[1:]
sys.path.insert(0, str(Path(script).resolve().parent))
spec = importlib.util.spec_from_file_location("mmw_verify_ticket", script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
rows = json.loads(os.environ["MMW_COMMANDS"])
prefix = int(os.environ.get("MMW_PREFIX_LEN") or "0")
prose = mod.checks_bounce_prose(rows, prefix)
out = Path(dest)
out.joinpath("summary").write_text(prose["summary"], encoding="utf-8")
out.joinpath("rest").write_text(prose["rest"], encoding="utf-8")
out.joinpath("commands").write_text(
    json.dumps(prose["commands"], ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8")
PY
    then
      rm -rf "$prose_dir"
      echo "dispatch: could not build the checks report for #$number" >&2
      return 2
    fi
    summary="$(cat "$prose_dir/summary")"
    rest="$(cat "$prose_dir/rest")"
    commands_json="$(cat "$prose_dir/commands")"
    rm -rf "$prose_dir"
    prose_dir=""
    text="$text Failed checks: $summary."
    fields=(--json-field "commands=$commands_json")
  fi

  gh_ issue reopen "$number" >/dev/null 2>&1 \
    || { echo "dispatch: could not reopen #$number after its merge $reason" >&2; return 2; }
  gh_ issue edit "$number" --remove-label "$remove_label" --add-label "$add_label" \
      --remove-assignee @me >/dev/null 2>&1 \
    || { echo "dispatch: #$number is open, but could not be $outcome and unassigned" >&2; return 2; }
  if ! post_event "$number" ticket.bounced --ticket "$number" --spec "$spec" \
      --line "$text" \
      --text-file <(printf '%s\n' "$rest") \
      --field "reason=$reason" --field "commit=$base" \
      --field "into=$into" \
      "${fields[@]}"; then
    echo "dispatch: #$number was relabelled after its landing failure, but its ticket.bounced event was not written" >&2
    return 2
  fi
  stop_live_ticket_agents "$number" \
    || echo "dispatch: #$number was bounced, but its sessions could not be read and stopped" >&2
}


load_repo_url() {
  REPO_URL="$(gh_ repo view --json url -q .url 2>/dev/null | tr -d '[:space:]')"
  if [ -z "$REPO_URL" ]; then
    echo "dispatch: the tracker could not provide this repository's web URL; ticket.landed will be recorded without compare or commit links" >&2
  fi
}


landed_merge_and_base() {
  local root="$1" passed="$2" into="$3" candidate first_parent
  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    first_parent="$(git -C "$root" rev-parse "$candidate^1" 2>/dev/null)" || continue
    if git -C "$root" merge-base --is-ancestor "$passed" "$candidate" \
       && ! git -C "$root" merge-base --is-ancestor "$passed" "$first_parent"; then
      printf '%s\t%s\n' "$candidate" "$first_parent"
      return 0
    fi
  done < <(git -C "$root" rev-list --first-parent --reverse --merges \
            "origin/$into" 2>/dev/null)
}


commits_outside_base() {
  git -C "$1" rev-list --count "origin/$3..$2" 2>/dev/null
}


delete_landed_ticket_branch() {
  local root="$1" number="$2" into="$3" branch remote_ref remote_tip ahead output probe_rc

  branch="$(ticket_branch "$number")"
  [[ "$branch" =~ ^issue-[0-9]+$ ]] || return 0
  [ "$branch" != "$into" ] || return 0
  remote_ref="refs/remotes/origin/$branch"

  if git -C "$root" worktree list --porcelain \
       | grep -Fx "branch refs/heads/$branch" >/dev/null; then
    echo "dispatch: keeping $branch because a worktree still has it checked out" >&2
    return 0
  fi

  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
    ahead="$(commits_outside_base "$root" "refs/heads/$branch" "$into")" || ahead=""
    if [ -z "$ahead" ]; then
      echo "dispatch: keeping local $branch because its containment in origin/$into could not be checked" >&2
    elif [ "$ahead" -ne 0 ]; then
      echo "dispatch: keeping local $branch because it has $ahead commit(s) not in origin/$into" >&2
    elif ! output="$(git -C "$root" branch -D "$branch" 2>&1)"; then
      echo "dispatch: could not delete local $branch: $(printf '%s' "$output" | tail -2 | tr '\n' ' '); delete it manually with: git branch -D $branch" >&2
    fi
  fi

  git -C "$root" show-ref --verify --quiet "$remote_ref" || return 0
  remote_tip="$(git -C "$root" rev-parse "$remote_ref")"
  ahead="$(commits_outside_base "$root" "$remote_ref" "$into")" || ahead=""
  if [ -z "$ahead" ]; then
    echo "dispatch: keeping origin/$branch because its containment in origin/$into could not be checked" >&2
    return 0
  fi
  if [ "$ahead" -ne 0 ]; then
    echo "dispatch: keeping origin/$branch because it has $ahead commit(s) not in origin/$into" >&2
    return 0
  fi
  if output="$(git -C "$root" push \
      "--force-with-lease=refs/heads/$branch:$remote_tip" origin --delete "$branch" 2>&1)"; then
    return 0
  fi
  git -C "$root" ls-remote --exit-code origin "refs/heads/$branch" >/dev/null 2>&1
  probe_rc=$?
  if [ "$probe_rc" -eq 2 ]; then
    return 0
  fi
  [ "$probe_rc" -eq 0 ] \
    || output="$output The remote could not be checked after the failed deletion."
  echo "dispatch: could not delete origin/$branch: $(printf '%s' "$output" | tr '\n' ' '); after confirming its tip is contained in origin/$into, delete it manually with: git push origin --delete $branch" >&2
}


ticket_is_landed() {
  local folded
  folded="$(ticket_events "$1" fold)" || return 2
  printf '%s\n' "$folded" | python3 -c '
import json, sys
raise SystemExit(0 if json.load(sys.stdin).get("landed") else 1)
'
}


finish_landing() {
  local root="$1" number="$2" spec="$3" into="$4" passed="$5"
  local merge_commit="$6" base="$7" mode="$8" landing_state
  ticket_is_landed "$number"; landing_state=$?
  if [ "$landing_state" -eq 0 ]; then
    archive_workspace "$number" || return 1
    delete_landed_ticket_branch "$root" "$number" "$into"
    return 0
  fi
  if [ "$landing_state" -eq 2 ]; then
    echo "dispatch: could not read #$number before recording ticket.landed; nothing was written and the landing can be retried" >&2
    return 1
  fi
  archive_workspace "$number" || return 1
  if [ "$mode" = land ]; then
    gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1 \
      || echo "land: could not give #$number's claim back" >&2
    post_event "$number" ticket.released --ticket "$number" --spec "$spec" \
        --line "Gave the claim on #$number back: its work is over" --field reason=landed \
      || echo "land: #$number's claim is given back, but its ticket.released event was not written" >&2
  fi
  if record_landed "$number" "$spec" "$into" "$passed" "$merge_commit" "$base"; then
    delete_landed_ticket_branch "$root" "$number" "$into"
  else
    return 1
  fi
}


land_one_via_origin() {
  local root="$1" number="$2" spec="$3" into="$4" passed="$5" mode="${6:-advance}"
  local attempt merge_root base merge_commit landed_base rc files push_error=""
  for ((attempt = 1; attempt <= MERGE_TRIES; attempt++)); do
    prepare_merge_worktree "$root" "$into"; rc=$?
    [ "$rc" -eq 0 ] || return "$rc"
    merge_root="$MERGE_ROOT"
    base="$(git -C "$merge_root" rev-parse "origin/$into")"
    if git -C "$merge_root" merge-base --is-ancestor "$passed" "origin/$into"; then
      merge_commit=""
      landed_base=""
      IFS=$'\t' read -r merge_commit landed_base \
        < <(landed_merge_and_base "$merge_root" "$passed" "$into") || true
      finish_landing "$root" "$number" "$spec" "$into" "$passed" \
        "$merge_commit" "$landed_base" "$mode" \
        || { release_merge_lock; return 2; }
      release_merge_lock
      return 3
    fi
    if ! git -C "$merge_root" merge --no-ff -m "Merge branch 'issue-$number'" "$passed" >/dev/null 2>&1; then
        if git -C "$merge_root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
          files="$(git -C "$merge_root" diff --name-only --diff-filter=U \
            | python3 -c 'import json, sys; print(json.dumps([l.rstrip("\n") for l in sys.stdin if l.strip()]))')"
          git -C "$merge_root" merge --abort >/dev/null 2>&1 || true
          git -C "$merge_root" reset --hard "origin/$into" >/dev/null
          echo "dispatch: #$number conflicts in $files; Coordinator: resolve the merge of $passed into origin/$into in a separate integration checkout, run repository checks, commit and fast-forward push HEAD:$into, then retry advance or land. The passed result is unchanged; no Worker was requeued." >&2
          release_merge_lock
          return 2
        fi
        release_merge_lock
        [ "$attempt" -lt "$MERGE_TRIES" ] && { sleep 2; continue; }
        echo "dispatch: could not merge ticket.passed commit $passed for #$number after $MERGE_TRIES tries" >&2
        return 2
    fi
    merge_commit="$(git -C "$merge_root" rev-parse HEAD)"

    run_merge_checks "$merge_root" "origin/$into" "$root/.worktrees/issue-$number" "$number"; rc=$?
    if [ "$rc" -eq 1 ]; then
      git -C "$merge_root" reset --hard "origin/$into" >/dev/null
      if ! bounce_ticket "$merge_root" "$number" "$spec" "$into" "$base" checks "$MERGE_CHECKS_FAILED"; then
        release_merge_lock
        return 2
      fi
      release_merge_lock
      return 1
    elif [ "$rc" -ne 0 ]; then
      git -C "$merge_root" reset --hard "origin/$into" >/dev/null
      release_merge_lock
      if [ "$rc" -eq 3 ]; then
        echo "dispatch: #$number is not landed, and stays passed rather than bounced: the merge with origin/$into has no check to run: $MERGE_CHECKS_DETAIL. Commit an executable scripts/check to origin/$into" >&2
      else
        printf 'dispatch: #%s is not landed, and stays passed rather than bounced: %s\nFix that on this machine; the ticket needs nothing\n' \
          "$number" "$MERGE_CHECKS_DETAIL" >&2
      fi
      return 2
    fi

    if push_error="$(git -C "$merge_root" push origin "HEAD:$into" 2>&1)"; then
      finish_landing "$root" "$number" "$spec" "$into" "$passed" \
        "$merge_commit" "$base" "$mode" \
        || { release_merge_lock; return 2; }
      release_merge_lock
      return 0
    fi
    release_merge_lock
    [ "$attempt" -lt "$MERGE_TRIES" ] && continue
  done
  echo "dispatch: the fast-forward push of #$number to origin/$into was rejected after $MERGE_TRIES merge attempts; nothing was force-pushed: $(printf '%s' "$push_error" | tail -2 | tr '\n' ' ')" >&2
  return 2
}


record_landed() {
  local number="$1" spec="${2:-}" into="$3" commit="$4" merge="${5:-}" base="${6:-}" branch line
  local -a fields
  branch="$(ticket_branch "$number")"
  line="Landed $branch into $into"
  if [ -n "$REPO_URL" ] && [ -n "$merge" ] && [ -n "$base" ]; then
    line="$line: $REPO_URL/compare/$base...$merge (merge commit $REPO_URL/commit/$merge)"
  elif [ -n "$REPO_URL" ] && [ -z "$merge" ]; then
    line="$line: $REPO_URL/commit/$commit"
  fi
  fields=(--field "branch=$branch" --field "into=$into" --field "commit=$commit")
  [ -z "$merge" ] || fields+=(--field "merge=$merge")
  [ -z "$base" ] || fields+=(--field "base=$base")
  if ! post_event "$number" ticket.landed --ticket "$number" --spec "$spec" \
      --line "$line" "${fields[@]}"; then
    echo "dispatch: $commit is in origin/$into, but the ticket.landed event on #$number was not written; the tickets it blocks stay blocked until the next advance or land writes it" >&2
    return 1
  fi
}


land_tickets() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to land into"
  load_repo_url

  local -a numbers=("$@")

  local plan
  plan="$(python3 "$STATUS" --land-plan "${numbers[@]}")" \
    || refuse "could not read $(printf '#%s ' "${numbers[@]}")from the tracker"

  local merged=0 already=0 bounced=0 kept=0 failed=0 environment_failed=0 number passed into archive_into rc spec
  local -a attempted_numbers=()
  while IFS= read -r number; do
    [ -n "$number" ] || continue
    attempted_numbers+=("$number")
    passed="$(ticket_passed_commit "$number")" \
      || { echo "land: #$number has no usable ticket.passed commit" >&2; failed=$((failed + 1)); continue; }
    spec="$(ticket_spec "$number")"
    into="$(passed_into "$number")" \
      || { echo "land: #$number has no base branch in its events" >&2; failed=$((failed + 1)); continue; }
    land_one_via_origin "$root" "$number" "$spec" "$into" "$passed" land
    rc=$?
    case "$rc" in
      0) merged=$((merged + 1)) ;;
      1) bounced=$((bounced + 1)) ;;
      3) already=$((already + 1)) ;;
      4) failed=$((failed + 1)); environment_failed=1 ;;
      *) failed=$((failed + 1)) ;;
    esac
  done < <(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }')

  # A handed-back ticket has no MERGE line, but land still gives back a claim left on
  # it and preserves its standing worktree for the next start.
  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    case " ${attempted_numbers[*]-} " in *" $number "*) continue ;; esac
    local cwd
    cwd="$(workspace_cwd_for "$number")"
    [ -z "$cwd" ] || worktree_environment "$cwd" down || true
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      post_event "$number" ticket.released --ticket "$number" --spec "$(ticket_spec "$number")" \
          --line "Gave the claim on #$number back: its work is over" --field reason=landed \
        || echo "land: #$number's claim is given back, but its ticket.released event was not written" >&2
    else
      echo "land: could not give #$number's claim back" >&2
    fi
  done

  # A closed ticket with no pass is not silently archived while its branch still has
  # work that origin/<into> does not contain.
  for number in $(printf '%s\n' "$plan" | awk '$1 == "ARCHIVE" { print $2 }'); do
    case " ${attempted_numbers[*]-} " in *" $number "*) continue ;; esac
    archive_into="$(ticket_into "$number")" \
      || { echo "land: #$number has no base branch in its events; not archiving it" >&2; failed=$((failed + 1)); continue; }
    fetch_origin "$root" \
      || { echo "land: could not fetch origin before deciding whether to archive #$number" >&2; failed=$((failed + 1)); continue; }
    if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null \
       && ! git -C "$root" merge-base --is-ancestor "refs/heads/issue-$number" \
            "origin/${archive_into}" 2>/dev/null; then
      echo "land: #$number is closed but issue-$number is not in origin/${archive_into}; not archiving it" >&2
      failed=$((failed + 1))
      continue
    fi
    if archive_workspace "$number"; then
      if ticket_is_landed "$number"; then
        delete_landed_ticket_branch "$root" "$number" "$archive_into"
      fi
    else
      failed=$((failed + 1))
    fi
  done

  while IFS= read -r line; do
    [ -n "$line" ] || continue
    echo "  $line" >&2
    kept=$((kept + 1))
  done < <(printf '%s\n' "$plan" | sed -n 's/^HOLD \(.*\)$/#\1/p')

  # A ticket that needs nothing is named too. Landing one and landing none print the
  # same tally otherwise, and the difference is the whole question the caller asked.
  local nothing=0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    echo "  $line" >&2
    nothing=$((nothing + 1))
  done < <(printf '%s\n' "$plan" | sed -n 's/^NOTHING \([0-9]*\) \(.*\)$/#\1 needs nothing: \2/p')

  echo "land: merged $merged, already in $already, bounced $bounced, still working $kept, already landed $nothing, failed $failed" >&2

  # `land <n>` is the whole ending of a ticket outside a night, so the watch `open-ticket`
  # opened for it closes here, and the relay with it when it watched nothing else. A
  # night's watch is not this one and is left alone.
  local relay_left=0
  if [ "$kept" -eq 0 ] && [ "$failed" -eq 0 ]; then
    for number in "${numbers[@]}"; do
      stop_relay --tickets "$number"
      [ "$?" = 1 ] && relay_left=1
    done
  fi
  [ "$environment_failed" -eq 0 ] || return 2
  [ "$failed" -eq 0 ] && [ "$relay_left" -eq 0 ] || return 1
}
