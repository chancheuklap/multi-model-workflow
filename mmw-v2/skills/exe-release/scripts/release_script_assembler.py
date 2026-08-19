# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2"]
# ///
"""把受 schema 约束的 release adapter 装配为构建机输入。"""

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

from builders import nuitka
from release_contracts import (
    BuildTarget,
    ReleaseAdapterManifest,
    ReleaseBuildHooks,
)


def powershell_literal(value: str) -> str:
    """把一个动态值表示成不求值的 PowerShell 单引号字面量。"""
    return "'" + value.replace("'", "''") + "'"


def assert_repo_relative(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or ":" in path.parts[0]
        or ".." in path.parts
    ):
        raise ValueError(f"{field} 必须是无 .. 的仓库相对 POSIX 路径")
    return path


def atomic_write(path: Path, content: str, *, encoding: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding=encoding)
    return tmp


def _restore(path: Path, *, previous: bytes | None, existed: bool) -> None:
    if existed:
        rollback = path.with_name(f".{path.name}.rollback")
        rollback.write_bytes(previous or b"")
        rollback.replace(path)
    elif path.is_file():
        path.unlink()


# v1 每条 runtime 车道一份模板:embedded_python 走通用 Electron 七步;core_exe 的出包主体是
# 产品自己的一体化脚本(经 runtime_prepare 钩子),模板只做验工具+钩子编排四步。
#
# v2 只有一份模板。车道不再选模板——步骤由钥匙声明了什么决定,而三个产品的差异全部是值。
_TEMPLATE_BY_LANE = {
    "embedded_python": "windows_electron_python.ps1.tmpl",
    "core_exe": "windows_core_exe.ps1.tmpl",
}
_TEMPLATE_V2 = "nuitka_electron.ps1.tmpl"
# hook token 在两份模板里挂的步号不同,但 hook 生命周期(runtime_ready/artifact_ready/
# release_ready)一致;check() 按车道校验对应步集。
_STAGES_BY_LANE = {
    "embedded_python": [1, 2, 3, 4, 5, 6, 7],
    "core_exe": [1, 2, 3, 4],
}
_STEP_TOTAL_BY_LANE = {"embedded_python": 7, "core_exe": 4}


def _render_bootstrap(context_path: Path, manifest: ReleaseAdapterManifest) -> str:
    if manifest.schema_version == "2":
        return _render_bootstrap_v2(context_path, manifest)
    lane = manifest.build_target.runtime_lane
    template = (
        Path(__file__).parent / "release_templates" / _TEMPLATE_BY_LANE[lane]
    ).read_text(encoding="utf-8")
    hook_calls = _hook_calls(manifest)
    replacements = {
        "${CONTEXT_DEFAULT_PATH}": powershell_literal(context_path.name),
        "${DESKTOP_DIR_LITERAL}": powershell_literal(manifest.build_target.desktop_dir),
        "${LANE_BLOCK}": _render_lane_block(manifest),
        "${RENDERED_HOOK_FUNCTIONS}": _render_hook_functions(),
        "${RUNTIME_HOOK_CALLS}": _render_hook_calls(hook_calls, stage=3),
        "${ARTIFACT_HOOK_CALLS}": _render_hook_calls(hook_calls, stage=6),
        "${RELEASE_HOOK_CALLS}": _render_hook_calls(hook_calls, stage=7),
    }
    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    if re.search(r"\$\{[^}]+\}", rendered):
        raise ValueError("release template 含未消费 token")
    return rendered


def _hook_calls(manifest: ReleaseAdapterManifest) -> list[dict[str, object]]:
    hooks = manifest.build_hooks.model_dump(mode="json")
    definitions = [
        (3, "runtime_prepare", "runtime_ready", True),
        (3, "asset_parity", "runtime_ready", False),
        (3, "credential_proof", "runtime_ready", False),
        (6, "artifact_scan", "artifact_ready", True),
        (7, "package_integrity", "release_ready", True),
    ]
    calls = []
    for stage, name, phase, required in definitions:
        argv = hooks[name]
        if argv is not None:
            _assert_safe_argv(argv, field=f"build_hooks.{name}")
        calls.append(
            {
                "stage": stage,
                "name": name,
                "phase": phase,
                "required": required,
                "skipped": argv is None,
                "argv": argv,
            }
        )
    return calls


