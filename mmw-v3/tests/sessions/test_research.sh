#!/usr/bin/env bash
#
# Tests for `dispatch.sh research <n>` of the mmw-mode skill. One scenario per run:
#
#   bash mmw-v3/tests/sessions/test_research.sh research|researchworktree|researchreuse
#   bash mmw-v3/tests/sessions/test_research.sh researchprompt|researchusage|researchdefaultrow
#   bash mmw-v3/tests/sessions/test_research.sh all
#
# A fake `paseo`, a fake `herdr`, a fake `orca` and a fake `gh` sit in front of the real
# ones on PATH and write every call they receive to a log, one call per line, fields
# joined by ` :: `. What the script does to a runner and to the tracker is therefore
# checkable without a daemon, a network, or a ticket. MMW_HOME and HOME point into this
# run's temporary directory, so nothing here reads or writes the machine's ~/.mmw. The
# last line of a passing run is the scenario's EXPECT string; everything before it says
# what was checked.

set -uo pipefail
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID HERDR_ENV TMUX
unset MMW_SPEC MMW_TICKET MMW_TASK_SCOPE MMW_KIND MMW_ROLE MMW_CATALOG_MODE MMW_EVENTS_PY

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname "$(dirname "$HERE")")/skills/mmw-mode"
DISPATCH="$SKILL/scripts/dispatch.sh"

rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/home"

# `paseo run -d --json … -- <prompt>`: records the request in the shape the checks read
# (runs.jsonl, newest last), lists the agent, answers with its id.
cat > "$TMP/bin/paseo" <<'FAKE'
#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("paseo" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")

args = sys.argv[1:]
state = Path(os.environ["MMW_FAKE_PASEO_STATE"])
state.mkdir(parents=True, exist_ok=True)
scenario = os.environ.get("MMW_FAKE_PASEO_SCENARIO", "")


def load(name):
    path = state / name
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def save(name, rows):
    (state / name).write_text(json.dumps(rows), encoding="utf-8")


if args[:1] == ["run"]:
    if scenario == "run-fail":
        print("Error: Failed to create agent: provider initialization failed", file=sys.stderr)
        sys.exit(1)
    rest = args[1:]
    prompt = rest[rest.index("--") + 1] if "--" in rest else rest[-1]
    def flag(name):
        return rest[rest.index(name) + 1] if name in rest else None
    labels = {}
    for i, a in enumerate(rest):
        if a == "--label" and i + 1 < len(rest) and "=" in rest[i + 1]:
            k, v = rest[i + 1].split("=", 1)
            labels[k] = v
    settings = {}
    if flag("--mode"):
        settings["modeId"] = flag("--mode")
    if flag("--thinking"):
        settings["thinkingOptionId"] = flag("--thinking")
    rows = load("agents.json")
    ident = "agt_run_%d" % (len(rows) + 1)
    request = {
        "id": ident,
        "background": "-d" in rest,
        "title": flag("--title"),
        "provider": flag("--provider"),
        "settings": settings,
        "labels": labels,
        "cwd": flag("--cwd"),
        "initialPrompt": prompt,
        "environment": [rest[i + 1] for i, value in enumerate(rest[:-1]) if value == "--env"],
    }
    with open(state / "runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(request) + "\n")
    rows.append({"id": ident, "name": request["title"] or ident, "status": "running",
                 "cwd": request["cwd"], "labels": labels})
    save("agents.json", rows)
    print(json.dumps({"agentId": ident, "status": "running", "cwd": request["cwd"]}))
    sys.exit(0)

print("{}", file=sys.stderr)
sys.exit(2)
FAKE

# Orca and Herdr are never the runner here (MMW_RUNNER=paseo); these log any call so a
# scenario can show none was made.
for fake in orca herdr; do
  cat > "$TMP/bin/$fake" <<FAKE
#!/usr/bin/env bash
line=$fake
for a in "\$@"; do line="\$line :: \$a"; done
echo "\$line" >> "\$MMW_TEST_LOG"
echo "fake $fake: not expected in these scenarios" >&2
exit 2
FAKE
done

# The tracker: `gh repo view` names the repository; any other call is logged and refused.
cat > "$TMP/bin/gh" <<'FAKE'
#!/usr/bin/env bash
line=gh
for a in "$@"; do line="$line :: $a"; done
echo "$line" >> "$MMW_TEST_LOG"
case "$*" in
  "repo view"*)
    printf '%s\n' "${FAKE_GH_REPO:-o/r}" ;;
  *)
    echo "fake gh: no answer for: $*" >&2
    exit 2 ;;
esac
FAKE

