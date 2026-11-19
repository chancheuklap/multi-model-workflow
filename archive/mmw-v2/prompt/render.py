#!/usr/bin/env python3
"""把 shared.md 与 hosts/<host>.md 拼成 Codex、Pi、Grok 各自的用户级 AGENTS.md。

    render.py            写
    render.py --check    只比对；有不一致回 1，不写
    render.py --adopt    目标不是本脚本写的、或被人直接改过，也覆盖（首次装、或改动已搬回源里）

生成文件第一行是 HTML 注释，带正文的 sha256。再次运行时：
  - 哈希对得上：是上次写的、没人动过，直接覆盖
  - 哈希对不上：有人直接改了生成文件，拒绝覆盖并退出 2，改动要搬回源里
  - 没有这一行：不是本脚本写的，没有 --adopt 就拒绝

MMW_V2_HOME 把 host 主目录整体搬到别处，只给测试用。
"""
import hashlib
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE / "shared.md"
HOSTS = HERE / "hosts"

MARK = "mmw prompt-sync"
HEADER_RE = re.compile(r"^<!-- " + re.escape(MARK) + r": .* body-sha256=([0-9a-f]{64}) -->\n")


def targets(home: Path):
    codex = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    pi = Path(os.environ.get("PI_CODING_AGENT_DIR",
                             Path(os.environ.get("PI_HOME", home / ".pi")) / "agent"))
    grok = home / ".grok"
    return {
        "codex": (codex, codex / "AGENTS.md"),
        "pi": (pi, pi / "AGENTS.md"),
        "grok": (grok, grok / "AGENTS.md"),
    }


def body_for(host: str) -> str:
    local_path = HOSTS / f"{host}.md"
    local = local_path.read_text().rstrip("\n") if local_path.exists() else ""
    shared = SHARED.read_text()
    return (local + "\n\n" if local else "") + shared


def render(host: str) -> str:
    body = body_for(host)
    digest = hashlib.sha256(body.encode()).hexdigest()
    header = (f"<!-- {MARK}: generated from mmw-v2/prompt/shared.md + mmw-v2/prompt/hosts/{host}.md; "
              f"edit those, not this file. body-sha256={digest} -->\n")
    return header + body


def classify(existing: str) -> str:
    """现有目标文件是什么：ours（上次写的，没人动）/ edited（有人直接改过）/ foreign（不是本脚本写的）。"""
    m = HEADER_RE.match(existing)
    if not m:
        return "foreign"
    body = existing[m.end():]
    return "ours" if hashlib.sha256(body.encode()).hexdigest() == m.group(1) else "edited"


def grok_compat_on(grok_home: Path) -> bool:
    """Grok 的 [compat.claude] agents 开着时，它会把 ~/.claude/CLAUDE.md 再读一遍。Grok 的默认值是开。"""
    cfg = grok_home / "config.toml"
    if not cfg.exists():
        return True
    section = None
    for line in cfg.read_text().splitlines():
        s = line.split("#", 1)[0].strip()
        if s.startswith("["):
            section = s
        elif section == "[compat.claude]" and s.startswith("agents"):
            return s.split("=", 1)[1].strip().lower() == "true"
    return True


def main(argv):
    mode = "check" if "--check" in argv else "write"
    adopt = "--adopt" in argv
    home = Path(os.environ.get("MMW_V2_HOME", Path.home()))
    if not SHARED.exists():
        print(f"缺    {SHARED}", file=sys.stderr)
        return 1
    rc = 0
    for host, (host_home, target) in targets(home).items():
        if not host_home.is_dir():
            print(f"跳过  {target}（host 没装）")
            continue
        want = render(host)
        existing = target.read_text() if target.exists() else None
        state = "absent" if existing is None else classify(existing)
        if existing == want:
            if mode == "write":
                print(f"不变  {target}")
            continue
        if mode == "check":
            why = {"absent": "不存在", "ours": "落后于源", "edited": "被直接改过", "foreign": "不是生成物"}[state]
            print(f"不齐  {target} {why}，跑一次 render.py", file=sys.stderr)
            rc = 1
            continue
        if state == "edited" and not adopt:
            print(f"拒绝  {target} 被直接改过；把改动搬进 mmw-v2/prompt/hosts/{host}.md 或 shared.md，"
                  f"再跑 render.py --adopt", file=sys.stderr)
            rc = 2
            continue
        if state == "foreign" and not adopt:
            print(f"拒绝  {target} 不是 render.py 写的；确认它的内容已在源里，再跑 render.py --adopt",
                  file=sys.stderr)
            rc = 2
            continue
        target.write_text(want)
        print(f"已写  {target}")
    grok_home = targets(home)["grok"][0]
    if grok_home.is_dir() and grok_compat_on(grok_home):
        print(f"注意  {grok_home / 'config.toml'} 的 [compat.claude] agents 不是 false：Grok 会把 "
              f"~/.claude/CLAUDE.md 再读一遍，提示词进两次", file=sys.stderr)
        rc = rc or 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