def _assert_safe_argv(argv: list[str], *, field: str) -> None:
    for index, token in enumerate(argv):
        if any(char in token for char in ("\n", "\r", "\x00", "&", ";", "|")):
            raise ValueError(f"{field}[{index}] 含不允许的 shell 控制字符")


def _render_hook_functions() -> str:
    return """function Invoke-ReleaseHook {
  param([string]$Name, [string[]]$Argv, [string]$Phase)
  if ($null -eq $Argv -or $Argv.Count -eq 0) {
    throw "Required release hook missing: $Name"
  }
  $command = [string]$Argv[0]
  $arguments = @()
  if ($Argv.Count -gt 1) { $arguments += @($Argv[1..($Argv.Count - 1)]) }
  $arguments += @('--release-context', $ReleaseContextPath, '--release-phase', $Phase)
  # 钩子 argv 是仓库相对路径(如 scripts/release/prepare_*.py):构建机把功能分支源码解到
  # $RepoRoot,故从 $RepoRoot 跑钩子,而非 pnpm/electron/NSIS 步所在的 $DesktopDir。
  # $ReleaseContextPath 已在脚本头绝对化,cwd 切换不影响它被钩子读到。
  Push-Location $RepoRoot
  try {
    & $command @arguments
    if ($LASTEXITCODE -ne 0) { throw "Release hook failed: $Name phase=$Phase" }
  } finally {
    Pop-Location
  }
}

function Write-HookSkipped {
  param([string]$Name)
  Write-Host "HOOK-SKIPPED:$Name:not-configured"
}"""


def _render_hook_functions_v2() -> str:
    """v2 的钩子辅助函数。

    跟 v1 的差别有两处，都不是修辞：v2 里缺席的钩子整步都不生成，所以没有「跳过」要打印；
    钩子的 cwd 注释也不再提 Electron——一个没有外壳的产品，脚本里根本没有那个变量。
    """
    return """function Invoke-ReleaseHook {
  param([string]$Name, [string[]]$Argv, [string]$Phase)
  $command = [string]$Argv[0]
  $arguments = @()
  if ($Argv.Count -gt 1) { $arguments += @($Argv[1..($Argv.Count - 1)]) }
  $arguments += @('--release-context', $ReleaseContextPath, '--release-phase', $Phase)
  # 钩子 argv 是仓库相对路径。构建机把这一轮的源码解到 $RepoRoot，所以钩子从那里跑，
  # 而不是从某个构建步骤当时所在的目录。$ReleaseContextPath 已在脚本头绝对化，
  # cwd 怎么切都不影响钩子读到它。
  Push-Location $RepoRoot
  try {
    & $command @arguments
    if ($LASTEXITCODE -ne 0) { throw "Release hook failed: $Name phase=$Phase" }
  } finally {
    Pop-Location
  }
}"""


def _render_hook_calls(calls: list[dict[str, object]], *, stage: int) -> str:
    rendered = []
    for call in calls:
        if call["stage"] != stage:
            continue
        if call["skipped"]:
            rendered.append(
                f"  Write-HookSkipped -Name {powershell_literal(str(call['name']))}"
            )
            continue
        argv = call["argv"]
        assert isinstance(argv, list)
        tokens = ", ".join(powershell_literal(str(token)) for token in argv)
        rendered.append(
            "  Invoke-ReleaseHook "
            f"-Name {powershell_literal(str(call['name']))} -Argv @({tokens}) "
            f"-Phase {powershell_literal(str(call['phase']))}"
        )
    return "\n".join(rendered)


