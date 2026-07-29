#!/usr/bin/env bash
# MMW Cursor：Serena / Graphifyy 上游 uv tool 的「有更新才升」+ 合同自检 + 失败回滚。
# 由 serena-mcp.sh / graphify-mcp.sh 在 exec 前 source。
#
# 自定义永不让位：
# - Serena：插件 context yml + 四工具合同
# - Graphify：插件 graphify_mcp.py + graphify_ensure.py；禁止官方 graphify.serve 工具面
set -euo pipefail

_mmw_retrieval_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

MMW_RETRIEVAL_PLUGIN_ROOT="${MMW_RETRIEVAL_PLUGIN_ROOT:-$(_mmw_retrieval_root)}"
MMW_RETRIEVAL_CONTRACTS="${MMW_RETRIEVAL_CONTRACTS:-$MMW_RETRIEVAL_PLUGIN_ROOT/config/retrieval/contracts.json}"
MMW_RETRIEVAL_STATE_DIR="${MMW_RETRIEVAL_STATE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/mmw-cursor-retrieval}"
MMW_RETRIEVAL_STATE="${MMW_RETRIEVAL_STATE:-$MMW_RETRIEVAL_STATE_DIR/tool-state.json}"
MMW_RETRIEVAL_PYPI_TIMEOUT="${MMW_RETRIEVAL_PYPI_TIMEOUT:-3}"
MMW_RETRIEVAL_SKIP_UPGRADE="${MMW_RETRIEVAL_SKIP_UPGRADE:-0}"

_mmw_log() { echo "[mmw-retrieval] $*" >&2; }

_mmw_uv() {
  if [ -n "${MMW_UV_BIN:-}" ] && [ -x "${MMW_UV_BIN}" ]; then
    printf '%s' "$MMW_UV_BIN"
    return 0
  fi
  command -v uv 2>/dev/null || true
}

_mmw_state_get() {
  local pkg="$1" key="$2"
  python3 - "$MMW_RETRIEVAL_STATE" "$pkg" "$key" <<'PY'
import json, sys
from pathlib import Path
path, pkg, key = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if not path.is_file():
    raise SystemExit(0)
data = json.loads(path.read_text())
tools = data.get("tools") or {}
entry = tools.get(pkg) or {}
val = entry.get(key)
if val:
    print(val)
PY
}