chmod +x "$TMP/bin/paseo" "$TMP/bin/herdr" "$TMP/bin/orca" "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export HOME="$TMP/home"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_FAKE_PASEO_STATE="$TMP/paseo-state"
export MMW_HOME="$TMP/mmw-home"
# Tonight's runner is pinned: the session running this suite may itself sit in Orca,
# Herdr or tmux, and runtime detection would pick that runner.
export MMW_RUNNER=paseo
export MMW_HOST_CATALOG="$HERE/catalog.json"
mkdir -p "$MMW_HOME"
# The models.json every scenario starts from, all five rows. It is this suite's own
# fixture, not hosts.json's defaults: what a fresh machine is given can change without
# changing what the scenarios exercise.
cat > "$MMW_HOME/models.json" <<'JSON'
{"version":1,"runner":"orca","rows":{"junior-worker":{"host":"cursor","model":"grok 4.6","effort":"high"},"senior-worker":{"host":"grok","model":"grok 4.6","effort":"xhigh"},"reviewer":{"host":"claude","model":"opus 5","effort":"high"},"advisor":{"host":"claude","model":"fable 5.1","effort":"medium"},"researcher":{"host":"codex","model":"gpt 5.6 sol","effort":"high"}}}
JSON

# ------------------------------------------------------------------ harness

reset_log() {
  mkdir -p "$TMP/installed/mmw-v3" "$MMW_HOME"
  printf '%s\n' "$TMP/installed/mmw-v3" > "$MMW_HOME/installed-root"
  : > "$MMW_TEST_LOG"
  mkdir -p "$MMW_FAKE_PASEO_STATE"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"
  rm -f "$MMW_FAKE_PASEO_STATE/runs.jsonl"
  rm -rf "$MMW_HOME/state"
}
hasnt() { grep -qF -- "$1" "$MMW_TEST_LOG" && fail "should not have called: $1"; return 0; }
count_of() { grep -cF -- "$1" "$MMW_TEST_LOG" | tr -d ' '; }

run_dispatch() { (cd "$TMP/repo" && "$@") > "$TMP/out" 2> "$TMP/err"; echo "$?"; }

hasnt_runner_worktree() {
  hasnt "paseo :: workspace :: create"
  hasnt "paseo :: workspace :: archive"
  hasnt "orca :: worktree :: create"
  hasnt "orca :: worktree :: rm"
  hasnt "orca :: worktree :: ps"
}

never_ran() { hasnt "paseo :: run"; }
nothing_printed() { [ ! -s "$TMP/out" ] || fail "stdout should be empty: $(cat "$TMP/out")"; }

# One field of the newest `paseo run` request the fake recorded. Nested keys use one
# dot: `settings.thinkingOptionId` is settings["thinkingOptionId"].
out_json() {
  MMW_JSON_PATH="$1" python3 -c '
import json, os, sys
from pathlib import Path
node = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
path = os.environ["MMW_JSON_PATH"]
if "." in path:
    top, rest = path.split(".", 1)
    node = node[top][rest]
else:
    node = node[path]
print(node)
' "$MMW_FAKE_PASEO_STATE/runs.jsonl"
}

started_once() {
  [ "$(count_of "paseo :: run")" = 1 ] \
    || fail "expected exactly one paseo run, got $(count_of "paseo :: run")"
}

fresh_repo() {
  rm -rf "$TMP/repo" "$TMP/origin.git" "$TMP/mapper"
  git init -q --bare -b main "$TMP/origin.git"
  git init -q -b main "$TMP/repo"
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture
  git -C "$TMP/repo" remote add origin "$TMP/origin.git"
  git -C "$TMP/repo" push -q -u origin main
}

commit_file() {
  local repo="$1" file="$2" text="$3" message="$4"
  printf '%s\n' "$text" > "$repo/$file"
  git -C "$repo" add "$file"
  git -C "$repo" -c user.email=t@t -c user.name=t commit -q -m "$message"
}

# Saves the fixture models.json to <saved>, then gives the researcher row <effort>.
add_researcher_row() {
  cp "$MMW_HOME/models.json" "$1"
  python3 - "$MMW_HOME/models.json" "${2:-high}" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
data["rows"]["researcher"] = {"host": "codex", "model": "gpt 5.6 sol", "effort": sys.argv[2]}
json.dump(data, open(path, "w"))
PY
}

assert_launch_prompt() {
  local role="$1"
  python3 - "$MMW_FAKE_PASEO_STATE/runs.jsonl" "$role" "$MMW_HOME" "$TMP/installed/mmw-v3" <<'PY' || fail "$role launch prompt or frozen data paths are wrong"
import json, sys
from pathlib import Path
runs, role, home, installed = sys.argv[1:]
prompt = json.loads(Path(runs).read_text().splitlines()[-1])["initialPrompt"]
pointers = {"researcher": "research-a-question#Name the decision it feeds"}
data = (Path(home) / "state/o__r/prompts" / f"61-{role}.md").resolve()
assert prompt == f"Use the mmw-mode skill. Role {role}, ticket #61, unattended: mmw-mode {pointers[role]}. Data: {data}.", repr(prompt)
assert "\n" not in prompt and "\r" not in prompt, repr(prompt)
lines = data.read_text().splitlines()
assert all(line.startswith("- ") and ": " in line for line in lines), lines
skills = Path(installed).resolve() / "skills"
slug = pointers[role].split("#")[0]
expected = [f"- Playbook: {skills}/mmw-mode/playbooks/{slug}.md",
            f"- dispatch.sh: {skills}/mmw-mode/scripts/dispatch.sh"]
assert lines == expected, lines
PY
}