def _render_lane_block(manifest: ReleaseAdapterManifest) -> str:
    # 造运行时(嵌入式 Python / 编译后端 / 补原生 DLL / 落资产 / BGM)是每个产品出包独特的一步,
    # 各产品不同、无法通用几行复刻。按设计留在仓库当"钥匙",由钥匙的 runtime_prepare 钩子整段
    # 准备(仓库侧的 prepare_*_runtime.py);
    # plugin 只做通用编排,不在模板里通用地造包——过度抽象只会让每接一个产品都更复杂、且复刻不全。
    # 两条车道都把造运行时交给紧随其后的 ${RUNTIME_HOOK_CALLS} 里的 runtime_prepare 钩子。
    lane = manifest.build_target.runtime_lane
    return (
        f"  Write-Host 'Runtime lane ({lane}) is prepared by the repository "
        "runtime_prepare hook'"
    )



# ── v2：一份模板，步骤由钥匙声明了什么决定 ──────────────────────────────────────
#
# v1 的两条车道各有一份模板，其中 core_exe 那份把整条出包链外包给仓库脚本，模板自己只做
# 四步编排。结果是「怎么打一个 Windows 安装包」这套知识有一份在技能里、一份在产品仓库里，
# 而后者每接一个产品要重写一遍。
#
# v2 把编译与打包的步骤放回技能，产品仓库只留它自己独有的交付格式（例如自更新
# feed 和它手写的 NSIS）。步号不再写死在模板里——哪几步存在由钥匙决定，所以步号是算出来的。

# 钩子挂阶段，不挂步号。
_HOOK_PHASES = {
    "runtime_prepare": "runtime_ready",
    "asset_parity": "runtime_ready",
    "credential_proof": "runtime_ready",
    "backend_verify": "backend_ready",
    "artifact_scan": "artifact_ready",
    "installer": "installer_ready",
    "package_integrity": "release_ready",
}


def _ps(value: str) -> str:
    return powershell_literal(value)


def _hook_line(name: str, argv: list[str] | None, indent: str = "  ") -> str:
    if argv is None:
        return f"{indent}Write-HookSkipped -Name {_ps(name)}"
    _assert_safe_argv(argv, field=f"build_hooks.{name}")
    tokens = ", ".join(_ps(token) for token in argv)
    return (
        f"{indent}Invoke-ReleaseHook -Name {_ps(name)} -Argv @({tokens}) "
        f"-Phase {_ps(_HOOK_PHASES[name])}"
    )


