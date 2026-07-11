import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1]
ASSEMBLER = SCRIPTS / "release_script_assembler.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "release-assembler"
TEMPLATE = SCRIPTS / "release_templates" / "windows_electron_python.ps1.tmpl"

sys.path.insert(0, str(SCRIPTS))
from release_contracts import BuildTarget, ReleaseBuildHooks  # noqa: E402


def _assemble(
    adapter: Path, output: Path, context_output: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ASSEMBLER),
            "assemble",
            "--adapter",
            str(adapter),
            "--repo-root",
            str(adapter.parent),
            "--output",
            str(output),
            "--context-output",
            str(context_output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _check(script: Path, context: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ASSEMBLER),
            "check",
            "--script",
            str(script),
            "--context",
            str(context),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_assemble_core_exe_writes_bom_script_and_validated_context(
    tmp_path: Path,
) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"

    result = _assemble(FIXTURES / "core-exe.adapter.json", output, context_output)

    assert result.returncode == 0, result.stderr
    assert output.read_bytes().startswith(b"\xef\xbb\xbf")
    context = json.loads(context_output.read_text(encoding="utf-8"))
    assert context["product"] == "desktop-core"
    assert context["build_target"]["runtime_lane"] == "core_exe"
    assert context["build_target"]["native_ext_dll"] == []
    assert context["build_hooks"]["runtime_prepare"] == ["prepare-runtime"]
    assert context["render_metadata"]["stages"] == [1, 2, 3, 4, 5, 6, 7]
    assert len(context["render_metadata"]["hook_calls"]) == 5
    assert (
        BuildTarget.model_validate(context["build_target"]).runtime_lane == "core_exe"
    )
    assert ReleaseBuildHooks.model_validate(context["build_hooks"]).artifact_scan == [
        "scan-artifact"
    ]


def test_assemble_embedded_python_preserves_build_teeth_deterministically(
    tmp_path: Path,
) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"

    first = _assemble(FIXTURES / "embedded-python.adapter.json", output, context_output)
    first_script = output.read_bytes()
    first_context = context_output.read_bytes()
    second = _assemble(
        FIXTURES / "embedded-python.adapter.json", output, context_output
    )

    assert first.returncode == second.returncode == 0
    assert output.read_bytes() == first_script
    assert context_output.read_bytes() == first_context
    context = json.loads(first_context)
    build_target = BuildTarget.model_validate(context["build_target"])
    assert build_target.deps_extra == "desktop-runtime"
    assert build_target.native_ext_dll[0].pyd_package == "native_pkg"
    assert build_target.native_ext_dll[1].dest == "dist_root"
    assert build_target.nuitka_include == ["native_pkg", "runtime_pkg"]
    assert build_target.nuitka_nofollow == ["scipy"]
    assert ReleaseBuildHooks.model_validate(context["build_hooks"]).asset_parity == [
        "verify-assets"
    ]


def test_assemble_rejects_unsafe_desktop_path_without_replacing_outputs(
    tmp_path: Path,
) -> None:
    adapter = json.loads((FIXTURES / "core-exe.adapter.json").read_text())
    adapter["build_target"]["desktop_dir"] = "../desktop"
    adapter_path = tmp_path / "unsafe.adapter.json"
    adapter_path.write_text(json.dumps(adapter), encoding="utf-8")
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    output.write_text("old script", encoding="utf-8")
    context_output.write_text("old context", encoding="utf-8")

    result = _assemble(adapter_path, output, context_output)

    assert result.returncode != 0
    assert output.read_text(encoding="utf-8") == "old script"
    assert context_output.read_text(encoding="utf-8") == "old context"


def test_assemble_rejects_windows_absolute_desktop_path(tmp_path: Path) -> None:
    adapter = json.loads((FIXTURES / "core-exe.adapter.json").read_text())
    adapter["build_target"]["desktop_dir"] = r"C:\desktop"
    adapter_path = tmp_path / "windows-absolute.adapter.json"
    adapter_path.write_text(json.dumps(adapter), encoding="utf-8")

    result = _assemble(
        adapter_path, tmp_path / "release.ps1", tmp_path / "release-context.json"
    )

    assert result.returncode != 0


@pytest.mark.parametrize(
    "mutation",
    [
        lambda adapter: adapter["build_target"].update({"desktop_dir": "/desktop"}),
        lambda adapter: adapter["build_hooks"].update({"runtime_prepare": []}),
        lambda adapter: adapter.update({"unexpected": True}),
        lambda adapter: adapter["build_target"]["native_ext_dll"].append(
            {
                "reason": "invalid package destination",
                "dll_names": ["broken.dll"],
                "dll_source": "repo",
                "dest": "pyd_package_dir",
            }
        ),
    ],
    ids=["absolute-path", "empty-required-hook", "unknown-field", "invalid-native-dll"],
)
def test_assemble_rejects_invalid_adapter_without_replacing_outputs(
    tmp_path: Path, mutation: object
) -> None:
    adapter = json.loads((FIXTURES / "core-exe.adapter.json").read_text())
    mutation(adapter)  # type: ignore[operator]
    adapter_path = tmp_path / "invalid.adapter.json"
    adapter_path.write_text(json.dumps(adapter), encoding="utf-8")
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    output.write_text("old script", encoding="utf-8")
    context_output.write_text("old context", encoding="utf-8")

    result = _assemble(adapter_path, output, context_output)

    assert result.returncode != 0
    assert output.read_text(encoding="utf-8") == "old script"
    assert context_output.read_text(encoding="utf-8") == "old context"


def test_check_accepts_matching_bom_script_and_context(tmp_path: Path) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    assert (
        _assemble(FIXTURES / "core-exe.adapter.json", output, context_output).returncode
        == 0
    )

    result = _check(output, context_output)

    assert result.returncode == 0, result.stderr


def test_assemble_keeps_existing_context_when_script_replacement_fails(
    tmp_path: Path,
) -> None:
    output = tmp_path / "release.ps1"
    output.mkdir()
    context_output = tmp_path / "release-context.json"
    context_output.write_text("old context", encoding="utf-8")

    result = _assemble(FIXTURES / "core-exe.adapter.json", output, context_output)

    assert result.returncode != 0
    assert context_output.read_text(encoding="utf-8") == "old context"


@pytest.mark.parametrize(
    "fixture", ["core-exe.adapter.json", "embedded-python.adapter.json"]
)
def test_assemble_renders_the_same_ordered_seven_stage_pipeline(
    tmp_path: Path, fixture: str
) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    assert _assemble(FIXTURES / fixture, output, context_output).returncode == 0
    script = output.read_text(encoding="utf-8-sig")

    positions = [script.index(f'Step "[{stage}/7]') for stage in range(1, 8)]
    assert positions == sorted(positions)
    for tool in ("python", "pnpm", "node", "uv", "makensis"):
        assert f"'{tool}'" in script
    for token in (
        "--frozen-lockfile",
        "--prefer-offline",
        "'run', 'build'",
        "electron-builder",
        "--win",
        "--prepackaged",
    ):
        assert token in script


def test_assemble_delegates_runtime_build_to_repo_hook_for_both_lanes(
    tmp_path: Path,
) -> None:
    # 造运行时是每个产品独特的一步(嵌入式 Python / 编译 / 补 DLL / 落资产各产品不同),
    # 按设计留在仓库、由钥匙的 runtime_prepare 钩子整段准备;通用模板两条车道都不在模板里
    # 通用地造包(不复刻 Nuitka / DLL),只把它交给紧随其后的 runtime_prepare 钩子。
    core_script = tmp_path / "core.ps1"
    core_context = tmp_path / "core-context.json"
    embedded_script = tmp_path / "embedded.ps1"
    embedded_context = tmp_path / "embedded-context.json"
    assert (
        _assemble(
            FIXTURES / "core-exe.adapter.json", core_script, core_context
        ).returncode
        == 0
    )
    assert (
        _assemble(
            FIXTURES / "embedded-python.adapter.json", embedded_script, embedded_context
        ).returncode
        == 0
    )

    for script_path in (core_script, embedded_script):
        script = script_path.read_text(encoding="utf-8-sig")
        # 两条车道都不在模板里通用地造包
        assert "nuitka" not in script.lower()
        assert "Remove-PythonBytecode" not in script
        assert "Copy-NativeExtensionDll" not in script
        assert "--include-package" not in script
        # 都把造运行时交给仓库的 runtime_prepare 钩子
        assert "prepared by the repository runtime_prepare hook" in script
        assert "-Name 'runtime_prepare'" in script


def test_check_rejects_script_missing_one_of_the_seven_stages(tmp_path: Path) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    assert (
        _assemble(FIXTURES / "core-exe.adapter.json", output, context_output).returncode
        == 0
    )
    output.write_text(
        output.read_text(encoding="utf-8-sig").replace(
            'Step "[5/7] Build win-unpacked"', ""
        ),
        encoding="utf-8-sig",
    )

    result = _check(output, context_output)

    assert result.returncode != 0


def test_template_and_neutral_fixtures_hold_no_product_specific_release_rules() -> None:
    product_specific_terms = (
        "duck",
        "parrot",
        "hedgehog",
        "agentflow",
        "scripts/release/",
    )
    template = TEMPLATE.read_text(encoding="utf-8").lower()

    assert not any(term in template for term in product_specific_terms)
    for fixture in FIXTURES.glob("*.json"):
        assert not any(
            term in fixture.read_text(encoding="utf-8").lower()
            for term in product_specific_terms
        )


@pytest.mark.parametrize(
    ("fixture", "optional_skipped"),
    [("core-exe.adapter.json", True), ("embedded-python.adapter.json", False)],
)
def test_check_reports_fixed_hook_lifecycle_contract(
    tmp_path: Path, fixture: str, optional_skipped: bool
) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    assert _assemble(FIXTURES / fixture, output, context_output).returncode == 0

    result = _check(output, context_output)

    assert result.returncode == 0, result.stderr
    hook_calls = json.loads(result.stdout)["hook_calls"]
    assert [(item["stage"], item["name"], item["phase"]) for item in hook_calls] == [
        (3, "runtime_prepare", "runtime_ready"),
        (3, "asset_parity", "runtime_ready"),
        (3, "credential_proof", "runtime_ready"),
        (6, "artifact_scan", "artifact_ready"),
        (7, "package_integrity", "release_ready"),
    ]
    assert [item["skipped"] for item in hook_calls] == [
        False,
        optional_skipped,
        optional_skipped,
        False,
        False,
    ]


def test_check_rejects_metadata_that_claims_an_unconfigured_hook_ran(
    tmp_path: Path,
) -> None:
    output = tmp_path / "release.ps1"
    context_output = tmp_path / "release-context.json"
    assert (
        _assemble(FIXTURES / "core-exe.adapter.json", output, context_output).returncode
        == 0
    )
    context = json.loads(context_output.read_text(encoding="utf-8"))
    context["render_metadata"]["hook_calls"][1]["skipped"] = False
    context_output.write_text(json.dumps(context), encoding="utf-8")

    result = _check(output, context_output)

    assert result.returncode != 0


@pytest.mark.parametrize(
    "unsafe_token", ["bad&hook", "bad;hook", "bad|hook", "bad\nhook", "bad\x00hook"]
)
def test_assemble_rejects_shell_control_characters_in_hook_argv(
    tmp_path: Path, unsafe_token: str
) -> None:
    adapter = json.loads((FIXTURES / "core-exe.adapter.json").read_text())
    adapter["build_hooks"]["runtime_prepare"] = [unsafe_token]
    adapter_path = tmp_path / "unsafe-hook.adapter.json"
    adapter_path.write_text(json.dumps(adapter), encoding="utf-8")

    result = _assemble(
        adapter_path, tmp_path / "release.ps1", tmp_path / "release-context.json"
    )

    assert result.returncode != 0


def test_assemble_escapes_a_single_quote_hook_token_without_shell_evaluation(
    tmp_path: Path,
) -> None:
    adapter = json.loads((FIXTURES / "core-exe.adapter.json").read_text())
    adapter["build_hooks"]["runtime_prepare"] = ["prepare'o", "--label", "O'Brien"]
    adapter_path = tmp_path / "quoted-hook.adapter.json"
    adapter_path.write_text(json.dumps(adapter), encoding="utf-8")
    output = tmp_path / "release.ps1"

    result = _assemble(adapter_path, output, tmp_path / "release-context.json")

    assert result.returncode == 0, result.stderr
    script = output.read_text(encoding="utf-8-sig")
    assert "'prepare''o'" in script
    assert "'O''Brien'" in script
    assert "Invoke-Expression" not in script
    assert "cmd.exe /c" not in script


def test_assembler_parses_under_declared_minimum_python() -> None:
    # 回归：assemble stage 以裸 python 调本模块，构建机 python 可能是声明的最低 3.11；
    # native DLL 拷贝行的路径拼接曾放进 f-string 表达式内含反斜杠，3.11 下模块解析即 SyntaxError。
    probe = subprocess.run(
        [
            "uv",
            "run",
            "--python",
            "3.11",
            "python",
            "-c",
            f"import ast; ast.parse(open({str(ASSEMBLER)!r}).read())",
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 and "No interpreter found" in (
        probe.stderr + probe.stdout
    ):
        pytest.skip("环境无 Python 3.11 解释器，跳过最低版本解析守卫")
    assert probe.returncode == 0, probe.stderr
