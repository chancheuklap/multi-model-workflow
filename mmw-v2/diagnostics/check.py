#!/usr/bin/env python3
"""对刚改过的文件跑一遍检查器，把问题交回给 agent。

五个宿主共用这一个入口，触发方式各不相同：Claude Code 与 Codex 从 PostToolUse hook
调它，Cursor 从 postToolUse 调它，Grok 从 Stop hook 调它，Pi 从扩展的 tool_result
调它。同一个仓库、同一份检查器表、同一份规则配置，所以五家看到的诊断是同一套。
CI 也调它，所以编辑时看到的和门禁判定的也是同一套。

为什么不自己写一个 LSP 客户端：跳转定义、找引用、找实现、列符号这几件事 Serena 已经
在五个宿主上都给了。缺的只有「编辑之后这个文件错没错」。而 pyright 的命令行和它的
language server 是同一个引擎，命令行跑出来的诊断和 LSP 推的是同一批——为这一件事再
维护一套 JSON-RPC 进程管理，多出来的只有故障点。

只读：跑检查器，读输出。不改文件。

    check.py --repo <仓库根> [--changed-only] [--json] <文件>...
    check.py --doctor            列出每个检查器解析到哪个可执行文件
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_DIR = HERE / "config"

# 语言工具的清单与安装都在 mmw-v2/tools/，不在这里：serena 的语言服务器用的是同一份
# 安装（pyright 那一条同时是命令行检查器和语言服务器），清单分两处就会出现同一个引擎
# 两个版本。
TOOLS = HERE.parent / "tools"
RULES = TOOLS / "tools.json"

# 装出来的东西在这两个目录里。分两个不是历史包袱：uv 装的是真的可执行文件，可以集中
# 放；pnpm 装的是按 $0 算相对路径的脚本外壳，软链到别处它就找不到自己的包（实测
# oxlint 会去 tools/.pnpm 找）。所以就地用，不搬。
TOOL_DIRS = (
    TOOLS / "bin",
    TOOLS / "node" / "node_modules" / ".bin",
)

CHECK_TIMEOUT = 120
MAX_LINES = 40


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_checkers() -> list[dict]:
    """从工具清单里挑出有 checker 这一段的，并把工具 id 带进去。

    清单里一个工具可以既是检查器又是语言服务器（pyright 就是），这里只取前者那一段。
    """
    out = []
    for tool in read_json(RULES).get("tools", []):
        spec = tool.get("checker")
        if not spec:
            continue
        out.append({"id": tool["id"], **spec})
    return out


def owning_workspace(repo: Path, rel_file: str, marker: str | None) -> str:
    """从文件往上找最近的工作区标记。一个仓库里可以有三个 Electron 壳各带一份
    node_modules，检查器必须用文件所属那一个，不是仓库根那一个。"""
    if not marker:
        return "."
    current = (repo / rel_file).parent
    while True:
        if (current / marker).is_file():
            return str(current.relative_to(repo)) or "."
        if current == repo or repo not in current.parents:
            return "."
        current = current.parent


def resolve_checker(repo: Path, workspace: str, checker: dict) -> str:
    """按固定的三段顺序找可执行文件：仓库自带的 → 我们装的 → PATH 上的。

    仓库自带的排第一：那是这个仓库锁定的版本，也是它的 CI 用的那一个。用别的版本，
    编辑时看到的错和门禁判定的对不上。2026-08-10 实测过一次：全局 pyright 1.1.411、
    仓库 .venv 里 1.1.409，两边结论不同。

    我们装的排第二、PATH 排第三：tools/ 由安装器保证存在且是最新稳定版，PATH 上那份
    是这台机器碰巧有什么就是什么。宁可用一份我们说得清来历的。
    """
    from shutil import which

    for rel in checker.get("project_bin", []):
        candidate = repo / workspace / rel
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    name = checker.get("bin", "")
    if not name:
        return ""
    for directory in TOOL_DIRS:
        ours = directory / name
        if ours.is_file() and os.access(ours, os.X_OK):
            return str(ours)
    return which(name) or ""


def parse_pyright_json(raw: str, repo: Path) -> list[str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [line for line in raw.splitlines() if line.strip()][:MAX_LINES]
    out = []
    for item in payload.get("generalDiagnostics", []):
        if item.get("severity") not in ("error", "warning"):
            continue
        start = item.get("range", {}).get("start", {})
        path = item.get("file", "")
        try:
            path = str(Path(path).relative_to(repo))
        except ValueError:
            pass
        message = " ".join(str(item.get("message", "")).split())
        rule = item.get("rule", "")
        suffix = f" ({rule})" if rule else ""
        out.append(
            f"{path}:{start.get('line', 0) + 1}:{start.get('character', 0) + 1}: "
            f"{item.get('severity')} {message}{suffix}"
        )
    return out


def parse_concise(raw: str, _repo: Path) -> list[str]:
    lines = []
    for line in raw.splitlines():
        text = line.strip()
        if not text or text.startswith("Found ") or text.startswith("["):
            continue
        if text.startswith("All checks passed"):
            continue
        lines.append(text)
    return lines


PARSERS = {"pyright_json": parse_pyright_json, "concise": parse_concise}


def scan_patterns(repo: Path, checker: dict, rel_file: str) -> list[str]:
    """明文密钥：纯正则，不需要任何外部命令，所以每个改过的文件都扫。"""
    try:
        text = (repo / rel_file).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    compiled = [re.compile(p, re.MULTILINE) for p in checker.get("patterns", [])]
    out = []
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern in compiled:
            if pattern.search(line):
                out.append(f"{rel_file}:{number}:1: error 这一行像是明文凭证，移到密钥文件里")
                break
    return out


def run_checker(repo: Path, workspace: str, checker: dict, rel_file: str) -> list[str]:
    if checker.get("kind") == "patterns":
        return scan_patterns(repo, checker, rel_file)

    executable = resolve_checker(repo, workspace, checker)
    if not executable:
        # 缺检查器不能静默：没跑跟跑完没问题看起来一模一样，而前者是漏检。
        return [f"（{checker['id']} 没装，这一类问题这次没有检查。跑 mmw-v2/install.sh 装上）"]

    workdir = repo / workspace
    try:
        target = str((repo / rel_file).relative_to(workdir))
    except ValueError:
        target = str(repo / rel_file)

    command = [executable, *checker.get("file_args", [])]
    if checker.get("config"):
        command += [checker["config_flag"], str(CONFIG_DIR / checker["config"])]
    command.append(target)

    # tools/bin 放进 PATH：检查器会自己去找同伴程序，而工作目录是被检查的仓库，
    # 那里没有我们装的东西。oxlint 的类型感知规则要调 tsgolint，找不到不会报错，
    # 只是那一类规则安静地不生效。
    env = dict(os.environ)
    ours = os.pathsep.join(str(d) for d in TOOL_DIRS)
    env["PATH"] = f"{ours}{os.pathsep}{env.get('PATH', '')}"

    try:
        result = subprocess.run(
            command,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"（{checker['id']} 没能跑起来：{exc}）"]
    raw = f"{result.stdout}\n{result.stderr}".strip()
    parser = PARSERS.get(checker.get("parse", "concise"), parse_concise)
    return parser(raw, repo)


LINE_PATTERN = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+):")


def changed_lines(repo: Path, rel_file: str) -> set[int] | None:
    """这个文件相对 HEAD 改了哪几行。返回 None 表示拿不到，调用方据此不过滤。

    为什么要这一层：一个有历史类型债的文件，每次编辑都会把那几十条旧账全报一遍。
    报三次之后没有人会再看它，这个通道就废了。只报落在改动行上的，历史债由专门的
    一轮去清。
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "diff", "--unified=0", "HEAD", "--", rel_file],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    diff = result.stdout
    if not diff.strip():
        # 相对 HEAD 没有差异。可能是未跟踪的新文件——那种情况整份都是新的，不过滤。
        tracked = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--error-unmatch", rel_file],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return set() if tracked.returncode == 0 else None
    lines: set[int] = set()
    for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.MULTILINE):
        start = int(hunk.group(1))
        count = int(hunk.group(2) or 1)
        lines.update(range(start, start + count))
    return lines