def _v2_steps(manifest: ReleaseAdapterManifest) -> list[dict[str, object]]:
    """算出这把钥匙要走哪几步。每一步是 (标题, PowerShell 行, 这一步回调了哪些钩子)。"""
    hooks = manifest.build_hooks
    backend = manifest.python_backend
    electron = manifest.electron
    desktop_dir = manifest.build_target.desktop_dir
    steps: list[dict[str, object]] = []

    tools = ", ".join(_ps(tool) for tool in manifest.toolchain)
    steps.append(
        {
            "title": "Validate prerequisites",
            "hooks": [],
            "lines": [
                f"  foreach ($tool in @({tools})) {{",
                "    Assert-Tool $tool",
                "  }",
            ],
        }
    )

    if electron is not None:
        install_args = ", ".join(_ps(arg) for arg in electron.install_args)
        steps.append(
            {
                "title": "Install frontend dependencies",
                "hooks": [],
                "lines": [
                    f"  Invoke-Checked -Command {_ps(electron.package_manager)} "
                    f"-WorkingDirectory $DesktopDir -Arguments @({install_args})",
                ],
            }
        )

    runtime_hooks = [
        name
        for name in ("runtime_prepare", "asset_parity", "credential_proof")
        if getattr(hooks, name) is not None
    ]
    if runtime_hooks:
        steps.append(
            {
                "title": "Prepare runtime",
                "hooks": runtime_hooks,
                "lines": [_hook_line(name, getattr(hooks, name)) for name in runtime_hooks],
            }
        )

    steps.append(
        {
            "title": "Compile Python backend",
            "hooks": [],
            "lines": _compile_lines(backend, manifest.build_target, desktop_dir),
        }
    )

    verify_lines: list[str] = []
    if backend.smoke is not None:
        exe = nuitka.expand(
            f"{backend.output_dir}/{backend.smoke.exe}",
            desktop_dir=desktop_dir,
            build_root=backend.build_root,
        )
        verify_lines.append(
            f"  Invoke-BuiltExeSmoke -Exe (Join-Path $RepoRoot {_ps(exe)}) "
            f"-Module {_ps(backend.smoke.run_module)} "
            f"-TimeoutSeconds {backend.smoke.timeout_seconds}"
        )
    verify_hooks = ["backend_verify"] if hooks.backend_verify is not None else []
    for name in verify_hooks:
        verify_lines.append(_hook_line(name, getattr(hooks, name)))
    if verify_lines:
        steps.append(
            {
                "title": "Verify compiled backend",
                "hooks": verify_hooks,
                "lines": verify_lines,
            }
        )

    if electron is not None:
        steps.append(
            {
                "title": "Build Electron application",
                "hooks": [],
                "lines": [
                    f"  Invoke-Checked -Command {_ps(electron.package_manager)} "
                    f"-WorkingDirectory $DesktopDir "
                    f"-Arguments @('run', {_ps(electron.build_script)})",
                ],
            }
        )
        steps.append(
            {
                "title": "Build win-unpacked",
                "hooks": [],
                "lines": [
                    f"  Invoke-Checked -Command {_ps(electron.package_manager)} "
                    "-WorkingDirectory $DesktopDir "
                    "-Arguments @('exec', 'electron-builder', '--win', 'dir', "
                    "'--publish', 'never', \"-c.compression=$BuilderCompression\")",
                    "  if (-not (Test-Path $UnpackedDir)) {",
                    "    throw 'electron-builder did not create the unpacked directory'",
                    "  }",
                ],
            }
        )

    # 扫源码泄漏是技能每次都做的，不是产品可选的检查：编译这一整套动作的目的就是
    # 不发源码。产品的 artifact_scan 钩子加在它后面，扫产品自己关心的东西。
    scan_lines = _source_scan_lines(manifest)
    if hooks.artifact_scan is not None:
        scan_lines.append(_hook_line("artifact_scan", hooks.artifact_scan))
    if scan_lines:
        steps.append(
            {
                "title": "Scan release artifacts",
                "hooks": ["artifact_scan"] if hooks.artifact_scan is not None else [],
                "lines": scan_lines,
            }
        )

    if electron is not None and electron.installer == "electron_builder":
        steps.append(
            {
                "title": "Build installer",
                "hooks": [],
                "lines": _nsis_lines(electron.package_manager),
            }
        )
    elif hooks.installer is not None:
        steps.append(
            {
                "title": "Build installer",
                "hooks": ["installer"],
                "lines": [_hook_line("installer", hooks.installer)],
            }
        )

    verify_lines = []
    if _has_installer_step(manifest) and manifest.build_target.installer_glob:
        verify_lines.append(
            "  Assert-InstallerProduced -Glob (Join-Path $RepoRoot "
            f"{_ps(manifest.build_target.installer_glob)})"
        )
    if hooks.package_integrity is not None:
        verify_lines.append(_hook_line("package_integrity", hooks.package_integrity))
    if verify_lines:
        steps.append(
            {
                "title": "Verify package integrity",
                "hooks": ["package_integrity"] if hooks.package_integrity is not None else [],
                "lines": verify_lines,
            }
        )
    return steps


def _has_installer_step(manifest: ReleaseAdapterManifest) -> bool:
    electron = manifest.electron
    return bool(
        (electron is not None and electron.installer == "electron_builder")
        or manifest.build_hooks.installer is not None
    )


def _source_scan_lines(manifest: ReleaseAdapterManifest) -> list[str]:
    """扫哪几棵树，用哪几个包名——两样都从钥匙已有的字段推，不新增一个字段。

    树：Electron 打出来的目录，和后端编译产物的目录。包名：include_packages，
    也就是「这个产品自己的代码」的定义，它本来就在钥匙里。
    """
    backend = manifest.python_backend
    packages = sorted(set(backend.include_packages))
    if not packages:
        return []
    desktop_dir = manifest.build_target.desktop_dir
    roots: list[str] = []
    if manifest.electron is not None and desktop_dir is not None:
        roots.append("$UnpackedDir")
    roots.append(
        "(Join-Path $RepoRoot "
        + _ps(
            nuitka.expand(
                backend.output_dir,
                desktop_dir=desktop_dir,
                build_root=backend.build_root,
            )
        )
        + ")"
    )
    return [
        "  Assert-NoBusinessSource -Roots @(" + ", ".join(roots) + ") "
        "-Packages @(" + ", ".join(_ps(name) for name in packages) + ")"
    ]


