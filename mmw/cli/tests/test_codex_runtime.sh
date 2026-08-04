#!/usr/bin/env bash
# Codex 原生 plugin、agent、worktree 合同与旧 Claude bridge 迁移清理。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
RUNTIME="$ROOT/codex/runtime.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
check() {
  local name="$1"
  shift
  if "$@"; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    fail=$((fail + 1))
  fi
}

printf 'Codex source parity\n'
check "runtime materialize --check" python3 "$RUNTIME" materialize --check
check "marketplace JSON" python3 -m json.tool "$REPO/.agents/plugins/marketplace.json"
check "plugin manifest JSON" python3 -m json.tool "$ROOT/.codex-plugin/plugin.json"
check "plugin MCP JSON" python3 -m json.tool "$ROOT/.mcp-codex.json"

python3 - "$ROOT" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
profiles = json.loads((root/'codex/profiles.json').read_text())
raw = json.dumps(profiles, ensure_ascii=False).lower()
for banned in ('"family"', '"provider"', 'claude', 'grok'):
    assert banned not in raw, banned
assert set(profiles['subagents']) == {'investigator', 'reviewer'}
assert set(profiles['background_roles']) == {'worker', 'worker-high-risk', 'planner'}
for group in ('subagents', 'background_roles'):
    for profile in profiles[group].values():
        assert profile['model'].startswith('gpt-')

agents = sorted((root/'codex/agents').glob('mmw-*.toml'))
assert [p.name for p in agents] == ['mmw-investigator.toml', 'mmw-reviewer.toml']
for path in agents:
    text = path.read_text()
    assert 'sandbox_mode = "read-only"' in text
    assert 'model = "gpt-' in text

skills = root/'skills-codex'
bad = ('mmw dispatch', 'codex exec', 'reviewer-gpt', 'reviewer-claude',
       'Claude Code', 'EnterWorktree', 'enter_worktree', 'mmw task new',
       'mmw task enter', 'mmw task cleanup', 'subagent({', '.dispatch/',
       '另一个模型')
for path in skills.rglob('*.md'):
    text = path.read_text()
    for token in bad:
        assert token not in text, f'{path}: {token}'
    assert '[[mmw-launch:' not in text
    assert '[[mmw-launch-group:' not in text

implement = (skills/'mmw-implement/SKILL.md').read_text()
assert '调用 `create_thread`' in implement and 'environment.type 设为 `worktree`' in implement
assert 'gpt-5.6-sol' in implement and '思考档设为 `high`' in implement
assert '`create_thread`' in implement and '`wait_threads`' in implement
assert 'clientThreadId' in implement and 'startingState.type' in implement
research = (skills/'mmw-research/SKILL.md').read_text()
assert 'agent 设为 `mmw-investigator`' in research
review = (skills/'mmw-review/SKILL.md').read_text()
assert 'agent 都设为 `mmw-reviewer`' in review
assert '只使用内置 GPT 模型' in review

mcp = json.loads((root/'.mcp-codex.json').read_text())
assert set(mcp) == {'serena', 'graphify', 'context7'}
assert '${PLUGIN_ROOT}' in json.dumps(mcp)
assert 'CLAUDE_PLUGIN_ROOT' not in json.dumps(mcp)
PY
check "Codex 合同无旧宿主语义" true

printf '\nBind current detached worktree\n'
git -C "$WORK" init -q main
git -C "$WORK/main" config user.name test
git -C "$WORK/main" config user.email test@example.com
printf 'base\n' > "$WORK/main/file.txt"
git -C "$WORK/main" add file.txt
git -C "$WORK/main" commit -q -m base
base="$(git -C "$WORK/main" rev-parse HEAD)"
git -C "$WORK/main" worktree add -q --detach "$WORK/detached" "$base"
bind="$ROOT/skills/mmw-start/scripts/bind-current-worktree.sh"
(cd "$WORK/detached" && bash "$bind" codex/feat-native '用户原话') >/dev/null
check "绑定 codex 分支" test "$(git -C "$WORK/detached" branch --show-current)" = "codex/feat-native"
check "保留用户原话" grep -qF "用户原话" <(git -C "$WORK/detached" log -1 --format=%B)
if (cd "$WORK/main" && bash "$bind" codex/not-linked x) >/dev/null 2>&1; then
  check "拒绝主 checkout" false
else
  check "拒绝主 checkout" true
fi

printf '\nVerify background result\n'
git -C "$WORK/main" branch codex/worker-result "$base"
git -C "$WORK/main" worktree add -q "$WORK/worker" codex/worker-result
printf 'worker\n' >> "$WORK/worker/file.txt"
git -C "$WORK/worker" add file.txt
git -C "$WORK/worker" commit -q -m worker
head="$(git -C "$WORK/worker" rev-parse HEAD)"
verify="$ROOT/skills/mmw-integrate/scripts/verify-worker-result.sh"
(cd "$WORK/main" && bash "$verify" codex/worker-result "$head" "$base") >/dev/null
check "验证分支 SHA 与基点" true
if (cd "$WORK/main" && bash "$verify" codex/worker-result "$base" "$base") >/dev/null 2>&1; then
  check "拒绝伪造 SHA" false
else
  check "拒绝伪造 SHA" true
fi
if (cd "$WORK/main" && bash "$verify" worker-result "$head" "$base") >/dev/null 2>&1; then
  check "拒绝非 codex 结果分支" false
else
  check "拒绝非 codex 结果分支" true
fi

printf '\nRuntime install and legacy cleanup\n'
fake_home="$WORK/home"
fake_codex="$fake_home/.codex"
fake_bin="$fake_home/bin"
mkdir -p "$fake_codex/skills" "$fake_bin"
main_root="$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir)"
main_root="$(dirname "$main_root")"
for skill in mmw-planner mmw-reviewer mmw-tdd; do
  ln -s "$main_root/mmw/skills/$skill" "$fake_codex/skills/$skill"
done
printf 'keep = true\n' > "$fake_codex/config.toml"
HOME="$fake_home" CODEX_HOME="$fake_codex" MMW_CODEX_BIN_DIR="$fake_bin" \
  python3 "$RUNTIME" install >/dev/null
check "只安装两个只读 agent" test "$(find "$fake_codex/agents" -type f -name 'mmw-*.toml' | wc -l | tr -d ' ')" = 2
check "旧 Claude bridge 已清" test ! -e "$fake_codex/skills/mmw-tdd"
check "不改 config.toml" grep -qxF 'keep = true' "$fake_codex/config.toml"
check "安装 mmw 转发脚本" test -x "$fake_bin/mmw"
check "runtime check" env HOME="$fake_home" CODEX_HOME="$fake_codex" MMW_CODEX_BIN_DIR="$fake_bin" python3 "$RUNTIME" check
HOME="$fake_home" CODEX_HOME="$fake_codex" MMW_CODEX_BIN_DIR="$fake_bin" \
  python3 "$RUNTIME" uninstall >/dev/null
check "uninstall 清理两个 agent" test "$(find "$fake_codex/agents" -type f -name 'mmw-*.toml' | wc -l | tr -d ' ')" = 0
check "uninstall 保留 config.toml" grep -qxF 'keep = true' "$fake_codex/config.toml"

printf '\n过 %s，失败 %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
