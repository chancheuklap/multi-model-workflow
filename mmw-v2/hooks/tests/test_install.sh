#!/usr/bin/env bash
# install.sh 在 MMW_V2_HOME 临时根装 hook 层：合并不覆盖、幂等、清单、--check、冲突非零、退役清理。
set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
H="$(dirname "$HERE")"
V2="$(cd "$H/.." && pwd -P)"
rc=0
fail() { echo "失败：$1" >&2; rc=1; }
T="$(mktemp -d)"
mkdir -p "$T/.claude" "$T/.codex" "$T/.cursor" "$T/.grok" "$T/.pi/agent"
printf '{"model":"keep-me","hooks":{"SessionStart":[{"matcher":"*","hooks":[{"type":"command","command":"bash foreign.sh session","timeout":10}]}]}}\n' > "$T/.claude/settings.json"
printf '{"version":1,"hooks":{"sessionStart":[{"command":"bash other.sh session"}]}}\n' > "$T/.cursor/hooks.json"

MMW_V2_HOME="$T" bash "$V2/install.sh" >/dev/null 2>&1 || fail "首次安装应退出 0"
python3 - "$T" "$H" <<'PY' || fail "合并写入"
import json, sys, os
T, H = sys.argv[1:3]
c = json.load(open(f"{T}/.claude/settings.json"))
assert c["model"] == "keep-me", "settings.json 其它键被丢了"
ss = c["hooks"]["SessionStart"]; assert ss[0]["hooks"][0]["command"].startswith("bash foreign.sh"), "他方 SessionStart 条目被覆盖"
assert any(H + "/mmw-activate.js" in h["command"] and "--host claude" in h["command"] for g in ss for h in g["hooks"]), "Claude 缺开场 hook"
assert c["hooks"]["SubagentStart"] and c["hooks"]["Stop"], "Claude 缺 SubagentStart/Stop"
x = json.load(open(f"{T}/.codex/hooks.json")); assert "--host codex" in x["hooks"]["Stop"][0]["hooks"][0]["command"]
u = json.load(open(f"{T}/.cursor/hooks.json")); assert u["version"] == 1
assert u["hooks"]["sessionStart"][0]["command"] == "bash other.sh session", "Cursor 他方条目被覆盖"
assert list(u["hooks"]["sessionStart"][1]) == ["command"] and "--host cursor" in u["hooks"]["sessionStart"][1]["command"]
assert "stop" in u["hooks"] and "subagentStart" in u["hooks"]
g = json.load(open(f"{T}/.grok/hooks/mmw-discipline.json")); assert "--host grok" in g["hooks"]["Stop"][0]["hooks"][0]["command"]
assert os.readlink(f"{T}/.grok/rules/mmw-discipline.md") == f"{H}/discipline/worker.md"
assert os.readlink(f"{T}/.pi/agent/extensions/mmw-discipline") == f"{H}/pi-extension"
for home in (".claude", ".codex", ".cursor", ".grok", ".pi/agent"):
    assert os.path.exists(f"{T}/{home}/.mmw-hooks"), home + " 缺 .mmw-hooks 清单"
PY

# 幂等：再装一次，条目数不变。
MMW_V2_HOME="$T" bash "$V2/install.sh" >/dev/null 2>&1 || fail "二次安装应退出 0"
python3 - "$T" <<'PY' || fail "二次安装不该重复条目"
import json, sys; T = sys.argv[1]
c = json.load(open(f"{T}/.claude/settings.json")); assert len(c["hooks"]["SessionStart"]) == 2 and len(c["hooks"]["Stop"]) == 1
u = json.load(open(f"{T}/.cursor/hooks.json")); assert len(u["hooks"]["sessionStart"]) == 2 and len(u["hooks"]["stop"]) == 1
PY

MMW_V2_HOME="$T" bash "$V2/install.sh" --check >/dev/null 2>&1 || fail "--check 应退出 0"

# --check 只读：拿掉一条后应报缺且不改文件。
python3 - "$T" <<'PY'
import json, sys; T = sys.argv[1]; p = f"{T}/.cursor/hooks.json"; u = json.load(open(p)); del u["hooks"]["stop"]; json.dump(u, open(p, "w"))
PY
before="$(cat "$T/.cursor/hooks.json")"
if MMW_V2_HOME="$T" bash "$V2/install.sh" --check >/dev/null 2>&1; then fail "--check 缺条目应退出 1"; fi
[ "$before" = "$(cat "$T/.cursor/hooks.json")" ] || fail "--check 不该改文件"
MMW_V2_HOME="$T" bash "$V2/install.sh" >/dev/null 2>&1 || fail "补装应退出 0"

# 冲突：同名脚本指向别处、同名扩展目录不是软链 → 非零、不覆盖。
printf '{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"node /elsewhere/mmw-stop.mjs"}]}]}}\n' > "$T/.codex/hooks.json"
rm "$T/.pi/agent/extensions/mmw-discipline"; mkdir "$T/.pi/agent/extensions/mmw-discipline"
if MMW_V2_HOME="$T" bash "$V2/install.sh" >/dev/null 2>"$T/err"; then fail "冲突应退出 1"; fi
grep -q "冲突.*codex/hooks.json" "$T/err" || fail "应报 Codex 条目冲突"
grep -q "冲突.*extensions/mmw-discipline" "$T/err" || fail "应报 pi 扩展目录冲突"
[ -d "$T/.pi/agent/extensions/mmw-discipline" ] && [ ! -L "$T/.pi/agent/extensions/mmw-discipline" ] || fail "冲突目录不该被覆盖"
grep -q '/elsewhere/mmw-stop.mjs' "$T/.codex/hooks.json" || fail "冲突文件不该被改写"
rmdir "$T/.pi/agent/extensions/mmw-discipline"; printf '{"hooks":{}}\n' > "$T/.codex/hooks.json"

# 退役清理：清单里记着、这次安装点里没有的链接，装前摘掉。
echo "link|$T/.grok/rules/retired.md" >> "$T/.grok/.mmw-hooks"
ln -s "$H/discipline/verifier.md" "$T/.grok/rules/retired.md"
ln -s /elsewhere/x "$T/.grok/rules/foreign.md"; echo "link|$T/.grok/rules/foreign.md" >> "$T/.grok/.mmw-hooks"
MMW_V2_HOME="$T" bash "$V2/install.sh" >/dev/null 2>&1 || fail "清理后安装应退出 0"
[ ! -e "$T/.grok/rules/retired.md" ] || fail "退役的本仓库链接应被摘掉"
[ -L "$T/.grok/rules/foreign.md" ] || fail "不指回本仓库的链接不能动"
grep -q "retired" "$T/.grok/.mmw-hooks" && fail "清单不该再记退役条目"

exit "$rc"
