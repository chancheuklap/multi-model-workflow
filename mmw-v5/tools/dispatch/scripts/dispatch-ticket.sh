# Ticket dispatch and batch lifecycle. Sourced by dispatch.sh.
DEFAULT_WORKER=junior-worker

ticket_events() {
  local number="$1" json
  shift
  json="$(ticket_comments "$number")" || return 2
  printf '%s' "$json" | python3 "$EVENTS" "$@" "$number" --comments-file -
}

session_on_ticket() {
  local number="$1" kind="${2:-}"
  if [ -n "$kind" ]; then
    ticket_events "$number" session --kind "$kind"
  else
    ticket_events "$number" session
  fi
}

sessions_on_ticket() {
  ticket_events "$1" sessions
}

live_workers_on_ticket() {
  ticket_events "$1" live --kind worker
}

last_worker_on_ticket() {
  ticket_events "$1" fold | python3 -c '
import json, sys
state = json.load(sys.stdin)
workers = [r for r in state.get("sessions") or [] if r.get("kind") == "worker"]
if not workers:
    raise SystemExit(0)
last = workers[-1]
how = ("it was replaced" if last.get("live")
       else "its hold ended with " + str(last.get("ended_by") or "an event"))
print("worker %s on %s, left when %s" % (last.get("session"), last.get("runner"), how))
'
}

newest_field() {
  local number="$1" field="$2" json
  shift 2
  json="$(ticket_comments "$number")" || return 2
  printf '%s' "$json" | MMW_EVENT_NAMES="$*" MMW_FIELD="$field" MMW_N="$number" \
    python3 -c '
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("mmw_events", os.environ["MMW_DISPATCH_EVENTS"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    comments = mod.read_comments(None, "-")
except mod.Unreadable as exc:
    print("dispatch: " + str(exc), file=sys.stderr)
    raise SystemExit(2)
state = mod.fold(comments)
if mod.refuse_unreadable(state, int(os.environ["MMW_N"])):
    raise SystemExit(2)
names = os.environ["MMW_EVENT_NAMES"].split()
record = mod.newest(comments, *names)
if record is None or (len(names) > 1 and record["event"] != names[0]):
    raise SystemExit(3)
value = record["payload"].get(os.environ["MMW_FIELD"])
if value in (None, ""):
    raise SystemExit(4)
print(value)
'
}

newest_worker_field() {
  local number="$1" field="$2" value rc
  value="$(newest_field "$number" "$field" worker.started)"
  rc=$?
  case "$rc" in
    0) printf '%s\n' "$value" ;;
    2) echo "dispatch: could not read #$number's events, so its $field is unknown" >&2; return 2 ;;
    3 | 4) return 3 ;;
    *) echo "dispatch: could not resolve #$number's $field from its worker.started event" >&2; return 2 ;;
  esac
}

base_commit() {
  git -C "$1" merge-base "origin/$2" "$3" 2>/dev/null
}

worker_base() {
  local number="$1" root="$2" into="$3" head="$4"
  newest_field "$number" event worker.started ticket.landed >/dev/null
  case "$?" in
    0) newest_worker_field "$number" base
       case "$?" in
         0) ;;
         3) base_commit "$root" "$into" "$head" || true ;;
         *) return 2 ;;
       esac ;;
    3) base_commit "$root" "$into" "$head" || true ;;
    *) echo "dispatch: could not read #$number's events, so whether its earlier work has landed, and with it the base to record, is unknown; run this again once the tracker answers" >&2; return 2 ;;
  esac
}

ticket_into() {
  newest_worker_field "$1" into
}

passed_into() {
  local number="$1" into rc
  into="$(newest_field "$number" into ticket.passed)"; rc=$?
  case "$rc" in
    0) printf '%s\n' "$into" ;;
    2) echo "dispatch: could not read #$number's events, so its base branch is unknown" >&2; return 2 ;;
    *) echo "dispatch: #$number carries no ticket.passed with a base branch" >&2; return 2 ;;
  esac
}

night_into() {
  local into rc
  into="$(newest_field "$1" into spec.opened spec.suspended spec.closed)"
  rc=$?
  case "$rc" in
    0) printf '%s\n' "$into" ;;
    3) return 3 ;;
    *) echo "dispatch: could not read whether the night on #$1 is open, so its base branch is unknown" >&2; return 2 ;;
  esac
}

ticket_spec() {
  local found
  found="$(gh_ issue view "$1" --json parent --jq '.parent.number // empty' | head -n 1)" \
    || { echo "dispatch: cannot read native parent of #$1" >&2; return 2; }
  case "$found" in "" | *[!0-9]*) return 0 ;; esac
  printf '%s\n' "$found"
}

machine_name() {
  python3 -c 'import socket; print(socket.gethostname())'
}

post_event() {
  local issue="$1" body file code
  shift
  body="$(python3 "$EVENTS" emit "$@")" || return 2
  file="$(mktemp)" || return 2
  printf '%s\n' "$body" >"$file"
  gh_ issue comment "$issue" --body-file "$file" >/dev/null
  code=$?
  rm -f "$file"
  return "$code"
}

relay_watches() {
  local number="$1" spec="$2" repo
  repo="$(repo_slug)" || return 2
  local -a which=()
  [ -z "$number" ] || which+=(--ticket "$number")
  [ -z "$spec" ] || which+=(--spec "$spec")
  python3 "$RELAY" watching --repo "$repo" "${which[@]}" >/dev/null
}