def _compile_lines(backend, build_target: BuildTarget, desktop_dir: str | None) -> list[str]:
    """编译后端。原生扩展缺的 DLL 先探再编——探不到当场停，不进几十分钟的编译。"""
    nuitka.validate_import_plan(backend)
    lines: list[str] = []
    runner = ", ".join(_ps(token) for token in backend.runner)
    for name, value in backend.env.items():
        rendered = _ps(value)
        if "${REPO_ROOT}" in value:
            head, _, tail = value.partition("${REPO_ROOT}")
            pieces = [p for p in (_ps(head), "$RepoRoot", _ps(tail)) if p != "''"]
            rendered = pieces[0] if len(pieces) == 1 else "(" + " + ".join(pieces) + ")"
        lines.append(f"  $env:{name} = {rendered}")
    for source, name in nuitka.probe_names(build_target.native_ext_dll):
        var = "$Dll_" + "".join(
            char if char.isalnum() else "_" for char in f"{source}:{name}"
        )
        lines.append(
            f"  {var} = Resolve-BuildDll -Source {_ps(source)} -Name {_ps(name)} "
            f"-RunnerArgv @({runner}) -WorkingDirectory $RepoRoot"
        )
    commands = nuitka.commands(
        backend,
        desktop_dir=desktop_dir,
        native_ext_dll=build_target.native_ext_dll,
    )
    compile_lines: list[str] = []
    for target, segments in zip(backend.targets, commands, strict=True):
        argv = nuitka.powershell_argv(segments)
        compile_lines.append(f"  Write-Host {_ps('  compiling ' + target.exe)}")
        compile_lines.append(f"  $argv = {argv}")
        compile_lines.append(
            "  Invoke-Checked -Command ([string]$argv[0]) "
            "-Arguments @($argv[1..($argv.Count - 1)]) -WorkingDirectory $RepoRoot"
        )
    if not backend.isolate_dirs:
        return [*lines, *compile_lines]

    isolate = ", ".join(
        f"(Join-Path $RepoRoot {_ps(nuitka.expand(path, desktop_dir=desktop_dir, build_root=backend.build_root))})"
        for path in backend.isolate_dirs
    )
    lines.append(
        "  $moved = Move-AsideForCompile -Paths @(" + isolate + ") "
        "-Holding (Join-Path $RepoRoot 'runtime/.mmw-compile-holding')"
    )
    lines.append("  try {")
    lines.extend("  " + line for line in compile_lines)
    lines.append("  }")
    lines.append("  finally { Restore-AfterCompile -Moved $moved }")
    return lines


def _nsis_lines(package_manager: str) -> list[str]:
    """electron-builder 出 NSIS。

    不用 Invoke-Checked：electron-builder 打完 NSIS 清理临时 nsis.7z 偶发 ENOENT unlink
    竞态返非零，而安装包其实已产出。捕获合并输出（内存变量，不用 Out-File——脱附会话不可靠），
    安装包已产出且日志命中 nsis.7z ENOENT 时只告警继续，否则 throw。
    """
    return [
        f"  $nsisOut = (& {package_manager} --dir $DesktopDir exec electron-builder --win nsis "
        "--publish never --prepackaged $UnpackedDir "
        '"-c.compression=$BuilderCompression" 2>&1 | Out-String)',
        "  $nsisExit = $LASTEXITCODE",
        "  Write-Host $nsisOut",
        "  $installerExists = [bool](Get-ChildItem -Path $DistDir -Filter '*.exe' "
        "-File -ErrorAction SilentlyContinue)",
        "  if ($nsisExit -ne 0) {",
        "    $enoent = ($nsisOut -like '*ENOENT: no such file or directory, unlink*' "
        "-and $nsisOut -like '*nsis.7z*')",
        "    if ($enoent -and $installerExists) {",
        "      Write-Host '  electron-builder NSIS cleanup ENOENT after installer "
        "output; continuing to artifact verification' -ForegroundColor Yellow",
        "    } else {",
        '      throw "electron-builder NSIS failed ($nsisExit)"',
        "    }",
        "  }",
        "  if (-not $installerExists) {",
        "    throw 'electron-builder did not create an installer'",
        "  }",
    ]


