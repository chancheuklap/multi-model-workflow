#!/usr/bin/env python3
"""P1 失败时，把 findings 写成一份修复简报，交给正在驱动这次出包的 agent。

## 为什么它在技能里

这个文件原本在产品仓库，两个产品仓库各一份、字节完全相同。它引用的是 MMW 自己的东西
（`$MMW_PLUGIN_DIR/plugin/scripts/worker.sh`），而 MMW 把那个插件整个删掉时，够不到住在产品
仓库里的这两份引用——于是 P1 派修静默坏掉，出包一遇到可修的失败就只能停下交人。

它站错了边。引用谁的东西，就该住在谁那里。

## 它现在怎么工作

没有「派一个 agent 去修」这条路了，因为技能不再自带 worker。但**驱动这次出包的本来就是一个
会写代码的 agent**——`driving.md` 里 `PAUSED:needs-context` 那一节写的就是「你自己能处理的
就自己处理」。所以这里不再试图召人，而是：

1. 把 findings 写成一份人和 agent 都读得懂的简报，落到本轮的产物目录；
2. 打印简报路径；
3. 非零退出。

引擎看到非零退出就 `PAUSED:needs-context` 并保留现场。驱动 agent 读 receipt、按简报改代码、
提交到当前分支、`resume`。

**这条路上必须提交。** 远端构建取的是 `git archive HEAD`，改动留在工作树到不了构建机——
不提交就等于没改，而下一轮会用同一份代码再失败一次。（`resume` 看见 HEAD 变了会重验全部
stage，这正是要的。）

`RELEASE_FIX_BACKEND` 是逃生口，走的是另一条路：那时引擎在动作返回后收集工作树改动、过路径闸、
统一提交，所以交给后端的简报说的是「不要自己提交」。两份简报的措辞按路走，不能混。
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

BRIEF_NAME = "release-fix-brief.md"


def _die(message: str) -> int:
    print(f"fix_dispatch: {message}", file=sys.stderr)
    return 1


def _load_findings(path: str) -> list[dict]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    findings = doc.get("findings", doc) if isinstance(doc, dict) else doc
    return findings if isinstance(findings, list) else [findings]


_AGENT_RULES = [
    "- 只改这把钥匙 `editable_paths` 允许的文件。碰受保护路径的改动引擎会拒。",
    "- 改完**提交到当前分支**，再 `resume`。远端构建取的是 `git archive HEAD`，"
    "改动留在工作树到不了构建机——不提交等于没改，下一轮用同一份代码再失败一次。",
    "- 同一个根因修第二次还不过，停下交人，不要继续循环。",
]

_BACKEND_RULES = [
    "- 只改路径闸允许的文件。引擎会拒绝任何越界改动。",
    "- 改完把改动留在工作树——**不要 git add，不要 git commit**。",
    "  这条路上引擎是唯一的 committer，它会统一过路径闸再提交。",
    "- 同一个根因修第二次还不过，停下交人，不要继续循环。",
]


def brief(findings: list[dict], *, for_backend: bool = False) -> str:
    """写给谁，规则就按谁那条路写。

    默认这份是给驱动 agent 的：它在引擎之外，所以必须自己提交。给外部后端的那份相反——
    引擎会在动作返回后收工作树、过路径闸、统一提交。措辞混了，改动要么到不了构建机，
    要么绕过路径闸。
    """
    lines = [
        "# Release fix brief",
        "",
        "出包卡在一条可修的失败上。按下面的 findings 改。",
        "",
        "规则：",
        "",
        *(_BACKEND_RULES if for_backend else _AGENT_RULES),
        "",
        "## Findings",
        "",
    ]
    for finding in findings:
        fingerprint = finding.get("root_cause_fingerprint") or ""
        lines.append(
            f"- [{finding.get('tier') or '?'}] "
            f"{finding.get('name')} ({fingerprint}): {finding.get('detail') or ''}"
        )
        if finding.get("remediation"):
            lines.append(f"  建议：{finding['remediation']}")
    return "\n".join(lines) + "\n"


def _brief_path(repo_root: Path) -> Path:
    """简报落在 findings 旁边。

    那是引擎本轮的产物目录，receipt 已经会指向它，所以人和 agent 从 receipt 一路走过来就能
    看见这份简报。不写临时目录：临时目录里的东西找不到，而这份简报的全部作用就是被读到。
    """
    findings = os.environ.get("RELEASE_FIX_FINDINGS", "").strip()
    if findings:
        return Path(findings).parent / BRIEF_NAME
    return repo_root / BRIEF_NAME


def _head_sha(repo_root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _unwind_worker_commits(repo_root: Path, start_sha: str) -> int:
    """把外部 worker 自建的提交回退成工作树改动，交回引擎统一过路径闸再提交。

    引擎（cmd_dispatch_direct）是唯一 committer：它在 fix 动作返回后收集工作树候选、过路径闸
    才提交。但外部 worker 可能逐步自行提交；若把这些提交留在功能分支，引擎看到干净树会误判
    「无改动」，同时已提交（可能触碰计费 / 迁移等受保护路径）的改动绕过路径闸。

    所以 dispatch 返回后**无论退出码**都确定性地 reset --mixed 回 start_sha：保留全部改动、
    清空暂存、不动 untracked。**失败路径尤其必须回退**——worker 修到一半失败时若已提交，
    这些未过路径闸的提交会留在 HEAD，人工 resume 时被误采纳为基线出货。
    """
    current = _head_sha(repo_root)
    if current is None:
        return _die("dispatch 后无法解析 HEAD，无法回退 worker 提交")
    if current == start_sha:
        return 0
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "reset", "--mixed", start_sha],
        capture_output=True,
        text=True,
    )
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        return _die(f"无法把 worker 提交回退到 {start_sha}，保留现场交引擎")
    return 0


def _run_backend(
    argv: list[str], repo_root: Path, ref_file: str | None, brief_path: Path
) -> int:
    start_sha = _head_sha(repo_root)
    if start_sha is None:
        return _die("dispatch 前无法解析 HEAD")

    # 后端的 argv 原样跑，简报路径走环境变量交给它：往 argv 尾部塞一个参数会改掉
    # 已经在用这个逃生口的命令行。
    env = {**os.environ, "RELEASE_FIX_BRIEF": str(brief_path)}
    proc = subprocess.run(
        argv, cwd=str(repo_root), capture_output=True, text=True, env=env
    )
    sys.stderr.write(proc.stderr)

    session = ""
    for line in proc.stdout.splitlines():
        if line.startswith("SESSION="):
            session = line[len("SESSION=") :].strip()
            if session == "unknown":
                session = ""
            break
    if ref_file:
        Path(ref_file).write_text(session, encoding="utf-8")

    unwind_rc = _unwind_worker_commits(repo_root, start_sha)
    if unwind_rc != 0:
        # 回退本身失败（无法 reset）比 worker 失败更严重：worker 提交仍卡 HEAD，
        # 必须 fail-loud 交人，不能用 worker 退出码掩盖。
        return unwind_rc
    return proc.returncode


def main() -> int:
    findings_path = os.environ.get("RELEASE_FIX_FINDINGS")
    ref_file = os.environ.get("RELEASE_FIX_WORKER_REF_FILE")
    repo_root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        ).stdout.strip()
        or "."
    )

    if not findings_path or not Path(findings_path).is_file():
        return _die("RELEASE_FIX_FINDINGS 没给，或不是一个文件")

    findings = _load_findings(findings_path)
    override = os.environ.get("RELEASE_FIX_BACKEND")
    path = _brief_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(brief(findings, for_backend=bool(override)), encoding="utf-8")

    if override:
        return _run_backend(shlex.split(override), repo_root, ref_file, path)

    if ref_file:
        Path(ref_file).write_text("", encoding="utf-8")
    print(f"FIX-BRIEF={path}")
    print(
        "没有配自动修复后端，这条 P1 交给正在驱动出包的 agent：读上面那份简报，改代码，"
        "提交到当前分支，然后 resume。"
        "要接一个外部修复后端就设 RELEASE_FIX_BACKEND。",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
