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

# 每条是 (引擎日志里的一整句, 期望的根因指纹, 引擎源码里逐字出现的片段)。
# 第三项跟前两项分开，是因为报错句里常常带变量（超时秒数、主机名），源码里没有那一段字面量。
ENGINE_ERRORS = [
    (
        "ERROR: remote build has no RELEASE_REMOTE_HOST",
        "env:missing_RELEASE_REMOTE_HOST",
        "ERROR: remote build has no RELEASE_REMOTE_HOST",
    ),
    (
        "ERROR: remote build has no RELEASE_REMOTE_ROOT",
        "env:missing_RELEASE_REMOTE_ROOT",
        "ERROR: remote build has no RELEASE_REMOTE_ROOT",
    ),
    (
        "ERROR: RELEASE_REMOTE_ROOT must be an absolute Windows path in safe characters",
        "env:invalid_RELEASE_REMOTE_ROOT",
        "ERROR: RELEASE_REMOTE_ROOT must be an absolute Windows path in safe characters",
    ),
    (
        "ERROR: remote build produced no exitcode within 7200s (task=mmw-release-duck)",
        "env:remote_harness",
        "remote build produced no exitcode within ",
    ),
    (
        "ERROR: could not clear the previous round on the build machine; a stale exitcode "
        "would read as this round succeeding: D:/duck-release-input",
        "env:remote_harness",
        "could not clear the previous round on the build machine",
    ),
    (
        "ERROR: the detached build task never started on pc (no build-run.log and no "
        "exitcode ever appeared, task=mmw-release-duck)",
        "env:remote_harness",
        "the detached build task never started on ",
    ),
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
    (
        "Compiled backend import smoke ran but its exit code could not be read; "
        "treat this as a build harness fault, not a missing dependency",
        "env:smoke_harness:duck",
    ),
    ("Compiled backend import smoke timed out after 180s", "frozen_smoke_timeout:duck"),
    ("electron-builder did not create an installer", "build_step:duck"),
    (
        "Onefile payload mismatch: C:\\x\\core.exe carries the same payload as C:\\x\\launcher.exe "
        "-- one of them is the wrong program (payload: C:\\x\\core.onefile-build\\blobs\\__payload.bin)",
        "payload_mismatch:duck",
    ),
    (
        "Business Python source shipped in the package: C:\\x\\duck\\app.py",
        "shipped_source:duck",
    ),
    (
        "No installer matched the key's installer_glob: C:\\x\\dist\\*.exe",
        "installer_missing:duck",
    ),
]


@pytest.mark.parametrize(
    ("line", "fingerprint"),
    [(line, fp) for line, fp, _ in ENGINE_ERRORS] + list(TEMPLATE_ERRORS),
)
def test_every_engine_and_template_failure_is_translated(line, fingerprint):
    assert _fingerprints(f"...\n{line}\n...") == [fingerprint]


def test_the_engine_still_prints_the_lines_the_rules_match():
    """规则表和引擎在同一个仓库里，所以「报错改了、规则没跟上」这件事能当场查出来。

    只查引擎那几句固定前缀——它们是钥匙与产品仓库之外的失败现场唯一的入口文字。
    """
    engine = ENGINE.read_text(encoding="utf-8")
    for _, _, fragment in ENGINE_ERRORS:
        assert fragment in engine, (
            f"the engine no longer prints this, so its translation rule is dead: {fragment}"
        )


def test_the_template_still_throws_the_messages_the_rules_match():
    template = TEMPLATE.read_text(encoding="utf-8")
    for fragment in (
        "Required build tool is unavailable:",
        "Build command failed:",
        "Build machine is missing",
        "Compiled backend import smoke failed",
        "Compiled backend import smoke timed out",
        "import smoke ran but its exit code could not be read",
        "Business Python source shipped in the package",
        "No installer matched the key's installer_glob",
    ):
        assert fragment in template, f"the template no longer throws this, so its translation rule is dead: {fragment}"


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
        b"\xff\xfe" + "ERROR: remote build has no RELEASE_REMOTE_HOST".encode("utf-16-le")
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
    log.write_text(noise + "\nERROR: remote build has no RELEASE_REMOTE_HOST\n" + noise, "utf-8")
    (finding,) = dc.build_log_findings("duck", log, "build")
    assert len(finding["detail"]) < 600


