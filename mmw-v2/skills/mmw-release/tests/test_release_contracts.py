import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_contracts.py"
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


def test_manifest_missing_one_of_eight_rejected():
    good = _fake_manifest()
    del good["event_sink"]
    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(good)


def test_manifest_empty_stages_allowed():
    good = _fake_manifest()
    good["stages"] = []
    rc.ReleaseAdapterManifest.model_validate(good)


def test_manifest_rejects_echo_stage_as_fake_build_teeth():
    good = _fake_manifest()
    good["stages"][0]["run"] = ["echo", "not-a-build"]

    with pytest.raises(Exception, match="echo"):
        rc.ReleaseAdapterManifest.model_validate(good)


@pytest.mark.parametrize("field", ["build_target", "protection_source", "build_hooks"])
def test_manifest_requires_v3_contract_fields(field):
    bad = _fake_manifest()
    del bad[field]

    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(bad)


@pytest.mark.parametrize("field", ["p0_paths", "post_fix_diagnose"])
def test_manifest_rejects_removed_v2_fields(field):
    bad = _fake_manifest()
    bad[field] = ["legacy"]

    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(bad)


@pytest.mark.parametrize(
    "field", ["desktop_dir", "runtime_lane", "entry_module", "installer_brand"]
)
def test_build_target_requires_every_build_identity_field(field):
    bad = deepcopy(_fake_manifest()["build_target"])
    del bad[field]

    with pytest.raises(Exception):
        rc.BuildTarget.model_validate(bad)

    with pytest.raises(Exception):
        rc.BuildTarget.model_validate(
            {**_fake_manifest()["build_target"], "runtime_lane": "other"}
        )


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
    assert json.loads(ok.stdout)["product"] == "duck"
    bad = _cli("validate-manifest", "-", input='{"schema_version":"1"}')
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


def test_cli_validate_event_accepts_neutral_event_and_rejects_extra_field():
    event = {
        "schema_version": "1",
        "event": "paused",
        "product": "duck",
        "round": 1,
        "trace_id": "t-123",
        "timestamp": "2026-07-09T00:00:00Z",
    }
    ok = _cli("validate-event", "-", input=json.dumps(event))
    assert ok.returncode == 0
    bad = _cli(
        "validate-event", "-", input=json.dumps({**event, "audit_trace_id": "x"})
    )
    assert bad.returncode == 3


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
