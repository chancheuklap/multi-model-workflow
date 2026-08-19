# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2"]
# ///
"""把出包失败现场翻译成带 tier 与根因指纹的 finding。

## 为什么它在技能里

远端失败的根因只存在于构建机的日志里。不翻译，引擎就只能 UNCLASSIFIABLE 交人，自愈闭环断掉。

翻译规则原本整张表都在产品仓库。可其中大半条匹配的是**引擎自己打印的报错文字**——
`ERROR: remote build 缺 RELEASE_REMOTE_HOST`、`Required build tool is unavailable:`、
`Release hook failed:`、`Build command failed:`。于是改一句引擎的报错，就得同时去每个产品仓库
改一遍正则，否则那条根因静默失效。引擎侧的注释甚至专门写了「这两行报错文字是产品仓库
diagnose 的匹配面」——那正是这层耦合的自白。

规则跟着报错走。报错是谁打的，规则就该在谁那里。

## 产品还能加自己的规则

钥匙的 `diagnose_rules` 可以补产品特有的模式，排在通用表**前面**——产品比技能更知道自己那条
日志长什么样。规则表按顺序匹配，第一条命中即定根因。

## 指纹前缀是引擎的分派依据

- `transient:` 无代码可修，直接重跑这一阶段
- `env:` 环境处置（停进程、设变量），交驱动 agent，不派代码修复
- 其余进 P1 修复；P0 硬停
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

LOG_TAIL_CAP = 4000

# 通用规则表：顺序即优先级，第一条命中即定根因。
#
# 每条是 (正则, 名字, 指纹模板, 建议模板)。模板里 {group} 是正则第一个捕获组，
# {product} 是产品名。
RULES: tuple[tuple[str, str, str, str], ...] = (
    # ── 环境：一眼可读，禁止派代码修 ──
    (
        r"ERROR: remote build 缺 RELEASE_REMOTE_HOST",
        "missing_remote_host",
        "env:missing_RELEASE_REMOTE_HOST",
        "钥匙旁边的 remote-build.json 缺 host，或该文件不存在；补好后 resume"
        "（也可在驱动 shell 导出 RELEASE_REMOTE_HOST 临时覆盖）",
    ),
    (
        r"ERROR: remote build 缺 RELEASE_REMOTE_ROOT",
        "missing_remote_root",
        "env:missing_RELEASE_REMOTE_ROOT",
        "钥匙旁边的 remote-build.json 缺 root（安全字符 Windows 绝对路径，"
        "如 D:/agentflow-release-input）；补好后 resume"
        "（也可导出 RELEASE_REMOTE_ROOT 临时覆盖）",
    ),
    (
        r"ERROR: RELEASE_REMOTE_ROOT 必须是安全字符",
        "remote_root_charset",
        "env:invalid_RELEASE_REMOTE_ROOT",
        "远端根只能含盘符与字母数字._-/\\，去掉空格与特殊字符后 resume",
    ),
    (
        r"build machine setup failed|build-cache doctor failed",
        "build_machine_setup_failed",
        "env:build_machine_setup:{product}",
        "读构建机日志里 setup 的输出定位缺什么；常见是产品进程没停。处理完后 resume",
    ),
    (
        r"active product process|仍有活跃开发版|先停止",
        "active_product_process",
        "env:active_product_process:{product}",
        "先停止构建机上该产品的开发版与安装版（前端 watcher、后端、Electron 子进程），"
        "确认无残留后 resume",
    ),
    # ── 瞬态：无代码可修，重跑这一阶段 ──
    (
        # 错误码要加词边界。少了它，`ModuleNotFoundError` 里的 eNotFound 会被
        # 大小写不敏感地当成 ENOTFOUND——一条缺模块的编译失败被判成网络瞬态，
        # 于是引擎一遍遍重跑那个必然失败的阶段，直到轮次预算耗尽。
        r"(\bENOTFOUND\b|\bETIMEDOUT\b|\bECONNRESET\b|\bgetaddrinfo\b"
        r"|registry\.npmjs|\bERR_PNPM_(?:META_)?FETCH\b"
        r"|Couldn't resolve host|TLS handshake timeout|Connection reset by peer)",
        "remote_network_failure",
        "transient:network.build_fetch",
        "构建机网络瞬态失败，重跑该 stage；反复出现则检查构建机代理与镜像",
    ),
    (
        r"ssh: connect to host .*port \d+|kex_exchange_identification"
        r"|Connection timed out during banner exchange"
        r"|scp: .*(?:[Cc]onnection|lost connection|No route to host)|Broken pipe",
        "remote_transport_failure",
        "transient:network.remote_transport",
        "到构建机的 SSH/SCP 传输瞬态失败，重跑该 stage；反复出现则检查构建机可达性",
    ),
    (
        r"ERROR: remote build 超时|ERROR: 无法清除远端上一轮构建产物"
        r"|schtasks.*(?:失败|denied|ERROR)|Access is denied",
        "remote_harness_failure",
        "env:remote_harness",
        "远端调度（计划任务、产物清理、超时）失败，读日志定位构建机环境问题后 resume",
    ),
    # ── 编译与打包：可派代码修 ──
    (
        r"No module named ['\"]([\w.]+)['\"]",
        "frozen_import_missing",
        "missing_module:{group}",
        "把 {group} 补进钥匙 python_backend 的 include_packages 或 include_modules 后重建",
    ),
    (
        r"Required build tool is unavailable: (\S+)",
        "build_tool_missing",
        "env:missing_tool:{group}",
        "在构建机装上 {group} 并加进 PATH 后 resume",
    ),
    (
        r"Build machine is missing (\S+) at|is missing (\S+); an abi3",
        "native_ext_dll_missing",
        "env:missing_dll:{group}",
        "构建机缺这个原生扩展依赖的 DLL。补齐后 resume——缺它出的包，客户跑到那个功能才崩",
    ),
    (
        r"Compiled backend import smoke failed",
        "built_exe_smoke_failed",
        "frozen_smoke:{product}",
        "冻结产物缺动态依赖。按日志里的 ImportError 补钥匙 python_backend 的 include 后重建",
    ),
    (
        r"Compiled backend import smoke timed out",
        "built_exe_smoke_timeout",
        "frozen_smoke_timeout:{product}",
        "自检挂死，通常是某个 import 起了退不掉的后台线程。按日志定位那个模块",
    ),
    (
        r"Release hook failed: (\S+)",
        "release_hook_failed",
        "hook_failed:{group}",
        "读本日志里该钩子的输出定位根因；钩子脚本在产品仓库里，路径见钥匙的 build_hooks",
    ),
    (
        r"Nuitka[-:].*(?:error|FATAL)|FATAL:.*[Nn]uitka",
        "nuitka_build_failed",
        "nuitka_build:{product}",
        "按日志里 Nuitka 的报错修编译输入（钥匙的 include / nofollow / 依赖）后重建",
    ),
    (
        r"electron-builder did not create|Build command failed:",
        "build_step_failed",
        "build_step:{product}",
        "按日志里失败命令的输出修对应的打包步骤",
    ),
)


def read_log_text(path: Path) -> str:
    """按 BOM 认编码读日志。

    Windows PowerShell 5.1 的裸重定向写 UTF-16LE，`Out-File utf8` 带 BOM。固定按 UTF-8 读会把
    UTF-16 的日志读成夹着 NUL 的乱码，于是整张规则表一条都匹配不上——失败现场明明在日志里，
    翻译却全线失效。
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be", errors="replace")
    return raw.decode("utf-8-sig", errors="replace")


