"""一个刚长出来的产品，第一把钥匙。

这份测试是「这个技能是通用工具」的判据。它守的不是某个字段，是一条边界：
**加一个产品只需要写 JSON。** 任何一次改动，只要让新产品的第一把钥匙必须指向一份仓库侧
Python 才能过，都会在这里红。

红了不要往下面这把钥匙里加东西——那是把边界往回推。要么让新增的必填项有缺省值，要么让它
可选，要么把它做成技能自己提供的能力。
"""

from copy import deepcopy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "exe-release" / "scripts"
PWSH = shutil.which("pwsh")
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
        "installer_brand": "Newcomer",
        # 有出安装包这一步，就得说它落在哪：技能每次都去那里确认真有一个包，
        # 引擎也按它把包收拢到交付目录。
        "installer_glob": "desktop-newcomer/dist/*-setup.exe",
    },
    "python_backend": {
        "runner": ["uv", "run", "--extra", "newcomer", "python"],
        "output_dir": "${DESKTOP_DIR}/python-runtime/backend",
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
            "args": ["--run-module", "newcomer._build_smoke"],
            "modules": ["fastapi", "newcomer.app"],
        },
    },
    "electron": {},
}


@pytest.mark.skipif(
    os.name != "posix" or not PWSH,
    reason="Generated release behavior needs pwsh and POSIX fixture executables",
)
@pytest.mark.parametrize(
    ("missing_output", "error"),
    [
        pytest.param("backend", "Compiled backend is missing", id="missing-backend"),
        pytest.param("installer", "No installer matched", id="unrelated-exe"),
        pytest.param(None, None, id="declared-outputs"),
    ],
)
def test_generated_release_requires_the_declared_backend_and_installer(
    tmp_path, missing_output, error
):
    key = tmp_path / "newcomer.release-adapter.json"
    key.write_text(json.dumps(MINIMAL_KEY), encoding="utf-8")
    script = tmp_path / "release.ps1"
    context = tmp_path / "release-context.json"

    assembler.assemble(key, tmp_path, script, context)

    # Only the fixture tools are on PATH. The generated script checks pre-created outputs.
    tools = tmp_path / "bin"
    tools.mkdir()
    for name in ("uv", "pnpm"):
        tool = tools / name
        tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)
    source = tmp_path / "src/newcomer/__main__.py"
    source.parent.mkdir(parents=True)
    source.touch()
    dist = tmp_path / "desktop-newcomer/dist"
    (dist / "win-unpacked").mkdir(parents=True)
    (dist / "unrelated.exe").touch()
    if missing_output != "installer":
        (dist / "newcomer-setup.exe").touch()
    backend = tmp_path / "desktop-newcomer/python-runtime/backend/newcomer-backend.exe"
    backend.parent.mkdir(parents=True)
    if missing_output != "backend":
        backend.write_text(
            '#!/bin/sh\n[ "$#" -eq 2 ] && [ "$1" = --run-module ] && '
            '[ "$2" = newcomer._build_smoke ] || exit 1\n'
            'printf "newcomer smoke ran\\n"\n',
            encoding="utf-8",
        )
        backend.chmod(0o755)

    result = subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(script),
         "-ReleaseContextPath", str(context)],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(tools)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    if error:
        assert result.returncode != 0, output
        assert error in output, output
    else:
        assert result.returncode == 0, output
        assert "newcomer smoke ran" in result.stdout


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

    # 对照：声明了钩子，同一个标记就出现。没有这一条，函数改名之后上面那句永远为真。
    hooked = deepcopy(MINIMAL_KEY)
    hooked["build_hooks"] = {"package_integrity": ["true"]}
    key.write_text(json.dumps(hooked), encoding="utf-8")
    assembler.assemble(key, tmp_path, script, context)
    assert "Invoke-ReleaseHook" in script.read_text(encoding="utf-8")


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
    assert "'-m', 'nuitka'" in text


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


def test_a_key_with_an_installer_step_must_say_where_the_installer_lands():
    """「出安装包那一步退了 0」和「真的有一个安装包」是两回事。

    打包工具清理临时文件失败、钩子只走了一半，都能让那一步成功而目录里什么也没有。
    分不开这两件事，下一个发现的人是客户。
    """
    bad = json.loads(json.dumps(MINIMAL_KEY))
    del bad["build_target"]["installer_glob"]
    with pytest.raises(ValidationError, match="installer_glob"):
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
