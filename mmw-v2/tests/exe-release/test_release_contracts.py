import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "exe-release"
    / "scripts"
    / "release_contracts.py"
)
FIX = Path(__file__).resolve().parent / "fixtures" / "release-flow"

sys.path.insert(0, str(SCRIPT.parent))
import release_contracts as rc  # noqa: E402


def _fake_manifest():
    return json.loads((FIX / "manifest.fake.json").read_text())


def test_manifest_rejects_unknown_field():
    good = _fake_manifest()
    manifest = rc.ReleaseAdapterManifest.model_validate(good)
    assert manifest.build_target.desktop_dir == "desktop-fixture"
    assert manifest.build_hooks.runtime_prepare == ["true"]
    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate({**good, "bogus": 1})


@pytest.mark.parametrize(
    "field",
    ["event_sink", "derive"],
)
def test_a_product_can_ship_before_it_has_any_of_the_self_heal_machinery(field):
    """自愈与观测那一套是可选装备，不是入场券。

    一个产品第一次出包时，它没有派生物要重生、没有日志系统要接。把这些设成必填，
    等于要求「能出包」之前先写仓库侧 Python——而这个技能存在的全部理由就是不必再写那些。
    """
    good = _fake_manifest()
    del good[field]
    assert getattr(rc.ReleaseAdapterManifest.model_validate(good), field) is None


def test_manifest_empty_stages_allowed():
    good = _fake_manifest()
    good["stages"] = []
    rc.ReleaseAdapterManifest.model_validate(good)


@pytest.mark.parametrize(
    "source,destination",
    [
        ("../secret", "maps.zip"),
        ("/absolute", "maps.zip"),
        ("source/maps.zip", "../maps.zip"),
        ("source/maps.zip", "bad;command"),
    ],
)
def test_returned_artifacts_stay_within_build_and_loop_directories(source, destination):
    target = deepcopy(_fake_manifest()["build_target"])
    target["return_artifacts"] = {source: destination}
    with pytest.raises(Exception):
        rc.BuildTarget.model_validate(target)


def test_post_build_stage_names_cannot_repeat_pre_build_names():
    manifest = _fake_manifest()
    manifest["post_build_stages"] = [manifest["stages"][0]]
    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(manifest)


