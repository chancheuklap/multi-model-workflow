# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2"]
# ///
"""通用 release-flow 合同。

三合同: ReleaseAdapterManifest / ReleaseFinding / ReleaseLoopEvent。
CLI: validate-manifest / classify-findings / validate-event。
"""

import argparse
import json
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SchemaVersion = Literal["1", "2"]
# Finding / Event 的合同没变，仍然只认 "1"：钥匙升到 v2 不改这两个信封。
FindingSchemaVersion = Literal["1"]
Tier = Literal["P0", "P1", "P2"]
Status = Literal["ok", "warn", "fail", "deferred"]

_TIER_ORDER = {"P0": 0, "P1": 1, "P2": 2}


class ReleaseFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: FindingSchemaVersion
    product: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: Status
    tier: Tier | None = None
    root_cause_fingerprint: str | None = None
    locator: str | None = None
    detail: str = ""
    remediation: str | None = None

    @model_validator(mode="after")
    def _fail_needs_tier_and_fingerprint(self) -> "ReleaseFinding":
        if self.status != "fail":
            return self
        if self.tier is None:
            raise ValueError("status=fail 的 Finding 必须带 tier")
        if not self.root_cause_fingerprint:
            raise ValueError("status=fail 的 Finding 必须带 root_cause_fingerprint")
        return self


class ReleaseLoopEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: FindingSchemaVersion
    event: str = Field(min_length=1)
    product: str = Field(min_length=1)
    stage: str | None = None
    tier: Tier | None = None
    fingerprint: str | None = None
    round: int = Field(ge=1)
    trace_id: str = Field(min_length=1)
    correlation_id: str | None = None
    attempt_ref: str | None = None
    timestamp: str = Field(min_length=1)


class StageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    run: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _run_must_not_be_echo(self) -> "StageSpec":
        if self.run[0] == "echo":
            raise ValueError("build stage 不能是 echo")
        return self


RuntimeLane = Literal["core_exe", "embedded_python"]


class NativeExtDll(BaseModel):
    """一条产品特有的原生扩展 DLL 打包事实（消灭深抽丢编译知识：F-A）。

    Nuitka 冻结后端不会自动带 abi3 转发库 / MSVC C++ 运行库，必须显式打进包。
    这些事实随钥匙声明、由验钥匙对实际 `.pyd` 核对、由拼脚本器落进脚本；漏一条
    = 客户跑到该功能就空 ImportError 整批崩。
    """

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)
    dll_names: list[str] = Field(min_length=1)
    # compile_interpreter: 取自跑 Nuitka 的那个解释器目录（python3.dll 必须版本匹配）。
    # system32: 取自构建机 %SystemRoot%\\System32（MSVC 运行库，版本无关）。
    # repo: 取自仓库里 vendored 的一份。
    dll_source: Literal["compile_interpreter", "system32", "repo"] = (
        "compile_interpreter"
    )
    dest: Literal["pyd_package_dir", "dist_root"]
    # dll_source=repo 时的仓库相对目录。
    repo_dir: str | None = None
    pyd_package: str | None = None

    @model_validator(mode="after")
    def _sources_and_destinations_must_be_complete(self) -> "NativeExtDll":
        if self.dest == "pyd_package_dir" and not self.pyd_package:
            raise ValueError("dest=pyd_package_dir 必须给 pyd_package")
        if self.dll_source == "repo" and not self.repo_dir:
            raise ValueError("dll_source=repo 必须给 repo_dir")
        return self


class BuildTarget(BaseModel):
    """钥匙的 build 齿：声明本产品出包差异的**构建目标**（修正1 验齿 + 修正2 深抽）。

    非自由 argv——拼脚本器只认这里声明的产品差异，Mac 上跑裸 python 插不进；
    验钥匙拿这些字段对产品活状态核对，过时即 fail-loud（修正4 命根子）。
    """

    model_config = ConfigDict(extra="forbid")

    # 只有带 Electron 外壳的产品有。纯后端产品不声明。
    desktop_dir: str | None = None
    runtime_lane: RuntimeLane
    entry_module: str = Field(min_length=1)
    installer_brand: str = Field(min_length=1)
    # 成品安装包在源码树里的落点（仓库相对 glob）。出包成功后引擎按此把安装包从 commit 哈希构建目录
    # 收拢到统一交付目录。落点每个产品都不同，所以它是钥匙的值——引擎因此不需要知道任何产品。
    installer_glob: str | None = None
    deps_extra: str | None = None
    asset_roots: list[str] = Field(default_factory=list)
    native_ext_dll: list[NativeExtDll] = Field(default_factory=list)
    nuitka_include: list[str] = Field(default_factory=list)
    nuitka_nofollow: list[str] = Field(default_factory=list)