revive_night_watch() {
  local spec="$1" repo runner session out
  [ -n "$spec" ] || return 1
  runner="$(newest_field "$spec" runner spec.opened spec.suspended spec.closed 2>/dev/null)" || return 1
  session="$(newest_field "$spec" session spec.opened spec.suspended spec.closed 2>/dev/null)" || return 1
  repo="$(repo_slug)" || return 1
  out="$(python3 "$RELAY" start --repo "$repo" --spec "$spec" --runner "$runner" --session "$session" 2>&1)" \
    || { echo "dispatch: the night on #$spec is open and its watch could not be restored: ${out#relay: }" >&2; return 1; }
  python3 "$WATCHDOG" arm --repo "$repo" >&2 || return 1
  echo "dispatch: the night on #$spec is open and nothing watched it; the watch is restored with $runner session $session as its orchestrator" >&2
}

night_orchestrator_line() {
  local spec="$1" runner session line own
  runner="$(newest_field "$spec" runner spec.opened spec.suspended spec.closed 2>/dev/null)" || return 0
  session="$(newest_field "$spec" session spec.opened spec.suspended spec.closed 2>/dev/null)" || return 0
  if ! line="$(own_session 2>/dev/null)"; then
    echo "orchestrator: wake-ups go to $runner session $session; this session runs in no runner that can name it, so it cannot take the night over"
    return 0
  fi
  own="${line%%$'\t'*} session ${line#*$'\t'}"
  if [ "$own" = "$runner session $session" ]; then
    echo "orchestrator: wake-ups go to $runner session $session, this session"
  else
    echo "orchestrator: wake-ups go to $runner session $session, not this session ($own); run \`dispatch.sh open $spec --into BASE --project PROJECT --worker-task FILE --reviewer-task FILE\` from this session to take the night over"
  fi
}

stop_relay() {
  local repo out rc
  repo="$(repo_slug)" || return 1
  out="$(python3 "$RELAY" stop --repo "$repo" "$@" 2>&1)"
  rc=$?
  case "$rc" in
    0)
      case "$out" in stopped*) echo "dispatch: $out" >&2 ;; esac
      return 0
      ;;
    3) return 3 ;;
  esac
  echo "dispatch: ${out#relay: }" >&2
  return 1
}

open_relay() {
  local repo line runner session out
  repo="$(repo_slug)" || return 2
  line="$(own_session)" || return 2
  runner="${line%%$'\t'*}"
  session="${line#*$'\t'}"
  out="$(python3 "$RELAY" start --repo "$repo" "$@" --runner "$runner" --session "$session")" \
    || { echo "dispatch: the relay did not open the watch for $runner session $session (the reason is above), so nothing was opened" >&2; return 2; }
  if ! python3 "$WATCHDOG" arm --repo "$repo" >&2; then
    case "$out" in "opened "*) stop_relay "$@" ;; esac
    echo "dispatch: watchdog could not be armed; no session was started" >&2
    return 2
  fi
  printf '%s\n' "$out" | sed 's/^/dispatch: /' >&2
  case "$out" in
    "opened "*) printf '%s\t%s\tstarted\n' "$runner" "$session" ;;
    *) printf '%s\t%s\trunning\n' "$runner" "$session" ;;
  esac
}

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

retract_one() {
  local number="$1"

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] \
    || refuse "not inside a git repository, so there is no workspace to retract"

  local live_list worker_runner name session
  live_list="$(live_workers_on_ticket "$number")" || return 2
  while IFS=$'\t' read -r name session; do
    [ -n "$session" ] || continue
    [ "$(runner_call "$name" liveness "$session")" = stopped ] \
      || refuse "#$number worker $session on $name is not confirmed stopped; nothing was retracted"
  done <<<"$live_list"
  local line ident
  line="$(session_on_ticket "$number" worker)" \
    || refuse "could not read #$number's events, so whether a worker still runs there is unknown and nothing was archived"
  ident="$(printf '%s\n' "$line" | cut -f2)"
  worker_runner="${line%%$'\t'*}"
  [ -z "$line" ] || use_runner "$(printf '%s\n' "$line" | cut -f1)"
  if [ -n "$ident" ]; then
    case "$(runner liveness "$ident")" in
      stopped) ;;
      alive)
        refuse "#$number still has a live agent $ident on $RUNNER_NAME; retract is for a start whose session is gone"
        ;;
      *)
        refuse "cannot tell whether #$number's agent $ident is still running, so nothing was archived; retract only once that agent is shown to be stopped"
        ;;
    esac
  fi

  local cwd archived=0 claim=0
  cwd="$(workspace_cwd_for "$number")"
  if [ -n "$cwd" ] && [ -d "$cwd" ]; then
    local left_by="whoever claimed #$number with no session recorded on it"
    [ -z "$ident" ] || left_by="worker $ident on $RUNNER_NAME, left when its session stopped"
    keep_unfinished_work "$number" "$cwd" "$left_by" \
      || refuse "the uncommitted work in $cwd was not saved (the reason is above), and archiving would delete it; commit or set it aside on issue-$number, then retract again. Nothing was retracted"
    push_ticket_branch "$number" "$cwd" \
      || refuse "issue-$number was not pushed, so its worktree and claim were kept; reconcile it with origin/issue-$number and retract again"
  fi
  if [ -n "$cwd" ] && [ -d "$cwd" ]; then
    archive_workspace "$number" || return 1
    archived=1
  fi

  give_claim_back "$number"
  case "$?" in
    0) claim=1 ;;
    2) echo "dispatch: could not give back the claim on #$number" >&2 ;;
  esac

  local -a named=()
  [ -z "$ident" ] || named=(--field "session=$ident" --field "runner=$worker_runner")
  post_event "$number" worker.retracted --ticket "$number" --spec "$(ticket_spec "$number")" \
      --line "Retracted the start on #$number: archived $archived, claim given back $claim" \
      ${named[@]+"${named[@]}"} \
      --json-field "archived=$([ "$archived" = 1 ] && echo true || echo false)" \
      --json-field "claim_given_back=$([ "$claim" = 1 ] && echo true || echo false)" \
    || { echo "dispatch: could not write worker.retracted on #$number; run retract again" >&2; return 2; }

  while IFS=$'\t' read -r name session; do
    [ -n "$session" ] || continue
    [ "$name:$session" != "$worker_runner:$ident" ] || continue
    post_event "$number" worker.retracted --ticket "$number" --spec "$(ticket_spec "$number")" \
      --line "Retracted stopped worker $session on $name" --field "runner=$name" --field "session=$session" || return 2
  done <<<"$live_list"
  echo "retract #$number: archived $archived, claim given back $claim" >&2
}

