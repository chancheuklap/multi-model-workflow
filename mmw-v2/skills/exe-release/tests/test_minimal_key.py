"""一个刚长出来的产品，第一把钥匙。

这份测试是「这个技能是通用工具」的判据。它守的不是某个字段，是一条边界：
**加一个产品只需要写 JSON。** 任何一次改动，只要让新产品的第一把钥匙必须指向一份仓库侧
Python 才能过，都会在这里红。

红了不要往下面这把钥匙里加东西——那是把边界往回推。要么让新增的必填项有缺省值，要么让它
可选，要么把它做成技能自己提供的能力。
"""

from copy import deepcopy
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import release_contracts as rc  # noqa: E402
import release_script_assembler as assembler  # noqa: E402

# 一个带 Electron 外壳的 Python 后端产品，第一次出包。
# 这里的每一行都在回答「这个产品是什么样的」——没有一行在配置这个技能怎么运转。
MINIMAL_KEY = {
    "schema_version": "2",
    "product": "newcomer",
    "build_target": {
        "desktop_dir": "desktop-newcomer",
        "runtime_lane": "embedded_python",
        "entry_module": "newcomer",
        "installer_brand": "Newcomer",
        # 有出安装包这一步，就得说它落在哪：技能每次都去那里确认真有一个包，
        # 引擎也按它把包收拢到交付目录。
        "installer_glob": "desktop-newcomer/dist/*-setup.exe",
    },
    "toolchain": ["python", "pnpm", "node", "uv"],
    "python_backend": {
        "runner": ["uv", "run", "--extra", "newcomer", "python"],
        "output_dir": "${DESKTOP_DIR}/python-runtime/backend",
        "output_mode": "onefile",
        "jobs": {"default": 10},
        "include_packages": ["newcomer"],
        "include_package_data": ["newcomer"],
        "targets": [
            {
                "name": "newcomer-backend",
                "exe": "newcomer-backend.exe",
                "entrypoint": "src/newcomer/__main__.py",
            }
        ],
        "smoke": {
            "exe": "newcomer-backend.exe",
            "run_module": "newcomer._build_smoke",
            "modules": ["fastapi", "newcomer.app"],
        },
    },
    "electron": {},
    "stages": [
        {
            "name": "assemble",
            "run": [
                "uv",
                "run",
                "python",
                "${RELEASE_PLUGIN_DIR}/release_script_assembler.py",
                "assemble",
                "--adapter",
                "release/newcomer.release-adapter.json",
                "--repo-root",
                ".",
                "--output",
                "${RELEASE_LOOP_DIR}/release.ps1",
                "--context-output",
                "${RELEASE_LOOP_DIR}/release-context.json",
            ],
        },
        {
            "name": "build",
            "run": [
                "mmw-release-remote-build",
                "--script",
                "${RELEASE_LOOP_DIR}/release.ps1",
                "--context",
                "${RELEASE_LOOP_DIR}/release-context.json",
            ],
        },
    ],
    "diagnose": [
        "uv",
        "run",
        "python",
        "${RELEASE_PLUGIN_DIR}/diagnose_core.py",
        "--adapter",
        "release/newcomer.release-adapter.json",
    ],
    "build_hooks": {},
}


def test_a_brand_new_product_ships_on_json_alone():
    """这把钥匙里没有一条 argv 指向产品仓库自己的脚本。

    指向技能的（${RELEASE_PLUGIN_DIR}/…）不算：那是技能提供的能力，不是叫人再写一份。
    """
    manifest = rc.ReleaseAdapterManifest.model_validate(MINIMAL_KEY)
    assert manifest.product == "newcomer"

    repo_scripts = [
        token
        for value in MINIMAL_KEY.values()
        for argv in (value if isinstance(value, list) else [])
        for token in (argv["run"] if isinstance(argv, dict) else [argv])
        if isinstance(token, str)
        and token.endswith(".py")
        and not token.startswith("${RELEASE_PLUGIN_DIR}")
    ]
    assert repo_scripts == [], f"第一把钥匙就要求仓库先写 Python: {repo_scripts}"