@pytest.mark.parametrize("artifact_exists", [True, False])
def test_post_build_stage_requires_returned_artifact_before_remote_cleanup(
    tmp_path, artifact_exists
):
    """Transfer real bytes through the remote filesystem seam, then run the next stage."""
    fake_remote = FIX.parent / "fake-remote"
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("MMW_", "NMEM_", "RELEASE_", "FAKE_"))
        and key != "PASEO_AGENT_ID"
    }
    env.update(
        {
            "PATH": str(fake_remote) + os.pathsep + env["PATH"],
            "FAKE_REMOTE_ROOT": str(tmp_path / "remote-fs"),
            "FAKE_REMOTE_TASKS": str(tmp_path / "remote-tasks.json"),
            "RELEASE_REMOTE_HOST": "fake@pc",
            "RELEASE_REMOTE_ROOT": "C:/release-input",
            "RELEASE_REMOTE_BUILD_POLL_SECONDS": "0",
        }
    )

    def command(*argv):
        return subprocess.run(
            argv, cwd=tmp_path, env=env, capture_output=True, text=True
        )

    assert command("git", "init", "-q").returncode == 0
    (tmp_path / "source.txt").write_text("source\n")
    assert command("git", "add", "source.txt").returncode == 0
    assert (
        command(
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=t@t",
            "commit",
            "-qm",
            "source",
        ).returncode
        == 0
    )
    manifest = _fake_manifest()
    manifest.update({"stages": [], "event_sink": None})
    manifest["post_build_stages"] = [
        {
            "name": "publish_symbols",
            "run": [
                "python3",
                "-c",
                "from pathlib import Path; assert Path('.release/release-artifacts/_loop/symbols.zip').read_text() == 'fake installer\\n'; Path('published').touch()",
            ],
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    flow = str(SCRIPT.parent / "release-flow.sh")
    assert (
        command("bash", flow, "init", "--manifest", str(manifest_path)).returncode == 0
    )
    for stage in ("verify_key", "assemble"):
        assert command("bash", flow, "stage", "done", "--stage", stage).returncode == 0
    loop = tmp_path / ".release/release-artifacts/_loop"
    loop.mkdir(parents=True, exist_ok=True)
    (loop / "release.ps1").write_text("# fake release\n")
    artifact_path = (
        "out/test-product-setup.exe" if artifact_exists else "out/missing.zip"
    )
    (loop / "release-context.json").write_text(
        json.dumps(
            {
                "repo_root": "/placeholder",
                "product": "test-product",
                "build_target": {
                    "installer_glob": "out/*.exe",
                    "return_artifacts": {artifact_path: "symbols.zip"},
                },
            }
        )
    )
    assert (
        command("bash", flow, "stage", "run", "--stage", "publish_symbols").returncode
        != 0
    )
    assert not (tmp_path / "published").exists()
    build = command("bash", flow, "stage", "run", "--stage", "build")
    state = json.loads((tmp_path / ".release/release-state.json").read_text())
    build_status = next(
        stage["status"] for stage in state["stages"] if stage["name"] == "build"
    )
    remote_build_dirs = list((tmp_path / "remote-fs").rglob("run-release.cmd"))
    if artifact_exists:
        assert build.returncode == 0, build.stdout + build.stderr
        assert build_status == "done", build.stdout + build.stderr
        assert (loop / "symbols.zip").read_text() == "fake installer\n"
        assert not remote_build_dirs, "successful delivery must clean the remote tree"
        post = command("bash", flow, "stage", "run", "--stage", "publish_symbols")
        assert post.returncode == 0, post.stdout + post.stderr
        assert (tmp_path / "published").exists()
    else:
        assert build_status == "failed", build.stdout + build.stderr
        assert remote_build_dirs, "failed artifact transfer must preserve the build"
        assert not (loop / "symbols.zip").exists()
        assert (
            command(
                "bash", flow, "stage", "run", "--stage", "publish_symbols"
            ).returncode
            != 0
        )
        assert not (tmp_path / "published").exists()


def test_manifest_rejects_echo_stage_as_fake_build_teeth():
    good = _fake_manifest()
    good["stages"][0]["run"] = ["echo", "not-a-build"]

    with pytest.raises(Exception, match="echo"):
        rc.ReleaseAdapterManifest.model_validate(good)


@pytest.mark.parametrize("field", ["build_target", "python_backend", "electron"])
def test_a_key_must_say_what_it_builds(field):
    bad = _fake_manifest()
    del bad[field]

    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(bad)


@pytest.mark.parametrize("field", ["stages", "diagnose", "build_hooks"])
def test_a_key_leaves_the_standard_pipeline_to_the_engine(field):
    """这三段每把钥匙都一样，只有钥匙路径不同——抄四遍的直接后果是有一把抄成了
    指向另一把钥匙，而每一步都报绿。不声明就用引擎的标准流水线。"""
    lean = _fake_manifest()
    del lean[field]
    rc.ReleaseAdapterManifest.model_validate(lean)


@pytest.mark.parametrize("field", ["p0_paths", "post_fix_diagnose"])
def test_manifest_rejects_removed_v2_fields(field):
    bad = _fake_manifest()
    bad[field] = ["legacy"]

    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(bad)


@pytest.mark.parametrize("field", ["desktop_dir", "installer_brand"])
def test_build_target_requires_every_build_identity_field(field):
    bad = deepcopy(_fake_manifest()["build_target"])
    del bad[field]

    with pytest.raises(Exception):
        rc.BuildTarget.model_validate(bad)


def test_native_ext_dll_requires_non_empty_names_and_package_dir_target():
    base = _fake_manifest()["build_target"]["native_ext_dll"][0]
    rc.NativeExtDll.model_validate(base)
    with pytest.raises(Exception):
        rc.NativeExtDll.model_validate({**base, "dll_names": []})
    with pytest.raises(Exception):
        rc.NativeExtDll.model_validate({**base, "dest": "pyd_package_dir"})
    rc.NativeExtDll.model_validate(
        {**base, "dest": "pyd_package_dir", "pyd_package": "fixture"}
    )


def test_build_hooks_require_three_non_empty_argv_and_allow_optional_nulls():
    hooks = _fake_manifest()["build_hooks"]
    rc.ReleaseBuildHooks.model_validate(hooks)
    rc.ReleaseBuildHooks.model_validate(
        {
            key: value
            for key, value in hooks.items()
            if key not in {"asset_parity", "credential_proof"}
        }
    )
    with pytest.raises(Exception):
        rc.ReleaseBuildHooks.model_validate({**hooks, "runtime_prepare": []})
    with pytest.raises(Exception):
        rc.ReleaseBuildHooks.model_validate({**hooks, "unknown_hook": ["true"]})


def test_build_machine_is_optional_and_defaults_to_none():
    good = _fake_manifest()
    good.pop("build_machine", None)
    manifest = rc.ReleaseAdapterManifest.model_validate(good)
    assert manifest.build_machine is None


def test_build_machine_roundtrips_setup_teardown_and_forbids_extra():
    good = _fake_manifest()
    good["build_machine"] = {
        "setup": ["prep", "--mode", "setup"],
        "teardown": ["prep", "--mode", "teardown"],
    }
    manifest = rc.ReleaseAdapterManifest.model_validate(good)
    assert manifest.build_machine.setup == ["prep", "--mode", "setup"]
    assert manifest.build_machine.teardown == ["prep", "--mode", "teardown"]
    with pytest.raises(Exception):
        rc.BuildMachine.model_validate(
            {"setup": ["prep"], "teardown": ["prep"], "bogus": 1}
        )


def test_finding_fail_requires_tier_and_fingerprint():
    base = {
        "schema_version": "1",
        "product": "duck",
        "dimension": "x",
        "name": "n",
        "status": "fail",
        "detail": "",
    }
    with pytest.raises(Exception):
        rc.ReleaseFinding.model_validate(base)
    rc.ReleaseFinding.model_validate(
        {
            **base,
            "tier": "P1",
            "root_cause_fingerprint": "missing_module:foo",
        }
    )


def test_finding_deferred_needs_no_tier():
    rc.ReleaseFinding.model_validate(
        {
            "schema_version": "1",
            "product": "duck",
            "dimension": "x",
            "name": "n",
            "status": "deferred",
            "detail": "",
        }
    )


def test_event_is_neutral_and_forbids_extra():
    ev = {
        "schema_version": "1",
        "event": "paused",
        "product": "duck",
        "round": 1,
        "trace_id": "t-123",
        "timestamp": "2026-07-09T00:00:00Z",
    }
    rc.ReleaseLoopEvent.model_validate(ev)
    assert "audit_trace_id" not in rc.ReleaseLoopEvent.model_fields
    with pytest.raises(Exception):
        rc.ReleaseLoopEvent.model_validate({**ev, "audit_trace_id": "x"})


def _cli(*args, **kw):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        **kw,
    )


def test_cli_validate_manifest_ok_and_bad():
    ok = _cli("validate-manifest", str(FIX / "manifest.fake.json"))
    assert ok.returncode == 0
    assert json.loads(ok.stdout)["product"] == "fixture-product"
    bad = _cli("validate-manifest", "-", input='{"schema_version":"2"}')
    assert bad.returncode == 3


def test_cli_classify_findings_highest_tier():
    r = _cli("classify-findings", str(FIX / "finding.p0.json"))
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["highest_tier"] == "P0"
    assert len(out["failing"]) == 2


def test_cli_classify_rejects_bad_finding():
    r = _cli("classify-findings", str(FIX / "finding.bad.json"))
    assert r.returncode == 3


def test_contract_import_robust_via_spec_from_file_location():
    # 跨仓消费方（agentflow tests/contracts）用最朴素 loader 动态 import 本合同：
    # spec_from_file_location + exec_module，不预注册 sys.modules。
    # 合同必须在这种 import 下也能 model_validate（挡"合同非 import-robust"回归）。
    import importlib.util

    spec = importlib.util.spec_from_file_location("release_contracts_probe", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ok = mod.ReleaseFinding.model_validate(
        {
            "schema_version": "1",
            "product": "duck",
            "dimension": "deps",
            "name": "missing_x",
            "status": "fail",
            "tier": "P1",
            "root_cause_fingerprint": "missing_module:x",
        }
    )
    assert ok.tier == "P1"
    with pytest.raises(Exception):
        mod.ReleaseFinding.model_validate(
            {
                "schema_version": "1",
                "product": "duck",
                "dimension": "deps",
                "name": "x",
                "status": "fail",
                "detail": "缺 tier",
            }
        )