resume_one() {
  local number="$1" text="$2" ident out
  [ -n "$text" ] || refuse "resume needs the text to send"
  local live line
  live="$(live_workers_on_ticket "$number")" \
    || refuse "could not read #$number's events, so whether a worker still holds it is unknown and nothing was sent; run resume again once the tracker answers, or fix the comment named above"
  line="$(printf '%s\n' "$live" | sed '/^$/d' | tail -n 1)"
  [ -n "$line" ] || refuse "$(ended_worker_hold "$number")"
  use_runner "$(printf '%s\n' "$line" | cut -f1)"
  ident="$(printf '%s\n' "$line" | cut -f2)"
  out="$(runner send "$ident" "$text" 2>&1)"
  local rc=$?
  case "$rc" in
    0 | 4)
      post_event "$number" worker.resumed --ticket "$number" --spec "$(ticket_spec "$number")" \
          --line "Resumed the worker $ident on $RUNNER_NAME" \
          --field "session=$ident" --field "runner=$RUNNER_NAME" \
        || echo "dispatch: the worker $ident took the message, but the worker.resumed event on #$number was not written" >&2
      [ "$rc" = 0 ] && return 0
      echo "dispatch: the worker $ident on #$number was handed the message, and $RUNNER_NAME cannot show a turn starting on it; the text is in the session, so do not send it again" >&2
      exit 4 ;;
    2) refuse "#$number worker $ident is no longer on $RUNNER_NAME; nothing was sent. Its event hold remains recorded. dispatch.sh retract $number checks that the session stopped before releasing that hold" ;;
  esac
  echo "dispatch: the worker $ident on #$number did not take the message" >&2
  [ -n "$out" ] && printf '  %s\n' "$out" >&2
  echo "dispatch: continuation was not accepted; adapter exit $rc. No retry or replacement was attempted" >&2
  exit 3
}

ended_worker_hold() {
  ticket_events "$1" fold | MMW_N="$1" python3 -c '
import json,os,sys
number=os.environ["MMW_N"]
state=json.load(sys.stdin)
workers=[row for row in state["sessions"] if row["kind"]=="worker"]
if workers:
    row=workers[-1]
    print("#%s has no live worker hold. Worker %s on %s ended with %s. " %
          (number,row.get("session"),row.get("runner"),row.get("ended_by") or "an event"),end="")
else:
    print("#%s has no worker.started record. " % number,end="")
print("Nothing was sent. A new start requires dispatch.sh start %s worker --task FILE." % number)
' || printf 'Cannot read why #%s has no worker hold; nothing was sent.\n' "$1"
}

result_event() {
  ticket_events "$1" fold | python3 - "$EVENTS" "$2" "${3:-}" /dev/fd/3 3<&0 <<'PYRESULT'
import importlib.util,json,sys
script,kind,prose,source=sys.argv[1:]
spec=importlib.util.spec_from_file_location('dispatch_events',script)
events=importlib.util.module_from_spec(spec);spec.loader.exec_module(events)
with open(source) as stream:state=json.load(stream)
if events.refuse_unreadable(state,None):raise SystemExit(2)
record=state['results'].get(kind)
starts=[s for s in state['sessions'] if s['kind']==kind]
if record and (not starts or record['comment']>starts[-1]['comment']):
    print(events.describe(record))
    if prose:print(events.BLOCK_RE.sub('',record['body']).strip())
PYRESULT
}

wait_one() {
  local number="$1" kind="$2"
  case "$kind" in
    worker|reviewer) ;;
    *) refuse "the second argument is worker or reviewer, got $kind" ;;
  esac

  local head prose=""
  [ "$kind" = reviewer ] && prose="--prose"
  head="$(result_event "$number" "$kind" $prose)" \
    || refuse "could not read #$number's events, so what its $kind reported is unknown"
  if [ -n "$head" ]; then
    printf '%s\n' "$head"
    return 0
  fi

  local line
  line="$(session_on_ticket "$number" "$kind")" \
    || refuse "could not read #$number's events, so what its $kind reported is unknown"
  [ -n "$line" ] || refuse "#$number has no $kind.started event, so there is no result to read"
  echo "dispatch: #$number carries no result of its $kind yet; read notifications with dispatch.sh wait-wake" >&2
  exit 3
}

