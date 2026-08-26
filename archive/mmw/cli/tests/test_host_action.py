"""宿主动作表。跑法：uv run --with pytest python -m pytest mmw/cli/tests/test_host_action.py

技能正文对五个宿主是同一句 `mmw launch …`，动作由 cli/host-actions.json 在运行期回答。
表缺一条、模板变量少填一个，技能正文都读不出问题：正文里根本没有那段动作。
所以这里测的是表本身站不站得住，和插值有没有把变量全部填掉。

读真表和真 roles.json，不造假货：这一层要保证的就是「当前这份配置」能用。
不断言动作文案，那是散文，改文案不该让测试变红。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest  # pyright: ignore[reportMissingImports]

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import host_action as ha  # pyright: ignore[reportMissingImports]

表 = json.loads(ha.TABLE_PATH.read_text(encoding="utf-8"))
宿主 = sorted(表["launch"].keys())
角色 = sorted(
    (json.loads(ha.ROLES_PATH.read_text(encoding="utf-8")).get("roles") or {}).keys()
)


def 渲染(action: str, host: str, role: str, scope: str) -> str | None:
    """跑不出来就返回 None。有些组合本来就该拒绝，比如 Codex 给只读角色开后台 worktree。"""
    try:
        return ha.render(action, host, role, scope, bare=True)
    except SystemExit:
        return None


# ------------------------------------------------------------ 表本身

@pytest.mark.parametrize("host", 宿主)
@pytest.mark.parametrize("scope", ha.SCOPES)
def test_每个宿主的三种范围都有动作(host: str, scope: str) -> None:
    # 缺一条就是那个宿主在那种范围下没有派发方式，而技能正文不会告诉你这件事。
    assert 表["launch"][host].get(scope), f"launch.{host}.{scope} 是空的"


@pytest.mark.parametrize("host", sorted(表["post_launch_rule"].keys()))
def test_派后规则只挂在表里有动作的宿主上(host: str) -> None:
    assert host in 表["launch"], f"post_launch_rule.{host} 指向一个没有动作的宿主"


@pytest.mark.parametrize("host", sorted(表["resume"].keys()))
def test_续跑通道只声明给表里有动作的宿主(host: str) -> None:
    assert host in 表["launch"], f"resume.{host} 指向一个没有动作的宿主"


@pytest.mark.parametrize("host", sorted(表["resume"].keys()))
def test_续跑的范围名不写错(host: str) -> None:
    for scope in 表["resume"][host]:
        assert scope in ha.SCOPES, f"resume.{host}.{scope} 不是合法范围"


# ------------------------------------------------------------ 插值

@pytest.mark.parametrize("host", 宿主)
@pytest.mark.parametrize("role", 角色)
@pytest.mark.parametrize("scope", ha.SCOPES)
def test_跑得出来的动作里不留没填的变量(host: str, role: str, scope: str) -> None:
    # 加宿主时漏填一个 {model}，动作照样打得出来，agent 会把花括号当字面量读。
    for action in ("launch", "resume"):
        out = 渲染(action, host, role, scope)
        if out is None:
            continue
        assert "{" not in out, f"{action} {host} {role} {scope} 留了没填的变量：{out}"


@pytest.mark.parametrize("host", 宿主)
def test_审查启动组不留没填的变量(host: str) -> None:
    out = 渲染("launch-group", host, "reviewers", "none")
    assert out is not None
    assert "{" not in out


# ------------------------------------------------------------ 拒绝

def test_不认识的宿主当场失败() -> None:
    with pytest.raises(SystemExit):
        ha.render("launch", "nosuchhost", "worker", "none", bare=True)


def test_不在角色表里的角色当场失败() -> None:
    with pytest.raises(SystemExit):
        ha.render("launch", "pi", "nosuchrole", "none", bare=True)


def test_不认识的启动组当场失败() -> None:
    with pytest.raises(SystemExit):
        ha.render("launch-group", "pi", "nosuchgroup", "none", bare=True)


# ------------------------------------------------------------ 退路与输出形状

@pytest.mark.parametrize("host", 宿主)
@pytest.mark.parametrize("scope", ha.SCOPES)
def test_没有续跑通道的组合给退路而不是空手(host: str, scope: str) -> None:
    # 静默给一句空的，调用方会以为原上下文还在。退路必须写明重派要带什么。
    out = 渲染("resume", host, "worker", scope)
    assert out
    if not (表["resume"].get(host) or {}).get(scope):
        assert out.startswith(表["resume_fallback"].split("{")[0])


@pytest.mark.parametrize("host", 宿主)
def test_默认带宿主行_bare_不带(host: str) -> None:
    # 派发出问题时，宿主判定结果要当场可见。
    assert ha.render("launch", host, "reviewer-gpt", "none", bare=False).startswith(
        f"Host: {host}\n"
    )
    assert not ha.render(
        "launch", host, "reviewer-gpt", "none", bare=True
    ).startswith("Host:")