def test_it_assembles_into_a_build_that_goes_all_the_way_to_an_installer(tmp_path):
    key = tmp_path / "newcomer.release-adapter.json"
    key.write_text(json.dumps(MINIMAL_KEY), encoding="utf-8")
    script = tmp_path / "release.ps1"
    context = tmp_path / "release-context.json"

    assembler.assemble(key, tmp_path, script, context)
    assembler.check(script, context)

    titles = [
        step["title"]
        for step in json.loads(context.read_text(encoding="utf-8"))["render_metadata"][
            "steps"
        ]
    ]
    assert titles == [
        "Validate prerequisites",
        "Install frontend dependencies",
        "Compile Python backend",
        "Verify compiled backend",
        "Build Electron application",
        "Build win-unpacked",
        "Scan release artifacts",
        "Build installer",
        "Verify package integrity",
    ]


def test_the_key_carries_no_hook_and_the_script_calls_none(tmp_path):
    """钩子是「这个产品在这一刻要做的事」。它一件都没有，脚本里就不该有一次回调。

    强制声明只会逼出一条什么也不做的命令，那比不声明更糟：它看着配好了。
    """
    key = tmp_path / "k.json"
    key.write_text(json.dumps(MINIMAL_KEY), encoding="utf-8")
    script = tmp_path / "release.ps1"
    context = tmp_path / "ctx.json"
    assembler.assemble(key, tmp_path, script, context)

    # 连辅助函数都不该生成：生成出来的脚本里躺着一段谁也不调用的钩子机器，
    # 读脚本的人会以为这里配了钩子。
    assert "Invoke-ReleaseHook" not in script.read_text(encoding="utf-8")
    assert json.loads(context.read_text(encoding="utf-8"))["render_metadata"][
        "hook_calls"
    ] == []


@pytest.mark.parametrize(
    "field",
    [
        "fix_executor",
        "editable_paths",
        "protection_source",
        "post_fix_gate",
        "derive",
        "event_sink",
        "build_machine",
        "diagnose_branches",
        "diagnose_rules",
    ],
)
def test_the_self_heal_equipment_is_all_optional(field):
    """自愈与观测那一套，一个产品第一次出包时一件都没有。

    每一件都对应一份仓库侧 Python 或一份仓库侧配置。把它们设成必填，等于要求
    「能出包」之前先写四五份脚本——而这个技能存在的全部理由就是不必再写那些。
    """
    assert field not in MINIMAL_KEY and field not in MINIMAL_KEY["build_target"]
    rc.ReleaseAdapterManifest.model_validate(MINIMAL_KEY)


def test_a_product_without_an_electron_shell_also_assembles(tmp_path):
    """纯后端产品：没有前端，也就没有 desktop_dir、没有装依赖、没有打壳、没有安装包步。"""
    bare = json.loads(json.dumps(MINIMAL_KEY))
    del bare["electron"]
    del bare["build_target"]["desktop_dir"]
    del bare["build_target"]["installer_glob"]
    bare["python_backend"]["output_dir"] = "build/backend"
    bare["toolchain"] = ["python", "uv"]

    key = tmp_path / "k.json"
    key.write_text(json.dumps(bare), encoding="utf-8")
    script = tmp_path / "release.ps1"
    context = tmp_path / "ctx.json"
    assembler.assemble(key, tmp_path, script, context)
    assembler.check(script, context)

    text = script.read_text(encoding="utf-8")
    assert "$DesktopDir" not in text, "没有外壳却造出了 $DesktopDir，它指向不存在的目录"
    titles = [
        step["title"]
        for step in json.loads(context.read_text(encoding="utf-8"))["render_metadata"][
            "steps"
        ]
    ]
    assert titles == [
        "Validate prerequisites",
        "Compile Python backend",
        "Verify compiled backend",
        # 没有外壳、没有安装包，源码泄漏这一条照样查：它查的是编译产物的目录。
        "Scan release artifacts",
    ]


