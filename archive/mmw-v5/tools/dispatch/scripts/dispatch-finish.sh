# Merge a summarized batch into its project and retain unfinished work. Sourced by dispatch.sh.
spec_numbers() {
  local slug
  slug="$(repo_slug)" || return 2
  gh_ api --paginate "repos/$slug/issues?state=all&labels=mmw%3Aspec&per_page=100" \
    --jq '.[].number' 2>/dev/null
}


spec_children() {
  local spec="$1" slug
  slug="$(repo_slug)" || return 2
  gh_ api --paginate "repos/$slug/issues/$spec/sub_issues?per_page=100" --jq '.[].number' 2>/dev/null
}


finish_preflight() {
  local spec="$1" into="$2" specs children other active seen child state open="" rc
  newest_field "$spec" at spec.closed spec.opened >/dev/null 2>&1 \
    || { echo "dispatch: #$spec carries no spec.closed; run summary before finish" >&2; return 2; }

  specs="$(spec_numbers)" || {
    echo "dispatch: could not list specs while checking whether $into is still in use" >&2
    return 2
  }
  for other in $specs; do
    [ "$other" = "$spec" ] && continue
    active="$(newest_field "$other" into spec.opened spec.suspended spec.closed 2>/dev/null)"; rc=$?
    case "$rc" in
      0) ;;
      2) echo "dispatch: could not read #$other while checking open nights into $into" >&2; return 2 ;;
      3 | 4) active="" ;;
      *) echo "dispatch: could not decide whether #$other is an open night into $into" >&2; return 2 ;;
    esac
    if [ "$active" = "$into" ]; then
      echo "dispatch: #$other is another open night into $into; finish or suspend it before finish $spec" >&2
      return 2
    fi
  done

  for other in $specs; do
    seen="$(newest_field "$other" into spec.opened 2>/dev/null)"; rc=$?
    case "$rc" in
      0) ;;
      2) echo "dispatch: could not read #$other while finding specs that used $into" >&2; return 2 ;;
      3 | 4) seen="" ;;
      *) echo "dispatch: could not decide whether #$other used $into" >&2; return 2 ;;
    esac
    [ "$seen" = "$into" ] || continue
    children="$(spec_children "$other")" || {
      echo "dispatch: could not list #$other's tickets while checking tickets into $into" >&2
      return 2
    }
    for child in $children; do
      state="$(gh_ issue view "$child" --json state --jq .state 2>/dev/null)" || {
        echo "dispatch: could not read #$child while checking tickets into $into" >&2
        return 2
      }
      [ "$state" = CLOSED ] || open="$open #$child"
    done
  done
  if [ -n "$open" ]; then
    echo "dispatch: tickets still open on $into:${open}; finish $spec runs once each is closed" >&2
    return 2
  fi
}


record_spec_merged() {
  local spec="$1" into="$2" project="$3" merge="$4" base="$5" line
  line="Merged $into into $project"
  if [ -n "$REPO_URL" ]; then
    line="$line: $REPO_URL/compare/$base...$merge (merge commit $REPO_URL/commit/$merge)"
  fi
  post_event "$spec" spec.merged --spec "$spec" --line "$line" \
    --field "into=$into" --field "project=$project" --field "merge=$merge" --field "base=$base"
}


