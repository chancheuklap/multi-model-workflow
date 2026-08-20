# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2"]
# ///
"""出包前把钥匙对着仓库核一遍。

这一步在 Mac 上跑，秒级完成，挡的是「钥匙里写错一个路径，四十分钟编译之后才知道」。
构建机上的一轮很贵：传源码、装依赖、编译、打包，中间任何一步炸掉，拿回来的都是一句
文件不存在。而这些错在出发前全都看得见。

**只查机器能直接判定的事实**：钥匙点到的文件在不在、声明之间自不自洽。包能不能编出来、
产物对不对，那是构建机的事，不在这里假装。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders import nuitka  # noqa: E402
from release_contracts import ReleaseAdapterManifest  # noqa: E402


def _finding(
    product: str,
    dimension: str,
    name: str,
    locator: str,
    detail: str,
    remediation: str,
) -> dict:
    return {
        "schema_version": "1",
        "product": product,
        "dimension": dimension,
        "name": name,
        "status": "fail",
        # P0：钥匙不对，重跑多少次都是同一个结果，自动修复也没有可修的东西。
        "tier": "P0",
        "root_cause_fingerprint": f"key:{name}:{locator}",
        "locator": locator,
        "detail": detail,
        "remediation": remediation,
    }


# argv 里的仓库相对脚本按扩展名认，不猜顶级目录——钩子放在哪个目录是产品自己的事。
# 含 ${...} 的是引擎注入的路径（技能自己的脚本、本轮工作目录），在 Mac 上还没有值，跳过。
_SCRIPT_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-./]+\.(?:py|mjs|cjs|js|ps1|sh)$")


def _iter_argvs(manifest: ReleaseAdapterManifest) -> list[tuple[str, list[str]]]:
    """钥匙里全部会被执行的 argv。"""
    argvs: list[tuple[str, list[str]]] = [
        *((f"stages[{stage.name}]", stage.run) for stage in manifest.stages),
        ("diagnose", manifest.diagnose),
        *(
            (f"diagnose_branches[{index}]", argv)
            for index, argv in enumerate(manifest.diagnose_branches)
        ),
        ("toolchain", manifest.toolchain),
    ]
    for field in ("derive", "fix_executor", "post_fix_gate", "event_sink"):
        value = getattr(manifest, field)
        if value:
            argvs.append((field, value))
    if manifest.build_machine is not None:
        for field in ("setup", "teardown"):
            value = getattr(manifest.build_machine, field)
            if value:
                argvs.append((f"build_machine.{field}", value))
    for field, value in manifest.build_hooks.model_dump().items():
        if value:
            argvs.append((f"build_hooks.{field}", value))
    return argvs


def _electron_builder_output_dir(config: Path) -> str | None:
    """从 electron-builder.yml 读 directories.output（行级解析，读不出返回 None）。"""
    try:
        lines = config.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    in_directories = False
    for line in lines:
        stripped = line.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        if not stripped.startswith((" ", "\t")):
            in_directories = stripped.strip() == "directories:"
            continue
        if in_directories and stripped.strip().startswith("output:"):
            return stripped.split(":", 1)[1].strip().strip("'\"").rstrip("/")
    return None


def _expand(manifest: ReleaseAdapterManifest, value: str) -> str | None:
    backend = manifest.python_backend
    try:
        return nuitka.expand(
            value,
            desktop_dir=manifest.build_target.desktop_dir,
            build_root=backend.build_root if backend else None,
        )
    except ValueError:
        return None


def verify(manifest: ReleaseAdapterManifest, repo_root: Path, adapter: Path) -> list[dict]:
    product = manifest.product
    backend = manifest.python_backend
    if backend is None:  # schema_version=2 的合同已经挡住，这里是防御
        raise ValueError("verify_key 只认声明了 python_backend 的钥匙")
    findings: list[dict] = []

    def missing(dimension: str, name: str, rel: str, what: str) -> None:
        findings.append(
            _finding(
                product,
                dimension,
                name,
                rel,
                f"{what}在仓库里不存在: {rel}",
                f"改钥匙指向真实路径，或把 {what}加进仓库",
            )
        )

    # ── 钥匙点到的每个路径 ──────────────────────────────────────────────────
    for target in backend.targets:
        rel = _expand(manifest, target.entrypoint)
        if rel is None or not (repo_root / rel).is_file():
            missing("compile", "entrypoint_missing", target.entrypoint, "编译入口")

    if backend.icon:
        rel = _expand(manifest, backend.icon)
        if rel is None or not (repo_root / rel).is_file():
            missing("compile", "icon_missing", backend.icon, "图标")

    for entry in backend.include_data_dirs:
        rel = _expand(manifest, entry.source)
        if rel is None or not (repo_root / rel).is_dir():
            missing("compile", "data_dir_missing", entry.source, "要打进包的数据目录")

    if manifest.build_target.desktop_dir:
        if not (repo_root / manifest.build_target.desktop_dir).is_dir():
            missing(
                "electron",
                "desktop_dir_missing",
                manifest.build_target.desktop_dir,
                "Electron 应用目录",
            )

    if manifest.protection_source:
        if not (repo_root / manifest.protection_source).is_file():
            missing("guard", "protection_source_missing", manifest.protection_source, "保护规则源")

    # ── 声明之间自不自洽 ────────────────────────────────────────────────────
    if backend.smoke is not None:
        exes = {target.exe for target in backend.targets}
        if backend.smoke.exe not in exes:
            findings.append(
                _finding(
                    product,
                    "compile",
                    "smoke_exe_not_built",
                    backend.smoke.exe,
                    f"自检要跑 {backend.smoke.exe}，但编译产物只有 {sorted(exes)}",
                    "把 smoke.exe 改成 targets 里真会编出来的那一个",
                )
            )

    # 编译产物之间不能重名：同一个 output_dir 里后编的直接盖掉先编的，
    # 而两次编译都报成功，少掉的那个要到 app 起不来才发现。
    seen: dict[str, str] = {}
    for target in backend.targets:
        if target.exe in seen:
            findings.append(
                _finding(
                    product,
                    "compile",
                    "duplicate_output_filename",
                    target.exe,
                    f"target {seen[target.exe]} 与 {target.name} 输出同一个文件名，后者会盖掉前者",
                    "给每个 target 一个自己的 exe 名",
                )
            )
        seen[target.exe] = target.name

    try:
        nuitka.validate_import_plan(backend)
    except ValueError as exc:
        findings.append(
            _finding(
                product,
                "compile",
                "nofollow_blocks_smoke_module",
                "python_backend.nofollow_imports",
                str(exc),
                "把被挡的模块从 nofollow_imports 里去掉，或从 smoke.modules 里去掉",
            )
        )

    # ── 钥匙点到的每一条命令，里面的仓库脚本在不在 ──────────────────────────
    #
    # 钩子路径拼错一个字母，要到构建机跑到那一步才知道——而那时候已经编了四十分钟。
    repo_resolved = repo_root.resolve()
    for label, argv in _iter_argvs(manifest):
        for token in argv:
            if "${" in token or token.startswith("/") or not _SCRIPT_TOKEN_RE.match(token):
                continue
            candidate = (repo_root / token).resolve()
            if not candidate.is_relative_to(repo_resolved):
                findings.append(
                    _finding(
                        product,
                        "key",
                        "argv_script_outside_repo",
                        label,
                        f"{label} 引用越出仓库根: {token}",
                        "改成仓库内的相对路径",
                    )
                )
            elif not candidate.is_file():
                findings.append(
                    _finding(
                        product,
                        "key",
                        "argv_script_missing",
                        label,
                        f"{label} 引用的仓库文件不存在: {token}",
                        f"改钥匙指向真实路径，或把 {token} 加进仓库",
                    )
                )

    # ── electron-builder 的产物落点跟钥匙说的是不是同一处 ────────────────────
    #
    # 钥匙的 dist_dir 决定装配出来的脚本去哪里捡安装包；yml 的 directories.output 决定
    # electron-builder 把它放到哪里。两处漂开，构建机会在长编译之后报一句「找不到」。
    if manifest.electron.installer == "electron_builder" and manifest.build_target.desktop_dir:
        config = repo_root / manifest.build_target.desktop_dir / "electron-builder.yml"
        declared = manifest.electron.dist_dir.rstrip("/")
        if not config.is_file():
            missing(
                "electron",
                "electron_builder_config_missing",
                f"{manifest.build_target.desktop_dir}/electron-builder.yml",
                "electron-builder 配置",
            )
        else:
            actual = _electron_builder_output_dir(config)
            if actual != declared:
                findings.append(
                    _finding(
                        product,
                        "electron",
                        "electron_builder_output_drift",
                        f"{manifest.build_target.desktop_dir}/electron-builder.yml",
                        f"directories.output 是 {actual!r}，钥匙的 electron.dist_dir 是 {declared!r}",
                        "把两处改成同一个目录",
                    )
                )

    # ── 钥匙里指向钥匙自己的地方，指的是不是自己 ────────────────────────────
    #
    # stages 与 diagnose 都带一条 --adapter。这一段在每把钥匙里几乎一样，于是它是抄的，
    # 而抄的时候最容易留下上一把钥匙的文件名。照那样跑，装配读的是另一把钥匙、出来的是
    # 另一个产品的脚本，**而每一步都报绿**。这种错只有对着文件名看才发现得了。
    name = adapter.name
    for label, argv in [
        *((f"stages[{stage.name}]", stage.run) for stage in manifest.stages),
        ("diagnose", manifest.diagnose),
    ]:
        for token in argv:
            if token.endswith(".release-adapter.json") or token.endswith(".v2.json"):
                if Path(token).name != name:
                    findings.append(
                        _finding(
                            product,
                            "key",
                            "adapter_points_at_another_key",
                            label,
                            f"{label} 的 --adapter 指着 {token}，不是这把钥匙 {name}",
                            f"改成指向 {name}——否则这一轮用的是另一把钥匙，而日志每一步都是绿的",
                        )
                    )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify_key")
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path("."), type=Path)
    args = parser.parse_args(argv)

    manifest = ReleaseAdapterManifest.model_validate_json(
        args.adapter.read_text(encoding="utf-8")
    )
    findings = verify(manifest, args.repo_root.resolve(), args.adapter)
    print(
        json.dumps(
            {"schema_version": "1", "product": manifest.product, "findings": findings},
            ensure_ascii=False,
        )
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