def filter_to_changed(entries: list[str], rel_file: str, allowed: set[int] | None) -> list[str]:
    if allowed is None:
        return entries
    kept = []
    for entry in entries:
        found = LINE_PATTERN.match(entry)
        if not found:
            kept.append(entry)
            continue
        if not entry.startswith(rel_file):
            kept.append(entry)
            continue
        if int(found.group("line")) in allowed:
            kept.append(entry)
    return kept


def applies_to(checker: dict, rel_file: str) -> bool:
    extensions = checker.get("extensions")
    if extensions is None:
        return True
    return any(rel_file.endswith(ext) for ext in extensions)


def check(repo: Path, files: list[str], changed_only: bool = False) -> dict:
    checkers = load_checkers()
    findings: dict[str, list[str]] = {}
    outside: list[str] = []
    suppressed = 0
    # 有没有真的按改动行过滤过。不是 git 仓库、或者文件还没提交过时拿不到改动行，
    # 那时报的是整份文件——说成「改动行上共 N 条」就是假话。
    filtered = False

    for raw_file in files:
        path = Path(raw_file)
        if not path.is_absolute():
            path = repo / raw_file
        # 两边都 resolve 再比。macOS 上 /tmp 是指向 /private/tmp 的软链，只 resolve
        # 一边的话 relative_to 会失败，于是这个文件被跳过——什么都不报，看起来跟
        # 检查通过一模一样。
        path = path.resolve()
        if not path.is_file():
            continue
        try:
            rel_file = str(path.relative_to(repo))
        except ValueError:
            # 不在这个仓库里的文件不是"没问题"，是我们没法检查。说出来。
            outside.append(str(path))
            continue

        allowed = changed_lines(repo, rel_file) if changed_only else None
        filtered = filtered or allowed is not None

        for checker in checkers:
            if not applies_to(checker, rel_file):
                continue
            workspace = owning_workspace(repo, rel_file, checker.get("workspace_marker"))
            lines = run_checker(repo, workspace, checker, rel_file)
            if not lines:
                continue
            kept = filter_to_changed(lines, rel_file, allowed)
            suppressed += len(lines) - len(kept)
            if kept:
                findings.setdefault(checker["id"], []).extend(kept)

    return {
        "findings": findings,
        "suppressed": suppressed,
        "outside": outside,
        "filtered": filtered,
    }


