#!/usr/bin/env python3
"""界面 QA 开跑之前的事实收集。

技能正文原先用五步分别跑五件事：查工作树、查依赖、找 product 与四份文件、
校验接线、跑设计系统格式校验。五件都是机械判定，agent 跑它们只是照抄命令，
中间还要读四张表才知道每种结果怎么走。这里一次跑完，打印一份事实 JSON。

这里只给事实，不做决策。缺了可访问性规则引擎，这里说「缺，声明的降级行为是
degrade，影响 A2」；跳不跳、报告头怎么写，由技能正文那张表决定。product 选哪
一个也不在这里——那要问用户，命令问不了。

输出到标准输出的永远是一份 JSON。退出码：0 收集完成（就算里面全是坏消息），
1 连事实都取不到（不在 git 仓库、读不了声明），2 用法错。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEPS_JSON = HERE / "deps.json"
FORWARDER = HERE / "mmw-ui-qa"


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    except (OSError, ValueError) as exc:
        return 127, "", str(exc)
    return p.returncode, p.stdout, p.stderr


def git_facts() -> dict[str, Any]:
    code, out, err = run(["git", "status", "--porcelain"])
    if code != 0:
        return {"inRepo": False, "error": err.strip()}
    dirty = [line for line in out.splitlines() if line.strip()]
    return {"inRepo": True, "clean": not dirty, "uncommitted": dirty}


def dep_facts() -> dict[str, Any]:
    """每个能力装没装，以及声明里写的缺失行为。降级映射来自 deps.json，不在这里写死。"""
    try:
        declared = json.loads(DEPS_JSON.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"读不出依赖声明 {DEPS_JSON}：{exc}")

    code, out, err = run(["bash", str(HERE / "install-ui-qa-deps.sh"), "--check"])
    report = (out + err).strip()

    caps = []
    for entry in declared["packages"]:
        # --check 缺哪个就点名哪个包。这里按包名回读，不另跑一遍装配检查。
        present = entry["package"] not in report if code != 0 else True
        caps.append(
            {
                "capability": entry["capability"],
                "package": entry["package"],
                "present": present,
                "onMissing": entry["missing"],
                "skips": entry.get("skips", []),
            }
        )

    missing = [c for c in caps if not c["present"]]
    return {
        "ok": code == 0,
        "capabilities": caps,
        "stopMissing": [c["capability"] for c in missing if c["onMissing"] == "stop"],
        "skipChecks": sorted({s for c in missing for s in c["skips"]}),
        "raw": report,
    }


def artifact_path(category: str, sub: str) -> str | None:
    code, out, _ = run(["mmw", "artifact", "path", category, "--sub", sub])
    return out.strip() if code == 0 and out.strip() else None


def product_facts(product: str | None) -> dict[str, Any]:
    """列出已有 product，以及给定 product 的四份文件在不在。"""
    probe = artifact_path("ui-qa-wiring", "probe.json")
    if not probe:
        return {"wiringRootReadable": False, "products": []}

    root = Path(probe).parent
    products = []
    if root.is_dir():
        for f in sorted(root.glob("*.json")):
            try:
                name = json.loads(f.read_text()).get("product")
            except (OSError, json.JSONDecodeError):
                name = None
            products.append({"product": name, "wiring": str(f), "readable": name is not None})

    facts: dict[str, Any] = {"wiringRootReadable": True, "products": products}
    if not product:
        return facts

    wiring = artifact_path("ui-qa-wiring", f"{product}.json")
    thresholds = artifact_path("ui-criteria", "thresholds.json")
    usability = artifact_path("ui-criteria", f"products/{product}.md")
    facts["selected"] = {
        "product": product,
        "wiring": file_fact(wiring),
        "thresholds": file_fact(thresholds),
        "usability": file_fact(usability),
    }
    return facts


def file_fact(path: str | None) -> dict[str, Any]:
    if not path:
        return {"path": None, "exists": False}
    return {"path": path, "exists": Path(path).is_file()}


def wiring_lint(path: str) -> dict[str, Any]:
    code, out, err = run(["python3", str(HERE / "wiring_lint.py"), path])
    return {"ok": code == 0, "output": (err + out).strip()}


def design_system_facts(wiring_path: str, repo_root: Path) -> dict[str, Any]:
    try:
        wiring = json.loads(Path(wiring_path).read_text())
    except (OSError, json.JSONDecodeError):
        return {"declared": None, "reason": "接线文件读不出来，先看 wiringLint"}

    declared = wiring.get("designSystem")
    if not declared:
        return {"declared": None}

    path = (repo_root / declared).resolve()
    if not path.is_file():
        return {"declared": declared, "path": str(path), "exists": False}

    code, out, err = run([str(FORWARDER), "design-lint", str(path)])
    raw = (out + err).strip()
    try:
        findings = json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        # 校验器没吐 JSON。技能那张表对这种情况有一行：继续，报告头写「本次没 lint 判据」。
        return {
            "declared": declared,
            "path": str(path),
            "exists": True,
            "linted": False,
            "raw": raw,
        }

    items = findings if isinstance(findings, list) else findings.get("findings", [])
    sev = [str(i.get("severity", "")) for i in items if isinstance(i, dict)]
    return {
        "declared": declared,
        "path": str(path),
        "exists": True,
        "linted": code == 0 or bool(items),
        "errors": sev.count("error"),
        "warnings": sev.count("warning"),
        "findings": items,
    }


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        print("用法：mmw-ui-qa preflight [<product-id>]", file=sys.stderr)
        return 2
    product = argv[0] if argv else None

    git = git_facts()
    if not git["inRepo"]:
        print(json.dumps({"error": "不在 git 仓库里", "detail": git.get("error")},
                         ensure_ascii=False, indent=2))
        return 1

    code, root_out, _ = run(["git", "rev-parse", "--show-toplevel"])
    repo_root = Path(root_out.strip()) if code == 0 else Path.cwd()

    facts: dict[str, Any] = {
        "git": git,
        "deps": dep_facts(),
        "criteria": product_facts(product),
    }

    selected = facts["criteria"].get("selected")
    if selected and selected["wiring"]["exists"]:
        wiring_path = selected["wiring"]["path"]
        facts["wiringLint"] = wiring_lint(wiring_path)
        facts["designSystem"] = design_system_facts(wiring_path, repo_root)

    print(json.dumps(facts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
