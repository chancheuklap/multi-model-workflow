#!/usr/bin/env bash

scenario_codexappdispatch() {
  reset_log
  fresh_repo
  local code first second executor="$SKILL/scripts/runners/codex-app-tools.js"
  cat > "$TMP/bin/app-runtime" <<'APP'
#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
assert sys.argv[1] == 'app-server', sys.argv
path=Path(os.environ['MMW_NATIVE_FIXTURE'])/'native-sessions.json'
for line in sys.stdin:
 packet=json.loads(line); method=packet['method']; params=packet.get('params',{})
 if method=='initialized': continue
 result={}
 if method=='project/list': result={'data':[],'nextCursor':None}
 if method=='thread/start':
  rows=json.loads(path.read_text()) if path.exists() else []
  row={'id':'fixture-chat-'+str(len(rows)+1),'cwd':params['cwd'],'active':False}
  rows.append(row); path.write_text(json.dumps(rows))
  result={'thread':row,'approvalPolicy':params.get('approvalPolicy'),
          'sandbox':{'type':'dangerFullAccess'}}
 print(json.dumps({'id':packet['id'],'result':result}),flush=True)
APP
  chmod +x "$TMP/bin/app-runtime"
  export CODEX_APP_RUNTIME_CLI_PATH="$TMP/bin/app-runtime"
  export CODEX_APP_TOOLS_PIPE_PATH=fixture-binding CODEX_THREAD_ID=fixture-orchestrator
  export CODEX_PERMISSION_PROFILE=:danger-full-access MMW_NATIVE_FIXTURE="$TMP"
  export MMW_RUNNER=codex-app
  python3 - "$MMW_HOME/models.json" <<'PY'
import json,sys
from pathlib import Path
path=Path(sys.argv[1]); config=json.loads(path.read_text())
for row in config['rows'].values(): row.update(host='codex',model='gpt 5.6 sol',effort='high')
path.write_text(json.dumps(config))
PY
  local command
  printf -v command '%q ' bash "$DISPATCH" "${TOOLS[@]}" start 61 worker
  code="$(run_dispatch node "$HERE/native-tools-fixture.mjs" "$executor" "$command" "$TMP")"
  [ "$code" = 0 ] || { fail "native worker dispatch: $(cat "$TMP/err") $(cat "$TMP/out")"; return 1; }
  first="$(tail -n 1 "$TMP/out")"
  [ "$first" = fixture-chat-1 ] || fail "confirmed worker identity: $first"
  [ "$(posted_events 61 runner session branch | tail -n 1)" = \
      'worker.started runner=codex-app session=fixture-chat-1 branch=issue-61' ] \
    || fail "native start registration: $(posted_events 61 runner session branch)"
  assert_wt 61
  printf -v command '%q ' bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer
  code="$(run_dispatch node "$HERE/native-tools-fixture.mjs" "$executor" "$command" "$TMP")"
  [ "$code" = 0 ] || { fail "native reviewer dispatch: $(cat "$TMP/err") $(cat "$TMP/out")"; return 1; }
  second="$(tail -n 1 "$TMP/out")"
  [ "$second" = fixture-chat-2 ] || fail "independent reviewer identity: $second"
  python3 - "$TMP/native-sessions.json" "$(wt 61)" <<'PY'
import json,sys
from pathlib import Path
rows=json.loads(Path(sys.argv[1]).read_text())
assert len(rows)==2, rows
assert all(Path(row['cwd']).resolve()==Path(sys.argv[2]).resolve() for row in rows), rows
assert '\n\nDispatched: worker, ticket #61, base ' in rows[0]['prompt'], rows
assert '\n\nDispatched: reviewer, ticket #61, base ' in rows[1]['prompt'], rows
assert all('Read the mmw-mode skill in full, then follow ' in row['prompt'] for row in rows), rows
PY
  [ "$?" = 0 ] || fail 'worker and reviewer must have separate prompts and the same ticket worktree'
  printf -v command '%q ' bash "$DISPATCH" "${TOOLS[@]}" start 61 worker
  local before
  before="$(posted_events 61 runner session)"
  code="$(run_dispatch env FAKE_NATIVE_STOP_FAIL=1 node "$HERE/native-tools-fixture.mjs" "$executor" "$command" "$TMP")"
  [ "$code" = 2 ] || fail "failed native stop must refuse replacement: $code"
  [ "$(posted_events 61 runner session)" = "$before" ] || fail 'failed stop must preserve tracker history'
  assert_wt 61
  code="$(run_dispatch node "$HERE/native-tools-fixture.mjs" "$executor" "$command" "$TMP")"
  [ "$code" = 0 ] || fail "confirmed native replacement: $(cat "$TMP/err") $(cat "$TMP/out")"
  [ "$(tail -n 1 "$TMP/out")" = fixture-chat-3 ] || fail 'replacement needs its own confirmed identity'
  [ "$(posted_events 61 runner session | tail -n 2 | head -n 1)" = \
      'worker.replaced runner=codex-app session=fixture-chat-1' ] \
    || fail "replacement must retire the old App worker: $(posted_events 61 runner session)"
}
