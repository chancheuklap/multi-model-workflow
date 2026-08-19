"""日志翻译：引擎自己的报错，由引擎自己这边的规则认。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ENGINE = SCRIPTS / "release-flow.sh"
TEMPLATE = SCRIPTS / "release_templates" / "nuitka_electron.ps1.tmpl"

sys.path.insert(0, str(SCRIPTS))
import diagnose_core as dc  # noqa: E402


def _fingerprints(text: str, product: str = "duck") -> list[str]:
    log = Path(_tmp) / "build-run.log"
    log.write_text(text, encoding="utf-8")
    return [f["root_cause_fingerprint"] for f in dc.build_log_findings(product, log, "build")]


@pytest.fixture(autouse=True)
def _with_tmp(tmp_path):
    global _tmp
    _tmp = tmp_path


# ── 这份测试的核心：引擎与模板打印的每一句失败，规则表都认得 ──────────────────────
#
# 规则表原本在产品仓库，匹配的却是引擎打印的文字。改一句引擎的报错，要去每个产品仓库改一遍
# 正则，否则那条根因静默失效。规则搬到引擎这边之后，这条对照就能在同一个仓库里验。

ENGINE_ERRORS = [
    ("ERROR: remote build 缺 RELEASE_REMOTE_HOST", "env:missing_RELEASE_REMOTE_HOST"),
    ("ERROR: remote build 缺 RELEASE_REMOTE_ROOT", "env:missing_RELEASE_REMOTE_ROOT"),
    (
        "ERROR: RELEASE_REMOTE_ROOT 必须是安全字符的 Windows 绝对路径",
        "env:invalid_RELEASE_REMOTE_ROOT",
    ),
    ("ERROR: remote build 超时", "env:remote_harness"),
    ("ERROR: 无法清除远端上一轮构建产物", "env:remote_harness"),
]

TEMPLATE_ERRORS = [
    ("Required build tool is unavailable: makensis", "env:missing_tool:makensis"),
    ("Build command failed: pnpm (1)", "build_step:duck"),
    ("Release hook failed: package_integrity phase=release_ready", "hook_failed:package_integrity"),
    (
        "Build machine is missing msvcp140.dll at C:\\Windows\\System32\\msvcp140.dll",
        "env:missing_dll:msvcp140.dll",
    ),
    ("Compiled backend import smoke failed (1)", "frozen_smoke:duck"),
    ("Compiled backend import smoke timed out after 180s", "frozen_smoke_timeout:duck"),
    ("electron-builder did not create an installer", "build_step:duck"),
]


@pytest.mark.parametrize(("line", "fingerprint"), [*ENGINE_ERRORS, *TEMPLATE_ERRORS])
def test_every_engine_and_template_failure_is_translated(line, fingerprint):
    assert _fingerprints(f"...\n{line}\n...") == [fingerprint]


def test_the_engine_still_prints_the_lines_the_rules_match():
    """规则表和引擎在同一个仓库里，所以「报错改了、规则没跟上」这件事能当场查出来。

    只查引擎那几句固定前缀——它们是钥匙与产品仓库之外的失败现场唯一的入口文字。
    """
    engine = ENGINE.read_text(encoding="utf-8")
    for line, _ in ENGINE_ERRORS:
        assert line in engine, f"引擎不再打印这句，对应的翻译规则成了死规则：{line}"


def test_the_template_still_throws_the_messages_the_rules_match():
    template = TEMPLATE.read_text(encoding="utf-8")
    for fragment in (
        "Required build tool is unavailable:",
        "Build command failed:",
        "Build machine is missing",
        "Compiled backend import smoke failed",
        "Compiled backend import smoke timed out",
    ):
        assert fragment in template, f"模板不再抛这句，对应的翻译规则成了死规则：{fragment}"


# ── 其余行为 ────────────────────────────────────────────────────────────────────


def test_missing_module_names_the_module_in_both_fingerprint_and_advice():
    log = Path(_tmp) / "log"
    log.write_text("ModuleNotFoundError: No module named 'uharfbuzz'", encoding="utf-8")
    (finding,) = dc.build_log_findings("parrot", log, "build")
    assert finding["root_cause_fingerprint"] == "missing_module:uharfbuzz"
    assert "uharfbuzz" in finding["remediation"]


def test_utf16_logs_are_read_not_mangled():
    """Windows PowerShell 的裸重定向写 UTF-16LE。按 UTF-8 硬读会读成夹 NUL 的乱码，
    于是整张规则表一条都匹配不上——失败现场明明在日志里，翻译却全线失效。"""
    log = Path(_tmp) / "utf16.log"
    log.write_bytes(
        b"\xff\xfe" + "ERROR: remote build 缺 RELEASE_REMOTE_HOST".encode("utf-16-le")
    )
    (finding,) = dc.build_log_findings("duck", log, "build")
    assert finding["root_cause_fingerprint"] == "env:missing_RELEASE_REMOTE_HOST"


def test_an_unrecognised_failure_still_produces_something_to_act_on():
    """认不出来也要给一条带日志尾的 P1，让驱动 agent 拿原文判断，而不是空手 PAUSE。"""
    log = Path(_tmp) / "log"
    log.write_text("something nobody has seen before", encoding="utf-8")
    (finding,) = dc.build_log_findings("duck", log, "build")
    assert finding["root_cause_fingerprint"] == "build_failure_unclassified:duck:build"
    assert "something nobody has seen before" in finding["detail"]


def test_env_and_transient_findings_carry_a_short_excerpt_not_the_whole_tail():
    """回执要人一眼读懂。环境类失败塞 4000 字日志尾，等于没写。"""
    noise = "x" * 5000
    log = Path(_tmp) / "log"
    log.write_text(noise + "\nERROR: remote build 缺 RELEASE_REMOTE_HOST\n" + noise, "utf-8")
    (finding,) = dc.build_log_findings("duck", log, "build")
    assert len(finding["detail"]) < 600


def test_product_rules_win_over_the_generic_table():
    """产品比技能更知道自己那条日志长什么样，所以它的规则排在前面。"""
    log = Path(_tmp) / "log"
    log.write_text("Build command failed: pnpm (1)", encoding="utf-8")
    extra = (
        (r"Build command failed: pnpm", "pnpm_failed", "pnpm:{product}", "改前端"),
    )
    (finding,) = dc.build_log_findings("duck", log, "build", extra)
    assert finding["root_cause_fingerprint"] == "pnpm:duck"


def test_a_findings_envelope_from_a_local_stage_is_taken_as_is():
    log = Path(_tmp) / "stage.log"
    envelope = {
        "findings": [
            {"schema_version": "1", "status": "fail", "name": "verify_key_failed"}
        ]
    }
    log.write_text(json.dumps(envelope), encoding="utf-8")
    assert dc.stage_log_findings(log) == envelope["findings"]


def test_plain_text_stage_output_falls_through_to_the_translator():
    """信封不在就返回 None，让调用方走文本翻译——SSH / SCP / 调度失败只有纯文本。"""
    log = Path(_tmp) / "stage.log"
    log.write_text("ssh: connect to host pc port 22: Connection refused", "utf-8")
    assert dc.stage_log_findings(log) is None
    (finding,) = dc.build_log_findings("duck", log, "build")
    assert finding["root_cause_fingerprint"] == "transient:network.remote_transport"


def test_an_empty_envelope_is_not_retranslated_into_noise():
    """合同产物在、但没有可派发项，是一个合法结果。再当纯文本翻一遍只会产生假根因。"""
    log = Path(_tmp) / "stage.log"
    log.write_text(json.dumps({"findings": []}), encoding="utf-8")
    assert dc.stage_log_findings(log) == []


def test_every_rule_pattern_compiles():
    for pattern, *_ in dc.RULES:
        re.compile(pattern)


def test_transient_is_a_prefix_the_engine_really_acts_on():
    """`transient:` 是引擎唯一按前缀分派的：全部 finding 都是 transient 就直接重跑这一阶段，
    不派代码修复、也不消耗修复轮次。所以这个前缀写错，一条网络抖动会被当成代码问题去修。

    （`env:` 是给人和 agent 读的约定，引擎不按它分派。）
    """
    engine = ENGINE.read_text(encoding="utf-8")
    assert 'startswith("transient:")' in engine
    assert any(fp.startswith("transient:") for _, _, fp, _ in dc.RULES)


def test_a_missing_module_is_not_mistaken_for_a_network_blip():
    """`ModuleNotFoundError` 里藏着 eNotFound。不加词边界，它会大小写不敏感地命中
    Node 的 ENOTFOUND，于是一条必然失败的编译被判成瞬态，引擎一遍遍重跑到预算耗尽。"""
    log = Path(_tmp) / "log"
    log.write_text("ModuleNotFoundError: No module named 'moderngl'", encoding="utf-8")
    (finding,) = dc.build_log_findings("hedgehog", log, "build")
    assert finding["root_cause_fingerprint"] == "missing_module:moderngl"


def test_a_missing_log_is_not_a_finding():
    assert dc.build_log_findings("duck", Path(_tmp) / "nope.log", "build") == []


def test_branch_argv_with_an_unresolved_product_artifact_is_skipped():
    """产物还没出来时整条支路跳过。拿不到产物的产物检查只会产出「文件不存在」，
    盖住真正的根因。"""
    argv = ["python", "smoke.py", "--core-exe", "${CORE_EXE}"]
    assert dc._expand(argv, None) is None
    assert dc._expand(argv, "/x/core.exe")[-1] == "/x/core.exe"
    assert dc._expand(["python", "doctor.py"], None) == ["python", "doctor.py"]


def test_cli_runs_the_branches_the_key_declares(tmp_path):
    key = tmp_path / "key.json"
    key.write_text(
        json.dumps(
            {
                "product": "duck",
                "diagnose_branches": [
                    [
                        sys.executable,
                        "-c",
                        'print(\'{"findings": [{"schema_version": "1",'
                        ' "status": "ok", "name": "doctor"}]}\')',
                    ]
                ],
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "diagnose_core.py"), "--adapter", str(key),
         "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert [f["name"] for f in doc["findings"]] == ["doctor"]


def test_cli_fails_loudly_when_a_branch_cannot_produce_findings(tmp_path):
    key = tmp_path / "key.json"
    key.write_text(
        json.dumps(
            {
                "product": "duck",
                "diagnose_branches": [[sys.executable, "-c", "print('not json')"]],
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "diagnose_core.py"), "--adapter", str(key),
         "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "diagnose_core" in result.stderr
