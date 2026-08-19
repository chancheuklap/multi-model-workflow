"""v2 装配：一份模板，步骤由钥匙声明了什么决定。

v1 的两条车道各有一份模板，步号写死在模板里。v2 只有一份，步号是算出来的——所以这里验的是
「钥匙里有什么，脚本里就有哪几步」，而不是「这条车道该有几步」。
"""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIX = Path(__file__).resolve().parent / "fixtures" / "release-assembler"

sys.path.insert(0, str(SCRIPTS))
import release_contracts as rc  # noqa: E402



def _key():
    return json.loads((FIX / "v2.adapter.json").read_text(encoding="utf-8"))


def _assemble(tmp_path, doc):
    adapter = tmp_path / "key.json"
    adapter.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    script = tmp_path / "release.ps1"
    context = tmp_path / "release-context.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "release_script_assembler.py"),
            "assemble",
            "--adapter",
            str(adapter),
            "--repo-root",
            str(tmp_path),
            "--output",
            str(script),
            "--context-output",
            str(context),
        ],
        capture_output=True,
        text=True,
    )
    return result, script, context


def _steps(script: Path) -> list[str]:
    text = script.read_text(encoding="utf-8-sig")
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith('Step "[')
    ]


def test_assembles_and_the_script_parses_as_one_pipeline(tmp_path):
    result, script, context = _assemble(tmp_path, _key())
    assert result.returncode == 0, result.stderr
    steps = _steps(script)
    # 第 0 步是构建机准备，它是 build_machine 声明的，不算进流水线编号的分母。
    assert steps[0].startswith('Step "[0/')
    titles = [step.split("] ", 1)[1].rstrip('"') for step in steps]
    assert titles == [
        "Prepare build machine",
        "Validate prerequisites",
        "Install frontend dependencies",
        "Prepare runtime",
        "Compile Python backend",
        "Verify compiled backend",
        "Build Electron application",
        "Build win-unpacked",
        "Scan release artifacts",
        "Build installer",
        "Verify package integrity",
    ]
    doc = json.loads(context.read_text(encoding="utf-8"))
    assert doc["schema_version"] == "2"
    assert [step["title"] for step in doc["render_metadata"]["steps"]] == titles[1:]


def test_compile_step_carries_every_nuitka_flag_from_the_key(tmp_path):
    _, script, _ = _assemble(tmp_path, _key())
    text = script.read_text(encoding="utf-8-sig")
    key = _key()["python_backend"]
    for package in key["include_packages"]:
        assert f"'--include-package={package}'" in text
    for package in key["include_package_data"]:
        assert f"'--include-package-data={package}'" in text
    for module in key["nofollow_imports"]:
        assert f"'--nofollow-import-to={module}'" in text
    for target in key["targets"]:
        assert f"'--output-filename={target['exe']}'" in text
        assert target["entrypoint"] in text


def test_a_key_without_electron_drops_the_electron_steps(tmp_path):
    doc = deepcopy(_key())
    doc["electron"] = None
    doc["build_hooks"]["installer"] = None
    result, script, _ = _assemble(tmp_path, doc)
    assert result.returncode == 0, result.stderr
    titles = [step.split("] ", 1)[1].rstrip('"') for step in _steps(script)]
    assert "Build Electron application" not in titles
    assert "Build win-unpacked" not in titles
    assert "Compile Python backend" in titles


def test_repo_hook_installer_replaces_the_electron_builder_step(tmp_path):
    doc = deepcopy(_key())
    doc["electron"]["installer"] = "repo_hook"
    doc["build_hooks"]["installer"] = ["true", "--hook", "installer"]
    result, script, context = _assemble(tmp_path, doc)
    assert result.returncode == 0, result.stderr
    text = script.read_text(encoding="utf-8-sig")
    assert "electron-builder --win nsis" not in text
    assert "-Name 'installer'" in text
    calls = json.loads(context.read_text(encoding="utf-8"))["render_metadata"][
        "hook_calls"
    ]
    assert {"name": "installer", "phase": "installer_ready"}.items() <= next(
        call for call in calls if call["name"] == "installer"
    ).items()


