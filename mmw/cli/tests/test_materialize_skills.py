"""技能物化。跑法：uv run --with pytest python -m pytest mmw/cli/tests/test_materialize_skills.py

物化是发布面的最后一道：技能源写对了，这一层错了，各宿主拿到的技能就是错的，
而且技能正文读起来仍然通顺，没有任何运行时报错。

测的是外部可观察的产出：给定一份技能源，各宿主目录里落下什么文本、哪些文件根本
不该出现、以及哪几种输入必须当场失败。不碰模块内部的私有函数。

源目录由这里造，不读仓库里的真货：真技能源随时在改，拿它当预期值就是把测试
绑死在当前内容上。派发动作不在物化这一层，它归 test_host_action.py。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest  # pyright: ignore[reportMissingImports]

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import materialize_skills as ms  # noqa: E402

def 写(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def 假源(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    src = tmp_path / "skills-src"
    写(src / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "派活：跑 `mmw launch worker --scope worktree`。\n\n"
       "见 `/mmw-beta`。\n")
    写(src / "mmw-beta" / "SKILL.md",
       "---\nname: mmw-beta\ndescription: 乙。\n---\n\n乙的正文。\n")
    monkeypatch.setattr(ms, "SKILLS_SRC", src)
    return src


def 物化(host: str, out: Path) -> int:
    return ms.materialize_host(host, out, check=False)


def 读(out: Path, rel: str) -> str:
    return (out / rel).read_text(encoding="utf-8")


# -------------------------------------------------------------- 废弃的标记

@pytest.mark.parametrize("host", ["pi", "claude-code", "codex", "cursor", "grok"])
def test_物化后不留任何未展开的标记(假源: Path, tmp_path: Path, host: str) -> None:
    out = tmp_path / host
    assert 物化(host, out) == 0
    for path in out.rglob("*.md"):
        assert "[[mmw-" not in path.read_text(encoding="utf-8")


# ------------------------------------------------------------------ Codex 专属

def test_codex_把技能引用改成自己的调用写法(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "codex"
    物化("codex", out)
    assert "`$mmw:mmw-beta`" in 读(out, "mmw-alpha/SKILL.md")


def test_别的宿主保留斜杠写法(假源: Path, tmp_path: Path) -> None:
    for host in ("pi", "claude-code", "cursor"):
        out = tmp_path / host
        物化(host, out)
        正文 = 读(out, "mmw-alpha/SKILL.md")
        assert "`/mmw-beta`" in 正文
        assert "$mmw:" not in 正文


# ------------------------------------------------------------------ 必须当场失败


@pytest.mark.parametrize("标记", [
    "[[mmw-launch:worker:worktree]]",    # 派发改成 `mmw launch`，这个写法不再展开
    "[[mmw-require-task-branch]]",       # 同上，正文里已经内联
    "[[mmw-summon:worker:none]]",        # 根本没有过这个标记
])
def test_展不开的标记不许留进产物(假源: Path, tmp_path: Path, 标记: str) -> None:
    # 展不开还照抄进产物，技能正文里就留着一行方括号：读到的 agent 不会报错，
    # 只会当成一句看不懂的话跳过去，那一步就静悄悄地没人做了。
    写(假源 / "mmw-alpha" / "SKILL.md",
       f"---\nname: mmw-alpha\ndescription: 甲。\n---\n\n{标记}\n")
    with pytest.raises(SystemExit):
        物化("pi", tmp_path / "pi")


# -------------------------------------------------------------------- 谁不该进

def test_旧背景材料目录不进任何产物(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-setup" / "legacy.md", "旧材料。\n")
    for host in ("pi", "claude-code", "codex", "cursor", "grok"):
        out = tmp_path / host
        物化(host, out)
        assert not (out / "mmw-setup").exists()


def test_只给人调的技能不进_pi_技能目录但进别的宿主(
    假源: Path, tmp_path: Path
) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\ndisable-model-invocation: true\n---\n\n甲。\n")
    pi = tmp_path / "pi"
    物化("pi", pi)
    assert not (pi / "mmw-alpha").exists()
    cc = tmp_path / "cc"
    物化("claude-code", cc)
    assert (cc / "mmw-alpha" / "SKILL.md").is_file()
    cursor = tmp_path / "cursor"
    物化("cursor", cursor)
    assert (cursor / "mmw-alpha" / "SKILL.md").is_file()


@pytest.mark.parametrize("host", ["pi", "claude-code", "codex"])
def test_argument_hint_在三个宿主的产物里逐字保留(
    假源: Path, tmp_path: Path, host: str
) -> None:
    # 挂标签的技能把范围档和产品名全压在这个字段上。字段被丢掉或改写时，
    # 用户挂的标签不再生效，而技能正文读起来完全正常——没有任何运行时报错。
    # 断言针对 materialize_host：普通技能走的是它，render_pi_prompt 只处理
    # Pi 的用户命令，只覆盖那一条分支会漏掉三个宿主的普通技能产物。
    原句 = 'argument-hint: "[本任务|全量] [产品名；留空自动判定]"'
    写(假源 / "mmw-alpha" / "SKILL.md",
       f"---\nname: mmw-alpha\ndescription: 甲。\n{原句}\n---\n\n甲。\n")
    out = tmp_path / host
    assert 物化(host, out) == 0
    assert 原句 in 读(out, "mmw-alpha/SKILL.md")


def test_二进制文件原样复制(假源: Path, tmp_path: Path) -> None:
    原始 = bytes([0x89, 0x50, 0x4E, 0x47, 0x00, 0xFF, 0xFE])
    (假源 / "mmw-alpha" / "diagram.png").write_bytes(原始)
    out = tmp_path / "pi"
    物化("pi", out)
    assert (out / "mmw-alpha" / "diagram.png").read_bytes() == 原始


# ---------------------------------------------------------------------- check

def test_check_在产物与源一致时是零(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    assert ms.materialize_host("pi", out, check=True) == 0


def test_check_认得出改过的文件(假源: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    (out / "mmw-alpha" / "SKILL.md").write_text("被人手改过。\n", encoding="utf-8")
    assert ms.materialize_host("pi", out, check=True) == 1
    assert "异" in capsys.readouterr().out


def test_check_认得出少掉的文件(假源: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    (out / "mmw-beta" / "SKILL.md").unlink()
    assert ms.materialize_host("pi", out, check=True) == 1
    assert "缺" in capsys.readouterr().out


def test_check_认得出多出来的文件(假源: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    (out / "mmw-alpha" / "多的.md").write_text("不该在这里。\n", encoding="utf-8")
    assert ms.materialize_host("pi", out, check=True) == 1
    assert "多" in capsys.readouterr().out


def test_check_不改动产物(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    改过的 = "被人手改过。\n"
    (out / "mmw-alpha" / "SKILL.md").write_text(改过的, encoding="utf-8")
    ms.materialize_host("pi", out, check=True)
    assert 读(out, "mmw-alpha/SKILL.md") == 改过的


def test_重复物化产出一致(假源: Path, tmp_path: Path) -> None:
    一 = tmp_path / "一"
    二 = tmp_path / "二"
    物化("codex", 一)
    物化("codex", 二)
    甲 = {p.relative_to(一): p.read_bytes() for p in 一.rglob("*") if p.is_file()}
    乙 = {p.relative_to(二): p.read_bytes() for p in 二.rglob("*") if p.is_file()}
    assert 甲 == 乙


# -------------------------------------------------------- Pi 用户命令的内联

def test_用户命令把_reference_接在正文后面(
    假源: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\ndisable-model-invocation: true\n---\n\n"
       "详见 [细则](detail.md)，也见 [上面](SKILL.md)。\n")
    写(假源 / "mmw-alpha" / "detail.md", "细则正文。\n")
    渲染 = ms.render_pi_prompt(假源 / "mmw-alpha")
    # 相对链接在单文件命令里点不动，必须换成方位词。
    assert "[细则](detail.md)" not in 渲染
    assert "“细则” below" in 渲染
    assert "“上面” above" in 渲染
    assert "## detail.md" in 渲染
    assert "细则正文。" in 渲染


def test_用户命令带上_description(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲的说明。\n---\n\n正文。\n")
    渲染 = ms.render_pi_prompt(假源 / "mmw-alpha")
    assert 渲染.startswith("---\n")
    assert json.dumps("甲的说明。", ensure_ascii=False) in 渲染


def test_用户命令缺_description_就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md", "---\nname: mmw-alpha\n---\n\n正文。\n")
    with pytest.raises(SystemExit):
        ms.render_pi_prompt(假源 / "mmw-alpha")


def test_用户命令链到本技能之外就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n见 [别处](../mmw-beta/SKILL.md)。\n")
    with pytest.raises(SystemExit):
        ms.render_pi_prompt(假源 / "mmw-alpha")