def test_product_rules_win_over_the_generic_table():
    """产品比技能更知道自己那条日志长什么样，所以它的规则排在前面。"""
    log = Path(_tmp) / "log"
    log.write_text("Build command failed: pnpm (1)", encoding="utf-8")
    extra = (
        (r"Build command failed: pnpm", "pnpm_failed", "pnpm:{product}", "fix the frontend"),
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


def test_a_smoke_that_ran_is_not_graded_as_a_missing_dependency():
    """自检跑完了、只是读不到退出码，跟自检真的失败是两回事。

    分不开这两条，一次构建机的机制故障会被派去改钥匙的 include——改不好，然后一遍遍重跑。
    真发生过：模板漏了 Start-Process 的句柄，退出码读成空，而 PowerShell 里 $null -ne 0 是真，
    于是日志上一行写着 smoke ok，下一行构建被判成缺依赖。
    """
    log = Path(_tmp) / "log"
    log.write_text(
        "duck built-exe import smoke ok (8 modules)\n"
        "Compiled backend import smoke ran but its exit code could not be read",
        encoding="utf-8",
    )
    (finding,) = dc.build_log_findings("duck", log, "build")
    assert finding["root_cause_fingerprint"] == "env:smoke_harness:duck"


def test_a_hook_that_crashed_printing_its_own_output_is_not_graded_as_a_hook_failure():
    """检查通过了，是打印检查输出的那一行自己崩了。

    构建机是中文 Windows：subprocess 的 text=True 按 GBK 解子进程输出，遇非 GBK 字节读取线程
    就死，stdout/stderr 变 None，随后 write(None) 抛 TypeError。日志里同时也有一句
    Release hook failed，按那一条得到的是「读日志定位根因」——而根因就是这个，往下读只会
    看见一个 traceback 指着报错语句自己。
    """
    log = Path(_tmp) / "log"
    log.write_text(
        "hedgehog python-runtime preflight passed\n"
        "Exception in thread Thread-2 (_readerthread):\n"
        "    buffer.append(fh.read())\n"
        "UnicodeDecodeError: 'gbk' codec can't decode byte 0x81 in position 27\n"
        "TypeError: write() argument must be str, not None\n"
        "Release hook failed: backend_verify phase=backend_ready\n",
        encoding="utf-8",
    )
    (finding,) = dc.build_log_findings("hedgehog", log, "build")
    assert finding["root_cause_fingerprint"] == "hook_output_encoding:hedgehog"


def test_a_hook_that_crashed_writing_its_own_output_is_the_same_root_cause():
    """反方向的同一件事：解码放宽之后，替换字符 U+FFFD 反而 GBK 编不出来。

    真发生过，而且就发生在修好解码那一侧之后的下一轮：失败点从 backend_verify 挪到了
    asset_parity，看着像换了个毛病，其实是同一处日志搬运。两个方向必须一起修。
    """
    log = Path(_tmp) / "log"
    log.write_text(
        "Installed 153 packages in 53.11s\n"
        "    sys.stdout.write(result.stdout or \"\")\n"
        "UnicodeEncodeError: 'gbk' codec can't encode character '\\ufffd' in position 15\n"
        "Release hook failed: asset_parity phase=runtime_ready\n",
        encoding="utf-8",
    )
    (finding,) = dc.build_log_findings("hedgehog", log, "build")
    assert finding["root_cause_fingerprint"] == "hook_output_encoding:hedgehog"
