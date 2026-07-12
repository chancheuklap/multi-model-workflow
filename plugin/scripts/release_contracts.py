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

SchemaVersion = Literal["1"]
Tier = Literal["P0", "P1", "P2"]
Status = Literal["ok", "warn", "fail", "deferred"]

_TIER_ORDER = {"P0": 0, "P1": 1, "P2": 2}


class ReleaseFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion
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

    schema_version: SchemaVersion
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
    = 客户跑到该功能就空 ImportError 整批崩（如 uharfbuzz 字幕、hedgehog 后端）。
    """

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)
    dll_names: list[str] = Field(min_length=1)
    dll_source: Literal["compile_interpreter", "repo"] = "compile_interpreter"
    dest: Literal["pyd_package_dir", "dist_root"]
    pyd_package: str | None = None

    @model_validator(mode="after")
    def _pyd_package_required_for_package_dir(self) -> "NativeExtDll":
        if self.dest == "pyd_package_dir" and not self.pyd_package:
            raise ValueError("dest=pyd_package_dir 必须给 pyd_package")
        return self


class BuildTarget(BaseModel):
    """钥匙的 build 齿：声明本产品出包差异的**构建目标**（修正1 验齿 + 修正2 深抽）。

    非自由 argv——拼脚本器只认这里声明的产品差异，Mac 上跑裸 python 插不进；
    验钥匙拿这些字段对产品活状态核对，过时即 fail-loud（修正4 命根子）。
    """

    model_config = ConfigDict(extra="forbid")

    desktop_dir: str = Field(min_length=1)
    runtime_lane: RuntimeLane
    entry_module: str = Field(min_length=1)
    installer_brand: str = Field(min_length=1)
    # 产品成品安装包在源码树里的落点（仓库相对 glob）。出包成功后引擎按此把安装包收拢到统一交付目录
    # （$RELEASE_DELIVERY_ROOT/<product>/），不再让客户去 commit 哈希构建目录里翻。产品各自落点不同
    # （duck 在 runtime/assistant-release，parrot/hedgehog 在 desktop-*/dist），故随钥匙声明、引擎零产品知识。
    installer_glob: str | None = None
    deps_extra: str | None = None
    asset_roots: list[str] = Field(default_factory=list)
    native_ext_dll: list[NativeExtDll] = Field(default_factory=list)
    nuitka_include: list[str] = Field(default_factory=list)
    nuitka_nofollow: list[str] = Field(default_factory=list)


class ReleaseBuildHooks(BaseModel):
    """流水线模板按具名阶段消费的仓库钩子 argv。"""

    model_config = ConfigDict(extra="forbid")

    runtime_prepare: list[str] = Field(min_length=1)
    artifact_scan: list[str] = Field(min_length=1)
    package_integrity: list[str] = Field(min_length=1)
    asset_parity: list[str] | None = None
    credential_proof: list[str] | None = None


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


class ReleaseAdapterManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion
    product: str = Field(min_length=1)
    build_target: BuildTarget
    build_machine: BuildMachine | None = None
    stages: list[StageSpec]
    diagnose: list[str] = Field(min_length=1)
    derive: list[str] = Field(min_length=1)
    editable_paths: list[str]
    protection_source: str = Field(min_length=1)
    build_hooks: ReleaseBuildHooks
    post_fix_gate: list[str] = Field(min_length=1)
    fix_executor: list[str] = Field(min_length=1)
    event_sink: list[str] = Field(min_length=1)


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
