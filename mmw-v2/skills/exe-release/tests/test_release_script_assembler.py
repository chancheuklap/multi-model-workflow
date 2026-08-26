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
import release_script_assembler as assembler  # noqa: E402



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
        "Check runtime assets",
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


def test_the_skill_puts_nothing_non_ascii_into_the_generated_script(tmp_path):
    """守：技能往 release.ps1 里写的每一个字节都是 ASCII。

    那份脚本在构建机上被读，而那台机器的控制台是 GBK。模板早就扫成纯 ASCII 了，装配器往同一个
    文件里写的注释却漏了三行中文——同一份文件，两个来源，只扫了一个。钥匙自己带的非 ASCII
    （产品显示名一类）不归这里管，所以用全 ASCII 的 fixture 钥匙：进去是 ASCII，出来就该是 ASCII。
    """
    _, script, _ = _assemble(tmp_path, _key())
    raw = script.read_bytes().lstrip(b"\xef\xbb\xbf")
    offenders = sorted({bytes([b]) for b in raw if b > 127})
    assert not offenders, f"技能往生成脚本里写了非 ASCII 字节: {offenders}"


VENDOR_ARTIFACT = {
    "name": "ffmpeg",
    "lock": "resources/ffmpeg/.lock.json",
    "members": [
        {
            "file": "ffmpeg.exe",
            "dest": "resources/ffmpeg/bin/ffmpeg.exe",
            "sha256_key": "ffmpeg_exe_sha256",
        }
    ],
}


def test_a_key_that_declares_a_vendor_artifact_gets_a_step_that_fetches_it(tmp_path):
    """守：太大不进 git 的第三方二进制由技能取，钥匙只声明要什么。

    这件事四个产品做的完全一样——从构建机上拷进来、对 sha256。写在产品仓库里，就是每加一个
    产品再抄一遍四百行 Python，而第四份正是某一步悄悄漏掉的地方。
    """
    doc = _key()
    doc["vendor_artifacts"] = [VENDOR_ARTIFACT]
    result, script, context = _assemble(tmp_path, doc)
    assert result.returncode == 0, result.stderr
    text = script.read_text(encoding="utf-8-sig")
    assert "Get-VendorArtifact" in text
    assert "'resources/ffmpeg/.lock.json'" in text
    assert "'ffmpeg_exe_sha256'" in text
    steps = _steps(script)
    assert any("Fetch vendor artifacts" in step for step in steps), steps


def test_a_licence_the_vendored_binary_needs_is_checked_against_the_finished_package(tmp_path):
    """守：拷进仓库 != 随包出厂。

    ffmpeg 是 GPL 的，义务是让客户拿到许可证正文和源码索取声明。两份文本都放进了树里，
    随后 electron-builder 的过滤规则把它们丢掉——构建全绿，装出来的包在违约。闸门不认
    路径（成品里的位置是打包配置的事），认字节。
    """
    doc = _key()
    artifact = deepcopy(VENDOR_ARTIFACT)
    artifact["members"].append(
        {
            "file": "LICENSE.txt",
            "dest": "resources/ffmpeg/LICENSE.txt",
            "sha256_key": "license_sha256",
            "license": True,
        }
    )
    artifact["notices"] = ["resources/ffmpeg/NOTICE-ffmpeg.txt"]
    doc["vendor_artifacts"] = [artifact]
    result, script, _ = _assemble(tmp_path, doc)
    assert result.returncode == 0, result.stderr
    text = script.read_text(encoding="utf-8-sig")
    gate = [line for line in text.splitlines() if "Assert-LicensesShipped -Licenses" in line]
    assert len(gate) == 1, text
    assert "'resources/ffmpeg/LICENSE.txt'" in gate[0]
    assert "'resources/ffmpeg/NOTICE-ffmpeg.txt'" in gate[0]
    assert "-PackageDir $UnpackedDir" in gate[0]
    # 有的产品的成品树是 installer 钩子造的，闸门必须在它之后。
    assert text.index("Assert-LicensesShipped -Licenses") > text.index("Build installer")
    # 二进制本身不是许可证，不进这道闸的名单。
    assert "ffmpeg.exe" not in gate[0]