# ------------------------------------------------------------------ scenarios

scenario_research() {
  local code saved="$TMP/models.saved"
  reset_log
  fresh_repo
  add_researcher_row "$saved" low
  code="$(run_dispatch bash "$DISPATCH" research 61)"
  [ "$code" = 0 ] || fail "research expected 0, got $code: $(cat "$TMP/err")"
  if [ "$code" = 0 ]; then
    started_once
    [ "$(cat "$TMP/out")" = agt_run_1 ] || fail "stdout should be the session id: $(cat "$TMP/out")"
    [ "$(out_json provider)" = codex/gpt-5.6-sol ] || fail "research did not use its row: $(out_json provider)"
    [ "$(out_json settings.thinkingOptionId)" = low ] || fail "research effort: $(out_json settings.thinkingOptionId)"
    hasnt "gh :: issue :: comment"
    hasnt_runner_worktree
  fi

  reset_log
  code="$(run_dispatch env MMW_FAKE_PASEO_SCENARIO=run-fail \
          bash "$DISPATCH" research 61)"
  [ "$code" = 2 ] || fail "refused research expected 2, got $code: $(cat "$TMP/err")"
  started_once
  nothing_printed
  hasnt "orca :: terminal :: create"
  hasnt "herdr :: agent :: start"
  hasnt "gh :: issue :: comment"
  mv "$saved" "$MMW_HOME/models.json"
}

scenario_researchworktree() {
  local code tree caller_head saved="$TMP/models.saved"
  reset_log
  fresh_repo
  add_researcher_row "$saved"
  git -C "$TMP/repo" worktree add --quiet -b mapper "$TMP/mapper"
  commit_file "$TMP/mapper" context.txt context context
  caller_head="$(git -C "$TMP/mapper" rev-parse HEAD)"
  code="$( (cd "$TMP/mapper" && bash "$DISPATCH" research 61) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  mv "$saved" "$MMW_HOME/models.json"
  tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/research-61"
  [ "$code" = 0 ] || fail "research from a linked checkout expected 0, got $code: $(cat "$TMP/err")"
  if [ "$code" = 0 ]; then
    [ "$(out_json cwd)" = "$tree" ] || fail "cwd: $(out_json cwd), want $tree"
    [ "$(git -C "$tree" branch --show-current)" = research/61 ] || fail "wrong research branch"
    [ "$(git -C "$tree" rev-parse HEAD)" = "$caller_head" ] || fail "research did not start at the caller's HEAD"
    [ ! -e "$TMP/mapper/.worktrees/research-61" ] || fail "worktree was placed under the calling checkout"
    if git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/research/61; then
      fail "dispatch pushed the research branch"
    fi
  fi
}

scenario_researchreuse() {
  local code tree head saved="$TMP/models.saved"
  reset_log
  fresh_repo
  add_researcher_row "$saved"
  tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/research-61"
  code="$(run_dispatch bash "$DISPATCH" research 61)"
  [ "$code" = 0 ] || fail "first research expected 0, got $code: $(cat "$TMP/err")"
  if [ "$code" = 0 ]; then
    commit_file "$tree" report.txt report report
    head="$(git -C "$tree" rev-parse HEAD)"
    commit_file "$TMP/repo" later.txt later later
    printf '%s\n' unfinished > "$tree/unfinished.txt"
    code="$(run_dispatch bash "$DISPATCH" research 61)"
    [ "$code" = 0 ] || fail "second research expected 0, got $code: $(cat "$TMP/err")"
    [ "$(count_of "paseo :: run")" = 2 ] || fail "second research did not start another session"
    [ "$(out_json cwd)" = "$tree" ] || fail "research did not reuse the worktree"
    [ "$(git -C "$TMP/repo" worktree list --porcelain | grep -cF "worktree $tree")" = 1 ] \
      || fail "research created another worktree"
    [ "$(git -C "$tree" rev-parse HEAD)" = "$head" ] || fail "research reset the branch"
    [ "$(cat "$tree/unfinished.txt")" = unfinished ] || fail "research lost unfinished work"
    rm "$tree/unfinished.txt"
    git -C "$TMP/repo" worktree remove "$tree"
    code="$(run_dispatch bash "$DISPATCH" research 61)"
    [ "$code" = 0 ] || fail "branch-only reuse expected 0, got $code: $(cat "$TMP/err")"
    [ "$(git -C "$tree" rev-parse HEAD)" = "$head" ] || fail "research replaced the standing branch"
    git -C "$tree" checkout -q -b other-research
    reset_log
    code="$(run_dispatch bash "$DISPATCH" research 61)"
    [ "$code" = 2 ] || fail "a worktree on another branch expected 2, got $code"
    grep -qF "$tree" "$TMP/err" || fail "the refusal did not name the worktree"
    [ "$(git -C "$tree" branch --show-current)" = other-research ] || fail "research changed another branch"
    never_ran
  fi
  mv "$saved" "$MMW_HOME/models.json"
}

