#!/usr/bin/env python3
"""按 agent.json + body.md 装配每个宿主的 agent 文件，写进各 agent 目录下的 out/。

一个 agent 一个目录：agents/<名>/ 里放 body.md（提示词正文，单一来源）和
agent.json（name、description、要不要 shell、五宿主各自的模型与工具）。这里只做格式
转换，五个宿主的文件格式是结构差异，属于代码，不属于配置：

  claude   -> out/claude.md       frontmatter: name/description/model/effort/tools
  cursor   -> out/cursor.md       frontmatter: name/description/model(带 [effort=…])/readonly
  codex    -> out/codex.toml      name/description/model/model_reasoning_effort/sandbox_mode/developer_instructions
  grok     -> out/grok.md         frontmatter: name/description/model；正文即提示词
           -> out/grok.role.toml  description/default_capability_mode/reasoning_effort（装到 ~/.grok/roles/）
  pi       -> out/pi.md           frontmatter: name/description/model/thinking/tools

agent.json 的 "shell"（默认 false）说这个 agent 要不要跑命令。Claude 与 pi 靠 tools
列表放行，另外三家各有一个开关，名字和取值都不一样，由这里翻译。Codex 那一档给的是
danger-full-access 而不是 workspace-write：跑得起验收命令的 agent 要装依赖、要写
工作区外的临时目录，workspace-write 两头都不对——它拦住工作区外，又放开工作区内。

用法：
  assemble.py            装配（有变化才写）
  assemble.py --check    只比对 out/ 是否与源一致。齐了回 0，不齐回 1
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def q(s: str) -> str:
    """JSON 字符串字面量，同时是合法的 YAML 双引号标量和 TOML basic string。"""
    return json.dumps(s, ensure_ascii=False)


def render(agent_dir: Path) -> dict[str, str]:
    spec = json.loads((agent_dir / "agent.json").read_text(encoding="utf-8"))
    body = (agent_dir / "body.md").read_text(encoding="utf-8").strip() + "\n"
    name, desc, hosts = spec["name"], spec["description"], spec["hosts"]
    shell = spec.get("shell", False)

    missing = {"claude", "cursor", "codex", "grok", "pi"} - hosts.keys()
    if missing:
        raise ValueError(f"{agent_dir.name}: agent.json 缺宿主 {sorted(missing)}")
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
        "model": h["model"],
        "effort": h["effort"],
        "tools": h["tools"],
    }) + body

    h = hosts["cursor"]
    out["cursor.md"] = fm({
        "name": name,
        "description": q(desc),
        "model": f"{h['model']}[effort={h['effort']}]",
        "readonly": "false" if shell else "true",
    }) + body

    h = hosts["codex"]
    out["codex.toml"] = (
        f"name = {q(name)}\n"
        f"description = {q(desc)}\n"
        f"model = {q(h['model'])}\n"
        f"model_reasoning_effort = {q(h['effort'])}\n"
        f'sandbox_mode = "{"danger-full-access" if shell else "read-only"}"\n'
        f"developer_instructions = '''\n{body}'''\n"
    )

    h = hosts["grok"]
    out["grok.md"] = fm({
        "name": name,
        "description": q(desc),
        "model": h["model"],
    }) + body
    out["grok.role.toml"] = (
        f"description = {q(desc)}\n"
        f'default_capability_mode = "{"execute" if shell else "read-only"}"\n'
        f"reasoning_effort = {q(h['effort'])}\n"
    )

    h = hosts["pi"]
    out["pi.md"] = fm({
        "name": name,
        "description": q(desc),
        "model": h["model"],
        "thinking": h["effort"],
        "tools": h["tools"],
    }) + body

    return out


def main() -> int:
    check = "--check" in sys.argv[1:]
    agent_dirs = sorted(d for d in ROOT.iterdir() if (d / "agent.json").is_file())
    if not agent_dirs:
        print("assemble: agents/ 下一个 agent 都没有", file=sys.stderr)
        return 1

    rc = 0
    for agent_dir in agent_dirs:
        rendered = render(agent_dir)
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