def test_a_key_that_says_where_its_finished_tree_is_gets_the_gate_pointed_there(tmp_path):
    """守：unpacked 目录只是个壳的产品，闸门要看它自己那棵成品树。

    第四个产品的 electron 产物是外壳，交给客户的那棵树由它自己的 installer 钩子在别处装配，
    树名里还带着版本号。闸门照默认去看 unpacked，看到的是一棵没有许可证也没有 ffmpeg 的树。
    """
    doc = _key()
    artifact = deepcopy(VENDOR_ARTIFACT)
    artifact["notices"] = ["resources/ffmpeg/NOTICE-ffmpeg.txt"]
    doc["vendor_artifacts"] = [artifact]
    doc["build_target"]["package_tree"] = "runtime/windows-release/product-v*/bundle"
    _, script, _ = _assemble(tmp_path, doc)
    text = script.read_text(encoding="utf-8-sig")
    gate = [line for line in text.splitlines() if "Assert-LicensesShipped -Licenses" in line]
    assert len(gate) == 1, text
    assert "'runtime/windows-release/product-v*/bundle'" in gate[0]
    assert "$UnpackedDir" not in gate[0]


def test_a_vendored_binary_with_no_licence_declared_gets_no_licence_gate(tmp_path):
    doc = _key()
    doc["vendor_artifacts"] = [VENDOR_ARTIFACT]
    _, script, _ = _assemble(tmp_path, doc)
    assert "Assert-LicensesShipped -Licenses" not in script.read_text(encoding="utf-8-sig")


def test_a_key_that_declares_no_vendor_artifact_has_no_such_step(tmp_path):
    # 函数定义一直在模板里；这里验的是没有人调用它，也没有那一步。
    _, script, _ = _assemble(tmp_path, _key())
    text = script.read_text(encoding="utf-8-sig")
    assert "Get-VendorArtifact -Name" not in text
    assert not any("Fetch vendor artifacts" in step for step in _steps(script))


def test_every_compiled_exe_is_checked_against_its_own_payload(tmp_path):
    """守：编译完当场验每个 exe 装的是不是自己这一轮的 payload。

    payload 走的是编译器缓存看不见的路，第二个目标曾经拿回第一个目标的 object——两个 exe
    字节相同、都在跑第一个程序，而每一步都是绿的。设置能被覆盖、默认会变、工具链会换，
    所以这里验的是 exe 里实际装着什么，跟走哪条路无关。
    """
    _, script, _ = _assemble(tmp_path, _key())
    text = script.read_text(encoding="utf-8-sig")
    assert "Assert-OnefilePayloads" in text
    for target in _key()["python_backend"]["targets"]:
        assert target["exe"] in text