_mmw_state_set() {
  local pkg="$1" key="$2" value="$3"
  mkdir -p "$MMW_RETRIEVAL_STATE_DIR" 2>/dev/null || true
  python3 - "$MMW_RETRIEVAL_STATE" "$pkg" "$key" "$value" <<'PY' || true
import json, sys
from pathlib import Path
path, pkg, key, value = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
try:
    data = {"tools": {}}
    if path.is_file():
        try:
            data = json.loads(path.read_text())
        except Exception:
            data = {"tools": {}}
    data.setdefault("tools", {})
    data["tools"].setdefault(pkg, {})
    data["tools"][pkg][key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
except OSError:
    # 状态缓存写失败不应阻断 MCP 启动（沙箱 / 只读盘）
    raise SystemExit(0)
PY
}

_mmw_installed_version() {
  local pkg="$1"
  python3 - "$pkg" <<'PY'
import sys
from pathlib import Path
pkg = sys.argv[1]
root = Path.home() / ".local/share/uv/tools" / pkg
# dist-info dir name may use underscores
cands = list(root.glob("lib/python*/site-packages/*.dist-info/METADATA"))
# prefer metadata whose Name matches package (normalized)
norm = pkg.replace("-", "_").lower()
picked = None
for meta in cands:
    text = meta.read_text(encoding="utf-8", errors="ignore")
    name = ""
    ver = ""
    for line in text.splitlines():
        if line.startswith("Name: "):
            name = line[6:].strip().lower().replace("-", "_")
        elif line.startswith("Version: "):
            ver = line[9:].strip()
    if name == norm and ver:
        picked = ver
        break
    if ver and picked is None:
        picked = ver
if picked:
    print(picked)
PY
}

_mmw_pypi_latest() {
  local pkg="$1"
  python3 - "$pkg" "$MMW_RETRIEVAL_PYPI_TIMEOUT" <<'PY'
import json, sys, urllib.request
pkg, timeout = sys.argv[1], float(sys.argv[2])
url = f"https://pypi.org/pypi/{pkg}/json"
try:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        data = json.load(resp)
    print(data["info"]["version"])
except Exception as exc:
    print(f"ERROR:{exc}", file=sys.stderr)
    raise SystemExit(2)
PY
}

_mmw_ensure_installed() {
  local pkg="$1"
  local uv_bin
  uv_bin="$(_mmw_uv)"
  [ -n "$uv_bin" ] || { _mmw_log "ERROR: 找不到 uv，无法安装/升级 $pkg"; return 2; }
  if [ -z "$(_mmw_installed_version "$pkg")" ]; then
    _mmw_log "install missing uv tool: $pkg"
    "$uv_bin" tool install "$pkg" >&2
  fi
}

_mmw_maybe_upgrade() {
  # stdout: upgraded|unchanged|skipped|offline
  local pkg="$1"
  local uv_bin installed latest
  if [ "$MMW_RETRIEVAL_SKIP_UPGRADE" = "1" ]; then
    echo skipped
    return 0
  fi
  uv_bin="$(_mmw_uv)"
  [ -n "$uv_bin" ] || { echo skipped; return 0; }
  _mmw_ensure_installed "$pkg" || return 2
  installed="$(_mmw_installed_version "$pkg")"
  if ! latest="$(_mmw_pypi_latest "$pkg" 2>/dev/null)"; then
    _mmw_log "PyPI 探测失败，跳过升级 $pkg（继续用已装 $installed）"
    echo offline
    return 0
  fi
  if [ -z "$installed" ]; then
    _mmw_log "ERROR: $pkg 安装后仍读不到版本"
    return 2
  fi
  if [ "$installed" = "$latest" ]; then
    _mmw_log "$pkg $installed 已是最新"
    echo unchanged
    return 0
  fi
  _mmw_state_set "$pkg" "pre_upgrade" "$installed"
  _mmw_log "upgrade $pkg: $installed -> $latest"
  if ! "$uv_bin" tool upgrade "$pkg" >&2; then
    _mmw_log "ERROR: uv tool upgrade $pkg 失败"
    return 2
  fi
  echo upgraded
}

_mmw_rollback() {
  local pkg="$1"
  local target="${2:-}"
  local uv_bin
  uv_bin="$(_mmw_uv)"
  [ -n "$uv_bin" ] || return 2
  if [ -z "$target" ]; then
    target="$(_mmw_state_get "$pkg" last_good)"
  fi
  if [ -z "$target" ]; then
    target="$(_mmw_state_get "$pkg" pre_upgrade)"
  fi
  if [ -z "$target" ]; then
    _mmw_log "ERROR: $pkg 合同失败且无 last_good/pre_upgrade 可回滚"
    return 2
  fi
  _mmw_log "rollback $pkg -> $target"
  "$uv_bin" tool install "${pkg}==${target}" --force >&2
}

_mmw_serena_contract() {
  local bin help
  bin="${SERENA_BIN:-$(command -v serena 2>/dev/null || true)}"
  [ -n "$bin" ] && [ -x "$bin" ] || { _mmw_log "contract: serena 不在 PATH"; return 1; }
  help="$("$bin" --help 2>&1 || true)"
  printf '%s' "$help" | grep -q 'start-mcp-server' || {
    _mmw_log "contract: serena 缺少 start-mcp-server"
    return 1
  }
  # 轻量 MCP tools/list（仅在刚升级或强制时）
  if [ "${1:-}" = "full" ]; then
    python3 - "$bin" "$MMW_RETRIEVAL_CONTRACTS" "$MMW_RETRIEVAL_PLUGIN_ROOT" <<'PY' || return 1
import json, subprocess, sys
bin_path, contracts_path, project = sys.argv[1], sys.argv[2], sys.argv[3]
contracts = json.loads(open(contracts_path, encoding="utf-8").read())
required = set(contracts["serena"]["required_mcp_tools"])
args = [bin_path, "start-mcp-server", "--enable-web-dashboard", "false",
     "--open-web-dashboard", "false", "--enable-gui-log-window", "false"]
if project:
    args.extend(["--project", project])
else:
    args.append("--project-from-cwd")
proc = subprocess.Popen(
    args,
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
  "protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mmw-contract","version":"0"}}})
send({"jsonrpc":"2.0","method":"notifications/initialized"})
send({"jsonrpc":"2.0","id":2,"method":"tools/list"})
out = []
# read a few lines
import select, time
deadline = time.time() + 8
buf = ""
while time.time() < deadline and len(out) < 3:
    line = proc.stdout.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    if msg.get("id") in (1, 2):
        out.append(msg)
    if len([m for m in out if m.get("id") == 2]) >= 1:
        break
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()
tools_msg = next((m for m in out if m.get("id") == 2), None)
if not tools_msg or "result" not in tools_msg:
    print("serena tools/list failed", file=sys.stderr)
    raise SystemExit(1)