def test_repo_hook_installer_without_the_hook_is_rejected(tmp_path):
    doc = deepcopy(_key())
    doc["electron"]["installer"] = "repo_hook"
    doc["build_hooks"]["installer"] = None
    result, script, context = _assemble(tmp_path, doc)
    assert result.returncode != 0
    assert "build_hooks.installer" in result.stderr
    assert not script.exists() and not context.exists()


def test_nofollow_that_blocks_a_smoke_module_stops_before_assembling(tmp_path):
    """编译一次几十分钟。nofollow 把 smoke 要 import 的模块挡掉了，要在装配这一刻就停。"""
    doc = deepcopy(_key())
    doc["python_backend"]["nofollow_imports"].append(
        doc["python_backend"]["smoke"]["modules"][0]
    )
    result, script, _ = _assemble(tmp_path, doc)
    assert result.returncode != 0
    assert "nofollow" in result.stderr
    assert not script.exists()


def test_check_accepts_the_pair_it_just_assembled(tmp_path):
    _, script, context = _assemble(tmp_path, _key())
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "release_script_assembler.py"),
            "check",
            "--script",
            str(script),
            "--context",
            str(context),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_check_rejects_a_script_whose_steps_do_not_match_its_context(tmp_path):
    _, script, context = _assemble(tmp_path, _key())
    text = script.read_text(encoding="utf-8-sig")
    script.write_text(
        text.replace('Step "[5/10] Verify compiled backend"', 'Step "[5/10] Nothing"'),
        encoding="utf-8-sig",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "release_script_assembler.py"),
            "check",
            "--script",
            str(script),
            "--context",
            str(context),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Verify compiled backend" in result.stderr


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": "1"},
        {"toolchain": []},
        {"python_backend": None},
    ],
)
def test_version_and_content_must_agree(mutation):
    doc = {**_key(), **mutation}
    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(doc)


def test_jobs_falls_back_when_the_override_is_not_a_number():
    key = rc.ReleaseAdapterManifest.model_validate(_key())
    from builders import nuitka  # noqa: PLC0415

    backend = key.python_backend
    assert nuitka.jobs(backend, {}) == backend.jobs.default
    assert nuitka.jobs(backend, {backend.jobs.env: "4"}) == 4
    assert nuitka.jobs(backend, {backend.jobs.env: "0"}) == 1
    assert nuitka.jobs(backend, {backend.jobs.env: "とても"}) == backend.jobs.default


def test_key_paths_must_stay_inside_the_repository():
    from builders import nuitka  # noqa: PLC0415

    assert nuitka.expand("${DESKTOP_DIR}/x", desktop_dir="d", build_root=None) == "d/x"
    for bad in ("/abs/path", "../escape", "a\\b", "${DESKTOP_DIR}/../out"):
        with pytest.raises(ValueError):
            nuitka.expand(bad, desktop_dir="d", build_root=None)
    with pytest.raises(ValueError, match="build_root"):
        nuitka.expand("${BUILD_ROOT}/x", desktop_dir="d", build_root=None)


def test_assemble_leaves_the_previous_pair_alone_when_the_key_is_bad(tmp_path):
    result, script, context = _assemble(tmp_path, _key())
    assert result.returncode == 0
    before = (script.read_bytes(), context.read_bytes())

    bad = deepcopy(_key())
    bad["python_backend"]["targets"] = []
    adapter = tmp_path / "key.json"
    adapter.write_text(json.dumps(bad), encoding="utf-8")
    again = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "release_script_assembler.py"),
            "assemble",
            "--adapter",
            str(adapter),
            "--repo-root",
            str(tmp_path),
            "--output",
            str(script),
            "--context-output",
            str(context),
        ],
        capture_output=True,
        text=True,
    )
    assert again.returncode != 0
    assert (script.read_bytes(), context.read_bytes()) == before