scenario_researchprompt() {
  local code saved="$TMP/models.saved"
  reset_log
  fresh_repo
  add_researcher_row "$saved"
  code="$(run_dispatch bash "$DISPATCH" research 61)"
  mv "$saved" "$MMW_HOME/models.json"
  [ "$code" = 0 ] || fail "research prompt expected 0, got $code: $(cat "$TMP/err")"
  if [ "$code" = 0 ]; then
    assert_launch_prompt researcher
  fi
}

scenario_researchusage() {
  local code
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" research)"
  [ "$code" = 2 ] || fail "research without a ticket expected 2, got $code"
  grep -qF 'dispatch.sh research <n>' "$TMP/err" || fail "usage omitted research"
  never_ran
}

# A models.json with no researcher row starts the session on the researcher row of
# hosts.json `defaults`, and leaves the file on disk exactly as it was.
scenario_researchdefaultrow() {
  local code saved="$TMP/models.saved" before="$TMP/models.before" want
  reset_log
  fresh_repo
  cp "$MMW_HOME/models.json" "$saved"
  python3 - "$MMW_HOME/models.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
del data["rows"]["researcher"]
json.dump(data, open(path, "w"))
PY
  cp "$MMW_HOME/models.json" "$before"
  want="$(python3 -c '
import json, sys
row = next(r for r in json.load(open(sys.argv[1]))["defaults"] if r["agent"] == "researcher")
print(row["host"], row["model"], row["effort"], sep="\t")
' "$SKILL/hosts.json")"
  [ "$want" = "codex	gpt 6 sol	high" ] \
    || fail "this scenario expects hosts.json's researcher default to be codex, gpt 6 sol, high; it is: $want"
  code="$(run_dispatch bash "$DISPATCH" research 61)"
  [ "$code" = 0 ] || fail "research with no researcher row expected 0, got $code: $(cat "$TMP/err")"
  if [ "$code" = 0 ]; then
    started_once
    [ "$(cat "$TMP/out")" = agt_run_1 ] || fail "stdout should be the session id: $(cat "$TMP/out")"
    [ "$(out_json provider)" = codex/gpt-6-sol ] || fail "research did not use the hosts.json default: $(out_json provider)"
    [ "$(out_json settings.thinkingOptionId)" = high ] || fail "default effort: $(out_json settings.thinkingOptionId)"
    assert_launch_prompt researcher
  fi
  cmp -s "$before" "$MMW_HOME/models.json" || fail "research changed models.json: $(cat "$MMW_HOME/models.json")"
  mv "$saved" "$MMW_HOME/models.json"
}

ALL="research researchworktree researchreuse researchprompt researchusage researchdefaultrow"

# One list of scenario names, ALL; a name on the command line is accepted when it is in it.
case " $ALL all " in
  *" ${1:-} "*) ;;
  *)
    echo "usage: test_research.sh $(echo "$ALL" | tr ' ' '|')|all" >&2
    exit 2 ;;
esac
if [ "$1" = all ]; then wanted="$ALL"; else wanted="$1"; fi

banner_for() {
  case "$1" in
    research) echo RESEARCH-OK ;;
    researchworktree) echo RESEARCH-WORKTREE-OK ;;
    researchreuse) echo RESEARCH-REUSE-OK ;;
    researchprompt) echo RESEARCH-PROMPT-OK ;;
    researchusage) echo RESEARCH-USAGE-OK ;;
    researchdefaultrow) echo RESEARCH-DEFAULT-ROW-OK ;;
  esac
}

for name in $wanted; do
  echo "=== $name"
  declare -F "scenario_$name" >/dev/null \
    || { echo "$name failed: this file has no scenario_$name" >&2; exit 1; }
  "scenario_$name"
  code=$?
  [ "$code" -eq 0 ] \
    || { echo "$name failed: scenario_$name exited $code without reporting" >&2; exit 1; }
  if [ "$rc" -eq 0 ]; then
    banner_for "$name"
  else
    echo "$name failed" >&2
    exit 1
  fi
done