branch_worktrees() {
  local root="$1" name="$2" path branch listing
  listing="$(git -C "$root" worktree list --porcelain)" || return 2
  while IFS=$'\t' read -r path branch; do
    [ "$branch" = "refs/heads/$name" ] || continue
    [ -n "$path" ] && printf '%s\n' "$path"
  done < <(printf '%s\n' "$listing" | awk '
    /^worktree / { path=substr($0,10); branch="" }
    /^branch / { branch=substr($0,8); print path "\t" branch }
  ')
}


delete_origin_base_branch() {
  local root="$1" into="$2" project="$3" remote="refs/remotes/origin/$into" tip ahead out rc
  git -C "$root" show-ref --verify --quiet "$remote" || return 0
  tip="$(git -C "$root" rev-parse "$remote")"
  ahead="$(git -C "$root" rev-list --count "origin/$project..$remote" 2>/dev/null)" || ahead=""
  if [ "$ahead" != 0 ]; then
    echo "dispatch: keeping origin/$into because its containment in origin/$project was not proved; after checking, run git push origin --delete $into" >&2
    return 0
  fi
  out="$(git -C "$root" push "--force-with-lease=refs/heads/$into:$tip" origin --delete "$into" 2>&1)" && return 0
  git -C "$root" ls-remote --exit-code origin "refs/heads/$into" >/dev/null 2>&1
  rc=$?
  [ "$rc" -eq 2 ] && return 0
  echo "dispatch: could not delete origin/$into: $(printf '%s' "$out" | tr '\n' ' '); run git push origin --delete $into" >&2
  return 2
}


retain_local_base_branch() {
  local root="$1" into="$2" project="$3" trees path main ahead tip out
  trees="$(branch_worktrees "$root" "$into")"
  if [ -n "$trees" ]; then
    main="$(main_checkout)" || main=""
    while IFS= read -r path; do
      if [ "$path" = "$main" ]; then
        echo "dispatch: keeping the main worktree $path on $into; once its session is done, detach it (git -C \"$path\" switch --detach)" >&2
        continue
      fi
      echo "dispatch: keeping worktree $path and the local $into it has checked out; once its session is done, remove the worktree (git worktree remove $path)" >&2
    done <<< "$trees"
    return 0
  fi
  git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$into" || return 0
  tip="$(git -C "$root" rev-parse "refs/remotes/origin/$into")"
  if git -C "$root" show-ref --verify --quiet "refs/heads/$into"; then
    ahead="$(git -C "$root" rev-list --count "origin/$project..refs/heads/$into" 2>/dev/null)" || ahead=""
    if [ "$ahead" != 0 ]; then
      echo "dispatch: keeping local $into because its containment in origin/$project was not proved" >&2
      return 0
    fi
    if ! git -C "$root" merge-base --is-ancestor "refs/heads/$into" "$tip"; then
      echo "dispatch: keeping local $into because it is not an ancestor of the fetched origin/$into tip" >&2
      return 0
    fi
    out="$(git -C "$root" branch --force "$into" "$tip" 2>&1)" || {
      echo "dispatch: could not fast-forward local $into to $tip: $out; keeping origin/$into; run finish again" >&2
      return 1
    }
  elif ! out="$(git -C "$root" branch "$into" "$tip" 2>&1)"; then
    echo "dispatch: could not restore local $into at $tip: $out; keeping origin/$into; run finish again" >&2
    return 1
  fi
}


clean_base_merge_worktree() {
  local root="$1" into="$2" main dest state failed=0
  main="$(main_checkout)" || return 0
  dest="$main/.worktrees/merge-$(merge_slug "$into")"
  if [ -e "$dest" ]; then
    worktree_environment "$dest" down || true
    git -C "$root" worktree remove --force "$dest" >/dev/null 2>&1 || {
      echo "dispatch: could not remove $dest; run git worktree remove --force $dest" >&2
      failed=2
    }
  fi
  state="$(repository_state_dir)" || return 2
  rm -f "$state/merge-$(merge_slug "$into").lock" || return 2
  return "$failed"
}


sync_local_project_branch() {
  local root="$1" project="$2" tip trees path ahead status out ref_rc before rollback
  tip="$(git -C "$root" rev-parse --verify "refs/remotes/origin/$project" 2>&1)" || {
    echo "dispatch: could not read origin/$project for local synchronization: $tip; run finish again" >&2
    return 2
  }
  trees="$(branch_worktrees "$root" "$project")" || {
    echo "dispatch: could not list worktrees for local $project; run finish again" >&2
    return 2
  }
  git -C "$root" show-ref --verify --quiet "refs/heads/$project"
  ref_rc=$?
  if [ "$ref_rc" -eq 0 ]; then
    ahead="$(git -C "$root" rev-list --count "$tip..refs/heads/$project" 2>&1)" || {
      echo "dispatch: could not check local $project against origin/$project: $ahead; run finish again" >&2
      return 2
    }
    if [ "$ahead" -ne 0 ]; then
      echo "dispatch: keeping local $project${trees:+ in worktree $trees} because it has $ahead commit(s) not in origin/$project" >&2
      return 0
    fi
  elif [ "$ref_rc" -ne 1 ]; then
    echo "dispatch: could not read local $project; run finish again" >&2
    return 2
  fi
  if [ -n "$trees" ]; then
    while IFS= read -r path; do
      if [ ! -d "$path" ]; then
        echo "dispatch: registered worktree $path for $project is missing; restore the directory, or inspect stale registrations with git -C \"$root\" worktree prune --dry-run --expire now and prune confirmed stale registrations with git -C \"$root\" worktree prune --expire now, then run finish again" >&2
        return 2
      fi
      status="$(git -C "$path" status --porcelain --untracked-files=no 2>&1)" || {
        echo "dispatch: could not inspect worktree $path on $project: $status; run finish again" >&2
        return 2
      }
      if [ -n "$status" ]; then
        echo "dispatch: keeping local $project and worktree $path because it has uncommitted changes" >&2
        return 0
      fi
      before="$(git -C "$path" rev-parse HEAD 2>&1)" || {
        echo "dispatch: could not read $project in worktree $path: $before; run finish again" >&2
        return 2
      }
      out="$(git -C "$path" merge --ff-only "$tip" 2>&1)" || {
        if [ "$(git -C "$path" rev-parse HEAD)" = "$before" ] \
           && git -C "$path" diff --cached --quiet "$tip"; then
          rollback="$(git -C "$path" read-tree -u -m "$tip" "$before" 2>&1)" || {
            echo "dispatch: could not restore worktree $path after the failed fast-forward: $rollback; inspect its changes before running finish again" >&2
          }
        fi
        echo "dispatch: could not fast-forward local $project in worktree $path: $out; run finish again" >&2
        return 2
      }
    done <<< "$trees"
  elif ! out="$(git -C "$root" branch --force "$project" "$tip" 2>&1)"; then
    echo "dispatch: could not synchronize local $project to origin/$project at $tip: $out; run finish again" >&2
    return 2
  fi
}


finish_cleanup() {
  local root="$1" into="$2" project="$3" failed=0
  fetch_origin "$root" || { echo "dispatch: merge was recorded, but origin could not be fetched for cleanup; run finish again" >&2; return 2; }
  sync_local_project_branch "$root" "$project" || return 2
  if git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$into" \
     && ! git -C "$root" merge-base --is-ancestor "origin/$into" "origin/$project" 2>/dev/null; then
    echo "dispatch: keeping $into because origin/$project does not contain origin/$into; run finish again after reconciling the branches" >&2
  elif ! retain_local_base_branch "$root" "$into" "$project" \
       || ! delete_origin_base_branch "$root" "$into" "$project"; then
    failed=2
  fi
  clean_base_merge_worktree "$root" "$into" || failed=2
  if [ "$failed" -ne 0 ]; then
    echo "dispatch: cleanup of $into is incomplete; run finish again" >&2
  fi
  return "$failed"
}


pr_gate() {
  local into="$1" project="$2" slug pr out problems=""
  pr="$(gh_ pr list --head "$into" --base "$project" --state open --json number --jq '.[0].number // empty' 2>&1)" || {
    echo "dispatch: could not list the pull requests from $into to $project: $(printf '%s' "$pr" | tr '\n' ' '); run finish again once GitHub answers" >&2
    return 2
  }
  if [ -z "$pr" ]; then
    echo "dispatch: no open pull request from $into to $project; open a pull request with explicit base and head, then run finish again" >&2
    return 2
  fi
  out="$(python3 - "$PR" "$into" "$project" "$pr" <<'PYCHECKS'
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

script, into, project, number = sys.argv[1:]
spec = importlib.util.spec_from_file_location('dispatch_pr', script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
try:
    result = mod.gh('pr', 'checks', number, '--json', 'name,bucket')
    if result.returncode == 1 and 'no checks reported' in result.stderr:
        rows = []
    elif result.returncode not in (0, 1):
        raise ValueError(result.stderr or result.stdout or 'could not read PR checks')
    else:
        rows = json.loads(result.stdout)
    if not isinstance(rows, list) or any(not isinstance(row, dict) or
            row.get('bucket') not in ('pass', 'skipping', 'fail', 'cancel', 'pending') or
            not isinstance(row.get('name'), str) for row in rows):
        raise ValueError('unreadable PR checks')
    if not rows:
        ref = 'origin/' + into
        paths = subprocess.run(['git', 'ls-tree', '-r', '--name-only', ref, '--', '.github/workflows/'],
                               capture_output=True, text=True, check=True).stdout.splitlines()
        with tempfile.TemporaryDirectory(prefix='mmw-v5-ci-') as temporary:
            for name in paths:
                if Path(name).suffix not in ('.yml', '.yaml'):
                    continue
                text = subprocess.run(['git', 'show', ref + ':' + name],
                                      capture_output=True, text=True, check=True).stdout
                path = Path(temporary) / Path(name).name
                path.write_text(text)
                if mod.read_workflow_triggers(path, project).covers(project):
                    raise ValueError(f'expected CI for {project}, but pull request #{number} has no checks; wait for CI before finish')
    for row in rows:
        if row['bucket'] not in ('pass', 'skipping'):
            print(row['name'] + ' ' + row['bucket'])
except (ValueError, OSError, subprocess.SubprocessError, mod.tracker.RepositoryError) as exc:
    print('dispatch: cannot finish: ' + str(exc), file=sys.stderr)
    raise SystemExit(2)
PYCHECKS
)" || return 2
  [ -n "$out" ] && problems="$problems; checks not green: $(printf '%s' "$out" | paste -sd, -)"
  slug="$(repo_slug)" || return 2
  out="$(python3 - "$TRACKER" "$slug" "$pr" <<'PYTHREADS'
import importlib.util,json,subprocess,sys
script,slug,number=sys.argv[1:]
spec=importlib.util.spec_from_file_location('dispatch_tracker',script)
tracker=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracker)
owner,name=slug.split('/',1)
query='query($owner:String!,$name:String!,$number:Int!,$cursor:String){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100,after:$cursor){nodes{isResolved path line} pageInfo{hasNextPage endCursor}}}}}'
cursor=None;seen=set()
while True:
    args=['gh','api','graphql','-f','query='+query,'-F','owner='+owner,'-F','name='+name,'-F','number='+number]
    if cursor is not None:args+=['-f','cursor='+cursor]
    run=subprocess.run(args,capture_output=True,text=True,env=tracker.environment())
    try:
        data=json.loads(run.stdout)
        if run.returncode or data.get('errors'):raise ValueError(run.stderr or str(data.get('errors')))
        threads=data['data']['repository']['pullRequest']['reviewThreads']
        nodes=threads['nodes'];page=threads['pageInfo']
        if not isinstance(nodes,list) or type(page['hasNextPage']) is not bool:raise ValueError('unreadable review threads')
        for row in nodes:
            if type(row.get('isResolved')) is not bool:raise ValueError('unreadable review thread')
            if not row['isResolved']:print(str(row.get('path'))+':'+str(row.get('line')))
        if not page['hasNextPage']:break
        cursor=page['endCursor']
        if not cursor or cursor in seen:raise ValueError('review thread pagination did not advance')
        seen.add(cursor)
    except (ValueError,KeyError,TypeError) as exc:
        print('dispatch: cannot read complete PR review threads: '+str(exc),file=sys.stderr);raise SystemExit(2)
PYTHREADS
)" || return 2
  [ -n "$out" ] && problems="$problems; review threads still open: $(printf '%s' "$out" | paste -sd, -)"
  if [ -n "$problems" ]; then
    echo "dispatch: pull request #$pr from $into to $project is not ready to merge: ${problems#; }; settle the checks and review threads, then run finish again; nothing was merged" >&2
    return 2
  fi
}