def test_the_onefile_payload_never_goes_through_a_compiler_cache(tmp_path):
    """守：payload 不许经过 C 编译器。

    Nuitka 在 zig 下的默认做法是写一个三百字节的 C 文件，用 C23 `#embed` 把整个 payload 吸进去。
    没有哪个编译器缓存会去哈希 `#embed` 进来的那个文件，而那三百字节对每个目标、每个产品、每一轮
    都逐字相同——于是第二次编译拿回第一次的 object，exe 里装着别的程序，构建日志全绿。这在构建机上
    实测过：同一轮两个目标产出了字节数完全相同、payload 也相同的两个 exe。
    """
    _, script, _ = _assemble(tmp_path, _key())
    text = script.read_text(encoding="utf-8-sig")
    assert "NUITKA_RESOURCE_MODE = 'coff_obj'" in text
    # zig 自己的编译缓存跟 ccache 一样有这个洞，也跟其他工具链缓存一样必须离开系统盘。
    assert "'ZIG_GLOBAL_CACHE_DIR'" in text
    assert "'ZIG_LOCAL_CACHE_DIR'" in text


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
    # 按标题找那一行，不写死步号：步号是算出来的，加一步就会把写死编号的测试打红，
    # 而它要守的根本不是编号。
    line = next(s for s in _steps(script) if "Verify compiled backend" in s)
    script.write_text(
        text.replace(line, line.replace("Verify compiled backend", "Nothing")),
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


@pytest.mark.parametrize("mutation", [{"schema_version": "1"}, {"python_backend": None}])
def test_a_key_that_says_nothing_about_the_backend_is_refused(mutation):
    doc = {**_key(), **mutation}
    with pytest.raises(Exception):
        rc.ReleaseAdapterManifest.model_validate(doc)


def test_the_tool_check_covers_every_command_the_script_actually_runs(tmp_path):
    """第一步查的工具从钥匙已经说过的话里推，不靠钥匙再抄一遍。

    抄漏了要等构建跑到那一步才炸；抄多了会把一台本来能用的构建机挡在第一步。
    """
    doc = {**_key(), "toolchain": ["makensis"]}
    key = tmp_path / "k.json"
    key.write_text(json.dumps(doc), encoding="utf-8")
    script = tmp_path / "release.ps1"
    assembler.assemble(key, tmp_path, script, tmp_path / "ctx.json")

    line = next(
        l for l in script.read_text(encoding="utf-8").splitlines() if "foreach ($tool" in l
    )
    manifest = rc.ReleaseAdapterManifest.model_validate(doc)
    assert manifest.python_backend.runner[0] in line, "编译用的解释器命令"
    assert assembler._PACKAGE_MANAGER in line, "前端包管理器"
    assert "makensis" in line, "钥匙补充的那件"


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


def test_package_integrity_hook_runs_before_the_installer_assert(tmp_path):
    """installer_glob 指交付件最后落在哪，而落它的可以就是 package_integrity 这个钩子。

    产品让钩子先判两道闸、判过了才把安装包拷进交付目录，是合理设计。断言排在钩子前面，
    这类产品第一次就被拒，日志里只看得到「没找到安装包」，看不出是顺序的问题。
    """
    result, script, _ = _assemble(tmp_path, _key())
    assert result.returncode == 0, result.stderr
    text = script.read_text(encoding="utf-8-sig")
    hook = text.index("'package_integrity'")
    assert_at = text.index("Assert-InstallerProduced -Glob")
    assert hook < assert_at


def test_compiler_intermediates_are_removed_after_the_payload_check(tmp_path):
    """Nuitka 的 .dist 与 .onefile-build 跟成品 exe 同一个目录，而那个目录整个进安装包。

    不删就是同一份内容发三遍：exe 里一份、dist 一份、payload.bin 一份。删必须排在 payload
    校验之后——校验正要读 payload。
    """
    result, script, _ = _assemble(tmp_path, _key())
    assert result.returncode == 0, result.stderr
    text = script.read_text(encoding="utf-8-sig")
    check = text.index("Assert-OnefilePayloads -Exes") if "Assert-OnefilePayloads -Exes" in text \
        else text.index("Assert-OnefilePayloads -OutputDir")
    cleanup = text.index("Remove-CompilerIntermediates -OutputDir")
    assert check < cleanup


def test_a_key_that_removes_the_output_itself_is_rejected(tmp_path):
    """钥匙自己传 --remove-output，目录在编译当场就没了，payload 校验只能退到比尾部。"""
    doc = _key()
    doc["python_backend"]["extra_flags"] = ["--remove-output"]
    adapter = tmp_path / "key.json"
    adapter.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    import subprocess as sp
    out = sp.run(
        [sys.executable, str(SCRIPTS / "verify_key.py"), "--adapter", str(adapter),
         "--repo-root", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert "remove_output_is_the_engine_s_job" in out.stdout, out.stdout + out.stderr


# ── 随包但不嵌入的数据 ─────────────────────────────────────────────────────────


RUNTIME_ASSETS = {
    "entries": [
        {"source": "src/app/assets", "dest": "app/assets"},
        {
            "source_package": "rapidocr_onnxruntime",
            "members": ["config.yaml", "models"],
            "dest": "app/rapidocr",
        },
    ]
}


def test_a_key_that_declares_runtime_assets_gets_a_step_that_stages_them(tmp_path):
    """守：随包但不嵌入的数据由技能拷，钥匙只说拷什么、拷到哪。

    嵌进编译产物（include_data_dirs）与放在 exe 旁边是两种落点，理由不同：有的包 Nuitka
    嵌不进去，有的资源大到不值得每次启动解压一遍。少了后一种，产品只能在自己仓库写一份
    拷贝脚本——两个产品两份，而其中一份改了三轮各 45–60 分钟的构建都没生效，因为出包
    不调用它。
    """
    doc = _key()
    doc["runtime_assets"] = deepcopy(RUNTIME_ASSETS)
    result, script, _ = _assemble(tmp_path, doc)
    assert result.returncode == 0, result.stderr
    text = script.read_text(encoding="utf-8-sig")
    assert "Copy-RuntimeAsset" in text
    # 仓库源那一条按仓库相对路径拷。
    assert "-Source 'src/app/assets'" in text
    # 包内数据那一条从编译解释器解析，且只取点名的成员——整包点名会把代码当数据发出去。
    assert "-SourcePackage 'rapidocr_onnxruntime'" in text
    assert "-Members @('config.yaml', 'models')" in text
    assert any("Stage runtime assets" in step for step in _steps(script))


def test_runtime_assets_land_beside_the_compiled_backend_by_default(tmp_path):
    """守：落点默认与编译产物平级。

    运行时按「exe 的上一层」找这棵树，所以这个默认值不是随便挑的：改了它，装出来的包里
    文件都在、程序却找不到，而构建每一步都是绿的。
    """
    doc = _key()
    doc["runtime_assets"] = deepcopy(RUNTIME_ASSETS)
    _, script, _ = _assemble(tmp_path, doc)
    assert "python-runtime/runtime-assets/app/assets" in script.read_text(encoding="utf-8-sig")


def test_runtime_assets_are_staged_between_fetching_and_checking(tmp_path):
    """守：顺序，抓 → 落地 → 核对。

    runtime_ready 里的三个钩子不在同一个时刻：`runtime_prepare` 是抓（造嵌入式解释器、
    按清单下载资源），`asset_parity` 与 `credential_proof` 是核对抓完的结果。技能落地
    随包资产属于「抓」的最后一步。

    排错了会怎样，是实测出来的：这一步曾经排在核对之后，于是小刺猬的 BGM 下载成功、
    asset_parity 却报 bgm_manifest.json 缺失——那份 manifest 正是由这一步从仓库拷过去的。
    排到抓之前也不行：抓下来的东西会盖在半棵树上。
    """
    doc = _key()
    doc["runtime_assets"] = deepcopy(RUNTIME_ASSETS)
    doc["build_hooks"] = dict(doc.get("build_hooks") or {})
    doc["build_hooks"]["runtime_prepare"] = ["python", "scripts/prepare.py"]
    doc["build_hooks"]["asset_parity"] = ["python", "scripts/parity.py"]
    _, script, _ = _assemble(tmp_path, doc)
    steps = _steps(script)
    prepare = next(i for i, s in enumerate(steps) if "Prepare runtime" in s)
    stage = next(i for i, s in enumerate(steps) if "Stage runtime assets" in s)
    check = next(i for i, s in enumerate(steps) if "Check runtime assets" in s)
    compiled = next(i for i, s in enumerate(steps) if "Compile Python backend" in s)
    assert prepare < stage < check < compiled, steps


def test_a_key_that_declares_no_runtime_assets_has_no_such_step(tmp_path):
    """守：不声明就没有这一步。引擎跳过，不报错，也不假装做过。"""
    doc = _key()
    doc.pop("runtime_assets", None)
    _, script, _ = _assemble(tmp_path, doc)
    # 函数定义住在模板里，恒在；判的是有没有人调用它。
    assert "Copy-RuntimeAsset -Label" not in script.read_text(encoding="utf-8-sig")
    assert not any("Stage runtime assets" in step for step in _steps(script))


def test_a_runtime_asset_whose_repo_source_is_missing_is_caught_before_the_build(tmp_path):
    """守：仓库里那一份源不在，秒级判得出来，不必等四十分钟编译之后。

    包内数据那一种判不了——源在构建机的编译环境里，这台机器上没有它。那一条由构建时
    当场 fail-loud，不在这里假装检查过。
    """
    doc = _key()
    doc["runtime_assets"] = {"entries": [{"source": "src/app/nope", "dest": "app/x"}]}
    adapter = tmp_path / "key.json"
    adapter.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify_key.py"), "--adapter", str(adapter),
         "--repo-root", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert "asset_source_missing" in out.stdout, out.stdout + out.stderr