class ReleaseBuildHooks(BaseModel):
    """流水线按具名阶段回调的仓库钩子 argv。

    钩子挂在阶段上，不挂在步号上：步号随钥匙声明的内容变，阶段不变。

    全部可选。钩子是「这个产品自己要在这个时刻做的事」，产品没有就是没有——
    强制声明只会逼出一条什么也不做的命令，那比不声明更糟：它看着配好了。

    | 阶段 | 钩子 | 这时候做什么 |
    | --- | --- | --- |
    | runtime_ready | runtime_prepare / asset_parity / credential_proof | 造运行时、核资产、出凭证证明 |
    | backend_ready | backend_verify | 编译产物刚出来，验它能不能起来 |
    | artifact_ready | artifact_scan | Electron 打完 dir，扫产物 |
    | installer_ready | installer | 产品自己出安装包（不走 electron-builder 那条） |
    | release_ready | package_integrity | 安装包已产出，验完整性 |
    """

    model_config = ConfigDict(extra="forbid")

    # 没有嵌入式运行时要造的产品，这一步本来就是空的。
    runtime_prepare: list[str] | None = None
    asset_parity: list[str] | None = None
    credential_proof: list[str] | None = None
    backend_verify: list[str] | None = None
    artifact_scan: list[str] | None = None
    installer: list[str] | None = None
    package_integrity: list[str] | None = None

    @model_validator(mode="after")
    def _declared_hooks_must_have_argv(self) -> "ReleaseBuildHooks":
        """要么不声明，要么给一条真命令。空 argv 是「声明了但什么也不做」，
        看着配好了、实际那一步是空的——这种失败要到出货之后才发现。"""
        empty = sorted(
            name
            for name in type(self).model_fields
            if getattr(self, name) is not None and not getattr(self, name)
        )
        if empty:
            raise ValueError(f"这些钩子的 argv 是空的: {', '.join(empty)}")
        return self


class BuildMachine(BaseModel):
    """构建机准备协议（通用，非产品专属）：长构建前先把构建机备好，避免"编到深处才炸"和"一个包打一天"。

    setup argv 在校验工具后、第一个耗时步骤前跑：它的 stdout 每一行 `KEY=VALUE` 由模板应用到**模板
    自身进程**的环境变量（uv 镜像 index / NUITKA_CCACHE_BINARY / 电子镜像 / PYTHONDONTWRITEBYTECODE /
    TEMP 重定向等），使随后所有步骤（含模板直接跑的 electron-builder 与钩子里的 uv/Nuitka）继承；setup
    内部还可加系统级杀软排除（对后续全部子进程生效）并跑构建缓存预检（缺被墙下载点/磁盘/依赖即 fail-loud）。
    setup 非零退出即中止构建。teardown 在 finally 跑（移除本次加的杀软排除等），best-effort，不改变构建判定。

    值与探测逻辑全在仓库侧脚本（探 ccache 真实路径、镜像默认值等），引擎只按协议搬运、不含项目知识。"""

    model_config = ConfigDict(extra="forbid")

    setup: list[str] | None = None
    teardown: list[str] | None = None


# ── 钥匙 schema v2：编译后端 ────────────────────────────────────────────────────
#
# 「怎么编译这个产品的 Python 后端」从前写在每个产品仓库自己的 Python 里，各自硬编码
# 同一套 Nuitka 知识。现在**差异**收进下面这些字段，**动作**收进技能的 builders/nuitka.py。
#
# 路径字段一律是仓库相对 POSIX 路径，可用两个模板变量：
#   ${DESKTOP_DIR}  build_target.desktop_dir
#   ${BUILD_ROOT}   python_backend.build_root（不声明时不可用）
# 它们在构建机上按 $RepoRoot 拼成绝对路径，钥匙里不写绝对路径。


