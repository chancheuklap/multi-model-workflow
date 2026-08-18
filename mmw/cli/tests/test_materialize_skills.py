"""技能物化。跑法：uv run --with pytest python -m pytest mmw/cli/tests/test_materialize_skills.py

物化是发布面的最后一道：技能源写对了，这一层错了，各宿主拿到的技能就是错的，
而且技能正文读起来仍然通顺，没有任何运行时报错。

测的是外部可观察的产出：给定一份技能源，各宿主目录里落下什么文本、哪些文件根本
不该出现、以及哪几种输入必须当场失败。不碰模块内部的私有函数。

源目录、角色表和 Codex profile 都由这里造，不读仓库里的真货：真技能源随时在改，
拿它当预期值就是把测试绑死在当前内容上。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest  # pyright: ignore[reportMissingImports]

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import materialize_skills as ms  # noqa: E402

角色表 = {
    "worker": "mmw-worker",
    "worker-high-risk": "mmw-worker",
    "planner": "mmw-planner",
    "reviewer-gpt": "mmw-reviewer-gpt",
    "reviewer-claude": "mmw-reviewer-claude",
}

CODEX_PROFILE = {
    "subagents": {
        "worker": {"name": "mmw-worker"},
        "reviewer-gpt": {"name": "mmw-reviewer-gpt"},
    },
    "background_roles": {
        "worker": {"model": "gpt-x", "thinking": "high", "method_skill": "mmw:mmw-tdd"},
        "worker-high-risk": {
            "model": "gpt-x",
            "thinking": "high",
            "method_skill": "mmw:mmw-tdd",
        },
    },
}


def 写(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def 假源(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    src = tmp_path / "skills-src"
    写(src / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "派活：[[mmw-launch:worker:worktree]]\n\n"
       "见 `/mmw-beta`。\n")
    写(src / "mmw-beta" / "SKILL.md",
       "---\nname: mmw-beta\ndescription: 乙。\n---\n\n乙的正文。\n")
    monkeypatch.setattr(ms, "SKILLS_SRC", src)
    return src


def 物化(host: str, out: Path) -> int:
    return ms.materialize_host(host, out, 角色表, CODEX_PROFILE, check=False)


def 读(out: Path, rel: str) -> str:
    return (out / rel).read_text(encoding="utf-8")


# ------------------------------------------------------------ 占位符整块替换

@pytest.mark.parametrize("host", ["pi", "claude-code", "codex", "cursor", "grok"])
def test_物化后不留任何未展开的标记(假源: Path, tmp_path: Path, host: str) -> None:
    out = tmp_path / host
    assert 物化(host, out) == 0
    for path in out.rglob("*.md"):
        assert "[[mmw-" not in path.read_text(encoding="utf-8")


def test_四个宿主对同一个占位符给出各自的动作(假源: Path, tmp_path: Path) -> None:
    产出 = {}
    for host in ("pi", "claude-code", "codex", "cursor"):
        out = tmp_path / host
        物化(host, out)
        产出[host] = 读(out, "mmw-alpha/SKILL.md")
    # Pi 直接调原生 subagent，Claude Code 走 mmw dispatch，Codex 开后台 worktree 任务，
    # Cursor 结果树走隔离包装 mmw-cursor-agent。
    assert "native `subagent` tool" in 产出["pi"]
    assert "mmw dispatch worker" in 产出["claude-code"]
    assert "create_thread" in 产出["codex"]
    assert "mmw-cursor-agent" in 产出["cursor"]
    assert "mmw task new" not in 产出["cursor"]
    assert len({产出["pi"], 产出["claude-code"], 产出["codex"], 产出["cursor"]}) == 4


@pytest.mark.parametrize(
    ("host", "启动命令"),
    [
        ("pi", "mmw worktree add <result branch>"),
        ("claude-code", "mmw worktree add <result branch>"),
        ("codex", "create_thread"),
        ("cursor", "mmw-cursor-agent"),
    ],
)
def test_worktree_模式不认领(
    假源: Path, tmp_path: Path, host: str, 启动命令: str
) -> None:
    out = tmp_path / host
    物化(host, out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert 启动命令 in 正文
    assert "mmw task" not in 正文
    assert "task bind" not in 正文
    assert "task new --name" not in 正文


def test_none_模式不提工作目录(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-launch:worker:none]]\n")
    out = tmp_path / "pi"
    物化("pi", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "mmw worktree add" not in 正文
    assert "cwd" not in 正文


def test_current_模式用当前任务_worktree(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-launch:worker:current]]\n")
    out = tmp_path / "pi"
    物化("pi", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "mmw worktree add" not in 正文
    assert "current worktree" in 正文


def test_cursor_current_模式不创建结果树(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "[[mmw-launch:planner:current]]\n")
    out = tmp_path / "cursor"
    物化("cursor", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "mmw-cursor-agent" not in 正文
    assert "--worktree" not in 正文
    assert "native Task tool" in 正文
    assert "does not open a result tree" in 正文
    assert "mmw task state" not in 正文


def test_require_task_branch_各宿主相同(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-require-task-branch]]\n")
    产出 = {}
    for host in ("pi", "claude-code", "codex", "cursor", "grok"):
        out = tmp_path / host
        物化(host, out)
        产出[host] = 读(out, "mmw-alpha/SKILL.md")
        文本 = 产出[host]
        assert "[[mmw-require-task-branch]]" not in 文本
        assert "git switch -c" in 文本
        assert "mmw task" not in 文本
        assert "open a worktree with this host" in 文本
    assert len(set(产出.values())) == 1


@pytest.mark.parametrize("cwd_mode", ["worktree", "current", "none"])
def test_claude_各工作目录模式直接从标准输入接收四栏_task(
    假源: Path, tmp_path: Path, cwd_mode: str
) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       f"[[mmw-launch:worker:{cwd_mode}]]\n")
    out = tmp_path / "claude-code"
    物化("claude-code", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "standard input" in 正文
    assert "write the task to a file" not in 正文
    assert "--task " not in 正文
    assert "--task-text" not in 正文
    assert (
        "Add `--issue <current decision ticket number>` when this task belongs to a "
        "decision ticket"
    ) in 正文


def test_claude_审查启动组直接从标准输入接收四栏_task(
    假源: Path, tmp_path: Path
) -> None:
    正文 = 审查组("claude-code", 假源, tmp_path)
    assert "standard input" in 正文
    assert "write the task to a file" not in 正文
    assert "--task " not in 正文
    assert "--task-text" not in 正文
    assert (
        "Add `--issue <current decision ticket number>` when this task belongs to a "
        "decision ticket"
    ) in 正文


# ---------------------------------------------------------------- 审查启动组

def 审查组(host: str, 假源: Path, tmp_path: Path) -> str:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "[[mmw-launch-group:reviewers:none]]\n")
    out = tmp_path / host
    物化(host, out)
    return 读(out, "mmw-alpha/SKILL.md")


def test_resume_只在已验证通道的宿主给出恢复动作(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-resume:worker:worktree]]\n")
    产出 = {}
    for host in ("pi", "claude-code", "codex", "cursor"):
        out = tmp_path / host
        物化(host, out)
        产出[host] = 读(out, "mmw-alpha/SKILL.md")
    assert "mmw dispatch worker" in 产出["claude-code"]
    assert "--resume" in 产出["claude-code"]
    # 修复 task 走标准输入，不落盘：`--task` 这个参数在升级后的接口里已经没有了，
    # 物化产物里出现它就是在教主 agent 去调一个不存在的参数。
    assert "--task " not in 产出["claude-code"]
    assert "standard input" in 产出["claude-code"]
    assert "mmw-cursor-agent --resume" in 产出["cursor"]
    assert "standard input" in 产出["cursor"]
    # 没验证过续跑通道的宿主给显式退路，不静默降级。
    for host in ("pi", "codex"):
        assert "--resume" not in 产出[host]
        assert "re-dispatch a new instance" in 产出[host]
        assert "the original report in full" in 产出[host]


def test_resume_的_cwd_模式落进恢复指令(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "[[mmw-resume:worker:worktree]]\n\n[[mmw-resume:worker:current]]\n\n"
       "[[mmw-resume:reviewer-gpt:none]]\n")
    out = tmp_path / "claude-code"
    物化("claude-code", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "original result worktree absolute path" in 正文
    assert "current task worktree absolute path" in 正文
    assert "mmw dispatch reviewer-gpt" in 正文


def test_resume_点了不存在的角色就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-resume:nobody:none]]\n")
    with pytest.raises(SystemExit):
        物化("claude-code", tmp_path / "claude-code")


@pytest.mark.parametrize("host", ["pi", "claude-code", "codex", "cursor"])
def test_每一道审都在启动组里有交代(假源: Path, tmp_path: Path, host: str) -> None:
    # 少写哪一道，主 agent 走到那一道就没有可执行的启动句，只能自己编一个。
    正文 = 审查组(host, 假源, tmp_path)
    for 哪一道 in ("⓪", "①", "②", "⑤"):
        assert 哪一道 in 正文


@pytest.mark.parametrize("host", ["pi", "claude-code", "cursor"])
def test_两个审查角色的宿主让共同理解审换一个模型(
    假源: Path, tmp_path: Path, host: str
) -> None:
    # ⓪ 审的是主 agent 自己问出来的共同理解，同一个模型审不出自己的盲点。
    正文 = 审查组(host, 假源, tmp_path)
    第零道 = 正文.split("①")[0]
    assert "reviewer-gpt" in 第零道
    assert "reviewer-claude" not in 第零道


def test_两个审查角色的宿主不叫主_agent_验证出处(
    假源: Path, tmp_path: Path
) -> None:
    for host in ("pi", "claude-code", "cursor", "grok"):
        正文 = 审查组(host, 假源, tmp_path)
        assert "verify the source" not in 正文
        assert "double-check" not in 正文
        assert "re-run" not in 正文
        assert "dispose as `/mmw-review` specifies" in 正文


def test_只有一个审查角色的宿主说清楚换不了模型(假源: Path, tmp_path: Path) -> None:
    正文 = 审查组("codex", 假源, tmp_path)
    assert "swaps the context, not the model" in 正文


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


def test_只有_codex_在派活后追加不重做规则(
    假源: Path, tmp_path: Path
) -> None:
    # 只有 Codex 的主 agent 会把 subagent 的活再干一遍。别的宿主发这条，等于把被禁的
    # 动作介绍给一个本来不会做它的 agent。
    片段 = "Dispatching hands the task over"
    out = tmp_path / "codex"
    物化("codex", out)
    assert 片段 in 读(out, "mmw-alpha/SKILL.md")
    for host in ("pi", "claude-code", "cursor", "grok"):
        out = tmp_path / host
        物化(host, out)
        assert 片段 not in 读(out, "mmw-alpha/SKILL.md")


@pytest.mark.parametrize("role", ["worker", "worker-high-risk"])
def test_codex_后台_worktree_任务不认领(
    假源: Path, tmp_path: Path, role: str
) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       f"[[mmw-launch:{role}:worktree]]\n")
    out = tmp_path / "codex"
    物化("codex", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "create_thread" in 正文
    assert "mmw task" not in 正文
    assert "第四字段" not in 正文
    assert (
        "the four-field task, the full result-branch name, and the base SHA at "
        "dispatch time"
    ) in 正文


# ------------------------------------------------------------------ 必须当场失败

def test_占位符点了一个不存在的角色就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-launch:nobody:none]]\n")
    with pytest.raises(SystemExit):
        物化("pi", tmp_path / "pi")


@pytest.mark.parametrize("标记", [
    "[[mmw-launch:worker:somewhere]]",   # 工作目录模式只认三种，第四种展不开
    "[[mmw-launch:worker]]",             # 少一段
    "[[mmw-summon:worker:none]]",        # 根本不是这两个动作块
])
def test_展不开的标记不许留进产物(假源: Path, tmp_path: Path, 标记: str) -> None:
    # 展不开还照抄进产物，技能正文里就留着一行方括号：读到的 agent 不会报错，
    # 只会当成一句看不懂的话跳过去，那一步就静悄悄地没人做了。
    写(假源 / "mmw-alpha" / "SKILL.md",
       f"---\nname: mmw-alpha\ndescription: 甲。\n---\n\n{标记}\n")
    with pytest.raises(SystemExit):
        物化("pi", tmp_path / "pi")


def test_不认识的启动组就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-launch-group:nosuch:none]]\n")
    with pytest.raises(SystemExit):
        物化("pi", tmp_path / "pi")


def test_codex_缺后台_profile_就退出(假源: Path, tmp_path: Path) -> None:
    没有后台角色 = {"subagents": CODEX_PROFILE["subagents"], "background_roles": {}}
    with pytest.raises(SystemExit):
        ms.materialize_host("codex", tmp_path / "codex", 角色表, 没有后台角色, check=False)


def test_审查组两个角色缺一个就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-launch-group:reviewers:none]]\n")
    只有一个 = {"worker": "mmw-worker", "reviewer-gpt": "mmw-reviewer-gpt"}
    with pytest.raises(SystemExit):
        ms.materialize_host("pi", tmp_path / "pi", 只有一个, CODEX_PROFILE, check=False)


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


def test_grok_worktree_含隔离不含认领(
    假源: Path, tmp_path: Path
) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "[[mmw-launch:worker:worktree]]\n")
    out = tmp_path / "grok"
    物化("grok", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "mmw task" not in 正文
    assert "worktree isolation" in 正文
    assert "mmw dispatch" not in 正文
    assert "grok -p" not in 正文
    assert "工人" not in 正文
    assert "The worker completes the work and commits" in 正文


def test_grok_none_与_current_不含_task_new(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n"
       "[[mmw-launch:worker:none]]\n[[mmw-launch:worker:current]]\n")
    out = tmp_path / "grok"
    物化("grok", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "mmw task" not in 正文
    assert "native subagent tool" in 正文
    assert "current worktree" in 正文


def test_grok_resume_含续跑(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n[[mmw-resume:worker:worktree]]\n")
    out = tmp_path / "grok"
    物化("grok", out)
    正文 = 读(out, "mmw-alpha/SKILL.md")
    assert "resume_from" in 正文
    assert "grok --resume" in 正文


def test_grok_审查组双角色(假源: Path, tmp_path: Path) -> None:
    正文 = 审查组("grok", 假源, tmp_path)
    assert "reviewer-gpt" in 正文
    assert "reviewer-claude" in 正文
    assert "swaps the context, not the model" not in 正文


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
    assert ms.materialize_host("pi", out, 角色表, CODEX_PROFILE, check=True) == 0


def test_check_认得出改过的文件(假源: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    (out / "mmw-alpha" / "SKILL.md").write_text("被人手改过。\n", encoding="utf-8")
    assert ms.materialize_host("pi", out, 角色表, CODEX_PROFILE, check=True) == 1
    assert "异" in capsys.readouterr().out


def test_check_认得出少掉的文件(假源: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    (out / "mmw-beta" / "SKILL.md").unlink()
    assert ms.materialize_host("pi", out, 角色表, CODEX_PROFILE, check=True) == 1
    assert "缺" in capsys.readouterr().out


def test_check_认得出多出来的文件(假源: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    (out / "mmw-alpha" / "多的.md").write_text("不该在这里。\n", encoding="utf-8")
    assert ms.materialize_host("pi", out, 角色表, CODEX_PROFILE, check=True) == 1
    assert "多" in capsys.readouterr().out


def test_check_不改动产物(假源: Path, tmp_path: Path) -> None:
    out = tmp_path / "pi"
    物化("pi", out)
    改过的 = "被人手改过。\n"
    (out / "mmw-alpha" / "SKILL.md").write_text(改过的, encoding="utf-8")
    ms.materialize_host("pi", out, 角色表, CODEX_PROFILE, check=True)
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


def test_用户命令展开_require_task_branch(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\ndisable-model-invocation: true\n---\n\n"
       "建树：[[mmw-require-task-branch]] 重新运行。\n")
    渲染 = ms.render_pi_prompt(假源 / "mmw-alpha", 角色表, CODEX_PROFILE)
    assert "[[mmw-require-task-branch]]" not in 渲染
    assert "git switch -c" in 渲染
    assert "mmw task" not in 渲染


def test_用户命令缺_description_就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md", "---\nname: mmw-alpha\n---\n\n正文。\n")
    with pytest.raises(SystemExit):
        ms.render_pi_prompt(假源 / "mmw-alpha")


def test_用户命令链到本技能之外就退出(假源: Path, tmp_path: Path) -> None:
    写(假源 / "mmw-alpha" / "SKILL.md",
       "---\nname: mmw-alpha\ndescription: 甲。\n---\n\n见 [别处](../mmw-beta/SKILL.md)。\n")
    with pytest.raises(SystemExit):
        ms.render_pi_prompt(假源 / "mmw-alpha")