names = {t.get("name") for t in tools_msg["result"].get("tools") or []}
missing = sorted(required - names)
if missing:
    print("serena missing tools:", ", ".join(missing), file=sys.stderr)
    raise SystemExit(1)
PY
  fi
  return 0
}

_mmw_graphify_contract() {
  local graphify_bin ensure_py server_py help
  graphify_bin="$(command -v graphify 2>/dev/null || true)"
  [ -n "$graphify_bin" ] || { _mmw_log "contract: graphify 不在 PATH"; return 1; }
  help="$("$graphify_bin" --help 2>&1 || true)"
  for sub in query affected path explain; do
    # 子命令的 --help 不一定可用（query/affected 会把参数当问题）；认主 help 清单。
    printf '%s\n' "$help" | grep -Eq "^[[:space:]]*${sub}[[:space:]]" || {
      _mmw_log "contract: graphify --help 未列出子命令 $sub"
      return 1
    }
  done
  ensure_py="$MMW_RETRIEVAL_PLUGIN_ROOT/skills/graphify/scripts/graphify_ensure.py"
  server_py="$MMW_RETRIEVAL_PLUGIN_ROOT/skills/graphify/scripts/graphify_mcp.py"
  [ -f "$ensure_py" ] || { _mmw_log "contract: 缺少插件 ensure $ensure_py"; return 1; }
  [ -f "$server_py" ] || { _mmw_log "contract: 缺少插件 MCP $server_py"; return 1; }
  python3 - "$server_py" "$MMW_RETRIEVAL_CONTRACTS" <<'PY' || return 1
import json, subprocess, sys
server, contracts_path = sys.argv[1], sys.argv[2]
contracts = json.loads(open(contracts_path, encoding="utf-8").read())
g = contracts["graphify"]
proc = subprocess.Popen(
    [sys.executable, server],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
  "protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mmw-contract","version":"0"}}})
send({"jsonrpc":"2.0","id":2,"method":"tools/list"})
msgs = []
while len(msgs) < 2:
    line = proc.stdout.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    if msg.get("id") in (1, 2):
        msgs.append(msg)
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()
tools_msg = next((m for m in msgs if m.get("id") == 2), None)
if not tools_msg:
    print("graphify wrapper tools/list failed", file=sys.stderr)
    raise SystemExit(1)
tools = tools_msg["result"].get("tools") or []
names = {t.get("name") for t in tools}
if g["required_mcp_tool"] not in names:
    print("wrapper missing tool graphify", file=sys.stderr)
    raise SystemExit(1)
forbidden = set(g["forbidden_mcp_tools"]) & names
if forbidden:
    print("wrapper exposed forbidden official tools:", ", ".join(sorted(forbidden)), file=sys.stderr)
    raise SystemExit(1)
tool = next(t for t in tools if t.get("name") == g["required_mcp_tool"])
actions = set((((tool.get("inputSchema") or {}).get("properties") or {}).get("action") or {}).get("enum") or [])
missing = sorted(set(g["required_mcp_actions"]) - actions)
if missing:
    print("wrapper missing actions:", ", ".join(missing), file=sys.stderr)
    raise SystemExit(1)
PY
  return 0
}

mmw_maintain_serena() {
  local status
  status="$(_mmw_maybe_upgrade serena-agent)" || return 2
  local mode=light
  if [ "$status" = upgraded ]; then
    mode=full
  fi
  if ! _mmw_serena_contract "$mode"; then
    if [ "$status" = upgraded ]; then
      _mmw_rollback serena-agent || return 2
      _mmw_serena_contract full || return 2
      _mmw_log "Serena 升级破坏合同，已回滚并复检通过"
    else
      return 2
    fi
  else
    local ver
    ver="$(_mmw_installed_version serena-agent)"
    [ -n "$ver" ] && _mmw_state_set serena-agent last_good "$ver"
  fi
}

mmw_maintain_graphify() {
  local status
  status="$(_mmw_maybe_upgrade graphifyy)" || return 2
  if ! _mmw_graphify_contract; then
    if [ "$status" = upgraded ]; then
      _mmw_rollback graphifyy || return 2
      _mmw_graphify_contract || return 2
      _mmw_log "graphifyy 升级破坏合同，已回滚；插件包装器未改动"
    else
      return 2
    fi
  else
    local ver
    ver="$(_mmw_installed_version graphifyy)"
    [ -n "$ver" ] && _mmw_state_set graphifyy last_good "$ver"
  fi
}