advance() {
  local spec="$1" task expected_into
  task="$(newest_field "$spec" worker_task spec.opened spec.suspended spec.closed)" || refuse "#$spec has no caller worker task; open it with --worker-task FILE"
  [ -s "$task" ] || refuse "caller task file $task is unavailable"
  expected_into="$(night_into "$spec")" || refuse "#$spec has no open target branch"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to merge into"

  export MMW_SPEC="$spec"
  load_repo_url

  local watched
  watched="$(relay_watches "" "$spec" 2>&1)" \
    || revive_night_watch "$spec" \
    || refuse "the night on #$spec is not open: ${watched#relay: }. Nothing would wake you when a ticket lands, so nothing was merged or started; run open $spec first"

  stop_returned_ticket_agents "$spec" \
    || echo "dispatch: could not finish checking returned tickets under #$spec" >&2

  local plan plan_err plan_status cap_failed=0
  plan_err="$(mktemp)"
  plan="$(python3 "$STATUS" --advance-plan "$spec" 2>"$plan_err")"
  plan_status=$?
  case "$plan_status" in
    0) ;;
    3) cap_failed=1; cat "$plan_err" >&2 ;;
    *) cat "$plan_err" >&2; rm -f "$plan_err"; refuse "could not read the batch under #$spec" ;;
  esac
  rm -f "$plan_err"

  local merged=0 skipped=0 bounced=0 failed=0 bounced_this_advance="" number passed into rc
  for number in $(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }'); do
    if ! passed="$(ticket_passed_commit "$number")"; then
      echo "dispatch: #${number}'s ticket.passed event carries no usable commit, so it is not landed" >&2
      failed=$((failed + 1)); continue
    fi
    if ! into="$(passed_into "$number")"; then
      echo "dispatch: #${number}'s events carry no usable base branch, so it is not landed" >&2
      failed=$((failed + 1)); continue
    fi
    if [ "$into" != "$expected_into" ]; then
      echo "dispatch: #$number passed for $into, but #$spec targets $expected_into; nothing was merged for that ticket" >&2
      failed=$((failed + 1)); continue
    fi
    land_one_via_origin "$root" "$number" "$spec" "$into" "$passed"
    rc=$?
    case "$rc" in
      0)
        merged=$((merged + 1))
        echo "merged issue-$number into origin/$into" >&2
        ;;
      1)
        bounced=$((bounced + 1))
        bounced_this_advance="${bounced_this_advance:+$bounced_this_advance }$number"
        ;;
      3) skipped=$((skipped + 1)) ;;
      *)
        echo "dispatch: #$number is not landed: could not land it into origin/$into (the reason is above); run advance again once that is fixed" >&2
        failed=$((failed + 1))
        ;;
    esac
  done

  local released=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      released=$((released + 1))
      echo "released the claim on #$number: it is open in the agent queue and an event on it ended its worker's hold, so the worker that claimed it is gone" >&2
      post_event "$number" ticket.released --ticket "$number" --spec "$spec" \
          --line "Gave the claim on #$number back: an event on it ended its worker's hold" \
          --field reason=worker-lost \
        || echo "dispatch: the claim on #$number is given back, but its ticket.released event was not written" >&2
    else
      echo "dispatch: could not take the claim off #$number, so it stays off the frontier" >&2
    fi
  done

  plan="$(python3 "$STATUS" --advance-plan "$spec")"
  plan_status=$?
  case "$plan_status" in
    0) ;;
    3) cap_failed=1 ;;
    *) refuse "could not read the batch under #$spec again after its merges, so nothing was started" ;;
  esac

  local started=0 refused=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
    case " $bounced_this_advance " in *" $number "*) continue ;; esac
    if bash "$SELF" start "$number" worker --task "$task"; then
      started=$((started + 1))
    else
      refused=$((refused + 1))
    fi
  done

  if [ -n "$bounced_this_advance" ]; then
    plan="$(python3 "$STATUS" --advance-plan "$spec")"
    plan_status=$?
    case "$plan_status" in
      0) ;;
      3) cap_failed=1 ;;
      *) refuse "could not read the batch under #$spec a third time, after its bounces, so the returned tickets were not restarted" ;;
    esac
    for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
      case " $bounced_this_advance " in *" $number "*) ;; *) continue ;; esac
      if bash "$SELF" start "$number" worker --task "$task"; then
        started=$((started + 1))
      else
        refused=$((refused + 1))
      fi
    done
  fi

  echo "advance #$spec: merged $merged, already in $skipped, bounced $bounced, released $released, started $started, refused $refused, failed $failed" >&2
  [ "$failed" -eq 0 ] || exit 2
  [ "$refused" -eq 0 ] || exit 4
  [ "$cap_failed" -eq 0 ] || exit 2
}

suspend_text() {
  local spec="$1" when="$2" ident="$3" number="$4"
  printf '%s\n' \
    "The night on spec #$spec was suspended at $when, so nothing here says whether this ticket's work is finished."
  if [ -n "$ident" ]; then
    printf '%s\n' "Interrupted: $ident. Its tracked edits were committed and issue-$number was pushed to origin before the hold ended. The batch is taken up again where it stands with advance."
  else
    printf '%s\n' "No session of ours was working on it at that moment. It keeps its label, so the next advance of #$spec starts it."
  fi
}