def test_the_generated_script_is_the_only_thing_the_build_machine_needs(tmp_path):
    """构建机上只有 release.ps1 和它的 context，技能的 Python 不在那里。

    所以编译命令必须已经烤成字面量。脚本里出现对技能脚本的调用，就意味着构建机上
    要有这个技能——那条依赖在远端一次也不成立。
    """
    key = tmp_path / "k.json"
    key.write_text(json.dumps(MINIMAL_KEY), encoding="utf-8")
    script = tmp_path / "release.ps1"
    assembler.assemble(key, tmp_path, script, tmp_path / "ctx.json")

    text = script.read_text(encoding="utf-8")
    assert "RELEASE_PLUGIN_DIR" not in text
    assert "release_script_assembler" not in text
    assert "-m', 'nuitka'" in text or "'-m', 'nuitka'" in text


def test_validate_manifest_cli_accepts_it(tmp_path):
    """引擎 init 走的是这条 CLI，不是 import。"""
    key = tmp_path / "k.json"
    key.write_text(json.dumps(MINIMAL_KEY), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release_contracts.py"), "validate-manifest", str(key)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_skill_scans_for_shipped_source_without_being_asked(tmp_path):
    """扫源码泄漏不是产品可选的检查。

    编译这一整套动作的目的就是不发源码；发出去了，这个产品的商业前提当场没了。而它不像
    崩溃那样会自己暴露——包能装、能用，源码就在里面躺着。所以钥匙里一个字都不用写：
    源码根从编译入口推，扫的树就是打包产物的树。
    """
    key = tmp_path / "k.json"
    key.write_text(json.dumps(MINIMAL_KEY), encoding="utf-8")
    script = tmp_path / "release.ps1"
    assembler.assemble(key, tmp_path, script, tmp_path / "ctx.json")

    text = script.read_text(encoding="utf-8")
    assert "Assert-NoBusinessSource" in text
    assert "-SourceRoots @('src')" in text, "源码根要从编译入口推出来"
    assert "Assert-InstallerProduced" in text


def test_a_key_with_an_installer_step_must_say_where_the_installer_lands():
    """「出安装包那一步退了 0」和「真的有一个安装包」是两回事。

    打包工具清理临时文件失败、钩子只走了一半，都能让那一步成功而目录里什么也没有。
    分不开这两件事，下一个发现的人是客户。
    """
    bad = json.loads(json.dumps(MINIMAL_KEY))
    del bad["build_target"]["installer_glob"]
    with pytest.raises(Exception, match="installer_glob"):
        rc.ReleaseAdapterManifest.model_validate(bad)


def test_third_party_packages_in_the_key_are_not_mistaken_for_business_source(tmp_path):
    """真发生过，而且卡住了一次正式出包。

    include_packages 里混着第三方依赖（一把真钥匙里 hedgehog 跟 moderngl、glcontext 并排）。
    照它扫，嵌入式运行时里合法的 moderngl/__init__.py 会被判成源码泄漏，出包停在一个
    不存在的问题上。业务代码的定义只有一个可靠来源：这个仓库源码根下面有什么。
    """
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["include_packages"] = ["newcomer", "moderngl", "glcontext"]
    key = tmp_path / "k.json"
    key.write_text(json.dumps(doc), encoding="utf-8")
    script = tmp_path / "release.ps1"
    assembler.assemble(key, tmp_path, script, tmp_path / "ctx.json")

    scan = next(
        line for line in script.read_text(encoding="utf-8").splitlines()
        if "Assert-NoBusinessSource -Roots" in line
    )
    assert "moderngl" not in scan and "glcontext" not in scan
    assert "-SourceRoots @('src')" in scan
