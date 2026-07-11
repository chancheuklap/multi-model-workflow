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

from release_contracts import BuildTarget, ReleaseAdapterManifest, ReleaseBuildHooks


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


def _render_bootstrap(context_path: Path, manifest: ReleaseAdapterManifest) -> str:
    template = (
        Path(__file__).parent / "release_templates" / "windows_electron_python.ps1.tmpl"
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
  & $command @arguments
  if ($LASTEXITCODE -ne 0) { throw "Release hook failed: $Name phase=$Phase" }
}

function Write-HookSkipped {
  param([string]$Name)
  Write-Host "HOOK-SKIPPED:$Name:not-configured"
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
    target = manifest.build_target
    if target.runtime_lane == "core_exe":
        return "  Write-Host 'core_exe runtime lane is supplied by the repository hook'"
    if not target.deps_extra:
        raise ValueError("embedded_python 车道必须声明 build_target.deps_extra")

    asset_roots = ", ".join(powershell_literal(item) for item in target.asset_roots)
    nuitka_include = "\n".join(
        f"  $NuitkaArgs += {powershell_literal(f'--include-package={module}')}"
        for module in target.nuitka_include
    )
    nuitka_nofollow = "\n".join(
        f"  $NuitkaArgs += {powershell_literal(f'--nofollow-import-to={module}')}"
        for module in target.nuitka_nofollow
    )
    dll_calls = "\n".join(
        _render_dll_copy_call(item.model_dump(mode="json"))
        for item in target.native_ext_dll
    )
    return f"""  function Remove-PythonBytecode {{
    param([string]$RuntimeRoot)
    Get-ChildItem -Path $RuntimeRoot -Directory -Filter '__pycache__' -Recurse -ErrorAction Stop | Remove-Item -Recurse -Force
    Get-ChildItem -Path $RuntimeRoot -File -Filter '*.pyc' -Recurse -ErrorAction Stop | Remove-Item -Force
  }}

  function Copy-NativeExtensionDll {{
    param([string[]]$SourceRoots, [string]$DllName, [string]$Destination)
    $Source = @($SourceRoots | ForEach-Object {{ Join-Path $_ $DllName }} | Where-Object {{ Test-Path $_ }} | Select-Object -First 1)
    if ($Source.Count -ne 1) {{ throw "Missing declared native DLL: $DllName" }}
    $destinationParent = Split-Path -Parent $Destination
    if (-not (Test-Path $destinationParent)) {{ throw "Missing declared native DLL destination: $destinationParent" }}
    Copy-Item -Path $Source[0] -Destination $Destination -Force -ErrorAction Stop
  }}

  $RuntimeRoot = Join-Path $DesktopDir 'python-runtime'
  $CompileInterpreterRoot = (& uv run --extra {powershell_literal(target.deps_extra or "")} python -c 'import sys; print(sys.base_prefix)').Trim()
  foreach ($assetRoot in @({asset_roots})) {{
    if (-not (Test-Path (Join-Path $RepoRoot $assetRoot))) {{ throw "Missing declared asset root: $assetRoot" }}
  }}
  $NuitkaArgs = @('--standalone', '--onefile', '--assume-yes-for-downloads')
{nuitka_include}
{nuitka_nofollow}
  $NuitkaEntry = Join-Path $RepoRoot {powershell_literal(f"src/{target.entry_module}/__main__.py")}
  & uv run --extra {powershell_literal(target.deps_extra or "")} --extra build python -m nuitka @NuitkaArgs $NuitkaEntry
  if ($LASTEXITCODE -ne 0) {{ throw 'Nuitka backend build failed' }}
  Remove-PythonBytecode -RuntimeRoot $RuntimeRoot
{dll_calls}"""


def _render_dll_copy_call(item: dict[str, object]) -> str:
    destination = "backend"
    if item["dest"] == "pyd_package_dir":
        destination = "Lib\\site-packages\\" + str(item["pyd_package"])
    source_roots = "@($RepoRoot)"
    if item["dll_source"] == "compile_interpreter":
        source_roots = (
            "@($CompileInterpreterRoot, (Join-Path $CompileInterpreterRoot 'DLLs'))"
        )
    calls = []
    for dll_name in item["dll_names"]:
        # 反斜杠不能出现在 f-string 表达式内(Python 3.11 SyntaxError),提到普通语句里拼。
        dest_rel = destination + "\\\\" + str(dll_name)
        calls.append(
            "  Copy-NativeExtensionDll "
            f"-SourceRoots {source_roots} -DllName {powershell_literal(str(dll_name))} "
            f"-Destination (Join-Path $RuntimeRoot {powershell_literal(dest_rel)})"
        )
    return "\n".join(calls)


def _validate_paths(repo_root: Path, output: Path, context_output: Path) -> None:
    if not repo_root.is_dir():
        raise ValueError(f"--repo-root 不存在或不是目录: {repo_root}")
    if output.parent.resolve() != context_output.parent.resolve():
        raise ValueError("--output 与 --context-output 必须在同一目录")
    for label, path in (("--output", output), ("--context-output", context_output)):
        if not path.name:
            raise ValueError(f"{label} 必须指向文件")


def _validate_manifest_paths(manifest: ReleaseAdapterManifest) -> None:
    assert_repo_relative(
        manifest.build_target.desktop_dir, field="build_target.desktop_dir"
    )
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
    hook_calls = _hook_calls(manifest)
    context = {
        "schema_version": manifest.schema_version,
        "product": manifest.product,
        "repo_root": str(repo_root.resolve()),
        "build_target": manifest.build_target.model_dump(mode="json"),
        "build_hooks": manifest.build_hooks.model_dump(mode="json"),
        "render_metadata": {
            "stages": [1, 2, 3, 4, 5, 6, 7],
            "hook_calls": [
                {key: value for key, value in call.items() if key != "argv"}
                for call in hook_calls
            ],
        },
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
    BuildTarget.model_validate(context_doc["build_target"])
    ReleaseBuildHooks.model_validate(context_doc["build_hooks"])
    if context_doc.get("schema_version") != "1" or not context_doc.get("product"):
        raise ValueError("context 缺少有效 schema_version 或 product")
    script_text = script_bytes.decode("utf-8-sig")
    expected_context_literal = powershell_literal(context.name)
    if expected_context_literal not in script_text:
        raise ValueError("script 未引用对应的 context 文件")
    expected_stages = [1, 2, 3, 4, 5, 6, 7]
    if context_doc.get("render_metadata", {}).get("stages") != expected_stages:
        raise ValueError("context 未声明完整七步流水线")
    stage_positions = [
        script_text.find(f'Step "[{stage}/7]') for stage in expected_stages
    ]
    if -1 in stage_positions or stage_positions != sorted(stage_positions):
        raise ValueError("script 未按顺序包含完整七步流水线")
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