suspend_night() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local root git_dir
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so this night's workspaces have no name"
  git_dir="$(git -C "$root" rev-parse --absolute-git-dir 2>/dev/null)"
  [ -n "$git_dir" ] || refuse "not inside a git repository, so this night's workspaces have no name"

  local grades queued batch left=0
  grades="$(python3 "$STATUS" --worker-grades "$spec")" \
    || refuse "could not read the batch under #$spec"
  queued="$(printf '%s\n' "$grades" | awk '$1 == "GRADE" { print $2 }')"
  batch="$(printf '%s\n' "$grades" | awk '$1 == "BATCH" { print $2 }')"

  local live="" number ident name sessions stopped=0 kept="" push_failed=""
  for number in $batch; do
    if ! sessions="$(ticket_events "$number" live)"; then
      echo "dispatch: could not read #$number's events, so whether a session still runs on it is unknown; it is left as it is" >&2
      kept="$kept $number"
      left=$((left + 1))
      continue
    fi
    while IFS=$'\t' read -r name ident; do
      [ -n "$ident" ] || continue
      use_runner "$name"
      [ "$(runner liveness "$ident")" = stopped ] && continue
      if runner stop "$ident"; then
        stopped=$((stopped + 1))
        live="$live$number"$'\t'"$ident"$'\n'
      else
        echo "dispatch: could not stop $ident on #$number, so it is still running" >&2
        kept="$kept $number"
        left=$((left + 1))
        break
      fi
    done <<<"$sessions"
  done

  local cwd left_by
  for number in $queued; do
    case " $kept " in *" $number "*) continue ;; esac
    printf '%s\n' "$live" | awk -F '\t' -v n="$number" '$1 == n { found=1 } END { exit !found }' \
      || continue
    cwd="$(workspace_cwd_for "$number")"
    [ -n "$cwd" ] || continue
    left_by="$(last_worker_on_ticket "$number")" || left_by=""
    [ -n "$left_by" ] || left_by="the suspended work on #$number"
    if ! keep_unfinished_work "$number" "$cwd" "$left_by" \
        || ! push_ticket_branch "$number" "$cwd"; then
      echo "dispatch: #$number could not commit and push its ticket branch, so its workspace, claim and event hold are kept" >&2
      kept="$kept $number"
      push_failed="$push_failed $number"
      left=$((left + 1))
    fi
  done

  for number in $batch; do
    case " $kept " in *" $number "*) continue ;; esac
    cwd="$(workspace_cwd_for "$number")"
    [ -z "$cwd" ] || worktree_environment "$cwd" down || true
  done

  local when commented=0
  when="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  post_event "$spec" spec.suspended --spec "$spec" --line "NIGHT SUSPENDED #$spec" \
      --field "suspended_at=$when" \
    || { echo "dispatch: could not write the spec.suspended event on #$spec" >&2; left=$((left + 1)); }
  for number in $queued; do
    case " $kept " in *" $number "*) continue ;; esac
    ident="$(printf '%s\n' "$live" | awk -F '\t' -v n="$number" '$1 == n { ids = ids sep $2; sep = ", " } END { print ids }')"
    local -a interrupted=()
    [ -z "$ident" ] || interrupted=(--field "interrupted=$ident")
    if post_event "$number" spec.suspended --ticket "$number" --spec "$spec" \
         --line "NIGHT SUSPENDED #$spec" --text-file <(suspend_text "$spec" "$when" "$ident" "$number") \
         --field "suspended_at=$when" ${interrupted[@]+"${interrupted[@]}"}; then
      commented=$((commented + 1))
    else
      echo "dispatch: could not comment on #$number, so nothing on it says the night was suspended" >&2
      left=$((left + 1))
    fi
  done

  local claims=0
  for number in $queued; do
    [ -n "$number" ] || continue
    case " $kept " in *" $number "*) continue ;; esac
    give_claim_back "$number"
    case "$?" in
      0)
        claims=$((claims + 1))
        echo "gave back the claim on #$number: the night is suspended, so the next advance can start it again" >&2
        post_event "$number" ticket.released --ticket "$number" --spec "$spec" \
            --line "Gave the claim on #$number back: the night on #$spec is suspended" \
            --field reason=suspended \
          || echo "dispatch: the claim on #$number is given back, but its ticket.released event was not written" >&2
        ;;
      2)
        echo "dispatch: could not give back the claim on #$number" >&2
        left=$((left + 1))
        ;;
    esac
  done

  stop_relay --spec "$spec"
  case "$?" in
    1) left=$((left + 1)) ;;
    3) echo "dispatch: the relay running for this repository does not watch #$spec, so it was left running" >&2 ;;
  esac

  echo "suspend #$spec: stopped $stopped, commented $commented, claims given back $claims"
  [ "$left" -eq 0 ] || exit 1
}

ticket_comments() {
  python3 - "$VERIFY" "$1" <<'PY'
import importlib.util,json,sys
from pathlib import Path
script,number=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
spec=importlib.util.spec_from_file_location('dispatch_verify',script)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
try: print(json.dumps(mod.fetch_comments(int(number))))
except (ValueError,RuntimeError) as exc:
    print(f'dispatch: cannot read #{number} comments: {exc}',file=sys.stderr);raise SystemExit(2)
PY
}

caller_task() {
  [ -f "$1" ] && [ -s "$1" ] || { echo "dispatch: no nonempty caller task at $1" >&2; return 2; }
  realpath "$1"
}

read_ticket() {
  python3 - "$STATUS" "$1" "${2:-worker}" <<'PY'
import importlib.util,sys
script,number,kind=sys.argv[1:]
spec=importlib.util.spec_from_file_location('dispatch_status',script)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
ticket=mod.read_ticket(int(number))
why=mod.unreadable_reason(ticket)
if not why and kind=='worker':
    row=mod.build_rows([int(number)],{int(number):ticket})[0]
    if ticket['state']!='OPEN':why='ticket is not open'
    elif 'ready-for-agent' not in ticket['labels']:why='ticket is not ready-for-agent'
    elif row['blocking']:why='blocked by '+mod.blocking_text(row['blocking'])
    elif ticket['assignees']:
        login=mod.own_login()
        if not login or any(a!=login for a in ticket['assignees']):why='claimed by '+', '.join(ticket['assignees'])
if why:print('REFUSE '+why);raise SystemExit(0)
print(' '.join(sorted(l for l in ticket['labels'] if l.endswith('-worker'))))
print(ticket['title'])
PY
}

