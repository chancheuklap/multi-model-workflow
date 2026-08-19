# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2"]
# ///
"""按钥匙生成 Nuitka 编译命令。

三个产品原本各有一份手写的 Nuitka argv（`release_builder._build_duck_nuitka_command`、
`build_parrot_dubbing_python_dist.build_backend_compile_command`、
`build_hedgehog_python_dist.build_backend_compile_command`）。三份写的是同一套知识，
只有值不同。这个模块是那套知识的唯一一份，值来自钥匙的 `python_backend` 段。

## 两个渲染面

命令在 Mac 上生成，在 Windows 构建机上执行，而仓库根目录只有构建机才知道。所以命令不是
一串字符串，是一串**片段**：字面量片段直接写，路径片段记成仓库相对路径，到两个出口才拼。

- `argv(spec, repo_root=...)` —— 拼成真的 argv。给对拍测试用：同一把钥匙、同一个根，
  跟旧代码生成的 argv 比。
- `powershell(spec)` —— 拼成 PowerShell 表达式，路径片段变成 `Join-Path $RepoRoot '…'`，
  烘进 `release.ps1`。

两个出口共用同一份片段，所以它们不可能各自漂移。

## Nuitka 的坑（三个产品各踩过，写在这里不再重踩）

- `--include-package` 只带代码。包里的数据文件要另外一条 `--include-package-data`，
  两条必须成对，漏了在客户机上是运行时 FileNotFound。
- 函数体里 lazy import 的 C 扩展 Nuitka 静态追不到。不显式 include 就不进产物，
  客户跑到那个功能才崩。
- `--nofollow-import-to` 能把 smoke 要 import 的模块一起挡掉。编译一次要几十分钟，
  所以 `validate_import_plan` 在编译前就查这一条。
- abi3 扩展按名字链 `python3.dll`；Windows 加载 `.pyd` 只在 `.pyd` 自己的目录找依赖，
  补的 DLL 落 dist 根找不到。见 `native_ext_dll` 的 `dest`。
- GUI 程序要 `--windows-console-mode=disable`，否则客户双击弹黑框。
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import PurePath, PurePosixPath

__all__ = [
    "Segment",
    "argv",
    "argv_all",
    "commands",
    "expand",
    "jobs",
    "powershell_argv",
    "validate_import_plan",
]


# ── 片段 ────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Segment:
    """一个 argv 元素。`parts` 里 `("lit", s)` 原样，`("path", rel)` 到出口才按根拼。"""

    parts: tuple[tuple[str, str], ...]

    @classmethod
    def lit(cls, value: str) -> "Segment":
        return cls((("lit", value),))

    @classmethod
    def flag(cls, name: str, rel_path: str, suffix: str = "") -> "Segment":
        parts: list[tuple[str, str]] = [("lit", name), ("path", rel_path)]
        if suffix:
            parts.append(("lit", suffix))
        return cls(tuple(parts))


def expand(value: str, *, desktop_dir: str, build_root: str | None) -> str:
    """把路径里的 `${DESKTOP_DIR}` / `${BUILD_ROOT}` 换成钥匙声明的值。

    展开后必须仍是一条不含 `..` 的仓库相对 POSIX 路径——钥匙不写绝对路径，因为写钥匙的
    人在 Mac 上，跑命令的是 Windows 构建机。
    """
    result = value.replace("${DESKTOP_DIR}", desktop_dir)
    if "${BUILD_ROOT}" in result:
        if not build_root:
            raise ValueError(f"用了 ${{BUILD_ROOT}} 但钥匙没声明 build_root: {value}")
        result = result.replace("${BUILD_ROOT}", build_root)
    if "${" in result:
        raise ValueError(f"路径里有认不出的模板变量: {value}")
    path = PurePosixPath(result)
    if not result or path.is_absolute() or ".." in path.parts or "\\" in result:
        raise ValueError(f"必须是无 .. 的仓库相对 POSIX 路径: {value}")
    return result


def jobs(spec, env: dict[str, str] | None = None) -> int:
    """并行度。钥匙给默认值，钥匙指名的环境变量能临时压低——构建机内存不够时 Nuitka 会被
    OOM 杀掉，那时唯一的手段就是当场调小它。读不成整数按默认值走，不让一个笔误挡住出包。"""
    source = os.environ if env is None else env
    name = spec.jobs.env
    raw = (source.get(name, "") if name else "").strip()
    if not raw:
        return spec.jobs.default
    try:
        return max(1, int(raw))
    except ValueError:
        return spec.jobs.default


# ── 命令构造 ────────────────────────────────────────────────────────────────────


def commands(
    spec,
    *,
    desktop_dir: str,
    native_ext_dll: list | None = None,
    job_count: int | None = None,
) -> list[list[Segment]]:
    """一个 target 一条命令。duck 编两个（launcher + core），另外两个产品各编一个。"""
    count = job_count if job_count is not None else jobs(spec)
    output_dir = expand(
        spec.output_dir, desktop_dir=desktop_dir, build_root=spec.build_root
    )

    def _path(value: str) -> str:
        return expand(value, desktop_dir=desktop_dir, build_root=spec.build_root)

    out: list[list[Segment]] = []
    for target in spec.targets:
        segments: list[Segment] = [Segment.lit(token) for token in spec.runner]
        segments += [
            Segment.lit("-m"),
            Segment.lit("nuitka"),
            Segment.lit("--standalone"),
            Segment.lit("--assume-yes-for-downloads"),
            Segment.lit(f"--jobs={count}"),
            Segment.flag("--output-dir=", output_dir),
            Segment.lit(f"--output-filename={target.exe}"),
        ]
        if spec.output_mode == "onefile":
            segments.append(Segment.lit("--onefile"))
        elif spec.folder_per_target:
            segments.append(Segment.lit(f"--output-folder-name={target.name}"))
        if spec.icon:
            segments.append(Segment.flag("--windows-icon-from-ico=", _path(spec.icon)))
        if not spec.console:
            segments.append(Segment.lit("--windows-console-mode=disable"))
        segments += [Segment.lit(flag) for flag in spec.extra_flags]
        segments += [
            Segment.lit(f"--nofollow-import-to={name}")
            for name in spec.nofollow_imports
        ]
        segments += [
            Segment.lit(f"--include-package={name}") for name in spec.include_packages
        ]
        segments += [
            Segment.lit(f"--include-package-data={name}")
            for name in spec.include_package_data
        ]
        segments += [
            Segment.lit(f"--include-module={name}") for name in spec.include_modules
        ]
        segments += [
            Segment.flag("--include-data-dir=", _path(entry.source), f"={entry.dest}")
            for entry in spec.include_data_dirs
        ]
        segments += [
            Segment.flag("--include-data-files=", _path(entry.source), f"={entry.dest}")
            for entry in spec.include_data_files
        ]
        segments += _native_ext_segments(native_ext_dll or [])
        segments.append(Segment.flag("", _path(target.entrypoint)))
        out.append(segments)
    return out


def _native_ext_segments(entries: list) -> list[Segment]:
    """原生扩展缺的 DLL。

    `compile_interpreter` / `system32` 两种来源的真实路径只有构建机知道，所以它们在这里
    留成一个 PowerShell 变量名，由模板先探好再代入；`repo` 来源在仓库里，直接拼。
    """
    segments: list[Segment] = []
    for entry in entries:
        for name in entry.dll_names:
            dest = (
                f"{entry.pyd_package}/{name}"
                if entry.dest == "pyd_package_dir"
                else name
            )
            if entry.dll_source == "repo":
                if not entry.repo_dir:
                    raise ValueError("dll_source=repo 必须给 repo_dir")
                segments.append(
                    Segment.flag(
                        "--include-data-files=",
                        f"{entry.repo_dir.rstrip('/')}/{name}",
                        f"={dest}",
                    )
                )
                continue
            segments.append(
                Segment(
                    (
                        ("lit", "--include-data-files="),
                        ("probe", f"{entry.dll_source}:{name}"),
                        ("lit", f"={dest}"),
                    )
                )
            )
    return segments


def probe_names(entries: list) -> list[tuple[str, str]]:
    """要构建机现场探的 DLL：`(来源, 文件名)`。模板照这个清单生成探测步骤。"""
    seen: list[tuple[str, str]] = []
    for entry in entries:
        if entry.dll_source == "repo":
            continue
        for name in entry.dll_names:
            pair = (entry.dll_source, name)
            if pair not in seen:
                seen.append(pair)
    return seen


# ── 出口一：真 argv，给对拍测试 ────────────────────────────────────────────────


def argv(
    segments: list[Segment],
    *,
    repo_root: PurePath,
    probes: dict[str, str] | None = None,
) -> list[str]:
    """把片段拼成 argv。`probes` 给现场探测的 DLL 填上假路径，对拍时两边填同一份。"""
    resolved = probes or {}
    out: list[str] = []
    for segment in segments:
        buffer = ""
        for kind, value in segment.parts:
            if kind == "lit":
                buffer += value
            elif kind == "path":
                buffer += str(repo_root / value)
            elif kind == "probe":
                if value not in resolved:
                    raise KeyError(f"没给这个 DLL 的探测结果: {value}")
                buffer += resolved[value]
            else:  # pragma: no cover - 片段类型是本模块自己造的
                raise ValueError(f"未知片段类型: {kind}")
        out.append(buffer)
    return out


def argv_all(
    spec,
    *,
    desktop_dir: str,
    repo_root: PurePath,
    native_ext_dll: list | None = None,
    job_count: int | None = None,
    probes: dict[str, str] | None = None,
) -> list[list[str]]:
    return [
        argv(segments, repo_root=repo_root, probes=probes)
        for segments in commands(
            spec,
            desktop_dir=desktop_dir,
            native_ext_dll=native_ext_dll,
            job_count=job_count,
        )
    ]


# ── 出口二：PowerShell，烘进 release.ps1 ────────────────────────────────────────


def _ps_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def powershell_argv(segments: list[Segment]) -> str:
    """渲染成一个 PowerShell 数组字面量。路径在构建机上按 `$RepoRoot` 拼。"""
    rendered: list[str] = []
    for segment in segments:
        pieces: list[str] = []
        literal_only = True
        for kind, value in segment.parts:
            if kind == "lit":
                if not value:
                    continue
                pieces.append(_ps_literal(value))
            elif kind == "path":
                literal_only = False
                pieces.append(f"(Join-Path $RepoRoot {_ps_literal(value)})")
            elif kind == "probe":
                literal_only = False
                pieces.append(f"$Dll_{_probe_var(value)}")
            else:  # pragma: no cover
                raise ValueError(f"未知片段类型: {kind}")
        if literal_only and len(pieces) == 1:
            rendered.append(pieces[0])
        else:
            rendered.append("(" + " + ".join(pieces) + ")")
    return "@(" + ", ".join(rendered) + ")"


def _probe_var(token: str) -> str:
    """`compile_interpreter:python3.dll` → `compile_interpreter_python3_dll`。"""
    return "".join(char if char.isalnum() else "_" for char in token)


# ── 编译前的自查 ────────────────────────────────────────────────────────────────


def validate_import_plan(spec) -> None:
    """`--nofollow-import-to` 不能挡掉 smoke 要 import 的模块。

    编译一次几十分钟。挡掉了要等编译结束、smoke 跑起来才报，所以在这里先查。
    nofollow 收的是 fnmatch 模式，`a.b` 也被 `a` 挡住（Nuitka 按包前缀切）。
    """
    if spec.smoke is None:
        return
    required = [
        *spec.include_modules,
        *spec.smoke.modules,
        spec.smoke.run_module,
    ]
    blocked = [
        f"{module} 被 --nofollow-import-to={pattern} 挡住"
        for module in required
        for pattern in spec.nofollow_imports
        if _nofollow_hits(pattern, module)
    ]
    if blocked:
        raise ValueError("Nuitka 的 nofollow 会挡掉编译后要 import 的模块：\n  - " + "\n  - ".join(blocked))


def _nofollow_hits(pattern: str, module: str) -> bool:
    if fnmatch.fnmatchcase(module, pattern):
        return True
    return module.startswith(f"{pattern}.")
