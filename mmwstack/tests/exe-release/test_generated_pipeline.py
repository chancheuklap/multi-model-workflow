"""Inspect actual assembled scripts with the PowerShell parser, without running a build."""

import json
import re
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from test_minimal_key import MINIMAL_KEY
from test_release_script_assembler import RUNTIME_ASSETS, VENDOR_ARTIFACT, _assemble, _key

POWERSHELL = shutil.which("pwsh")
pytestmark = pytest.mark.skipif(not POWERSHELL, reason="PowerShell AST checks require pwsh")


def _inspect(script):
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-File",
         str(Path(__file__).with_name("generated-pipeline.ps1")), "-Path", str(script)],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _pipeline(tmp_path, manifest):
    result, script, _ = _assemble(tmp_path, manifest)
    assert result.returncode == 0, result.stderr
    return _inspect(script)


def _calls(pipeline, name):
    return [call for call in pipeline["commands"] if (call["name"] or "").lower() == name.lower()]


def _arg(call, name):
    return next(v for k, v in call["named"].items() if k.lower() == name.lower())


def _strings(call, name):
    return _arg(call, name)["strings"]


def _paths(call, name):
    literals = _strings(call, name)
    return [value for value in literals if value.lower() != "join-path"]


def _compile(pipeline):
    return [entry for entry in pipeline["assignments"] if entry["variable"].lower() == "argv"]


def _order(*commands):
    offsets = [command["offset"] for command in commands]
    assert offsets == sorted(set(offsets))


def test_minimal_pipeline_gates_the_generated_artifacts(tmp_path):
    manifest = deepcopy(MINIMAL_KEY)
    manifest["python_backend"]["include_packages"] += ["moderngl", "glcontext"]
    p = _pipeline(tmp_path, manifest)
    labels = [call["positional"][0]["strings"][0] for call in _calls(p, "Step")]
    assert [re.sub(r"^\[\d+/\d+\]\s+", "", label) for label in labels] == [
        "Prepare build machine", "Validate prerequisites", "Install frontend dependencies",
        "Compile Python backend", "Verify compiled backend", "Build Electron application",
        "Build win-unpacked", "Scan release artifacts", "Build installer", "Verify package integrity",
    ]
    (argv,) = _compile(p)
    assert argv["value"]["strings"][:7] == ["uv", "run", "--extra", "newcomer", "python", "-m", "nuitka"]
    (smoke,) = _calls(p, "Invoke-BuiltExeSmoke")
    (source,) = _calls(p, "Assert-NoBusinessSource")
    (installer,) = _calls(p, "Assert-InstallerProduced")
    _order(argv, smoke, source, installer)
    assert _strings(source, "SourceRoots") == ["src"]
    assert _arg(source, "Roots")["variables"] == ["UnpackedDir", "RepoRoot"]
    assert _paths(source, "Roots") == ["desktop-newcomer/python-runtime/backend"]
    assert _paths(installer, "Glob") == [manifest["build_target"]["installer_glob"]]
    assert not _calls(p, "Invoke-ReleaseHook")
    assert not _calls(p, "Get-VendorArtifact")
    assert not _calls(p, "Assert-LicensesShipped")
    assert not _calls(p, "Copy-RuntimeAsset")
    assert not _calls(p, "Assert-CompiledModules")
    assert not _calls(p, "release_script_assembler.py")
    assert not any(token.startswith("--report=") for token in argv["value"]["strings"])


