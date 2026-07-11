# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2"]
# ///
"""把受 schema 约束的 release adapter 装配为构建机输入。"""

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

from release_contracts import BuildTarget, ReleaseAdapterManifest, ReleaseBuildHooks


def powershell_literal(value: str) -> str:
    """把一个动态值表示成不求值的 PowerShell 单引号字面量。"""
    return "'" + value.replace("'", "''") + "'"


def assert_repo_relative(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
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
    hook_literals = "\n".join(
        f"# {name}: " + ", ".join(powershell_literal(token) for token in argv)
        for name, argv in manifest.build_hooks.model_dump(mode="json").items()
        if argv is not None
    )
    return (
        "param(\n"
        f"  [string]$ReleaseContextPath = {powershell_literal(context_path.name)}\n"
        ")\n\n"
        "Set-StrictMode -Version Latest\n"
        "$ErrorActionPreference = 'Stop'\n\n"
        "# Pack 2.1 bootstrap. The seven-step template is added in Pack 2.2.\n"
        f"# Product: {powershell_literal(manifest.product)}\n"
        f"{hook_literals}\n"
    )


def _validate_paths(repo_root: Path, output: Path, context_output: Path) -> None:
    if not repo_root.is_dir():
        raise ValueError(f"--repo-root 不存在或不是目录: {repo_root}")
    if output.parent.resolve() != context_output.parent.resolve():
        raise ValueError("--output 与 --context-output 必须在同一目录")
    for label, path in (("--output", output), ("--context-output", context_output)):
        if not path.name:
            raise ValueError(f"{label} 必须指向文件")


def _validate_manifest_paths(manifest: ReleaseAdapterManifest) -> None:
    assert_repo_relative(manifest.build_target.desktop_dir, field="build_target.desktop_dir")
    assert_repo_relative(manifest.protection_source, field="protection_source")
    for index, root in enumerate(manifest.build_target.asset_roots):
        assert_repo_relative(root, field=f"build_target.asset_roots[{index}]")
    for index, path in enumerate(manifest.editable_paths):
        assert_repo_relative(path, field=f"editable_paths[{index}]")


def assemble(adapter: Path, repo_root: Path, output: Path, context_output: Path) -> None:
    """校验 adapter 后，成对写入 PowerShell 与它唯一对应的上下文。"""
    manifest = ReleaseAdapterManifest.model_validate_json(adapter.read_text(encoding="utf-8"))
    _validate_paths(repo_root, output, context_output)
    _validate_manifest_paths(manifest)
    context = {
        "schema_version": manifest.schema_version,
        "product": manifest.product,
        "repo_root": str(repo_root.resolve()),
        "build_target": manifest.build_target.model_dump(mode="json"),
        "build_hooks": manifest.build_hooks.model_dump(mode="json"),
        "render_metadata": {"stages": [], "hook_calls": []},
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
    expected_context_literal = powershell_literal(context.name)
    if expected_context_literal not in script_bytes.decode("utf-8-sig"):
        raise ValueError("script 未引用对应的 context 文件")


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