open_night() {
  local spec="$1" into="" project="" worker_task="" reviewer_task="" root rows line ahead behind presence branch opened name session how
  shift
  while [ "$#" -gt 0 ]; do
    [ "$#" -ge 2 ] || usage
    case "$1" in
      --into) into="$2" ;; --project) project="$2" ;;
      --worker-task) worker_task="$(caller_task "$2")" || return 2 ;;
      --reviewer-task) reviewer_task="$(caller_task "$2")" || return 2 ;;
      *) usage ;;
    esac
    shift 2
  done
  [ -n "$into" ] && [ -n "$project" ] && [ -n "$worker_task" ] && [ -n "$reviewer_task" ] || refuse 'open requires --into BASE --project PROJECT --worker-task FILE --reviewer-task FILE'
  git check-ref-format --branch "$into" >/dev/null && git check-ref-format --branch "$project" >/dev/null || refuse 'invalid base or project branch'
  [ "$into" != "$project" ] || refuse 'base and project branches must differ'
  root="$(git rev-parse --show-toplevel)" || return 2
  fetch_origin "$root" || return 2
  local default
  default="$(default_branch "$root")" || default=""
  [ -z "$default" ] || [ "$into" != "$default" ] || refuse "base $into is the repository default branch"
  rows=""
  for branch in "$project" "$into"; do
    line="$(branch_sync_counts "$root" "$branch")" || return 2
    IFS=$'\t' read -r ahead behind presence <<<"$line"
    [ "$ahead" = 0 ] || [ "$behind" = 0 ] || refuse "$branch and origin/$branch have diverged; nothing was pushed"
    rows="$rows$project"$'\t'"explicit"$'\t'"$branch"$'\t'"$ahead"$'\t'"$presence"$'\t'"$behind"$'\n'
  done
  push_open_branches "$root" "$rows" || return 2
  sync_base_with_project "$root" "$into" "$project" || return 2
  opened="$(open_relay --spec "$spec")" || return 2
  IFS=$'\t' read -r name session how <<<"$opened"
  if ! post_event "$spec" spec.opened --spec "$spec" --line "Opened #$spec into $into, project $project" \
      --field "runner=$name" --field "session=$session" --field "into=$into" --field "project=$project" \
      --field "worker_task=$worker_task" --field "reviewer_task=$reviewer_task"; then
    [ "$how" != started ] || stop_relay --spec "$spec"
    refuse "could not record spec.opened on #$spec; retry open once the tracker accepts comments"
  fi
  echo "opened #$spec: $into into $project; wake-ups go to $name session $session"
}

open_ticket() {
  local number="$1" into="" task="" root opened name session how
  shift
  while [ "$#" -gt 0 ]; do
    [ "$#" -ge 2 ] || usage
    case "$1" in --into) into="$2" ;; --task) task="$(caller_task "$2")" || return 2 ;; *) usage ;; esac
    shift 2
  done
  [ -n "$into" ] || refuse 'open-ticket requires --into BASE'
  git check-ref-format --branch "$into" >/dev/null || return 2
  root="$(git rev-parse --show-toplevel)" || return 2
  fetch_origin "$root" && require_origin_branch "$root" "$into" || return 2
  local missing
  missing="$(repository_check_missing "$root")" || return 2
  [ -z "$missing" ] || refuse "$missing"
  opened="$(open_relay --tickets "$number")" || return 2
  IFS=$'\t' read -r name session how <<<"$opened"
  local -a fields=(--field "into=$into" --field "runner=$name" --field "session=$session")
  [ -z "$task" ] || fields+=(--field "task=$task")
  if ! post_event "$number" ticket.opened --ticket "$number" --line "Opened ticket #$number into $into" "${fields[@]}"; then
    [ "$how" != started ] || stop_relay --tickets "$number"
    refuse "could not record #$number target branch; retry open-ticket"
  fi
  echo "opened #$number: $into; wake-ups go to $name session $session"
}

start_into() {
  local number="$1" spec="$2" previous="" active="" opened="" rc
  previous="$(ticket_into "$number")"; rc=$?
  [ "$rc" = 0 ] || [ "$rc" = 3 ] || return 2
  if [ -n "$spec" ]; then
    active="$(night_into "$spec")";rc=$?
    [ "$rc" = 0 ] || [ "$rc" = 3 ] || return 2
  fi
  if [ -n "$previous" ] && [ -n "$active" ] && [ "$previous" != "$active" ]; then
    echo "dispatch: #$number previously targeted $previous, but open spec #$spec targets $active; reconcile the target before starting" >&2
    return 2
  fi
  if [ -n "$previous" ];then printf '%s\n' "$previous";return;fi
  if [ -n "$active" ];then printf '%s\n' "$active";return;fi
  newest_field "$number" into ticket.opened
}

start_one() {
  local number="$1" kind="$2" task="" answer grades title spec into root profile row host model effort cwd created base head session pair old_runner old_ident
  shift 2
  [ "$#" = 2 ] && [ "$1" = --task ] || refuse 'start requires N worker|reviewer --task FILE'
  task="$(caller_task "$2")" || return 2
  case "$kind" in worker|reviewer) ;; *) usage ;; esac
  if [ "${MMW_TICKET_START_LOCKED:-}" != "$number" ]; then
    local state
    state="$(repository_state_dir)" || return 2
    python3 - "$STATEDIR" "$state/ticket-$number-start.lock" "$SELF" "$number" "$kind" "$task" <<'PY'