@pytest.mark.parametrize("custom_installer", [False, True])
def test_configured_pipeline_routes_inputs_and_proves_outputs_in_order(tmp_path, custom_installer):
    doc = _key()
    target = doc["build_target"]
    backend = doc["python_backend"]
    doc["toolchain"] = ["makensis"]
    doc["runtime_assets"] = deepcopy(RUNTIME_ASSETS)
    backend["required_modules_file"] = "scripts/release/required-modules.txt"
    backend["targets"].append({
        "name": "launcher", "exe": "launcher.exe", "entrypoint": "src/runtime_backend/launcher.py",
    })
    backend["console"] = custom_installer
    artifact = deepcopy(VENDOR_ARTIFACT)
    artifact["members"].append({
        "file": "LICENSE.txt", "dest": "resources/ffmpeg/LICENSE.txt",
        "sha256_key": "license_sha256", "license": True,
    })
    artifact["notices"] = ["resources/ffmpeg/NOTICE-ffmpeg.txt"]
    doc["vendor_artifacts"] = [artifact]
    if custom_installer:
        doc["electron"]["installer"] = "repo_hook"
        doc["build_hooks"]["installer"] = ["true", "--hook", "installer"]
        target["package_tree"] = "runtime/windows-release/product-v*/bundle"

    p = _pipeline(tmp_path, doc)
    hooks = {_strings(call, "Name")[0]: call for call in _calls(p, "Invoke-ReleaseHook")}
    assert {name: _strings(call, "Argv") for name, call in hooks.items()} == {
        name: argv for name, argv in doc["build_hooks"].items() if argv is not None
    }
    (vendor,) = _calls(p, "Get-VendorArtifact")
    assert _strings(vendor, "Name") == ["ffmpeg"]
    assert _paths(vendor, "LockPath") == [artifact["lock"]]
    assert _strings(vendor, "Members") == [
        field for member in artifact["members"] for field in
        ("File", member["file"], "Dest", member["dest"], "Sha256Key", member["sha256_key"])
    ]
    repo_asset, package_asset = _calls(p, "Copy-RuntimeAsset")
    assert _strings(repo_asset, "Source") == ["src/app/assets"]
    assert _paths(repo_asset, "Dest") == ["desktop/python-runtime/runtime-assets/app/assets"]
    assert _strings(package_asset, "SourcePackage") == ["rapidocr_onnxruntime"]
    assert _strings(package_asset, "Members") == ["config.yaml", "models"]
    assert _paths(package_asset, "Dest") == ["desktop/python-runtime/runtime-assets/app/rapidocr"]
    compile_assignments = _compile(p)
    assert len(compile_assignments) == 2
    compile_calls = [
        call for call in _calls(p, "Invoke-Checked")
        if "argv" in _arg(call, "Command")["variables"]
    ]
    assert len(compile_calls) == len(compile_assignments)
    for (assignment, call, compile_target) in zip(compile_assignments, compile_calls, backend["targets"]):
        tokens = assignment["value"]["strings"]
        assert tokens[:7] == backend["runner"] + ["-m", "nuitka"]
        assert {
            "--standalone", "--jobs=10", "--windows-icon-from-ico=", backend["icon"],
            f"--output-filename={compile_target['exe']}", compile_target["entrypoint"],
            "--include-data-dir=", "src/runtime_backend/assets", "=runtime_backend/assets",
            "=native_pkg/python3.dll", "=native_pkg/vcruntime140_1.dll", "=msvcp140.dll",
            *(f"--include-package={x}" for x in backend["include_packages"]),
            *(f"--include-package-data={x}" for x in backend["include_package_data"]),
            *(f"--include-module={x}" for x in backend["include_modules"]),
            *(f"--nofollow-import-to={x}" for x in backend["nofollow_imports"]),
            *backend["extra_flags"],
        } <= set(tokens)
        assert ("--windows-console-mode=disable" in tokens) is not custom_installer
        assert "--report=" in tokens
        _order(assignment, call)
    (modules,) = _calls(p, "Assert-CompiledModules")
    assert _paths(modules, "RequiredFile") == [backend["required_modules_file"]]
    assert _paths(modules, "Reports") == [
        f"runtime/.mmw-nuitka-reports/{item['name']}.xml" for item in backend["targets"]
    ]
    (payload,) = _calls(p, "Assert-OnefilePayloads")
    assert _paths(payload, "Exes") == [
        f"desktop/python-runtime/backend/{item['exe']}" for item in backend["targets"]
    ]
    (cleanup,) = _calls(p, "Remove-CompilerIntermediates")
    assert _paths(cleanup, "OutputDir") == _paths(payload, "OutputDir") == [
        "desktop/python-runtime/backend"
    ]
    (notice,) = _calls(p, "Assert-LicensesShipped")
    assert _strings(notice, "Licenses") == [
        "Name", "ffmpeg", "Path", "resources/ffmpeg/LICENSE.txt",
        "Name", "ffmpeg", "Path", "resources/ffmpeg/NOTICE-ffmpeg.txt",
    ]
    (proof,) = _calls(p, "Assert-InstallerProduced")
    assert _paths(proof, "Glob") == [target["installer_glob"]]
    nsis = [call for call in _calls(p, "pnpm")
            if any(arg["strings"] == ["nsis"] for arg in call["positional"])]
    if custom_installer:
        assert not nsis
        installer = hooks["installer"]
        assert _strings(installer, "Phase") == ["installer_ready"]
        assert _paths(notice, "PackageDir") == [target["package_tree"]]
    else:
        (installer,) = nsis
        assert _arg(notice, "PackageDir") == {"strings": [], "variables": ["UnpackedDir"]}
    _order(
        vendor, hooks["runtime_prepare"], repo_asset, package_asset, hooks["asset_parity"],
        hooks["credential_proof"], compile_assignments[0], compile_calls[0],
        compile_assignments[1], compile_calls[1], modules, payload, cleanup,
        hooks["backend_verify"], hooks["artifact_scan"], installer, notice,
        hooks["package_integrity"], proof,
    )
