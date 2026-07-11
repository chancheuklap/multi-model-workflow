import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1]
ASSEMBLER = SCRIPTS / "release_script_assembler.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "release-assembler"

sys.path.insert(0, str(SCRIPTS))
from release_contracts import BuildTarget, ReleaseBuildHooks  # noqa: E402


def _assemble(adapter: Path, output: Path, context_output: Path) -> subprocess.CompletedProcess[str]:
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


def test_assemble_core_exe_writes_bom_script_and_validated_context(tmp_path: Path) -> None:
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
    assert context["render_metadata"] == {"stages": [], "hook_calls": []}
    assert BuildTarget.model_validate(context["build_target"]).runtime_lane == "core_exe"
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
    second = _assemble(FIXTURES / "embedded-python.adapter.json", output, context_output)

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
    assert _assemble(FIXTURES / "core-exe.adapter.json", output, context_output).returncode == 0

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
