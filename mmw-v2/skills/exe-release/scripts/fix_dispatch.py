#!/usr/bin/env python3
"""P1 失败时，把 findings 写成一份修复简报，交给正在驱动这次出包的 agent。

## 为什么它在技能里

这个文件原本在产品仓库，两个产品仓库各一份、字节完全相同。它引用的是 MMW 自己的东西
（`$MMW_PLUGIN_DIR/plugin/scripts/worker.sh`），而 MMW 把那个插件整个删掉时，够不到住在产品
仓库里的这两份引用——于是 P1 派修静默坏掉，出包一遇到可修的失败就只能停下交人。

它站错了边。引用谁的东西，就该住在谁那里。

## 它现在怎么工作

没有「派一个 agent 去修」这条路——技能不再自带 worker.sh，也不再让钥匙声明一个可插拔的
修复执行器。**驱动这次出包的本来就是一个会写代码的 agent**——`driving.md` 里
`PAUSED:needs-context` 那一节写的就是「你自己能处理的就自己处理」。所以这里只做三件事：

1. 把 findings 写成一份人和 agent 都读得懂的简报，落到本轮的产物目录；
2. 打印简报路径；
3. 非零退出。

引擎看到非零退出就 `PAUSED:needs-context` 并保留现场。驱动 agent 读 receipt、按简报改代码、
提交到当前分支、`resume`。

**这条路上必须提交。** 远端构建取的是 `git archive HEAD`，改动留在工作树到不了构建机——
不提交就等于没改，而下一轮会用同一份代码再失败一次。（`resume` 看见 HEAD 变了会重验全部
stage，这正是要的。）
"""

from __future__ import annotations

import json
import os
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
    "- **Commit to the current branch**, then `resume`. The remote build takes `git archive HEAD`; "
    "edits left in the working tree never reach the build machine, so not committing means not changing, "
    "and the next round fails on the same code.",
    "- If the same root cause survives a second fix, stop and hand it to a human. Do not keep looping.",
]


def brief(findings: list[dict]) -> str:
    """写给驱动这次出包的 agent 的简报：它在引擎之外，所以必须自己提交。"""
    lines = [
        "# Release fix brief",
        "",
        "The release is stuck on a fixable failure. Fix it from the findings below.",
        "",
        "Rules:",
        "",
        *_AGENT_RULES,
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
            lines.append(f"  Suggested fix: {finding['remediation']}")
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


def main() -> int:
    findings_path = os.environ.get("RELEASE_FIX_FINDINGS")
    repo_root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        ).stdout.strip()
        or "."
    )

    if not findings_path or not Path(findings_path).is_file():
        return _die("RELEASE_FIX_FINDINGS is unset, or is not a file")

    findings = _load_findings(findings_path)
    path = _brief_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(brief(findings), encoding="utf-8")

    print(f"FIX-BRIEF={path}")
    print(
        "This P1 goes to the agent driving the release: read the brief above, change the code, "
        "commit to the current branch, then resume.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