def _excerpt_around(text: str, match: re.Match[str], *, radius: int = 280) -> str:
    """命中点附近的短摘录。回执要人一眼读懂，不塞 4000 字的日志尾。"""
    start = max(0, match.start() - radius // 4)
    end = min(len(text), match.end() + radius)
    chunk = text[start:end].strip()
    if start > 0:
        chunk = "…" + chunk
    if end < len(text):
        chunk = chunk + "…"
    return chunk


def _finding(
    *, product: str, name: str, fingerprint: str, locator: str, detail: str,
    remediation: str,
) -> dict:
    return {
        "schema_version": "1",
        "product": product,
        "dimension": "build-log",
        "name": name,
        "status": "fail",
        "tier": "P1",
        "root_cause_fingerprint": fingerprint,
        "locator": locator,
        "detail": detail,
        "remediation": remediation,
    }


def build_log_findings(
    product: str,
    log_path: Path,
    failed_stage: str,
    extra_rules: tuple[tuple[str, str, str, str], ...] = (),
) -> list[dict]:
    """把构建日志翻译成 finding；没日志返回空。

    一条都对不上时仍然产一条 unclassified 的 P1（带日志尾），让驱动 agent 拿着原文判断，
    而不是空手 PAUSE。
    """
    if not log_path.is_file():
        return []
    text = read_log_text(log_path)
    if not text.strip():
        return []
    tail = text[-LOG_TAIL_CAP:]
    for pattern, name, fingerprint_tpl, remediation_tpl in (*extra_rules, *RULES):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        group = next((g for g in (match.groups() or ()) if g), "")
        fingerprint = fingerprint_tpl.format(group=group, product=product)
        # env: / transient: 用短摘录；代码类失败带日志尾，方便直接改。
        detail = (
            _excerpt_around(text, match)
            if fingerprint.startswith(("env:", "transient:"))
            else tail
        )
        return [
            _finding(
                product=product,
                name=name,
                fingerprint=fingerprint,
                locator=str(log_path),
                detail=detail,
                remediation=remediation_tpl.format(group=group, product=product),
            )
        ]
    return [
        _finding(
            product=product,
            name="build_failure_unclassified",
            fingerprint=(
                f"build_failure_unclassified:{product}:{failed_stage or 'build'}"
            ),
            locator=str(log_path),
            detail=tail,
            remediation="按日志尾部定位失败命令；根因不在仓库可修范围时交驱动 agent 处置",
        )
    ]


def stage_log_findings(log_path: Path) -> list[dict] | None:
    """本地 stage（如 verify_key）失败时，它的 stdout 本身就是一份 findings 信封——直接采纳。

    三态：信封在就返回它的合规 findings（可以是空——那是「合同产物在，但没有可派发项」，
    不该再当纯文本翻译一遍出噪声）；不是 JSON（SSH/SCP/调度失败的现场）返回 None，
    交给文本翻译那条支路。
    """
    if not log_path.is_file():
        return None
    try:
        doc = json.loads(read_log_text(log_path))
    except json.JSONDecodeError:
        return None
    if isinstance(doc, dict) and isinstance(doc.get("findings"), list):
        return [
            item
            for item in doc["findings"]
            if isinstance(item, dict)
            and item.get("schema_version") == "1"
            and isinstance(item.get("status"), str)
        ]
    return None


# ── 产品自己的检查支路 ──────────────────────────────────────────────────────────


class BranchError(RuntimeError):
    """某条检查支路没能产出结构化 findings。"""


def _findings_from(doc: object) -> list[dict]:
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict) and isinstance(doc.get("findings"), list):
        return doc["findings"]
    raise BranchError(f"支路输出既不是 findings 列表也不是带 findings 的对象: {type(doc).__name__}")