import importlib.util,os,subprocess,sys
from pathlib import Path
script,lock,dispatch,number,kind,task=sys.argv[1:]
spec=importlib.util.spec_from_file_location('dispatch_statedir',script)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
try:
    with mod.locked(Path(lock),wait=6,purpose=f'starting ticket #{number}'):
        raise SystemExit(subprocess.call(['bash',dispatch,'start',number,kind,'--task',task],env=dict(os.environ,MMW_TICKET_START_LOCKED=number)))
except mod.LockHeld as exc:print(f'dispatch: {exc}',file=sys.stderr);raise SystemExit(2)
PY
    return "$?"
  fi
  answer="$(read_ticket "$number" "$kind")" || return 2
  case "$answer" in 'REFUSE '*) refuse "#$number ${answer#REFUSE }" ;; '') refuse "cannot read #$number" ;; esac
  { IFS= read -r grades; IFS= read -r title; } <<<"$answer"
  spec="$(ticket_spec "$number")" || return 2
  relay_watches "$number" "$spec" || revive_night_watch "$spec" || refuse "no running watch for #$number; open the spec or open-ticket with an explicit target"
  into="$(start_into "$number" "$spec")" || refuse "#$number has no target branch; open its spec or open-ticket --into BASE"
  use_runner "$(tonight_runner)";use_catalog_of "$RUNNER_NAME" || return 2
  profile=reviewer
  if [ "$kind" = worker ]; then
    local -a marked=()
    read -r -a marked <<<"$grades"
    case "${#marked[@]}" in 0) profile="$DEFAULT_WORKER" ;; 1) profile="${marked[0]}" ;; *) refuse "#$number has multiple worker grades: $grades" ;; esac
  fi
  row="$(row_for_role "$profile")" || return 2
  [ -n "$row" ] || refuse "no model row for $profile"
  IFS=$'\t' read -r host model effort <<<"$row"
  root="$(main_checkout)";[ -n "$root" ] || refuse 'no main worktree'
  workspace_origin_ready "$number" "$root" "$into" || return 2
  local live_list
  local -a replaced=()
  if [ "$kind" = worker ]; then
    live_list="$(live_workers_on_ticket "$number")" || return 2
    if [ -n "$live_list" ] && [ -n "${MMW_DISPATCH_ADVANCE:-}" ]; then
      echo "dispatch: #$number already has a worker; automatic advance starts no replacement" >&2;return 0
    fi
    while IFS=$'\t' read -r old_runner old_ident; do
      [ -n "$old_ident" ] || continue
      runner_call "$old_runner" stop "$old_ident" || refuse "could not stop #$number worker $old_ident; no replacement started"
      post_event "$number" worker.replaced --ticket "$number" --spec "$spec" --line "Stopped $old_ident before replacement" \
        --field "runner=$old_runner" --field "session=$old_ident" || refuse "stopped $old_ident, but could not record replacement; no new worker started"
    done <<<"$live_list"
  fi
  local ws_row
  ws_row="$(ensure_workspace "$number" "$root" "$into")" || return 2
  IFS=$'\t' read -r _ cwd created <<<"$ws_row"
  if [ "$kind" = worker ] && [ "$created" = 0 ]; then
    local left_by
    left_by="$(last_worker_on_ticket "$number")" || return 2
    if [ -n "$left_by" ]; then
      keep_unfinished_work "$number" "$cwd" "$left_by" && push_ticket_branch "$number" "$cwd" || return 2
    fi
  fi
  if [ "$kind" = worker ]; then base="$(worker_base "$number" "$root" "$into" "issue-$number")" || return 2
  else base="$(base_commit "$root" "$into" "issue-$number")" || return 2;fi
  [ -n "$base" ] || refuse "issue-$number has no merge-base with origin/$into"
  head="$(git -C "$cwd" rev-parse HEAD)" || return 2
  local prompt
  printf -v prompt 'Ticket #%s, role %s, base %s, head %s, target %s. Read task file %q and carry out its instructions.' "$number" "$kind" "$base" "$head" "$into" "$task"
  if [ "$kind" = reviewer ]; then
    printf -v prompt '%s\nReport command: MMW_HOME=%q python3 %q %s --review <report-file> --base %q --head %q' "$prompt" "$MMW_HOME" "$VERIFY" "$number" "$base" "$head"
  else
    printf -v prompt '%s\nReport command: MMW_HOME=%q python3 %q %s --closeout <report-file> --result <complete-or-incomplete> --commit <output-SHA> --into %q' "$prompt" "$MMW_HOME" "$VERIFY" "$number" "$into"
  fi
  if [ "$kind" = worker ]; then worktree_environment "$cwd" setup up || return 2;fi
  if ! session="$(start_session "$host" "$model" "$effort" "$cwd" "$prompt" "#$number $kind" "MMW_TICKET=$number" "MMW_SPEC=$spec")"; then
    echo "dispatch: startup failed for #$number; workspace $cwd and issue-$number were preserved. Inspect the adapter error and recovery identity before retrying" >&2;return 2
  fi
  local -a fields=(--field "session=$session" --field "runner=$RUNNER_NAME" --field "machine=$(machine_name)" \
    --field "host=$host" --field "model=$model" --field "effort=${effort:-—}" --field "grade=$profile" \
    --field "worktree=$cwd" --field "branch=issue-$number" --field "base=$base" --field "into=$into" --field "task=$task")
  [ "$kind" != reviewer ] || fields+=(--field "head=$head")
  if ! post_event "$number" "$kind.started" --ticket "$number" --spec "$spec" --line "$kind started on $RUNNER_NAME: $session" "${fields[@]}"; then
    runner stop "$session" || refuse "could not record or stop $RUNNER_NAME session $session; workspace $cwd retained; stop that exact session before retrying"
    refuse "could not record $kind.started on #$number; session $session stopped, workspace retained"
  fi
  local -a attach_args=(--cwd "$cwd" --issue "$number")
  [ "$kind" != worker ] || attach_args+=(--under-caller)
  runner attach "${attach_args[@]}" >/dev/null 2>&1 || echo "dispatch: session $session started, but runner could not attach its worktree" >&2
  printf '%s\n' "$session"
}