def render(report: dict) -> int:
    findings = report["findings"]
    suppressed = report.get("suppressed", 0)
    scope = "改动行上" if report.get("filtered") else ""
    for path in report.get("outside", []):
        print(f"（{path} 不在这个仓库里，没有检查）", file=sys.stderr)
    if not findings:
        # 只在真的压掉了东西时才提一句，否则每次干净通过都多一行噪音。
        if suppressed:
            print(
                f"（{scope}没有问题。这些文件另有 {suppressed} 条既有问题，不是这次引入的。）",
                file=sys.stderr,
            )
        return 0
    total = 0
    for checker_id, lines in findings.items():
        shown = lines[:MAX_LINES]
        total += len(lines)
        print(f"{checker_id}:", file=sys.stderr)
        for line in shown:
            print(f"  {line}", file=sys.stderr)
        if len(lines) > len(shown):
            print(f"  （还有 {len(lines) - len(shown)} 条未显示）", file=sys.stderr)
    tail = f"，另有 {suppressed} 条既有问题不是这次引入的" if suppressed else ""
    print(f"{scope}共 {total} 条{tail}。先看一遍再继续。", file=sys.stderr)
    return 2


def doctor(repo: Path) -> int:
    """每个检查器现在会用哪个可执行文件。装完之后应该一个 missing 都没有。"""
    checkers = load_checkers()
    status = 0
    for checker in checkers:
        if checker.get("kind") == "patterns":
            print(f"内置  {checker['id']}：不需要外部命令")
            continue
        found = resolve_checker(repo, ".", checker)
        if not found:
            print(f"缺    {checker['id']}：装不上就没有这一类诊断", file=sys.stderr)
            status = 1
            continue
        # 先判 tools/：mmw-v2 本身就在一个仓库里，先判仓库的话我们自己装的那份
        # 会被认成"仓库自带"。
        if any(found.startswith(str(d)) for d in TOOL_DIRS):
            where = "我们装的"
        elif found.startswith(str(repo)):
            where = "仓库自带"
        else:
            where = "PATH"
        print(f"可用  {checker['id']}：{found}（{where}）")
    return status


def main(argv: list[str]) -> int:
    repo = Path.cwd()
    as_json = False
    changed_only = False
    as_doctor = False
    files: list[str] = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--repo":
            repo = Path(args.pop(0)).resolve()
        elif arg == "--json":
            as_json = True
        elif arg == "--changed-only":
            changed_only = True
        elif arg == "--doctor":
            as_doctor = True
        else:
            files.append(arg)

    if as_doctor:
        return doctor(repo)
    if not files:
        return 0

    report = check(repo, files, changed_only=changed_only)
    if as_json:
        print(json.dumps(report, ensure_ascii=False))
        return 0
    return render(report)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