def run_branch(argv: list[str], *, cwd: Path) -> list[dict]:
    proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True)
    stdout = proc.stdout.strip()
    if not stdout:
        raise BranchError(
            f"支路没有 stdout (rc={proc.returncode}): {' '.join(argv)}\n{proc.stderr[-800:]}"
        )
    try:
        doc = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise BranchError(
            f"支路输出不是合法 JSON (rc={proc.returncode}): {' '.join(argv)}: {exc}\n"
            f"{proc.stderr[-800:]}"
        ) from exc
    return _findings_from(doc)


def _resolve_core_exe(repo_root: Path, pattern: str | None) -> str | None:
    """产品编译产物的位置。写成 glob 是因为 duck 的产物名带版本号。"""
    if not pattern:
        return None
    matches = sorted(repo_root.glob(pattern))
    return str(matches[0]) if len(matches) == 1 else None


def _expand(argv: list[str], core_exe: str | None) -> list[str] | None:
    """支路 argv 里的 `${CORE_EXE}`。产物还没出来时整条支路跳过——拿不到产物的产物检查
    只会产出「文件不存在」这种噪声，盖住真正的根因。"""
    if not any("${CORE_EXE}" in token for token in argv):
        return argv
    if core_exe is None:
        return None
    return [token.replace("${CORE_EXE}", core_exe) for token in argv]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="把出包失败现场翻译成 findings，并跑钥匙声明的检查支路"
    )
    parser.add_argument("--adapter", type=Path, required=True, help="这个产品的钥匙")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    key = json.loads(args.adapter.read_text(encoding="utf-8"))
    product = key["product"]
    repo_root = args.repo_root.resolve()
    extra_rules = tuple(
        (rule["pattern"], rule["name"], rule["fingerprint"], rule["remediation"])
        for rule in key.get("diagnose_rules", [])
    )
    core_exe = _resolve_core_exe(repo_root, key.get("diagnose_core_exe_glob"))

    findings: list[dict] = []
    try:
        for branch in key.get("diagnose_branches", []):
            expanded = _expand(branch, core_exe)
            if expanded is None:
                continue
            findings.extend(run_branch(expanded, cwd=repo_root))
    except BranchError as exc:
        print(f"diagnose_core: 支路失败，无法产出 findings: {exc}", file=sys.stderr)
        return 2

    # 失败现场翻译：引擎把远端构建日志和本地 stage 输出经环境变量交过来。
    failed_stage = os.environ.get("RELEASE_FAILED_STAGE", "")
    build_log = os.environ.get("RELEASE_BUILD_LOG", "")
    stage_log = os.environ.get("RELEASE_STAGE_LOG", "")
    translated: list[dict] = []
    if build_log:
        translated = build_log_findings(
            product, Path(build_log), failed_stage, extra_rules
        )
        findings.extend(translated)
    if stage_log:
        envelope = stage_log_findings(Path(stage_log))
        if envelope is not None:
            findings.extend(envelope)
        elif not translated:
            # 构建日志生成之前的失败（SSH 不通、SCP 上传、调度、wrapper 没起来）只存在于
            # 引擎侧 stage 日志的纯文本里。不翻译，最常见的远端瞬态失败就进不了重跑，
            # 整轮变成「无法分类」交人。
            findings.extend(
                build_log_findings(product, Path(stage_log), failed_stage, extra_rules)
            )

    print(json.dumps({"product": product, "findings": findings}, ensure_ascii=False))
    return 1 if any(item.get("status") == "fail" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