def _render_pipeline(steps: list[dict[str, object]]) -> str:
    total = len(steps)
    blocks: list[str] = []
    for index, step in enumerate(steps, start=1):
        lines = [f'  Step "[{index}/{total}] {step["title"]}"']
        lines.extend(step["lines"])  # type: ignore[arg-type]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _electron_setup(manifest: ReleaseAdapterManifest) -> str:
    """Electron 外壳那几个路径变量。没有外壳的产品这里是空的——凭空造出一个指向
    不存在目录的 $DesktopDir，只会让后面某一步以一个看不出根因的方式失败。"""
    electron = manifest.electron
    desktop_dir = manifest.build_target.desktop_dir
    if electron is None or desktop_dir is None:
        return ""
    compression = (
        f"if ($env:{electron.compression_env}) "
        f"{{ $env:{electron.compression_env} }} else {{ {_ps(electron.compression)} }}"
        if electron.compression_env
        else _ps(electron.compression)
    )
    return "\n".join(
        [
            f"$DesktopDir = Join-Path $RepoRoot {_ps(desktop_dir)}",
            f"$DistDir = Join-Path $DesktopDir {_ps(electron.dist_dir)}",
            f"$UnpackedDir = Join-Path $DesktopDir {_ps(electron.unpacked_dir)}",
            "",
            "# 安装包压缩档：嵌入式 runtime 几百 MB，压缩档对客户下载体验有实际影响，",
            "# 所以默认最高档。现场验证时用环境变量压到 store 换速度。",
            f"$BuilderCompression = {compression}",
        ]
    )


def _render_bootstrap_v2(
    context_path: Path, manifest: ReleaseAdapterManifest
) -> str:
    template = (Path(__file__).parent / "release_templates" / _TEMPLATE_V2).read_text(
        encoding="utf-8"
    )
    steps = _v2_steps(manifest)
    replacements = {
        "${CONTEXT_DEFAULT_PATH}": _ps(context_path.name),
        "${ELECTRON_SETUP}": _electron_setup(manifest),
        "${RENDERED_HOOK_FUNCTIONS}": (
            _render_hook_functions_v2()
            if any(step["hooks"] for step in steps)
            else ""
        ),
        "${STEP_TOTAL}": str(len(steps)),
        "${PIPELINE}": _render_pipeline(steps),
    }
    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    if re.search(r"\$\{[^}]+\}", rendered):
        raise ValueError("release template 含未消费 token")
    return rendered


def _v2_render_metadata(manifest: ReleaseAdapterManifest) -> dict[str, object]:
    steps = _v2_steps(manifest)
    return {
        "steps": [
            {"index": index, "title": step["title"], "hooks": step["hooks"]}
            for index, step in enumerate(steps, start=1)
        ],
        "hook_calls": [
            {
                "step": index,
                "name": name,
                "phase": _HOOK_PHASES[name],
                "skipped": getattr(manifest.build_hooks, name) is None,
            }
            for index, step in enumerate(steps, start=1)
            for name in step["hooks"]  # type: ignore[union-attr]
        ],
    }

def _validate_paths(repo_root: Path, output: Path, context_output: Path) -> None:
    if not repo_root.is_dir():
        raise ValueError(f"--repo-root 不存在或不是目录: {repo_root}")
    if output.parent.resolve() != context_output.parent.resolve():
        raise ValueError("--output 与 --context-output 必须在同一目录")
    for label, path in (("--output", output), ("--context-output", context_output)):
        if not path.name:
            raise ValueError(f"{label} 必须指向文件")


