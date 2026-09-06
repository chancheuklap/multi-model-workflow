#!/usr/bin/env python3
"""按 models.md + agent.json + body.md 为每个 host assemble 出 agent 文件，写进 agents/<名>/out/。

一个 agent 一个目录：agents/<名>/ 里放 body.md（提示词正文，单一来源）和
agent.json（name、description、sandbox、五个 host 各自的工具）。model 与 effort 不在这里，
在 skills/dispatch/models.md 里——每一个被派出去的 agent 的 model 只有那一处，user
只开那一个文件。这里只做格式转换，五个 host 的文件格式是结构差异，属于代码，不属于配置：

  claude   -> out/claude.md       frontmatter: name/description/model/effort/tools
  cursor   -> out/cursor.md       frontmatter: name/description/model/readonly
  codex    -> out/codex.toml      name/description/model/model_reasoning_effort/sandbox_mode/developer_instructions
  grok     -> out/grok.md         frontmatter: name/description/model；正文即提示词
           -> out/grok.role.toml  description/default_capability_mode/reasoning_effort（装到 ~/.grok/roles/）
  pi       -> out/pi.md           frontmatter: name/description/model/thinking/tools

agent.json 顶层可选键 sandbox 决定 Cursor、Codex、Grok 三家的沙箱档位，缺省
read-only。写 workspace-write 的 agent 才跑得起会写文件的命令——只给职责就是执行的
agent。Claude 与 pi 不看这个键，它们靠各自 hosts 里的 tools 列表放行。

用法：
  assemble.py            assemble（有变化才写）
  assemble.py --check    只比对 out/ 是否与源一致。齐了回 0，不齐回 1
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT.parent / "skills" / "dispatch" / "models.md"


def q(s: str) -> str:
    """JSON 字符串字面量，同时是合法的 YAML 双引号标量和 TOML basic string。"""
    return json.dumps(s, ensure_ascii=False)


def parse_model_rows() -> list[tuple[str, str, str, str, str]]:
    """models.md 表的每一行：(agent, host, model, effort, permissions)。

    install.sh 与本文件共用这一份解析。表头、分隔行、非五列的行丢掉。
    """
    if not MODELS.is_file():
        raise ValueError(f"缺 models.md：{MODELS}")
    rows: list[tuple[str, str, str, str, str]] = []
    for line in MODELS.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        agent, host, model, effort, permissions = cells
        if agent == "agent" or set(agent) <= set("- "):
            continue
        rows.append((agent, host, model, effort, permissions))
    if not rows:
        raise ValueError(f"{MODELS} 里一行 agent 都没有")
    return rows


def read_models() -> dict[tuple[str, str], tuple[str, str]]:
    """(agent, host) -> (model, effort)，跳过 read-only 行。

    read-only 是 Paseo 会话行，同名 agent 另有 — 行给原生 subagent（advisor）。
    bypass 行不跳：reviewer 会话行的 model 与 effort 也是三轴 subagent 的。
    """
    table: dict[tuple[str, str], tuple[str, str]] = {}
    for agent, host, model, effort, permissions in parse_model_rows():
        if permissions == "read-only":
            continue
        table[(agent, host)] = (model, effort)
    return table


def profile_rows() -> list[tuple[str, str, str, str, str]]:
    """生成 Agent profile 的行：bypass 与 read-only。"""
    return [row for row in parse_model_rows() if row[4] in ("bypass", "read-only")]


def create_agent_settings(host: str, permissions: str) -> dict:
    """permissions 单元格写成 create_agent 的 settings：`modeId` 或 `features`。

    claude / codex / 其它 三路。install 的 profile 与 dispatch 的 create_agent JSON
    都从这里取，所以一种 host 只有一种拼法。
    """
    if permissions == "bypass":
        if host == "claude":
            return {"modeId": "bypassPermissions"}
        if host == "codex":
            return {"modeId": "full-access"}
        return {"features": {"auto_accept": True}}
    if permissions == "read-only":
        if host == "claude":
            return {"modeId": "plan"}
        if host == "codex":
            # Codex 没有 read-only 模式（auto / auto-review / full-access）；auto 权限最低，仍可改文件。
            return {"modeId": "auto"}
        return {"features": {"auto_accept": False}}
    raise ValueError(f"permissions 只能是 bypass 或 read-only，得到 {permissions!r}")


def apply_permissions(profile: dict, host: str, permissions: str) -> dict:
    """按 host 把 permissions 单元格写成 profile 的 modeId / featureValues。

    一份，install 与 --check 共用。settings 的 `features` 在 profile 里叫 featureValues。
    """
    settings = create_agent_settings(host, permissions)
    if "features" in settings:
        profile["featureValues"] = settings["features"]
        profile.pop("modeId", None)
    else:
        profile["modeId"] = settings["modeId"]
        profile.pop("featureValues", None)
    return profile


def render(agent_dir: Path, table: dict[tuple[str, str], tuple[str, str]]) -> dict[str, str]:
    spec = json.loads((agent_dir / "agent.json").read_text(encoding="utf-8"))
    body = (agent_dir / "body.md").read_text(encoding="utf-8").strip() + "\n"
    name, desc, hosts = spec["name"], spec["description"], spec["hosts"]
    sandbox = spec.get("sandbox", "read-only")
    if sandbox not in ("read-only", "workspace-write"):
        raise ValueError(f"{agent_dir.name}: sandbox 只能是 read-only 或 workspace-write，得到 {sandbox!r}")
    readonly = sandbox == "read-only"

    missing = {"claude", "cursor", "codex", "grok", "pi"} - hosts.keys()
    if missing:
        raise ValueError(f"{agent_dir.name}: agent.json 缺 host {sorted(missing)}")

    listed = {h for h in hosts if (name, h) in table}
    unlisted = sorted(h for h in hosts if (name, h) not in table)
    if unlisted:
        raise ValueError(
            f"{agent_dir.name}: {MODELS} 里没有 {name} 在 {unlisted} 上的行，"
            f"model 与 effort 只从 models.md 读")
    if not listed:
        raise ValueError(
            f"{agent_dir.name}: {MODELS} 里没有 {name} 的行，"
            f"model 与 effort 只从 models.md 读")

    def model(host: str) -> str:
        return table[(name, host)][0]

    def effort(host: str) -> str:
        return table[(name, host)][1]
    if "'''" in body:
        raise ValueError(f"{agent_dir.name}: body.md 含 ''' ，会撑破 codex.toml 的多行字符串")

    def fm(fields: dict[str, str]) -> str:
        lines = ["---"]
        for k, v in fields.items():
            lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        return "\n".join(lines)

    out: dict[str, str] = {}

    if "claude" in listed:
        h = hosts["claude"]
        out["claude.md"] = fm({
            "name": name,
            "description": q(desc),
            "model": model("claude"),
            "effort": effort("claude"),
            "tools": h["tools"],
        }) + body

    # Cursor 把 effort 烧进模型名（cursor-grok-4.6-high 是一个名字），effort 列为 —；
    # 只有参数化模型才接受 [effort=…] 括号覆盖，那时 effort 列才有值。
    if "cursor" in listed:
        cursor_model = model("cursor")
        if effort("cursor") not in ("—", "-", ""):
            cursor_model += f"[effort={effort('cursor')}]"
        h = hosts["cursor"]
        out["cursor.md"] = fm({
            "name": name,
            "description": q(desc),
            "model": cursor_model,
            "readonly": "true" if readonly else "false",
        }) + body

    if "codex" in listed:
        h = hosts["codex"]
        out["codex.toml"] = (
            f"name = {q(name)}\n"
            f"description = {q(desc)}\n"
            f"model = {q(model('codex'))}\n"
            f"model_reasoning_effort = {q(effort('codex'))}\n"
            f'sandbox_mode = "{sandbox}"\n'
            f"developer_instructions = '''\n{body}'''\n"
        )

    if "grok" in listed:
        out["grok.md"] = fm({
            "name": name,
            "description": q(desc),
            "model": model("grok"),
        }) + body
        out["grok.role.toml"] = (
            f"description = {q(desc)}\n"
            f'default_capability_mode = "{"read-only" if readonly else "execute"}"\n'
            f"reasoning_effort = {q(effort('grok'))}\n"
        )

    if "pi" in listed:
        h = hosts["pi"]
        out["pi.md"] = fm({
            "name": name,
            "description": q(desc),
            "model": model("pi"),
            "thinking": effort("pi"),
            "tools": h["tools"],
        }) + body

    return out


def main() -> int:
    check = "--check" in sys.argv[1:]
    agent_dirs = sorted(d for d in ROOT.iterdir() if (d / "agent.json").is_file())
    if not agent_dirs:
        print("assemble: agents/ 下一个 agent 都没有", file=sys.stderr)
        return 1

    table = read_models()
    rc = 0
    for agent_dir in agent_dirs:
        rendered = render(agent_dir, table)
        out_dir = agent_dir / "out"
        for fname, want in rendered.items():
            path = out_dir / fname
            have = path.read_text(encoding="utf-8") if path.is_file() else None
            if have == want:
                continue
            if check:
                print(f"过期  {path}（改了源之后没重新跑 assemble.py）", file=sys.stderr)
                rc = 1
            else:
                out_dir.mkdir(exist_ok=True)
                path.write_text(want, encoding="utf-8")
                print(f"装配  {path}")
        # out/ 里多出来的孤儿也要报：host 那边的软链可能还指着它。
        if out_dir.is_dir():
            for stray in sorted(out_dir.iterdir()):
                if stray.name not in rendered:
                    print(f"多余  {stray}（源里已不产出，请删除并重装）", file=sys.stderr)
                    rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
