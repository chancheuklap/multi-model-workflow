"""角色物化。跑法：uv run --with pytest python -m pytest mmw/cli/tests/test_materialize_agents.py

把角色真源与模型档物化成 Pi、Cursor 的原生 subagent 文件。这一层错了，宿主照样
把 subagent 启起来，只是它拿着错的模型、错的工具集在干活——没有任何报错。

最该守住的三条：
  只读角色绝不能拿到可写工具集；
  清理只删自己管的文件，用户放在同一个目录里的东西不动；
  模型档的 hosts 覆盖按字段生效，覆盖了 effort 不该把 family 和 id 一起换掉。

profile、角色表、body 和模型档全部由这里造，不读仓库里的真货。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest  # pyright: ignore[reportMissingImports]

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import materialize_agents as ma  # noqa: E402


PROFILE = {
    "host": "testhost",
    "managed_glob": "mmw-*.md",
    "model_format": "{provider}/{id}[effort={effort}]",
    "provider_map": {"gpt": "openai", "claude": "anthropic"},
    "tools": {"writable": "读, 写, 跑命令", "readonly": "读"},
    "frontmatter": {
        "name": "{agent}",
        "description": "{description}",
        "model": "{model}",
        "tools": "{tools}",
        "readonly": "{readonly}",
        "skills": "{skill}",
    },
    "output": {"kind": "package-dir", "path": "unused"},
}

ROLES = {
    "worker": {
        "agent": "mmw-worker",
        "description": "按 plan 写代码",
        "writable": True,
        "body": "worker.md",
        "skill": "mmw-tdd",
    },
    "investigator": {
        "agent": "mmw-investigator",
        "description": "查事实，带出处",
        "writable": False,
        "body": "investigator.md",
    },
}

CONFIG = {
    "models": {
        "worker": {"family": "gpt", "id": "gpt-x", "effort": "high"},
        "investigator": {
            "family": "gpt",
            "id": "gpt-x",
            "effort": "medium",
            "hosts": {"testhost": {"effort": "low"}},
        },
    }
}


@pytest.fixture
def 假源(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    profiles = tmp_path / "profiles"
    bodies = tmp_path / "bodies"
    profiles.mkdir()
    bodies.mkdir()
    (profiles / "testhost.json").write_text(
        json.dumps(PROFILE, ensure_ascii=False), encoding="utf-8")
    (bodies / "worker.md").write_text("worker 的方法论。\n", encoding="utf-8")
    (bodies / "investigator.md").write_text("investigator 的方法论。\n", encoding="utf-8")
    monkeypatch.setattr(ma, "PROFILES_DIR", profiles)
    monkeypatch.setattr(ma, "BODIES_DIR", bodies)
    return tmp_path


def 物化(out: Path, roles=None, config=None, *, check=False) -> list[str]:
    return ma.materialize_host(
        "testhost", config or CONFIG, roles or ROLES,
        check_only=check, out_override=str(out))


def 读(out: Path, name: str) -> str:
    return (out / name).read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    块 = text.split("---\n")[1]
    return dict(
        (行.split(": ", 1)[0], 行.split(": ", 1)[1])
        for 行 in 块.strip().split("\n") if ": " in 行
    )


# ------------------------------------------------------------------ 工具集

def test_只读角色拿不到可写工具集(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    只读 = frontmatter(读(out, "mmw-investigator.md"))
    assert 只读["tools"] == "读"
    assert "写" not in 只读["tools"]
    assert 只读["readonly"] == "true"


def test_可写角色拿可写工具集(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    可写 = frontmatter(读(out, "mmw-worker.md"))
    assert 可写["tools"] == "读, 写, 跑命令"
    assert 可写["readonly"] == "false"


def test_profile_缺某一档工具集就退出(假源: Path, tmp_path: Path) -> None:
    残缺 = dict(PROFILE, tools={"readonly": "读"})
    (假源 / "profiles" / "testhost.json").write_text(
        json.dumps(残缺, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit):
        物化(tmp_path / "out")


# -------------------------------------------------------------- 模型档覆盖

def test_宿主覆盖只换被覆盖的那个字段(假源: Path, tmp_path: Path) -> None:
    # investigator 在 testhost 上只覆盖了 effort；family 与 id 必须还是基线那一份。
    out = tmp_path / "out"
    物化(out)
    assert frontmatter(读(out, "mmw-investigator.md"))["model"] == "openai/gpt-x[effort=low]"


def test_没有覆盖的角色用基线(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    assert frontmatter(读(out, "mmw-worker.md"))["model"] == "openai/gpt-x[effort=high]"


def test_别的宿主的覆盖不影响这个宿主(假源: Path, tmp_path: Path) -> None:
    配置 = json.loads(json.dumps(CONFIG))
    配置["models"]["worker"]["hosts"] = {"另一个宿主": {"id": "不该用到的"}}
    out = tmp_path / "out"
    物化(out, config=配置)
    assert "不该用到的" not in 读(out, "mmw-worker.md")


def test_模型档缺字段就退出(假源: Path, tmp_path: Path) -> None:
    配置 = {"models": {"worker": {"family": "gpt", "id": "gpt-x"},
                       "investigator": CONFIG["models"]["investigator"]}}
    with pytest.raises(SystemExit):
        物化(tmp_path / "out", config=配置)


def test_模型档整个少了一个角色就退出(假源: Path, tmp_path: Path) -> None:
    配置 = {"models": {"worker": CONFIG["models"]["worker"]}}
    with pytest.raises(SystemExit):
        物化(tmp_path / "out", config=配置)


def test_空字符串覆盖不算覆盖(假源: Path, tmp_path: Path) -> None:
    # 覆盖字段写成空串是配置写错，不能让它把基线值抹成空。
    配置 = json.loads(json.dumps(CONFIG))
    配置["models"]["worker"]["hosts"] = {"testhost": {"id": ""}}
    out = tmp_path / "out"
    物化(out, config=配置)
    assert "gpt-x" in 读(out, "mmw-worker.md")


# ------------------------------------------------------------------ 清理边界

def test_只清自己管的文件(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "mmw-已经不要了.md").write_text("上一轮留下的\n", encoding="utf-8")
    (out / "用户自己的.md").write_text("别动我\n", encoding="utf-8")
    (out / "notes.txt").write_text("也别动\n", encoding="utf-8")
    物化(out)
    assert not (out / "mmw-已经不要了.md").exists()
    assert 读(out, "用户自己的.md") == "别动我\n"
    assert 读(out, "notes.txt") == "也别动\n"


def test_角色改名后旧文件被清掉(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    assert (out / "mmw-worker.md").is_file()
    改名 = json.loads(json.dumps(ROLES))
    改名["worker"]["agent"] = "mmw-worker-新名"
    物化(out, roles=改名)
    assert not (out / "mmw-worker.md").exists()
    assert (out / "mmw-worker-新名.md").is_file()


def test_不留临时文件(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    assert [p.name for p in out.iterdir() if p.name.startswith(".")] == []


# ------------------------------------------------------------------- check

def test_check_一致时不报漂移(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    报告 = 物化(out, check=True)
    assert all(行.startswith("齐") for 行 in 报告)


def test_check_认得出被改过的文件(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    (out / "mmw-worker.md").write_text("被人手改过\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        物化(out, check=True)


def test_check_认得出少掉的文件(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    (out / "mmw-worker.md").unlink()
    with pytest.raises(SystemExit):
        物化(out, check=True)


def test_check_认得出多出来的文件(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    (out / "mmw-多的.md").write_text("不该在这里\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        物化(out, check=True)


def test_check_不动产物(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    改过的 = "被人手改过\n"
    (out / "mmw-worker.md").write_text(改过的, encoding="utf-8")
    with pytest.raises(SystemExit):
        物化(out, check=True)
    assert 读(out, "mmw-worker.md") == 改过的


def test_check_目录不存在就退出(假源: Path, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        物化(tmp_path / "从来没建过", check=True)


# --------------------------------------------------------- frontmatter 渲染

def test_角色没写_skill_时那个键整个省掉(假源: Path, tmp_path: Path) -> None:
    # 留一个空的 skills: 会让宿主去找一个叫空字符串的技能。
    out = tmp_path / "out"
    物化(out)
    assert "skills:" not in 读(out, "mmw-investigator.md")
    assert "skills: mmw-tdd" in 读(out, "mmw-worker.md")


def test_带冒号的描述会被引起来(假源: Path, tmp_path: Path) -> None:
    角色 = json.loads(json.dumps(ROLES))
    角色["worker"]["description"] = "用途: 写代码"
    out = tmp_path / "out"
    物化(out, roles=角色)
    assert 'description: "用途: 写代码"' in 读(out, "mmw-worker.md")


def test_多行描述用竖线块(假源: Path, tmp_path: Path) -> None:
    角色 = json.loads(json.dumps(ROLES))
    角色["worker"]["description"] = "第一行\n第二行"
    out = tmp_path / "out"
    物化(out, roles=角色)
    正文 = 读(out, "mmw-worker.md")
    assert "description: |" in 正文
    assert "  第一行" in 正文
    assert "  第二行" in 正文


def test_body_原样接在_frontmatter_之后(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    物化(out)
    assert 读(out, "mmw-worker.md").endswith("worker 的方法论。\n")


def test_body_不存在就退出(假源: Path, tmp_path: Path) -> None:
    角色 = json.loads(json.dumps(ROLES))
    角色["worker"]["body"] = "没有这份.md"
    with pytest.raises(SystemExit):
        物化(tmp_path / "out", roles=角色)


def test_profile_的_host_对不上就退出(假源: Path, tmp_path: Path) -> None:
    错的 = dict(PROFILE, host="别的宿主")
    (假源 / "profiles" / "testhost.json").write_text(
        json.dumps(错的, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit):
        物化(tmp_path / "out")


def test_重复物化产出一致(假源: Path, tmp_path: Path) -> None:
    一 = tmp_path / "一"
    二 = tmp_path / "二"
    物化(一)
    物化(二)
    甲 = {p.name: p.read_bytes() for p in 一.iterdir()}
    乙 = {p.name: p.read_bytes() for p in 二.iterdir()}
    assert 甲 == 乙