class PathTemplate(BaseModel):
    """一条 source=dest 的打包数据映射（--include-data-dir / --include-data-files）。"""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    dest: str = Field(min_length=1)


class NuitkaJobs(BaseModel):
    """并行度。构建机内存有限，jobs 开太大 Nuitka 会被 OOM 杀掉，所以它是钥匙的值不是常数。"""

    model_config = ConfigDict(extra="forbid")

    default: int = Field(ge=1)
    env: str | None = None


class NuitkaTarget(BaseModel):
    """一个编译产物。一个产品可以有多个（例如启动器与主进程各一个）。"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    exe: str = Field(min_length=1)
    entrypoint: str = Field(min_length=1)


class BuiltExeSmoke(BaseModel):
    """编译完当场用产物自己跑一次 import：把「冻结包缺动态依赖」暴露在构建机上，
    而不是等客户装完打开才崩。产品后端要接得住这个自检入口。"""

    model_config = ConfigDict(extra="forbid")

    exe: str = Field(min_length=1)
    run_module: str = Field(min_length=1)
    timeout_seconds: int = Field(default=180, ge=1)
    # 编译产物必须 import 得起来的模块。既是 smoke 的清单，也是编译前查
    # `--nofollow-import-to` 有没有把它们挡掉的依据。
    modules: list[str] = Field(default_factory=list)


class PythonBackend(BaseModel):
    """用 Nuitka 把 Python 后端编成 Windows exe。

    坑（每一条都是一次真实的出包失败换来的，写死在这里不再让下一个产品重踩）：
    - `--include-package` 只带代码，包内的数据文件要另外 `--include-package-data`。
    - 函数体里 lazy import 的 C 扩展 Nuitka 静态追不到，必须显式 include。
    - abi3 扩展按名字链 `python3.dll` 转发库和 MSVC
      C++ 运行库，Nuitka 都不带；而 Windows 加载 .pyd 只在 .pyd 自己的目录找依赖，
      所以补的 DLL 必须落到那个包目录，落 dist 根找不到。见 native_ext_dll。
    - GUI 程序要 `--windows-console-mode=disable`，否则客户双击弹黑框。
    """

    model_config = ConfigDict(extra="forbid")

    builder: Literal["nuitka"] = "nuitka"
    # 跑 Nuitka 的解释器命令，到 `python` 为止（`-m nuitka` 由技能补）。
    # 它决定编译时解析到哪一套依赖，所以是钥匙的值：装了什么就编出什么。
    runner: list[str] = Field(min_length=1)
    output_dir: str = Field(min_length=1)
    build_root: str | None = None
    output_mode: Literal["onefile", "standalone"]
    # standalone 模式下每个 target 落进各自的 <name>.dist 子目录，需要 --output-folder-name。
    folder_per_target: bool = False
    jobs: NuitkaJobs
    icon: str | None = None
    console: bool = True
    include_packages: list[str] = Field(default_factory=list)
    include_package_data: list[str] = Field(default_factory=list)
    # 有些包在运行时读自己的发行元数据（版本、entry points）。Nuitka 默认不带，
    # 带不带跟 include-package 是两回事，漏了在客户机上才炸。
    include_distribution_metadata: list[str] = Field(default_factory=list)
    include_modules: list[str] = Field(default_factory=list)
    nofollow_imports: list[str] = Field(default_factory=list)
    include_data_dirs: list[PathTemplate] = Field(default_factory=list)
    include_data_files: list[PathTemplate] = Field(default_factory=list)
    # 上面表达不了的原样 flag。它是逃生口，不是常规入口：能进上面字段的不要写这里。
    extra_flags: list[str] = Field(default_factory=list)
    targets: list[NuitkaTarget] = Field(min_length=1)
    smoke: BuiltExeSmoke | None = None
    # 编译时才要设的环境变量。值里可以用 ${REPO_ROOT}——构建机上的仓库路径每一轮都不同
    # （目录名带 commit），所以像 CCACHE_BASEDIR 这种「把源码路径归一化好让缓存能复用」的
    # 变量，只能在构建机上现算。
    env: dict[str, str] = Field(default_factory=dict)
    # 编译期间要挪开的目录。Electron 的 node_modules 被 hoist 到 Python 包扫描路径下时，
    # Nuitka 会去扫它——编译时间暴涨，还可能把前端的东西打进包。编译前挪走，之后必须原样挪回，
    # 挪不回去要当场停：留下一个没有 node_modules 的工作树，下一步 Electron 构建会莫名其妙地失败。
    isolate_dirs: list[str] = Field(default_factory=list)


class ElectronBuild(BaseModel):
    """Electron 外壳与安装包。NSIS 由 electron-builder 自带，不要求构建机 PATH 上有独立
    makensis——多要一件工具就把本来能用的构建机挡在第一步。"""

    model_config = ConfigDict(extra="forbid")

    # 前端包管理器与它的两条命令。默认那套是最常见的组合，产品用别的就在这里说。
    # 写死在技能里，等于把「换个包管理器就得改技能」写进设计。
    package_manager: str = "pnpm"
    # 装依赖。锁文件是依赖的唯一权威，出包时静默改写它意味着这次出的包
    # 用的依赖跟仓库记录的不是一套，所以默认带 --frozen-lockfile。
    install_args: list[str] = Field(
        default_factory=lambda: ["install", "--frozen-lockfile", "--prefer-offline"]
    )
    # 打前端的 package.json 脚本名。
    build_script: str = "build"
    # 打完 `--win dir` 之后产物落在哪（相对 desktop_dir）。
    unpacked_dir: str = "dist/win-unpacked"
    dist_dir: str = "dist"
    compression: Literal["store", "normal", "maximum"] = "maximum"
    compression_env: str | None = "MMW_ELECTRON_BUILDER_COMPRESSION"
    # 出安装包这一步交给 electron-builder，还是产品自己那套交付格式。
    installer: Literal["electron_builder", "repo_hook"] = "electron_builder"



class DiagnoseRule(BaseModel):
    """产品自己的一条日志翻译规则。

    通用规则表在技能里（`diagnose_core.RULES`），因为它匹配的是引擎和打包工具打印的文字。
    这里补的是这个产品自己的日志才有的模式，排在通用表前面——产品比技能更知道自己那条日志
    长什么样。

    `fingerprint` 的前缀决定引擎怎么分派：`transient:` 直接重跑，`env:` 交驱动 agent 处置，
    其余进 P1 修复。写错前缀等于把一条环境问题派给代码修复。
    """

    model_config = ConfigDict(extra="forbid")

    pattern: str = Field(min_length=1)
    name: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)
    remediation: str = Field(min_length=1)


class ReleaseAdapterManifestV2Fields(BaseModel):
    """v2 新增段。v1 钥匙这些全部缺席，两版并存到迁移收尾。"""

    model_config = ConfigDict(extra="forbid")

    python_backend: PythonBackend | None = None
    electron: ElectronBuild | None = None
    toolchain: list[str] = Field(default_factory=list)


class ReleaseAdapterManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion
    product: str = Field(min_length=1)
    build_target: BuildTarget
    build_machine: BuildMachine | None = None
    # v2 段。v1 钥匙不写，写了即报错——版本号与内容必须一致，否则装配器会按 v1 走却
    # 静默忽略这几段，出来一份看着对、其实少了编译步骤的脚本。
    python_backend: PythonBackend | None = None
    electron: ElectronBuild | None = None
    toolchain: list[str] = Field(default_factory=list)
    # 诊断：产品自己跑哪几条检查、认哪几条自己的日志模式、编译产物在哪。
    diagnose_branches: list[list[str]] = Field(default_factory=list)
    diagnose_rules: list[DiagnoseRule] = Field(default_factory=list)
    diagnose_core_exe_glob: str | None = None
    stages: list[StageSpec]
    diagnose: list[str] = Field(min_length=1)
    build_hooks: ReleaseBuildHooks
    # ── 以下都是自愈与观测的可选装备 ──────────────────────────────────────
    #
    # 一个产品第一次出包时，这些一个都没有：没有派生物要重生，没有闸门要跑，
    # 没有日志系统要接。把它们设成必填，等于要求「能出包」之前先写四份仓库侧
    # Python——而那正是这个技能存在的理由的反面。
    #
    # 没声明就没有那一步：引擎跳过，不报错，也不假装做过。
    fix_executor: list[str] | None = None
    editable_paths: list[str] = Field(default_factory=list)
    protection_source: str | None = None
    post_fix_gate: list[str] | None = None
    derive: list[str] | None = None
    event_sink: list[str] | None = None

    @model_validator(mode="after")
    def _version_matches_content(self) -> "ReleaseAdapterManifest":
        if self.editable_paths and self.protection_source is None:
            raise ValueError(
                "声明了 editable_paths 就必须声明 protection_source——"
                "允许自动修复改文件，却没有任何硬禁止路径，等于闸门整个是开的"
            )
        v2_fields = {
            "python_backend": self.python_backend,
            "electron": self.electron,
            "toolchain": self.toolchain or None,
            "diagnose_branches": self.diagnose_branches or None,
            "diagnose_rules": self.diagnose_rules or None,
            "diagnose_core_exe_glob": self.diagnose_core_exe_glob,
        }
        present = sorted(name for name, value in v2_fields.items() if value is not None)
        v2_hooks = sorted(
            name
            for name in ("backend_verify", "installer")
            if getattr(self.build_hooks, name) is not None
        )
        if self.schema_version == "1":
            if present or v2_hooks:
                raise ValueError(
                    "schema_version=1 的钥匙不能带 v2 段: "
                    + ", ".join([*present, *v2_hooks])
                )
            if self.build_hooks.runtime_prepare is None:
                raise ValueError("schema_version=1 的钥匙必须声明 build_hooks.runtime_prepare")
            return self
        if self.python_backend is None:
            raise ValueError("schema_version=2 的钥匙必须声明 python_backend")
        if not self.toolchain:
            raise ValueError("schema_version=2 的钥匙必须声明 toolchain")
        if self.electron and self.electron.installer == "repo_hook":
            if self.build_hooks.installer is None:
                raise ValueError(
                    "electron.installer=repo_hook 必须同时声明 build_hooks.installer——"
                    "否则装配出来的脚本走到出安装包那一步是空的"
                )
        elif self.build_hooks.installer is not None:
            raise ValueError(
                "build_hooks.installer 只在 electron.installer=repo_hook 时有意义"
            )
        return self


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _fail(message: str) -> int:
    print(f"INVALID: {message}", file=sys.stderr)
    return 3


def cmd_validate_manifest(path: str) -> int:
    try:
        manifest = ReleaseAdapterManifest.model_validate_json(_read(path))
    except Exception as exc:  # noqa: BLE001 - CLI must report validation failure.
        return _fail(f"manifest 不合规: {exc}")
    print(manifest.model_dump_json())
    return 0


def cmd_validate_event(path: str) -> int:
    try:
        ReleaseLoopEvent.model_validate_json(_read(path))
    except Exception as exc:  # noqa: BLE001 - CLI must report validation failure.
        return _fail(f"event 不合规: {exc}")
    return 0


def cmd_classify_findings(path: str) -> int:
    try:
        doc = json.loads(_read(path))
        findings = [
            ReleaseFinding.model_validate(item) for item in doc.get("findings", [])
        ]
    except Exception as exc:  # noqa: BLE001 - CLI must report validation failure.
        return _fail(f"findings 不合规: {exc}")

    failing = [item for item in findings if item.status == "fail"]
    highest = None
    if failing:
        highest = min(
            (item.tier for item in failing), key=lambda tier: _TIER_ORDER[tier]
        )
    print(
        json.dumps(
            {
                "highest_tier": highest,
                "failing": [
                    {
                        "tier": item.tier,
                        "root_cause_fingerprint": item.root_cause_fingerprint,
                        "name": item.name,
                        "dimension": item.dimension,
                        "locator": item.locator,
                        "remediation": item.remediation,
                    }
                    for item in failing
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="release_contracts")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate-manifest", "classify-findings", "validate-event"):
        sp = sub.add_parser(name)
        sp.add_argument("path", help="文件路径，或 - 读 stdin")
    args = parser.parse_args(argv)
    return {
        "validate-manifest": cmd_validate_manifest,
        "classify-findings": cmd_classify_findings,
        "validate-event": cmd_validate_event,
    }[args.cmd](args.path)


if __name__ == "__main__":
    raise SystemExit(main())