close_finished_spec() {
  local spec="$1" state out
  if ! state="$(gh_ issue view "$spec" --json state --jq .state 2>&1)"; then
    echo "dispatch: #$spec was not closed because its state could not be read: $state; run finish again (finish $spec)" >&2
    return 2
  fi
  case "$state" in
    CLOSED) return 0 ;;
    OPEN) ;;
    *) echo "dispatch: #$spec was not closed because its state is unreadable ($state); run finish again (finish $spec)" >&2; return 2 ;;
  esac
  if ! out="$(gh_ issue close "$spec" --reason completed 2>&1)"; then
    echo "dispatch: #$spec was not closed: $out; run finish again (finish $spec)" >&2
    return 2
  fi
}


finish_spec() {
  local spec="$1" root into project merged merge base attempt rc out files checked_by
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository"
  into="$(newest_field "$spec" into spec.opened 2>/dev/null)" || into=""
  project="$(newest_field "$spec" project spec.opened 2>/dev/null)" || project=""
  [ -n "$project" ] || refuse "#${spec}'s spec.opened carries no project branch; run open $spec again before finish"
  [ -n "$into" ] || refuse "#${spec}'s spec.opened carries no base branch; run open $spec again before finish"
  finish_preflight "$spec" "$into" || exit 2
  load_repo_url

  merged="$(newest_field "$spec" merge spec.merged spec.opened 2>/dev/null)" || merged=""
  if [ -n "$merged" ]; then
    finish_cleanup "$root" "$into" "$project" || return 2
    close_finished_spec "$spec" || return 2
    echo "finish #$spec: merge $merged was already recorded; cleanup checked"
    return 0
  fi

  for ((attempt = 1; attempt <= MERGE_TRIES; attempt++)); do
    prepare_merge_worktree "$root" "$project" || exit 2
    base="$(git -C "$MERGE_ROOT" rev-parse "origin/$project")"
    if ! git -C "$MERGE_ROOT" show-ref --verify --quiet "refs/remotes/origin/$into"; then
      if git -C "$root" show-ref --verify --quiet "refs/heads/$into" \
         && ! git -C "$root" merge-base --is-ancestor "refs/heads/$into" "origin/$project"; then
        release_merge_lock
        refuse "origin/$into is absent and the local $into is not contained in origin/$project; nothing was deleted"
      fi
      release_merge_lock
      finish_cleanup "$root" "$into" "$project" || return 2
      close_finished_spec "$spec" || return 2
      echo "finish #$spec: origin/$into was already absent; cleanup checked"
      return 0
    fi
    local summarized tip
    summarized="$(newest_field "$spec" commit spec.closed spec.opened spec.suspended)" || summarized=""
    tip="$(git -C "$MERGE_ROOT" rev-parse "origin/$into")" || { release_merge_lock; return 2; }
    if [ "$summarized" != "$tip" ]; then
      release_merge_lock
      refuse "#$spec summary names ${summarized:-no commit}, but origin/$into is $tip; run summary $spec again before finish"
    fi
    if git -C "$MERGE_ROOT" merge-base --is-ancestor "origin/$into" "origin/$project"; then
      merge=""
      IFS=$'\t' read -r merge base < <(landed_merge_and_base "$MERGE_ROOT" "origin/$into" "$project") || true
      if [ -n "$merge" ] && [ -n "$base" ]; then
        if ! record_spec_merged "$spec" "$into" "$project" "$merge" "$base"; then
          release_merge_lock
          refuse "origin/$project contains $into, but the spec.merged event on #$spec was not written; run finish again"
        fi
      fi
      release_merge_lock
      finish_cleanup "$root" "$into" "$project" || return 2
      close_finished_spec "$spec" || return 2
      echo "finish #$spec: origin/$project already contained $into; cleanup checked"
      return 0
    else
      if ! pr_gate "$into" "$project"; then
        release_merge_lock
        exit 2
      fi
      if ! git -C "$MERGE_ROOT" merge --no-ff -m "Merge branch '$into'" "origin/$into" >/dev/null 2>&1; then
        files="$(git -C "$MERGE_ROOT" diff --name-only --diff-filter=U | paste -sd, -)"
        git -C "$MERGE_ROOT" merge --abort >/dev/null 2>&1 || true
        git -C "$MERGE_ROOT" reset --hard "origin/$project" >/dev/null
        release_merge_lock
        echo "dispatch: finish #$spec conflicts in ${files:-unknown files}; nothing was pushed or deleted" >&2
        exit 1
      fi
      merge="$(git -C "$MERGE_ROOT" rev-parse HEAD)"
      # With origin/<project> inside origin/<into>, the merge's tree is origin/<into>'s. When
      # that tip is a ticket's landing, `land` already ran the checks on exactly this tree.
      rc=0
      tip="$(git -C "$MERGE_ROOT" rev-parse "origin/$into")"
      if git -C "$MERGE_ROOT" merge-base --is-ancestor "$base" "origin/$into" \
         && checked_by="$(landed_tip_ticket "$MERGE_ROOT" "$into")"; then
        echo "finish #$spec: repository checks not run again: the merge's tree is origin/$into, checked when #$checked_by landed"
      elif git -C "$MERGE_ROOT" merge-base --is-ancestor "$base" "origin/$into" \
         && repository_proof "$spec" "$tip" "$base" >/dev/null; then
        echo "finish #$spec: repository checks not run again: the merge's tree is origin/$into at ${tip:0:12}, which passed on this machine"
      else
        run_merge_checks "$MERGE_ROOT" "origin/$project" "$root" "spec-$spec"; rc=$?
      fi
      if [ "$rc" -ne 0 ]; then
        git -C "$MERGE_ROOT" reset --hard "origin/$project" >/dev/null
        release_merge_lock
      fi
      if [ "$rc" -eq 1 ]; then
        printf 'dispatch: finish #%s: the merge of %s into %s is red, so nothing was pushed or deleted: %s\n' \
          "$spec" "$into" "$project" "$MERGE_CHECKS_DETAIL" >&2
        exit 1
      elif [ "$rc" -ne 0 ]; then
        printf 'dispatch: finish #%s: the merge of %s into %s was not checked, so nothing was pushed or deleted: %s\nFix that, then run finish %s again\n' \
          "$spec" "$into" "$project" "$MERGE_CHECKS_DETAIL" "$spec" >&2
        exit 2
      fi
      out="$(git -C "$MERGE_ROOT" push origin "HEAD:$project" 2>&1)"
      if [ "$?" -ne 0 ]; then
        release_merge_lock
        [ "$attempt" -lt "$MERGE_TRIES" ] && continue
        echo "dispatch: the fast-forward push to origin/$project was rejected after $MERGE_TRIES attempts; nothing was deleted: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
        exit 2
      fi
    fi
    if ! record_spec_merged "$spec" "$into" "$project" "$merge" "$base"; then
      release_merge_lock
      refuse "origin/$project contains $into, but the spec.merged event on #$spec was not written; run finish again"
    fi
    release_merge_lock
    finish_cleanup "$root" "$into" "$project" || return 2
    close_finished_spec "$spec" || return 2
    echo "finish #$spec: merged $into into origin/$project at $merge; cleanup checked"
    return 0
  done
}
