"""出发前把钥匙对着仓库核一遍。

这一步秒级完成，挡的是「钥匙里写错一个路径，四十分钟编译之后才知道」。
每一条都对应一次真实的浪费，或者一次差点出货的错。
"""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import release_contracts as rc  # noqa: E402
import verify_key as vk  # noqa: E402

from test_minimal_key import MINIMAL_KEY  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    """一个刚好能让 MINIMAL_KEY 全过的仓库。"""
    (tmp_path / "src" / "newcomer").mkdir(parents=True)
    (tmp_path / "src" / "newcomer" / "__main__.py").write_text("", encoding="utf-8")
    (tmp_path / "desktop-newcomer").mkdir()
    return tmp_path


def _verify(doc, repo, name="newcomer.release-adapter.json"):
    manifest = rc.ReleaseAdapterManifest.model_validate(doc)
    return vk.verify(manifest, repo, Path(name))


def test_a_key_that_matches_its_repo_has_nothing_to_say(repo):
    assert _verify(MINIMAL_KEY, repo) == []


def test_a_missing_compile_entrypoint_is_caught_before_the_build(repo):
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["targets"][0]["entrypoint"] = "src/newcomer/nope.py"
    (finding,) = _verify(doc, repo)
    assert finding["name"] == "entrypoint_missing"
    assert finding["tier"] == "P0"


def test_a_missing_data_dir_is_caught_before_the_build(repo):
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["include_data_dirs"] = [
        {"source": "src/newcomer/assets", "dest": "newcomer/assets"}
    ]
    (finding,) = _verify(doc, repo)
    assert finding["name"] == "data_dir_missing"


def test_a_key_pointing_at_another_key_is_caught(repo):
    """真发生过，而且是最贵的一种：日志里每一步都绿。

    stages 与 diagnose 那一段在每把钥匙里几乎一样，所以它是抄的，抄的时候最容易留下
    上一把钥匙的文件名。照那样跑，装配读的是另一把钥匙、出来的是另一个产品的脚本，
    整条新通路一次都没跑到，而没有任何一步报错。
    """
    doc = deepcopy(MINIMAL_KEY)
    doc["stages"][0]["run"][-5] = "release/someone-else.release-adapter.json"
    findings = _verify(doc, repo)
    assert [f["name"] for f in findings] == ["adapter_points_at_another_key"]
    assert "someone-else" in findings[0]["detail"]


def test_a_smoke_that_names_an_exe_nobody_builds_is_caught(repo):
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["smoke"]["exe"] = "not-built.exe"
    (finding,) = _verify(doc, repo)
    assert finding["name"] == "smoke_exe_not_built"


def test_two_targets_writing_one_filename_is_caught(repo):
    """同一个 output_dir 里后编的直接盖掉先编的，而两次编译都报成功。

    少掉的那个 exe 要到 app 起不来才发现，那时包已经装到客户机器上了。
    """
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["targets"].append(
        {
            "name": "newcomer-launcher",
            "exe": "newcomer-backend.exe",
            "entrypoint": "src/newcomer/__main__.py",
        }
    )
    names = [f["name"] for f in _verify(doc, repo)]
    assert "duplicate_output_filename" in names


def test_a_nofollow_that_blocks_a_smoke_module_is_caught(repo):
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["nofollow_imports"] = ["newcomer"]
    names = [f["name"] for f in _verify(doc, repo)]
    assert "nofollow_blocks_smoke_module" in names


def test_the_cli_exits_non_zero_so_the_engine_stops_the_run(repo):
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["icon"] = "src/newcomer/nope.ico"
    key = repo / "newcomer.release-adapter.json"
    key.write_text(json.dumps(doc), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "verify_key.py"),
            "--adapter",
            str(key),
            "--repo-root",
            str(repo),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    # 信封要打在 stdout 上：引擎按信封收 findings，按退出码判成败。
    doc = json.loads(result.stdout)
    assert [f["name"] for f in doc["findings"]] == ["icon_missing"]


def test_every_finding_satisfies_the_finding_contract(repo):
    """引擎按合同 model_validate 每一条 finding。不合规的会被整批丢掉，
    于是钥匙明明是错的，回执里却什么也没有。"""
    doc = deepcopy(MINIMAL_KEY)
    doc["python_backend"]["targets"][0]["entrypoint"] = "src/newcomer/nope.py"
    doc["python_backend"]["smoke"]["exe"] = "not-built.exe"
    findings = _verify(doc, repo)
    assert len(findings) == 2
    for finding in findings:
        rc.ReleaseFinding.model_validate(finding)
