#!/usr/bin/env python3
"""按 models.md + agent.json + body.md 装配每个宿主的 agent 文件，写进 agents/<名>/out/。

一个 agent 一个目录：agents/<名>/ 里放 body.md（提示词正文，单一来源）和
agent.json（name、description、sandbox、五宿主各自的工具）。模型与思考强度不在这里，
在 skills/dispatch/models.md 那张表里——每一个被派出去的 agent 的模型只有那一处，用户
只开那一个文件。这里只做格式转换，五个宿主的文件格式是结构差异，属于代码，不属于配置：

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
  assemble.py            装配（有变化才写）
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


def read_models() -> dict[tuple[str, str], tuple[str, str]]:
    """models.md 那张表，取成 (agent 名, 宿主) -> (模型, 思考强度)。

    表里一行一个 (agent, 宿主)，五列 agent | host | model | effort | launch arguments。
    启动命令那一列非空的三行是经 Herdr 起的会话角色，它们的配置由 dispatch.sh 在派发
    那一刻现读，与本脚本无关；这里只取启动参数为 — 的那些行，也就是 subagent。
    """
    if not MODELS.is_file():
        raise ValueError(f"缺模型表：{MODELS}")
    table: dict[tuple[str, str], tuple[str, str]] = {}
    for line in MODELS.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        agent, host, model, effort, launch = cells
        if agent == "agent" or set(agent) <= set("- "):
            continue
        if launch not in ("—", "-", ""):
            continue
        table[(agent, host)] = (model, effort)
    if not table:
        raise ValueError(f"{MODELS} 里一行 subagent 都没有")
    return table


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
        raise ValueError(f"{agent_dir.name}: agent.json 缺宿主 {sorted(missing)}")

    unlisted = [h for h in hosts if (name, h) not in table]
    if unlisted:
        raise ValueError(
            f"{agent_dir.name}: {MODELS} 里没有 {name} 在 {sorted(unlisted)} 上的行，"
            f"模型与思考强度只从那张表读")

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

    h = hosts["claude"]
    out["claude.md"] = fm({
        "name": name,
        "description": q(desc),
        "model": model("claude"),
        "effort": effort("claude"),
        "tools": h["tools"],
    }) + body

    # Cursor 把思考强度烧进模型名（cursor-grok-4.6-high 是一个名字），effort 列为 —；
    # 只有参数化模型才接受 [effort=…] 括号覆盖，那时 effort 列才有值。
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

    h = hosts["codex"]
    out["codex.toml"] = (
        f"name = {q(name)}\n"
        f"description = {q(desc)}\n"
        f"model = {q(model('codex'))}\n"
        f"model_reasoning_effort = {q(effort('codex'))}\n"
        f'sandbox_mode = "{sandbox}"\n'
        f"developer_instructions = '''\n{body}'''\n"
    )

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
                print(f"过期  {path}（改了源之后没重新装配）", file=sys.stderr)
                rc = 1
            else:
                out_dir.mkdir(exist_ok=True)
                path.write_text(want, encoding="utf-8")
                print(f"装配  {path}")
        # out/ 里多出来的孤儿也要报：宿主软链可能还指着它。
        if out_dir.is_dir():
            for stray in sorted(out_dir.iterdir()):
                if stray.name not in rendered:
                    print(f"多余  {stray}（源里已不产出，请删除并重装）", file=sys.stderr)
                    rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
