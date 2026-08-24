#!/usr/bin/env bash
# landing-orchestrator 的离线测试：models.md 解析、前置检查的报错路径与通过路径、frontier 判定。
# 只靠退出码说话；输出不要接管道。
#
#   bash mmw-v2/skills/landing-orchestrator/tests/run.sh
set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname "$HERE")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fails=0
ok()   { printf 'ok   %s\n' "$1"; }
bad()  { printf 'FAIL %s\n' "$1" >&2; fails=$((fails + 1)); }
# 期望命令非零退出且 stderr 含某段文字
expect_fail() { # <名> <期望文字> <命令...>
  local name="$1" want="$2"; shift 2
  local err rc
  err="$("$@" 2>&1 >/dev/null)"; rc=$?
  if [ "$rc" -ne 0 ] && printf '%s' "$err" | grep -qF -- "$want"; then ok "$name"; else bad "$name (rc=$rc, stderr=$err)"; fi
}

# ---------- models.py ----------
M="$SKILL/scripts/models.py"
out="$(python3 "$M" "$SKILL/reference/models.md")" && printf '%s' "$out" | python3 -c '
import json,sys
t=json.load(sys.stdin)
assert list(t)==["orchestrator","planner","junior-worker","senior-worker","verifier","advisor"], list(t)
assert t["junior-worker"]=={"kind":"cursor","model":"cursor-grok-4.6-high","effort":"high"}, t["junior-worker"]
assert t["senior-worker"]["effort"]=="xhigh"
' && ok "models.py 解析模板得到六个角色" || bad "models.py 解析模板"

sed '/高级工人/d' "$SKILL/reference/models.md" > "$WORK/missing-role.md"
expect_fail "models.py 缺角色报错" "左列应固定为" python3 "$M" "$WORK/missing-role.md"
sed 's/| xhigh |/| ultra |/' "$SKILL/reference/models.md" > "$WORK/bad-effort.md"
expect_fail "models.py 强度不在集合内报错" "思考强度" python3 "$M" "$WORK/bad-effort.md"
sed 's/| 宿主 kind |/| 宿主 |/' "$SKILL/reference/models.md" > "$WORK/bad-header.md"
expect_fail "models.py 表头错报错" "表头应为" python3 "$M" "$WORK/bad-header.md"
expect_fail "models.py 文件不存在报错" "文件不存在" python3 "$M" "$WORK/nope.md"

# ---------- preflight.sh ----------
P="$SKILL/scripts/preflight.sh"
# 假的 gh 与 herdr 放在 PATH 最前，避免依赖本机认证与 Herdr 会话
mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'SH'
#!/usr/bin/env bash
[ "${FAKE_GH_AUTH:-ok}" = ok ] && exit 0 || exit 1
SH
cat > "$WORK/bin/herdr" <<'SH'
#!/usr/bin/env bash
printf '      --kind <KIND>\n          Supported agent kind and canonical executable\n          \n          [possible values: %s]\n' "${FAKE_HERDR_KINDS:-pi, claude, codex, cursor, grok}"
SH
chmod +x "$WORK/bin/gh" "$WORK/bin/herdr"
export PATH="$WORK/bin:$PATH"

repo="$WORK/repo"; mkdir -p "$repo/docs/agents"
git -C "$repo" init -q && git -C "$repo" remote add origin https://example.invalid/o/r.git
cp "$SKILL/reference/models.md" "$repo/docs/agents/models.md"

expect_fail "preflight 无 HERDR_ENV 报错" "HERDR_ENV" env -u HERDR_ENV bash "$P" "$repo"
expect_fail "preflight gh 未认证报错" "gh 未认证" env HERDR_ENV=1 FAKE_GH_AUTH=no bash "$P" "$repo"
norepo="$WORK/norepo"; mkdir -p "$norepo"; git -C "$norepo" init -q
expect_fail "preflight 无远端报错" "没有远端" env HERDR_ENV=1 bash "$P" "$norepo"
rm "$repo/docs/agents/models.md"
expect_fail "preflight 缺 models.md 报错" "缺 " env HERDR_ENV=1 bash "$P" "$repo"
cp "$WORK/missing-role.md" "$repo/docs/agents/models.md"
expect_fail "preflight models.md 解析失败报错" "解析失败" env HERDR_ENV=1 bash "$P" "$repo"
cp "$SKILL/reference/models.md" "$repo/docs/agents/models.md"
expect_fail "preflight kind 不在 herdr 支持内报错" "不在 herdr 支持的 kinds 内" env HERDR_ENV=1 FAKE_HERDR_KINDS="pi, claude, codex" bash "$P" "$repo"
out="$(env HERDR_ENV=1 bash "$P" "$repo")" && printf '%s' "$out" | python3 -c 'import json,sys; assert "verifier" in json.load(sys.stdin)' \
  && ok "preflight 四项全过输出表 JSON" || bad "preflight 通过路径"

# ---------- frontier.py ----------
F="$SKILL/scripts/frontier.py"
mk() { # number state blocked_by assignees(0/1) label
  printf '{"number":%s,"state":"%s","assignees":[%s],"labels":[{"name":"%s"}],"issue_dependencies_summary":{"blocked_by":%s}}' \
    "$1" "$2" "$( [ "$4" = 1 ] && printf '{"login":"x"}' )" "$5" "$3"
}
input="[$(mk 12 open 0 0 worker:senior),$(mk 10 open 0 0 worker:junior),$(mk 11 open 1 0 worker:junior),$(mk 13 open 0 1 worker:junior),$(mk 14 closed 0 0 worker:junior),$(mk 15 open 0 0 ready-for-agent)]"
got="$(printf '%s' "$input" | python3 "$F")"
want=$'10 worker:junior\n12 worker:senior\n15 ungraded'
[ "$got" = "$want" ] && ok "frontier 过滤阻塞/认领/关闭并按编号排序" || bad "frontier 判定（得到: $got）"
got="$(printf '[]' | python3 "$F")"; rc=$?
[ "$rc" -eq 0 ] && [ -z "$got" ] && ok "frontier 空输入退出 0 无输出" || bad "frontier 空输入"
expect_fail "frontier 非 JSON 报错" "不是 JSON" bash -c "printf 'nope' | python3 '$F'"
expect_fail "frontier 缺字段报错" "缺字段" bash -c "printf '[{\"number\":1}]' | python3 '$F'"

if [ "$fails" -eq 0 ]; then echo "LANDING-ORCHESTRATOR TESTS OK"; exit 0; fi
echo "LANDING-ORCHESTRATOR TESTS FAILED: $fails" >&2; exit 1