def _validate_manifest_paths(manifest: ReleaseAdapterManifest) -> None:
    if manifest.build_target.desktop_dir is not None:
        assert_repo_relative(
            manifest.build_target.desktop_dir, field="build_target.desktop_dir"
        )
    if manifest.protection_source is not None:
        assert_repo_relative(manifest.protection_source, field="protection_source")
    for index, root in enumerate(manifest.build_target.asset_roots):
        assert_repo_relative(root, field=f"build_target.asset_roots[{index}]")
    for index, path in enumerate(manifest.editable_paths):
        assert_repo_relative(path, field=f"editable_paths[{index}]")


def assemble(
    adapter: Path, repo_root: Path, output: Path, context_output: Path
) -> None:
    """校验 adapter 后，成对写入 PowerShell 与它唯一对应的上下文。"""
    manifest = ReleaseAdapterManifest.model_validate_json(
        adapter.read_text(encoding="utf-8")
    )
    _validate_paths(repo_root, output, context_output)
    _validate_manifest_paths(manifest)
    context = {
        "schema_version": manifest.schema_version,
        "product": manifest.product,
        "repo_root": str(repo_root.resolve()),
        "build_target": manifest.build_target.model_dump(mode="json"),
        "build_hooks": manifest.build_hooks.model_dump(mode="json"),
        "build_machine": (
            manifest.build_machine.model_dump(mode="json")
            if manifest.build_machine
            else None
        ),
    }
    if manifest.schema_version == "2":
        # 钩子要读得到「这次按哪把钥匙编的」——产品仓库的收尾步骤（例如自己组装 bundle）
        # 得知道编译产物叫什么、落在哪。
        context["python_backend"] = manifest.python_backend.model_dump(mode="json")
        context["electron"] = (
            manifest.electron.model_dump(mode="json") if manifest.electron else None
        )
        context["render_metadata"] = _v2_render_metadata(manifest)
    else:
        hook_calls = _hook_calls(manifest)
        context["render_metadata"] = {
            "stages": _STAGES_BY_LANE[manifest.build_target.runtime_lane],
            "hook_calls": [
                {key: value for key, value in call.items() if key != "argv"}
                for call in hook_calls
            ],
        }
    script = _render_bootstrap(context_output, manifest)
    script_tmp: Path | None = None
    context_tmp: Path | None = None
    output_existed = output.exists()
    context_existed = context_output.exists()
    output_previous = output.read_bytes() if output.is_file() else None
    context_previous = context_output.read_bytes() if context_output.is_file() else None
    output_replaced = False
    context_replaced = False
    try:
        context_tmp = atomic_write(
            context_output,
            json.dumps(context, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        script_tmp = atomic_write(output, script, encoding="utf-8-sig")
        context_tmp.replace(context_output)
        context_replaced = True
        script_tmp.replace(output)
        output_replaced = True
    except Exception:
        if output_replaced:
            _restore(output, previous=output_previous, existed=output_existed)
        if context_replaced:
            _restore(
                context_output,
                previous=context_previous,
                existed=context_existed,
            )
        raise
    finally:
        for tmp in (script_tmp, context_tmp):
            if tmp is not None and tmp.exists():
                tmp.unlink()


def _fail(message: str) -> int:
    print(f"INVALID: {message}", file=sys.stderr)
    return 3


def cmd_assemble(args: argparse.Namespace) -> int:
    try:
        assemble(args.adapter, args.repo_root, args.output, args.context_output)
    except Exception as exc:  # noqa: BLE001 - CLI must surface invalid release input.
        return _fail(str(exc))
    return 0


def check(script: Path, context: Path) -> None:
    script_bytes = script.read_bytes()
    if not script_bytes.startswith(b"\xef\xbb\xbf"):
        raise ValueError("script 必须是 UTF-8 BOM 编码")
    context_doc = json.loads(context.read_text(encoding="utf-8"))
    target = BuildTarget.model_validate(context_doc["build_target"])
    ReleaseBuildHooks.model_validate(context_doc["build_hooks"])
    if context_doc.get("schema_version") not in ("1", "2") or not context_doc.get(
        "product"
    ):
        raise ValueError("context 缺少有效 schema_version 或 product")
    script_text = script_bytes.decode("utf-8-sig")
    expected_context_literal = powershell_literal(context.name)
    if expected_context_literal not in script_text:
        raise ValueError("script 未引用对应的 context 文件")
    if context_doc["schema_version"] == "2":
        _check_v2(script_text, context_doc)
        return
    expected_stages = _STAGES_BY_LANE[target.runtime_lane]
    step_total = _STEP_TOTAL_BY_LANE[target.runtime_lane]
    if context_doc.get("render_metadata", {}).get("stages") != expected_stages:
        raise ValueError("context 未声明该车道的完整流水线")
    stage_positions = [
        script_text.find(f'Step "[{stage}/{step_total}]') for stage in expected_stages
    ]
    if -1 in stage_positions or stage_positions != sorted(stage_positions):
        raise ValueError("script 未按顺序包含该车道的完整流水线")
    hook_calls = context_doc.get("render_metadata", {}).get("hook_calls")
    if not isinstance(hook_calls, list):
        raise ValueError("context 缺少 hook 生命周期记录")
    hooks = ReleaseBuildHooks.model_validate(context_doc["build_hooks"])
    expected_hooks = [
        (3, "runtime_prepare", "runtime_ready", True, False),
        (3, "asset_parity", "runtime_ready", False, hooks.asset_parity is None),
        (3, "credential_proof", "runtime_ready", False, hooks.credential_proof is None),
        (6, "artifact_scan", "artifact_ready", True, False),
        (7, "package_integrity", "release_ready", True, False),
    ]
    actual_hooks = [
        (
            item.get("stage"),
            item.get("name"),
            item.get("phase"),
            item.get("required"),
            item.get("skipped"),
        )
        for item in hook_calls
        if isinstance(item, dict)
    ]
    if actual_hooks != expected_hooks:
        raise ValueError("context hook 生命周期绑定不完整或顺序错误")
    print(json.dumps({"hook_calls": hook_calls}, ensure_ascii=False))



def _check_v2(script_text: str, context_doc: dict) -> None:
    """脚本与它的 context 说的是不是同一件事。

    v1 的步号写死在模板里，所以那时校验的是「车道该有的步集」。v2 步号是算出来的，
    所以校验改成：context 记的每一步，在脚本里按同样的顺序、同样的步号出现。
    """
    metadata = context_doc.get("render_metadata")
    if not isinstance(metadata, dict):
        raise ValueError("context 缺少 render_metadata")
    steps = metadata.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("context 没记下这次装配了哪几步")
    total = len(steps)
    positions = []
    for step in steps:
        marker = f'Step "[{step["index"]}/{total}] {step["title"]}"'
        position = script_text.find(marker)
        if position < 0:
            raise ValueError(f"script 里找不到这一步: {marker}")
        positions.append(position)
    if positions != sorted(positions):
        raise ValueError("script 里的步骤顺序与 context 记的不一致")
    hook_calls = metadata.get("hook_calls")
    if not isinstance(hook_calls, list):
        raise ValueError("context 缺少 hook 生命周期记录")
    hooks = ReleaseBuildHooks.model_validate(context_doc["build_hooks"])
    for call in hook_calls:
        expected_skipped = getattr(hooks, call["name"]) is None
        if call["skipped"] != expected_skipped:
            raise ValueError(f"hook {call['name']} 的 skipped 与钥匙不一致")
    print(json.dumps({"steps": steps, "hook_calls": hook_calls}, ensure_ascii=False))


def cmd_check(args: argparse.Namespace) -> int:
    try:
        check(args.script, args.context)
    except Exception as exc:  # noqa: BLE001 - CLI must surface invalid release artifact.
        return _fail(str(exc))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="release_script_assembler")
    sub = parser.add_subparsers(dest="command", required=True)
    assemble_parser = sub.add_parser("assemble")
    assemble_parser.add_argument("--adapter", type=Path, required=True)
    assemble_parser.add_argument("--repo-root", type=Path, required=True)
    assemble_parser.add_argument("--output", type=Path, required=True)
    assemble_parser.add_argument("--context-output", type=Path, required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--script", type=Path, required=True)
    check_parser.add_argument("--context", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "assemble":
        return cmd_assemble(args)
    return cmd_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