send_ticket() {
  [ "$#" -ge 2 ] || usage
  local kind="$1" number="$2" task="" into="" spec
  [[ "$number" =~ ^[1-9][0-9]*$ ]] || refuse "a positive ticket number is required"
  shift 2
  while [ "$#" -gt 0 ]; do
    [ "$#" -ge 2 ] || usage
    case "$1" in --task) task="$(caller_task "$2")" || return 2 ;; --into) into="$2" ;; *) usage ;; esac
    shift 2
  done
  [ -n "$task" ] || refuse 'send worker|reviewer requires --task FILE'
  if [ "$kind" = worker ]; then
    spec="$(ticket_spec "$number")" || return 2
    if ! relay_watches "$number" "$spec"; then
      [ -n "$into" ] || refuse 'send worker outside an open watch requires --into BASE'
      open_ticket "$number" --into "$into" --task "$task" || return 2
    fi
  fi
  start_one "$number" "$kind" --task "$task"
}

summary_checks() {
  local spec="$1" root="$2" into="$3" expected="$4" out tip proof status detail
  prepare_merge_worktree "$root" "$into" || return 2
  tip="$(git -C "$MERGE_ROOT" rev-parse HEAD)"
  if [ "$tip" != "$expected" ]; then release_merge_lock;echo "dispatch: origin/$into moved; retry summary" >&2;return 2;fi
  if repository_proof "$spec" "$tip" "$tip" all >/dev/null; then
    release_merge_lock;echo "CHECK PASS all: origin/$into at $tip, reused spec.checked";return 0
  fi
  out="$(python3 - "$VERIFY" "$MERGE_ROOT" "$root" "$spec" <<'PY'
import importlib.util,json,sys
from pathlib import Path
script,root,worktree,number=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
spec=importlib.util.spec_from_file_location('dispatch_checks',script)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
result=mod.run_repository_check(Path(root),'HEAD',worktree,f'spec-{number}',tier='all')
if result['status']=='pass' and not result['proof']:
    result['status']='cannot-run';result['detail']='the checkout changed during scripts/check; no commit names that checked output'
print(result['status']);print(json.dumps(result['proof'] or {}));print(result['detail'])
PY
)" || { release_merge_lock;return 2; }
  release_merge_lock
  status="$(printf '%s\n' "$out" | sed -n 1p)";proof="$(printf '%s\n' "$out" | sed -n 2p)";detail="$(printf '%s\n' "$out" | sed -n '3,$p')"
  [ "$status" = pass ] || { echo "dispatch: summary #$spec $status: $detail" >&2;return 2; }
  local -a fields=()
  local field
  while IFS= read -r field;do fields+=(--json-field "$field");done < <(python3 -c 'import json,sys
for k,v in json.loads(sys.argv[1]).items():print(k+"="+json.dumps(v))' "$proof")
  post_event "$spec" spec.checked --spec "$spec" --line "Repository checks --all passed on $into at $tip" \
    "${fields[@]}" --field result=met || return 2
  echo "CHECK PASS all: origin/$into at $tip"
}

summary_spec() {
  local spec="$1" root into expected landed body counts unread open previous
  root="$(git rev-parse --show-toplevel)" || return 2
  into="$(newest_field "$spec" into spec.opened)" || refuse "#$spec has no explicit target branch"
  fetch_origin "$root" || return 2
  expected="$(git -C "$root" rev-parse "origin/$into")" || return 2
  landed="$(python3 "$STATUS" --closeout-ready "$spec")" || return 2
  body="$(python3 "$STATUS" --summary "$spec")" || return 2
  counts="$(printf '%s\n' "$body" | sed -n 's/^Findings routed: \([0-9][0-9/]*\).*$/\1/p' | head -1)"
  IFS=/ read -r _ _ _ _ unread open <<<"$counts"
  case "$unread:$open" in 0:0) ;; *) refuse "#$spec has unresolved or unread findings: ${counts:-count unavailable}; route them before summary" ;; esac
  summary_checks "$spec" "$root" "$into" "$expected" || return 2
  body="$body"$'\n'"Landed: $landed; repository checks --all passed on $expected"
  previous="$(newest_field "$spec" commit spec.closed spec.opened spec.suspended)" || previous=""
  if [ "$previous" != "$expected" ]; then
    post_event "$spec" spec.closed --spec "$spec" --line "$(printf '%s\n' "$body" | head -1)" \
      --text-file <(printf '%s\n' "$body" | tail -n +2) --field "commit=$expected" --field "into=$into" || return 2
  fi
  stop_relay --spec "$spec"
  case "$?" in 0|3) ;; *) return 1 ;; esac
  printf '%s\n' "$body"
}

tonight_runner() { python3 "$MODELS_PY" runner; }

use_catalog_of() {
  MMW_CATALOG_MODE="$(python3 "$MODELS_PY" catalog-source "$1")" || return 2
  export MMW_CATALOG_MODE
}
